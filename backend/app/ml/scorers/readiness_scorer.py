from typing import Any, Dict, List


class ReadinessScorer:
    """
    Internal readiness score that blends project quality with ecosystem fit.
    This is intentionally an explainable intelligence score, not a fake
    supervised success predictor.
    """

    @staticmethod
    def _ensure_list(value) -> List[str]:
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
    def _bounded_mean(values: List[float]) -> float:
        valid = [float(value) for value in values if value is not None]
        if not valid:
            return 0.0
        return max(0.0, min(sum(valid) / len(valid), 1.0))

    @staticmethod
    def _normalize_realism(value) -> float:
        if isinstance(value, (int, float)):
            return max(0.0, min(float(value), 1.0))
        text = str(value).strip().lower()
        mapping = {"low": 0.25, "moderate": 0.55, "medium": 0.55, "high": 0.9}
        return mapping.get(text, 0.5)

    @staticmethod
    def _top_score(items: List[Dict[str, Any]], key: str) -> float:
        if not items:
            return 0.0
        return max(float(item.get(key, 0.0)) for item in items) / 100.0

    def score_project(self, project: dict, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}

        evidences = self._ensure_list(project.get("evidence_tokens_norm"))
        skills = self._ensure_list(project.get("team_skill_needs_norm", project.get("team_skill_needs")))
        sectors = self._ensure_list(project.get("sector_norm"))

        stage_weights = {"idea": 0.2, "prototype": 0.45, "pilot": 0.7, "scale": 0.95}
        stage_score = stage_weights.get(project.get("stage_norm", "unknown"), 0.2)

        compliance_map = {"low": 0.2, "moderate": 0.55, "medium": 0.55, "high": 0.9}
        credibility_map = {"low": 0.25, "moderate": 0.55, "medium": 0.55, "high": 0.9}

        compliance_score = compliance_map.get(str(project.get("compliance_readiness", "")).lower(), 0.5)
        credibility_score = credibility_map.get(str(project.get("credibility_level", "")).lower(), 0.5)
        realism_score = self._normalize_realism(project.get("realism_score", 0.5))

        has_min = 1.0 if float(project.get("funding_need_min_norm", project.get("funding_need_min", 0)) or 0) > 0 else 0.0
        has_max = 1.0 if float(project.get("funding_need_max_norm", project.get("funding_need_max", 0)) or 0) > 0 else 0.0
        partner_structure = 1.0 if str(project.get("partnership_structure", "")).strip() else 0.0

        evidence_maturity = min(len(evidences) / 5.0, 1.0)
        operational_readiness = self._bounded_mean([stage_score, compliance_score, partner_structure])
        fundability = self._bounded_mean([has_min, has_max, realism_score, context.get("investor_fit_score", 0.0)])
        volunteer_fit = self._bounded_mean(
            [
                1.0 if skills else 0.0,
                context.get("volunteer_fit_score", 0.0),
            ]
        )
        ecosystem_fit = self._bounded_mean(
            [
                1.0 if sectors else 0.0,
                context.get("grant_fit_score", 0.0),
                context.get("activity_fit_score", 0.0),
            ]
        )
        precedent_relevance = self._bounded_mean(
            [
                context.get("activity_fit_score", 0.0),
                1.0 if context.get("activity_results_ratio", 0.0) > 0.35 else 0.4 if context.get("activity_count", 0) else 0.0,
            ]
        )

        total_readiness = (
            evidence_maturity * 0.18
            + credibility_score * 0.12
            + compliance_score * 0.12
            + operational_readiness * 0.18
            + ecosystem_fit * 0.12
            + fundability * 0.14
            + volunteer_fit * 0.08
            + precedent_relevance * 0.06
        )

        blockers = []
        risk_flags = []
        suggestions = []

        if evidence_maturity < 0.35:
            blockers.append("Evidence base is too thin for confident matching.")
            suggestions.append("Add stronger validation evidence such as pilot results, audited reports, or partner letters.")
        if compliance_score < 0.4:
            blockers.append("Compliance readiness is below investor-grade expectations.")
            suggestions.append("Document governance, reporting, and operational compliance requirements.")
        if fundability < 0.45:
            blockers.append("Funding structure is not yet clear enough for capital matching.")
            suggestions.append("Clarify minimum and maximum funding ask with a tighter use-of-funds narrative.")
        if volunteer_fit < 0.4:
            suggestions.append("Translate team needs into clearer volunteer-facing skill requirements.")
        if precedent_relevance < 0.35:
            suggestions.append("Strengthen external precedent alignment with clearer regional and sector framing.")

        if credibility_score < 0.4:
            risk_flags.append("Credibility signals remain weak")
        if ecosystem_fit < 0.45:
            risk_flags.append("Ecosystem fit is still emerging")
        if context.get("investor_fit_score", 0.0) < 0.45:
            risk_flags.append("Current investor resonance is limited")
        if context.get("volunteer_fit_score", 0.0) < 0.35:
            risk_flags.append("Volunteer-market fit is limited")

        missing_criticals = []
        if not has_max:
            missing_criticals.append("Funding Limit")
        if not partner_structure:
            missing_criticals.append("Partnership Structure")
        if not skills:
            missing_criticals.append("Team Skill Needs")
        if not evidences:
            missing_criticals.append("Evidence Tokens")

        sub_scores = {
            "evidence_maturity": round(evidence_maturity * 100, 1),
            "credibility": round(credibility_score * 100, 1),
            "compliance_readiness": round(compliance_score * 100, 1),
            "operational_readiness": round(operational_readiness * 100, 1),
            "ecosystem_fit": round(ecosystem_fit * 100, 1),
            "fundability": round(fundability * 100, 1),
            "volunteer_fit": round(volunteer_fit * 100, 1),
            "precedent_relevance": round(precedent_relevance * 100, 1),
        }

        return {
            "total_score": round(total_readiness * 100, 1),
            "sub_scores": sub_scores,
            "risk_flags": risk_flags,
            "missing_criticals": missing_criticals,
            "blockers": blockers,
            "improvement_suggestions": suggestions,
            "context_signals": {
                "investor_fit_score": round(context.get("investor_fit_score", 0.0) * 100, 1),
                "volunteer_fit_score": round(context.get("volunteer_fit_score", 0.0) * 100, 1),
                "grant_fit_score": round(context.get("grant_fit_score", 0.0) * 100, 1),
                "activity_fit_score": round(context.get("activity_fit_score", 0.0) * 100, 1),
            },
            "improvement_plan": suggestions[0] if suggestions else "Project is broadly aligned; continue improving proof points and execution depth.",
        }

    def build_context(
        self,
        investor_matches: List[Dict[str, Any]],
        volunteer_matches: List[Dict[str, Any]],
        grant_matches: List[Dict[str, Any]],
        activity_matches: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        activity_results = 0
        for item in activity_matches:
            snippet = str(item.get("description_snippet", "")).lower()
            if any(token in snippet for token in ["result", "outcome", "impact", "delivered", "implemented"]):
                activity_results += 1

        return {
            "investor_fit_score": self._top_score(investor_matches, "total_score"),
            "volunteer_fit_score": self._top_score(volunteer_matches, "total_score"),
            "grant_fit_score": self._top_score(grant_matches, "relevance_score"),
            "activity_fit_score": self._top_score(activity_matches, "relevance_score"),
            "activity_count": len(activity_matches),
            "activity_results_ratio": (activity_results / len(activity_matches)) if activity_matches else 0.0,
        }
