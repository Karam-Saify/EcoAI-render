import asyncio
import json
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    id: int
    job_type: str
    entity_type: str
    entity_id: int
    feature_snapshot_id: int | None
    model_name: str
    model_version: str
    feature_schema_version: str


class MLJobOrchestrationService:
    def __init__(self) -> None:
        self._stop_event = asyncio.Event()

    async def run_forever(self) -> None:
        if not settings.ML_WORKER_ENABLED:
            logger.info("ML orchestration worker disabled")
            return

        logger.info(
            "ML orchestration worker started interval=%ss batch_size=%s",
            settings.ML_WORKER_POLL_INTERVAL_SECONDS,
            settings.ML_WORKER_BATCH_SIZE,
        )

        while not self._stop_event.is_set():
            try:
                await asyncio.to_thread(self.run_once)
            except Exception:
                logger.exception("ML orchestration worker loop failed")

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=settings.ML_WORKER_POLL_INTERVAL_SECONDS,
                )
            except asyncio.TimeoutError:
                continue

        logger.info("ML orchestration worker stopped")

    def stop(self) -> None:
        self._stop_event.set()

    def run_once(self) -> int:
        processed = 0
        for _ in range(settings.ML_WORKER_BATCH_SIZE):
            if not self._process_next_job():
                break
            processed += 1
        return processed

    def _process_next_job(self) -> bool:
        session = SessionLocal()
        try:
            job = self._claim_next_job(session)
            if job is None:
                session.commit()
                return False

            try:
                self._execute_job(session, job)
                self._mark_job_succeeded(session, job.id)
            except Exception as exc:
                self._mark_job_failed(session, job.id, str(exc))
                logger.exception("Failed processing ML job %s", job.id)

            session.commit()
            return True
        except Exception:
            session.rollback()
            logger.exception("Unexpected failure while polling ML jobs")
            return False
        finally:
            session.close()

    def _claim_next_job(self, session: Session) -> JobRecord | None:
        row = session.execute(
            text(
                """
                SELECT id, job_type, entity_type, entity_id, feature_snapshot_id,
                       model_name, model_version, feature_schema_version
                FROM ecowise.ml_inference_job
                WHERE job_status IN ('PENDING', 'RETRY_SCHEDULED')
                  AND status_id = 1
                ORDER BY priority ASC, created_on ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """
            )
        ).mappings().first()

        if row is None:
            return None

        session.execute(
            text(
                """
                UPDATE ecowise.ml_inference_job
                SET job_status = 'RUNNING',
                    attempt_count = attempt_count + 1,
                    started_on = NOW(),
                    error_message = '',
                    updated_on = NOW()
                WHERE id = :id
                """
            ),
            {"id": row["id"]},
        )

        return JobRecord(
            id=row["id"],
            job_type=row["job_type"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            feature_snapshot_id=row["feature_snapshot_id"],
            model_name=row["model_name"] or "hybrid-baseline",
            model_version=row["model_version"] or "v1",
            feature_schema_version=row["feature_schema_version"] or "v1",
        )

    def _execute_job(self, session: Session, job: JobRecord) -> None:
        if job.entity_type == "project":
            self._process_project_job(session, job)
            return
        if job.entity_type == "government_issue":
            self._process_government_issue_job(session, job)
            return
        if job.entity_type == "issue_solution":
            self._process_issue_solution_job(session, job)
            return
        raise ValueError(f"Unsupported entity_type {job.entity_type}")

    def _mark_job_succeeded(self, session: Session, job_id: int) -> None:
        session.execute(
            text(
                """
                UPDATE ecowise.ml_inference_job
                SET job_status = 'SUCCEEDED',
                    finished_on = NOW(),
                    error_message = '',
                    updated_on = NOW()
                WHERE id = :job_id
                """
            ),
            {"job_id": job_id},
        )

    def _mark_job_failed(self, session: Session, job_id: int, message: str) -> None:
        session.execute(
            text(
                """
                UPDATE ecowise.ml_inference_job
                SET job_status = 'FAILED',
                    finished_on = NOW(),
                    error_message = :message,
                    updated_on = NOW()
                WHERE id = :job_id
                """
            ),
            {"job_id": job_id, "message": message[:1000]},
        )

    def _fetch_project_source(self, session: Session, project_id: int) -> dict[str, Any] | None:
        row = session.execute(
            text(
                """
                SELECT id, title, summary, description, country, city, target_geography,
                       implementation_needs, partnership_intent, expected_impact_metrics
                FROM ecowise.project
                WHERE id = :project_id
                  AND status_id = 1
                """
            ),
            {"project_id": project_id},
        ).mappings().first()
        if row is None:
            return None
        return {
            **dict(row),
            "text_payload": self._join_text(
                row["title"],
                row["summary"],
                row["description"],
                row["implementation_needs"],
                row["partnership_intent"],
                row["expected_impact_metrics"],
            ),
        }

    def _fetch_project_skills(self, session: Session, project_id: int) -> set[str]:
        rows = session.execute(
            text(
                """
                SELECT LOWER(TRIM(s.name)) AS skill_name
                FROM ecowise.project_required_skill prs
                JOIN ecowise.skill s ON s.id = prs.skill_id
                WHERE prs.project_id = :project_id
                """
            ),
            {"project_id": project_id},
        ).mappings().all()
        return {row["skill_name"] for row in rows if row["skill_name"]}

    def _fetch_project_match_candidates(self, session: Session, project_id: int) -> list[dict[str, Any]]:
        rows = session.execute(
            text(
                """
                WITH skill_rollup AS (
                    SELECT us.user_id,
                           array_remove(array_agg(LOWER(TRIM(s.name))), NULL) AS skills
                    FROM ecowise.user_skill us
                    JOIN ecowise.skill s ON s.id = us.skill_id
                    GROUP BY us.user_id
                )
                SELECT
                    pu.id AS user_id,
                    CASE
                        WHEN op.user_id IS NOT NULL THEN 'ORGANIZATION'
                        WHEN ip.user_id IS NOT NULL THEN 'INDIVIDUAL'
                        ELSE 'USER'
                    END AS matched_entity_type,
                    COALESCE(op.organization_name, CONCAT(ip.first_name, ' ', ip.last_name), pu.email) AS display_name,
                    COALESCE(op.country, ip.country, '') AS country,
                    COALESCE(op.city, ip.city, '') AS city,
                    pu.email_verified,
                    pu.profile_completed,
                    COALESCE(op.verification_status, 0) AS verification_status,
                    COALESCE(op.mission, '') AS mission,
                    COALESCE(op.implementation_capacity, '') AS implementation_capacity,
                    COALESCE(ip.headline, '') AS headline,
                    COALESCE(ip.bio, '') AS bio,
                    COALESCE(sr.skills, ARRAY[]::text[]) AS skills
                FROM ecowise.platform_user pu
                LEFT JOIN ecowise.organization_profile op ON op.user_id = pu.id
                LEFT JOIN ecowise.individual_profile ip ON ip.user_id = pu.id
                LEFT JOIN skill_rollup sr ON sr.user_id = pu.id
                WHERE pu.status_id = 1
                  AND pu.profile_completed = TRUE
                  AND pu.id <> (
                      SELECT owner_user_id
                      FROM ecowise.project
                      WHERE id = :project_id
                  )
                """
            ),
            {"project_id": project_id},
        ).mappings().all()

        candidates = []
        for row in rows:
            text_payload = self._join_text(
                row["display_name"],
                row["mission"],
                row["implementation_capacity"],
                row["headline"],
                row["bio"],
            )
            candidates.append(
                {
                    **dict(row),
                    "skills": {skill for skill in row["skills"] or [] if skill},
                    "text_payload": text_payload,
                }
            )
        return candidates

    def _fetch_government_issue_source(self, session: Session, issue_id: int) -> dict[str, Any] | None:
        row = session.execute(
            text(
                """
                SELECT id, title, summary, description, country, city, target_geography, expected_outcomes
                FROM ecowise.government_issue
                WHERE id = :issue_id
                  AND status_id = 1
                """
            ),
            {"issue_id": issue_id},
        ).mappings().first()
        if row is None:
            return None
        return {
            **dict(row),
            "text_payload": self._join_text(
                row["title"],
                row["summary"],
                row["description"],
                row["expected_outcomes"],
            ),
        }

    def _fetch_issue_solution_candidates(self, session: Session, issue_id: int) -> list[dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT
                    s.id,
                    s.organization_user_id,
                    s.project_id,
                    s.title,
                    s.summary,
                    s.proposal_description,
                    s.implementation_approach,
                    COALESCE((
                        SELECT COUNT(*)
                        FROM ecowise.issue_solution_upvote u
                        WHERE u.solution_id = s.id
                          AND u.status_id = 1
                    ), 0) AS upvote_count,
                    COALESCE((
                        SELECT COUNT(*)
                        FROM ecowise.issue_solution_contributor_interest c
                        WHERE c.solution_id = s.id
                          AND c.status_id = 1
                    ), 0) AS total_interests,
                    COALESCE(p.country, op.country, '') AS country,
                    COALESCE(p.city, op.city, '') AS city
                FROM ecowise.issue_solution s
                LEFT JOIN ecowise.project p ON p.id = s.project_id
                LEFT JOIN ecowise.organization_profile op ON op.user_id = s.organization_user_id
                WHERE s.issue_id = :issue_id
                  AND s.status_id = 1
                """
            ),
            {"issue_id": issue_id},
        ).mappings().all()
        return [
            {
                **dict(row),
                "text_payload": self._join_text(
                    row["title"],
                    row["summary"],
                    row["proposal_description"],
                    row["implementation_approach"],
                ),
            }
            for row in rows
        ]

    def _fetch_issue_solution_source(self, session: Session, solution_id: int) -> dict[str, Any] | None:
        row = session.execute(
            text(
                """
                SELECT id, issue_id, organization_user_id, project_id
                FROM ecowise.issue_solution
                WHERE id = :solution_id
                  AND status_id = 1
                """
            ),
            {"solution_id": solution_id},
        ).mappings().first()
        if row is None:
            return None

        interested_rows = session.execute(
            text(
                """
                SELECT interested_user_id
                FROM ecowise.issue_solution_contributor_interest
                WHERE solution_id = :solution_id
                  AND status_id = 1
                ORDER BY created_on ASC
                """
            ),
            {"solution_id": solution_id},
        ).scalars().all()

        return {
            **dict(row),
            "interested_user_ids": interested_rows,
        }

    def _soft_delete_graph_edges(self, session: Session, entity_type: str, entity_id: int) -> None:
        session.execute(
            text(
                """
                UPDATE ecowise.graph_edge
                SET status_id = -1,
                    updated_on = NOW()
                WHERE source_entity_type = :entity_type
                  AND source_entity_id = :entity_id
                  AND status_id = 1
                """
            ),
            {"entity_type": entity_type, "entity_id": entity_id},
        )

    def _insert_graph_edge(
        self,
        session: Session,
        source_entity_type: str,
        source_entity_id: int,
        target_entity_type: str,
        target_entity_id: int,
        edge_type: str,
        weight: float,
        confidence_score: float,
        rank: int,
        explanation_json: str,
        model_name: str,
        model_version: str,
        inference_job_id: int,
    ) -> None:
        session.execute(
            text(
                """
                INSERT INTO ecowise.graph_edge (
                    source_entity_type, source_entity_id, target_entity_type, target_entity_id,
                    edge_type, weight, confidence_score, rank, explanation_json, model_name,
                    model_version, inference_job_id, status_id
                )
                VALUES (
                    :source_entity_type, :source_entity_id, :target_entity_type, :target_entity_id,
                    :edge_type, :weight, :confidence_score, :rank, :explanation_json, :model_name,
                    :model_version, :inference_job_id, 1
                )
                """
            ),
            {
                "source_entity_type": source_entity_type,
                "source_entity_id": source_entity_id,
                "target_entity_type": target_entity_type,
                "target_entity_id": target_entity_id,
                "edge_type": edge_type,
                "weight": weight,
                "confidence_score": confidence_score,
                "rank": rank,
                "explanation_json": explanation_json,
                "model_name": model_name,
                "model_version": model_version,
                "inference_job_id": inference_job_id,
            },
        )

    def _process_project_job(self, session: Session, job: JobRecord) -> None:
        project = self._fetch_project_source(session, job.entity_id)
        if project is None:
            raise ValueError(f"Project {job.entity_id} not found")

        candidates = self._fetch_project_match_candidates(session, job.entity_id)
        project_skills = self._fetch_project_skills(session, job.entity_id)
        scored = []

        for candidate in candidates:
            skill_score = self._overlap_ratio(project_skills, candidate["skills"])
            geography_score = self._geography_fit(
                project.get("country", ""),
                project.get("city", ""),
                candidate.get("country", ""),
                candidate.get("city", ""),
            )
            text_score = self._text_similarity(project["text_payload"], candidate["text_payload"])
            credibility_score = self._candidate_credibility(candidate)
            user_type = candidate["matched_entity_type"]

            if user_type == "ORGANIZATION":
                total_score = (
                    skill_score * 0.15
                    + geography_score * 0.20
                    + text_score * 0.35
                    + credibility_score * 0.30
                ) * 100
            else:
                total_score = (
                    skill_score * 0.45
                    + geography_score * 0.20
                    + text_score * 0.20
                    + credibility_score * 0.15
                ) * 100

            confidence_score = min(100.0, total_score * 0.9 + (skill_score * 10))
            explanation = {
                "top_factors": self._top_factors(
                    {
                        "skills": skill_score,
                        "geography": geography_score,
                        "profile_text": text_score,
                        "credibility": credibility_score,
                    }
                ),
                "user_type": user_type,
                "candidate_summary": candidate["display_name"],
            }

            scored.append(
                {
                    "matched_user_id": candidate["user_id"],
                    "matched_entity_type": user_type,
                    "total_score": round(total_score, 2),
                    "sector_score": round(text_score * 100, 2),
                    "geography_score": round(geography_score * 100, 2),
                    "skills_score": round(skill_score * 100, 2),
                    "funding_score": None,
                    "credibility_score": round(credibility_score * 100, 2),
                    "confidence_score": round(confidence_score, 2),
                    "explanation_json": json.dumps(explanation),
                    "weight": round(total_score / 100.0, 4),
                    "edge_explanation_json": json.dumps(
                        {
                            "relationship": "project_match",
                            "display_name": candidate["display_name"],
                            "confidence_score": round(confidence_score, 2),
                        }
                    ),
                }
            )

        scored.sort(key=lambda item: item["total_score"], reverse=True)
        ranked = scored[: settings.ML_MAX_MATCH_RESULTS]

        session.execute(
            text(
                """
                UPDATE ecowise.match_result
                SET status_id = -1,
                    updated_on = NOW()
                WHERE project_id = :project_id
                  AND status_id = 1
                """
            ),
            {"project_id": job.entity_id},
        )
        self._soft_delete_graph_edges(session, "project", job.entity_id)

        for rank, match in enumerate(ranked, start=1):
            session.execute(
                text(
                    """
                    INSERT INTO ecowise.match_result (
                        project_id, matched_user_id, matched_entity_type, match_type, rank, total_score,
                        sector_score, geography_score, skills_score, funding_score, credibility_score,
                        confidence_score, explanation_json, feature_schema_version, model_name, model_version,
                        computed_at, expires_at, inference_job_id, status_id
                    )
                    VALUES (
                        :project_id, :matched_user_id, :matched_entity_type, :match_type, :rank, :total_score,
                        :sector_score, :geography_score, :skills_score, :funding_score, :credibility_score,
                        :confidence_score, :explanation_json, :feature_schema_version, :model_name, :model_version,
                        NOW(), NULL, :inference_job_id, 1
                    )
                    """
                ),
                {
                    "project_id": job.entity_id,
                    "matched_user_id": match["matched_user_id"],
                    "matched_entity_type": match["matched_entity_type"],
                    "match_type": "PROJECT_TO_USER",
                    "rank": rank,
                    "total_score": match["total_score"],
                    "sector_score": match["sector_score"],
                    "geography_score": match["geography_score"],
                    "skills_score": match["skills_score"],
                    "funding_score": match["funding_score"],
                    "credibility_score": match["credibility_score"],
                    "confidence_score": match["confidence_score"],
                    "explanation_json": match["explanation_json"],
                    "feature_schema_version": job.feature_schema_version,
                    "model_name": job.model_name,
                    "model_version": job.model_version,
                    "inference_job_id": job.id,
                },
            )

            self._insert_graph_edge(
                session=session,
                source_entity_type="project",
                source_entity_id=job.entity_id,
                target_entity_type="platform_user",
                target_entity_id=match["matched_user_id"],
                edge_type="MATCH_RECOMMENDATION",
                weight=match["weight"],
                confidence_score=match["confidence_score"],
                rank=rank,
                explanation_json=match["edge_explanation_json"],
                model_name=job.model_name,
                model_version=job.model_version,
                inference_job_id=job.id,
            )

    def _process_government_issue_job(self, session: Session, job: JobRecord) -> None:
        issue = self._fetch_government_issue_source(session, job.entity_id)
        if issue is None:
            raise ValueError(f"Government issue {job.entity_id} not found")

        solutions = self._fetch_issue_solution_candidates(session, job.entity_id)
        self._soft_delete_graph_edges(session, "government_issue", job.entity_id)

        scored = []
        for solution in solutions:
            text_score = self._text_similarity(issue["text_payload"], solution["text_payload"])
            geography_score = self._geography_fit(
                issue.get("country", ""),
                issue.get("city", ""),
                solution.get("country", ""),
                solution.get("city", ""),
            )
            traction_score = min(1.0, (solution["upvote_count"] * 0.15) + (solution["total_interests"] * 0.2))
            linked_project_bonus = 0.15 if solution["project_id"] else 0.0
            weight = min(1.0, text_score * 0.45 + geography_score * 0.20 + traction_score * 0.20 + linked_project_bonus)
            confidence = min(100.0, (weight * 100) * 0.92)

            scored.append(
                {
                    "solution_id": solution["id"],
                    "weight": round(weight, 4),
                    "confidence_score": round(confidence, 2),
                    "rank_signal": weight,
                    "explanation_json": json.dumps(
                        {
                            "top_factors": self._top_factors(
                                {
                                    "proposal_text": text_score,
                                    "geography": geography_score,
                                    "community_traction": traction_score,
                                    "linked_project_bonus": linked_project_bonus,
                                }
                            ),
                            "organization_user_id": solution["organization_user_id"],
                        }
                    ),
                }
            )

        scored.sort(key=lambda item: item["rank_signal"], reverse=True)
        for rank, edge in enumerate(scored, start=1):
            self._insert_graph_edge(
                session=session,
                source_entity_type="government_issue",
                source_entity_id=job.entity_id,
                target_entity_type="issue_solution",
                target_entity_id=edge["solution_id"],
                edge_type="ISSUE_TO_SOLUTION",
                weight=edge["weight"],
                confidence_score=edge["confidence_score"],
                rank=rank,
                explanation_json=edge["explanation_json"],
                model_name=job.model_name,
                model_version=job.model_version,
                inference_job_id=job.id,
            )

    def _process_issue_solution_job(self, session: Session, job: JobRecord) -> None:
        solution = self._fetch_issue_solution_source(session, job.entity_id)
        if solution is None:
            raise ValueError(f"Issue solution {job.entity_id} not found")

        self._soft_delete_graph_edges(session, "issue_solution", job.entity_id)

        edges = [
            {
                "target_entity_type": "platform_user",
                "target_entity_id": solution["organization_user_id"],
                "edge_type": "OWNED_BY_ORGANIZATION",
                "weight": 1.0,
                "confidence_score": 100.0,
                "rank": 1,
                "explanation_json": json.dumps({"relationship": "solution_owner"}),
            },
            {
                "target_entity_type": "government_issue",
                "target_entity_id": solution["issue_id"],
                "edge_type": "PROPOSES_FOR_ISSUE",
                "weight": 0.95,
                "confidence_score": 95.0,
                "rank": 2,
                "explanation_json": json.dumps({"relationship": "issue_solution_link"}),
            },
        ]

        if solution["project_id"]:
            edges.append(
                {
                    "target_entity_type": "project",
                    "target_entity_id": solution["project_id"],
                    "edge_type": "BACKED_BY_PROJECT",
                    "weight": 0.90,
                    "confidence_score": 92.0,
                    "rank": 3,
                    "explanation_json": json.dumps({"relationship": "linked_project"}),
                }
            )

        for idx, interested_user_id in enumerate(solution["interested_user_ids"], start=len(edges) + 1):
            edges.append(
                {
                    "target_entity_type": "platform_user",
                    "target_entity_id": interested_user_id,
                    "edge_type": "INTERESTED_CONTRIBUTOR",
                    "weight": 0.70,
                    "confidence_score": 75.0,
                    "rank": idx,
                    "explanation_json": json.dumps({"relationship": "active_interest"}),
                }
            )

        for edge in edges:
            self._insert_graph_edge(
                session=session,
                source_entity_type="issue_solution",
                source_entity_id=job.entity_id,
                target_entity_type=edge["target_entity_type"],
                target_entity_id=edge["target_entity_id"],
                edge_type=edge["edge_type"],
                weight=edge["weight"],
                confidence_score=edge["confidence_score"],
                rank=edge["rank"],
                explanation_json=edge["explanation_json"],
                model_name=job.model_name,
                model_version=job.model_version,
                inference_job_id=job.id,
            )

    def get_status(self) -> dict[str, Any]:
        session = SessionLocal()
        try:
            rows = session.execute(
                text(
                    """
                    SELECT job_status, COUNT(*) AS count
                    FROM ecowise.ml_inference_job
                    GROUP BY job_status
                    """
                )
            ).mappings().all()
            counts = {row["job_status"]: row["count"] for row in rows}
            return {
                "enabled": settings.ML_WORKER_ENABLED,
                "poll_interval_seconds": settings.ML_WORKER_POLL_INTERVAL_SECONDS,
                "batch_size": settings.ML_WORKER_BATCH_SIZE,
                "job_counts": counts,
            }
        finally:
            session.close()

    @staticmethod
    def _join_text(*parts: str) -> str:
        return "\n".join(part.strip() for part in parts if isinstance(part, str) and part.strip())

    @staticmethod
    def _normalize_text(value: str) -> list[str]:
        cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
        return [token for token in cleaned.split() if len(token) > 2]

    def _text_similarity(self, left: str, right: str) -> float:
        left_tokens = self._normalize_text(left)
        right_tokens = self._normalize_text(right)
        if not left_tokens or not right_tokens:
            return 0.0
        left_counter = Counter(left_tokens)
        right_counter = Counter(right_tokens)
        intersection = sum((left_counter & right_counter).values())
        denominator = max(len(set(left_tokens) | set(right_tokens)), 1)
        return intersection / denominator

    @staticmethod
    def _overlap_ratio(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / max(min(len(left), len(right)), 1)

    @staticmethod
    def _geography_fit(source_country: str, source_city: str, target_country: str, target_city: str) -> float:
        source_country = (source_country or "").strip().lower()
        source_city = (source_city or "").strip().lower()
        target_country = (target_country or "").strip().lower()
        target_city = (target_city or "").strip().lower()

        if source_country and target_country and source_country == target_country:
            if source_city and target_city and source_city == target_city:
                return 1.0
            return 0.75
        if not source_country or not target_country:
            return 0.35
        return 0.1

    @staticmethod
    def _candidate_credibility(candidate: dict[str, Any]) -> float:
        score = 0.2
        if candidate.get("email_verified"):
            score += 0.2
        if candidate.get("profile_completed"):
            score += 0.2
        verification_status = int(candidate.get("verification_status") or 0)
        if verification_status == 1:
            score += 0.25
        elif verification_status > 1:
            score += 0.1

        if candidate.get("matched_entity_type") == "ORGANIZATION" and candidate.get("implementation_capacity"):
            score += 0.15
        if candidate.get("matched_entity_type") == "INDIVIDUAL" and candidate.get("headline"):
            score += 0.15

        return min(score, 1.0)

    @staticmethod
    def _top_factors(factors: dict[str, float]) -> list[dict[str, float]]:
        return [
            {"name": name, "score": round(score, 4)}
            for name, score in sorted(factors.items(), key=lambda item: item[1], reverse=True)[:3]
        ]


ml_job_orchestration_service = MLJobOrchestrationService()
