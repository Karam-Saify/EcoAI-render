from typing import Any, Dict, List

import pandas as pd

from ..features.pair_featurizer import PairFeaturizer


class InvestorMatcher:
    def __init__(self, featurizer: PairFeaturizer):
        self.featurizer = featurizer

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
        left_values = set(InvestorMatcher._coerce_list(left))
        right_values = set(InvestorMatcher._coerce_list(right))
        if not left_values or not right_values:
            return 0.0
        return len(left_values & right_values) / min(len(left_values), len(right_values))

    def hard_filter(self, project: dict, investors: pd.DataFrame) -> pd.DataFrame:
        if investors.empty:
            return investors

        filtered = investors.copy()
        project_stage = project.get("stage_norm", "")
        project_country = project.get("country_iso2", "")
        project_region = project.get("region_norm", "")
        project_sector = self._coerce_list(project.get("sector_norm", []))
        project_compliance = str(project.get("compliance_readiness", "")).lower()
        project_need_min = float(project.get("funding_need_min_norm", project.get("funding_need_min", 0)) or 0)

        if "stage_norm" in filtered.columns:
            filtered = filtered[
                filtered["stage_norm"].apply(
                    lambda stages: project_stage in self._coerce_list(stages) if self._coerce_list(stages) else True
                )
            ]

        if "ticket_max_norm" in filtered.columns:
            filtered = filtered[(filtered["ticket_max_norm"] >= project_need_min) | (filtered["ticket_max_norm"].isna())]

        if "geography_focus_norm" in filtered.columns:
            filtered = filtered[
                filtered["geography_focus_norm"].apply(
                    lambda geos: project_country in self._coerce_list(geos) if self._coerce_list(geos) else True
                )
                |
                filtered.get("region_focus_norm", pd.Series([[]] * len(filtered), index=filtered.index)).apply(
                    lambda regions: project_region in self._coerce_list(regions) if self._coerce_list(regions) else True
                )
            ]

        if "sector_norm" in filtered.columns and project_sector:
            sector_mask = filtered["sector_norm"].apply(
                lambda sectors: self._overlap_ratio(project_sector, sectors) > 0 if self._coerce_list(sectors) else True
            )
            if sector_mask.any():
                filtered = filtered[sector_mask]

        if "eligibility_strictness" in filtered.columns and project_compliance in {"low", "moderate"}:
            filtered = filtered[
                ~(
                    filtered["eligibility_strictness"].astype(str).str.lower().eq("high")
                    & (project_compliance == "low")
                )
            ]

        return filtered

    def score_candidates(self, project: dict, candidates: pd.DataFrame, semantic_sims=None) -> List[Dict[str, Any]]:
        results = []
        project_country = project.get("country_iso2", "")
        project_region = project.get("region_norm", "")

        for idx, row in candidates.iterrows():
            investor = row.to_dict()
            sem_sim = semantic_sims[idx] if semantic_sims is not None and idx < len(semantic_sims) else 0.0
            features = self.featurizer.compute_project_investor_features(project, investor, sem_sim)

            geo_fit = max(
                self._overlap_ratio([project_country], investor.get("geography_focus_norm", [])),
                self._overlap_ratio([project_region], investor.get("region_focus_norm", [])),
            )
            stage_fit = float(features["stage_compatibility"])
            strictness = str(investor.get("eligibility_strictness", "moderate")).lower()
            compliance_fit = 1.0
            if strictness == "high" and str(project.get("compliance_readiness", "")).lower() in {"low", "moderate"}:
                compliance_fit = 0.45

            total_score = (
                features["sector_overlap_score"] * 0.22
                + features["sdg_overlap_score"] * 0.12
                + stage_fit * 0.10
                + features["budget_overlap_ratio"] * 0.18
                + geo_fit * 0.12
                + compliance_fit * 0.08
                + features["semantic_cosine_sim"] * 0.13
                + features["risk_alignment_score"] * 0.05
            ) * 100

            rationale = []
            if geo_fit >= 1.0:
                rationale.append("Exact geography fit")
            elif geo_fit >= 0.5:
                rationale.append("Regional fit")
            if features["sector_overlap_score"] > 0.5:
                rationale.append("High sector alignment")
            if stage_fit >= 1.0:
                rationale.append("Stage preference aligned")
            if features["budget_overlap_ratio"] > 0.8:
                rationale.append("Funding size fit")
            if features["semantic_cosine_sim"] > 0.7:
                rationale.append("Strong thematic textual match")

            results.append(
                {
                    "investor_id": investor.get("investor_id", "unknown"),
                    "investor_name": investor.get("name", "Unknown"),
                    "total_score": round(float(total_score), 1),
                    "factor_contributions": {
                        **{key: round(float(value), 3) for key, value in features.items()},
                        "geography_fit": round(float(geo_fit), 3),
                        "compliance_fit": round(float(compliance_fit), 3),
                    },
                    "rationale": ", ".join(rationale) if rationale else "Meets baseline investor compatibility",
                    "improvement": "Clarify compliance and use-of-funds framing" if compliance_fit < 0.8 else "Looks good",
                }
            )

        results.sort(key=lambda item: item["total_score"], reverse=True)
        return results

    def match(self, project: dict, investors: pd.DataFrame, semantic_sims=None, top_k: int = 10) -> List[Dict[str, Any]]:
        candidates = self.hard_filter(project, investors)
        scored = self.score_candidates(project, candidates, semantic_sims)
        return scored[:top_k]
