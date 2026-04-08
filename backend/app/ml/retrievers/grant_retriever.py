from typing import Any, Dict, List

import pandas as pd

from ..embeddings.vector_store import SemanticVectorStore


class GrantRetriever:
    """
    Hybrid grant retrieval: structured fit first, semantic reranking second.
    """

    def __init__(self, vector_store: SemanticVectorStore):
        self.vector_store = vector_store

    @staticmethod
    def _coerce_list(value) -> List[str]:
        if value is None:
            return []
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split("|") if item.strip()]
        return []

    @staticmethod
    def _overlap_ratio(left, right) -> float:
        left_values = set(GrantRetriever._coerce_list(left))
        right_values = set(GrantRetriever._coerce_list(right))
        if not left_values or not right_values:
            return 0.0
        return len(left_values & right_values) / min(len(left_values), len(right_values))

    def retrieve_grants(self, project_text: str, project_stage: str, grants_df: pd.DataFrame, grant_embeddings, top_k=5, project: dict | None = None) -> List[Dict[str, Any]]:
        if grants_df.empty or len(grant_embeddings) == 0:
            return []

        project = project or {}
        project_sectors = self._coerce_list(project.get("sector_norm", []))
        project_legal_form = str(project.get("legal_form", "")).lower()
        project_need_min = float(project.get("funding_need_min_norm", project.get("funding_need_min", 0)) or 0)
        project_need_max = float(project.get("funding_need_max_norm", project.get("funding_need_max", 0)) or 0)

        candidates = grants_df.copy()
        if "award_ceiling_norm" in candidates.columns and project_need_min > 0:
            budget_mask = candidates["award_ceiling_norm"].isna() | (candidates["award_ceiling_norm"] >= project_need_min)
            if budget_mask.any():
                candidates = candidates[budget_mask]

        sims = self.vector_store.query_similarity(project_text, grant_embeddings)

        results = []
        for idx, row in candidates.iterrows():
            grant = row.to_dict()
            semantic_score = float(sims[idx])
            grant_sectors = grant.get("sector_norm", [])
            sector_fit = self._overlap_ratio(project_sectors, grant_sectors)

            description = str(grant.get("description", "")).lower()
            stage_bump = 0.1 if project_stage and project_stage in description else 0.0

            legal_form_fit = 0.7
            applicant_types = " ".join(self._coerce_list(grant.get("applicant_types_norm", []))).lower()
            if project_legal_form == "nonprofit" and any(token in applicant_types for token in ["nonprofit", "ngo", "organization", "unrestricted"]):
                legal_form_fit = 1.0
            elif project_legal_form and applicant_types and all(token not in applicant_types for token in ["nonprofit", "ngo", "organization", "unrestricted", "business", "company"]):
                legal_form_fit = 0.6

            award_floor = grant.get("award_floor_norm")
            award_ceiling = grant.get("award_ceiling_norm")
            budget_fit = 0.6
            if project_need_max > 0 and (award_floor is not None or award_ceiling is not None):
                lower_ok = award_floor is None or award_floor <= project_need_max
                upper_ok = award_ceiling is None or award_ceiling >= project_need_min
                budget_fit = 1.0 if lower_ok and upper_ok else 0.35

            total_relevance = (
                semantic_score * 0.50
                + sector_fit * 0.18
                + budget_fit * 0.12
                + legal_form_fit * 0.10
                + stage_bump * 0.10
            )

            rationale_parts = []
            if sector_fit > 0.5:
                rationale_parts.append("Sector-aligned funding scope")
            if budget_fit > 0.8:
                rationale_parts.append("Funding band is compatible")
            if stage_bump > 0:
                rationale_parts.append("Grant language matches project stage")
            if semantic_score > 0.65:
                rationale_parts.append("High semantic relevance")

            results.append(
                {
                    "grant_id": grant.get("opportunity_id", "unk"),
                    "title": grant.get("title", ""),
                    "relevance_score": round(total_relevance * 100, 1),
                    "semantic_confidence": round(semantic_score * 100, 1),
                    "funder": grant.get("funder_name") or grant.get("agency_name") or grant.get("agency") or "Unlisted Agency",
                    "rationale": ", ".join(rationale_parts) if rationale_parts else "Partial relevance detected",
                    "application_complexity": grant.get("submission_complexity", "Medium"),
                }
            )

        results.sort(key=lambda item: item["relevance_score"], reverse=True)
        return results[:top_k]
