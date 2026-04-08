from typing import Any, Dict, List

import pandas as pd

from ..embeddings.vector_store import SemanticVectorStore


class ActivityRetriever:
    """
    Retrieves ecosystem precedents using country/sector compatibility plus
    semantic similarity.
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
        left_values = set(ActivityRetriever._coerce_list(left))
        right_values = set(ActivityRetriever._coerce_list(right))
        if not left_values or not right_values:
            return 0.0
        return len(left_values & right_values) / min(len(left_values), len(right_values))

    def retrieve_precedents(
        self,
        project_text: str,
        project_sector: list,
        act_df: pd.DataFrame,
        act_embs,
        top_k=5,
        project: dict | None = None,
    ) -> List[Dict[str, Any]]:
        if act_df.empty or len(act_embs) == 0:
            return []

        project = project or {}
        project_country = project.get("country_iso2", "")
        sims = self.vector_store.query_similarity(project_text, act_embs)

        results = []
        for idx in range(len(act_df)):
            act = act_df.iloc[idx].to_dict()
            semantic_score = float(sims[idx])
            sector_fit = self._overlap_ratio(project_sector, act.get("sector_norm", []))
            country_fit = self._overlap_ratio([project_country], act.get("recipient_country_norm", []))
            results_bonus = 0.08 if act.get("results_present") else 0.0

            total_relevance = (
                semantic_score * 0.60
                + sector_fit * 0.18
                + country_fit * 0.14
                + results_bonus
            )

            rationale = []
            if country_fit > 0.5:
                rationale.append("Country precedent match")
            if sector_fit > 0.5:
                rationale.append("Sector precedent match")
            if semantic_score > 0.65:
                rationale.append("Strong thematic similarity")
            if act.get("results_present"):
                rationale.append("Contains outcome evidence")

            results.append(
                {
                    "activity_id": act.get("activity_id", "unk"),
                    "reporting_org": act.get("ngo_name") or act.get("reporting_org_name") or act.get("reporting_org", "Global Entity"),
                    "relevance_score": round(total_relevance * 100, 1),
                    "semantic_confidence": round(semantic_score * 100, 1),
                    "description_snippet": str(act.get("description", "No active description"))[:140] + "...",
                    "rationale": ", ".join(rationale) if rationale else "Historical thematic similarity found",
                }
            )

        results.sort(key=lambda item: item["relevance_score"], reverse=True)
        return results[:top_k]
