from typing import Any, Dict, List

import pandas as pd


class VolunteerMatcher:
    """
    Hybrid volunteer matcher with hard operational filtering followed by an
    explainable fit score.
    """

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

    def _array_overlap(self, project_values, volunteer_values) -> float:
        project_set = set(self._coerce_list(project_values))
        volunteer_set = set(self._coerce_list(volunteer_values))
        if not project_set or not volunteer_set:
            return 0.0
        return len(project_set & volunteer_set) / max(len(project_set), 1)

    def hard_filter(self, project: dict, volunteers: pd.DataFrame) -> pd.DataFrame:
        if volunteers.empty:
            return volunteers

        filtered = volunteers.copy()
        project_country = project.get("country_iso2")
        project_stage = project.get("stage_norm", "")
        delivery_modes = set(self._coerce_list(project.get("delivery_model_norm", [])))

        if "work_mode_norm" in filtered.columns:
            if "results_framework" in delivery_modes or project_stage in {"pilot", "scale"}:
                filtered = filtered[filtered["work_mode_norm"].isin(["onsite", "hybrid", "remote"])]

        if project_country and "country_iso2" in filtered.columns:
            filtered = filtered[
                (filtered["country_iso2"] == project_country)
                | filtered["work_mode_norm"].isin(["remote", "hybrid"])
                | filtered["travel_willingness_norm"].isin(["yes", "flexible"])
            ]

        if "availability_hours_norm" in filtered.columns:
            filtered = filtered[filtered["availability_hours_norm"].fillna(0) >= 8]

        return filtered

    def score_candidates(self, project: dict, candidates: pd.DataFrame, semantic_sims=None) -> List[Dict[str, Any]]:
        results = []
        project_skills = project.get("team_skill_needs_norm", project.get("team_skill_needs", []))
        project_sdgs = project.get("sdg_norm", [])
        project_sectors = project.get("sector_norm", [])
        project_country = project.get("country_iso2", "")

        for idx, row in candidates.iterrows():
            volunteer = row.to_dict()
            sem_sim = semantic_sims[idx] if semantic_sims is not None and idx < len(semantic_sims) else 0.0

            skill_fit = self._array_overlap(project_skills, volunteer.get("skills_norm", []))
            sdg_fit = self._array_overlap(project_sdgs, volunteer.get("sdg_norm", []))
            sector_fit = self._array_overlap(project_sectors, volunteer.get("sector_norm", []))

            geography_fit = 1.0 if volunteer.get("country_iso2") == project_country else 0.6 if volunteer.get("work_mode_norm") in {"remote", "hybrid"} else 0.3
            availability = float(volunteer.get("availability_hours_norm", volunteer.get("availability_hours_per_week", 0)) or 0)
            availability_fit = 1.0 if availability >= 20 else 0.7 if availability >= 10 else 0.4
            mobility_fit = 1.0 if volunteer.get("travel_willingness_norm") in {"yes", "flexible"} else 0.6

            total_score = (
                skill_fit * 0.34
                + sdg_fit * 0.12
                + sector_fit * 0.12
                + geography_fit * 0.12
                + availability_fit * 0.10
                + mobility_fit * 0.05
                + sem_sim * 0.15
            ) * 100

            rationale = []
            if skill_fit >= 0.5:
                rationale.append("Relevant skill coverage")
            if sector_fit >= 0.5:
                rationale.append("Sector preference aligned")
            if geography_fit >= 1.0:
                rationale.append("Same-country delivery fit")
            elif geography_fit >= 0.6:
                rationale.append("Remote or hybrid delivery possible")
            if sem_sim > 0.65:
                rationale.append("Strong semantic profile alignment")

            results.append(
                {
                    "volunteer_id": volunteer.get("volunteer_id", "unk"),
                    "name": volunteer.get("full_name", "Unknown"),
                    "total_score": round(float(total_score), 1),
                    "skill_fit": round(skill_fit * 100, 1),
                    "operational_fit": round(self._array_overlap(project_sdgs, volunteer.get("sdg_norm", [])) * 100, 1),
                    "expertise_level": volunteer.get("seniority_band", "Mid-Level"),
                    "rationale": ", ".join(rationale) if rationale else "Partial capabilities matched.",
                }
            )

        return sorted(results, key=lambda item: item["total_score"], reverse=True)

    def match(self, project: dict, volunteers: pd.DataFrame, semantic_sims=None, top_k: int = 10):
        candidates = self.hard_filter(project, volunteers)
        scored = self.score_candidates(project, candidates, semantic_sims)
        return scored[:top_k]
