import hashlib
import json
import os
from typing import Any, Dict, List


class LLMEnricherStub:
    """
    Deterministic, cache-backed enrichment layer that returns strict JSON.
    This can be swapped with a real LLM provider later without changing the
    output contract used by the rest of the platform.
    """

    def __init__(self, cache_dir: str = "artifacts/model_outputs/llm_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

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

    def _get_cache_key(self, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def _read_cache(self, key: str):
        path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        return None

    def _write_cache(self, key: str, payload: Dict[str, Any]):
        path = os.path.join(self.cache_dir, f"{key}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)

    @staticmethod
    def _humanize(token: str) -> str:
        return str(token).replace("_", " ").title()

    def enrich_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = self._get_cache_key({"project_id": project.get("project_id"), "project": project})
        cached = self._read_cache(cache_key)
        if cached:
            return cached

        sectors = self._coerce_list(project.get("sector_norm", []))
        sdgs = self._coerce_list(project.get("sdg_labels", project.get("sdg_norm", [])))
        skills = self._coerce_list(project.get("team_skill_needs_norm", project.get("team_skill_needs", [])))
        evidences = self._coerce_list(project.get("evidence_tokens_norm", []))
        stage = str(project.get("stage_norm", "unknown"))
        geography = str(project.get("country_norm", project.get("country", "")))

        normalized_tags = {
            "sector_tags": sectors,
            "sdg_tags": sdgs,
            "stage_tag": stage,
            "geography_tags": [geography] if geography else [],
            "skill_tags": skills,
            "evidence_tags": evidences,
        }

        hidden_needs = []
        if any(token in sectors for token in ["renewable_energy", "water", "agriculture", "climate_resilience"]):
            hidden_needs.append("field_operations_capacity")
        if stage in {"idea", "prototype"}:
            hidden_needs.append("pilot_validation_partners")
        if "monitoring_evaluation" in skills:
            hidden_needs.append("measurement_framework_support")
        if not skills:
            hidden_needs.append("team_design_support")

        quality_indicators = {
            "problem_clarity": 0.85 if str(project.get("problem_statement", "")).strip() else 0.35,
            "solution_specificity": 0.8 if str(project.get("solution_summary", "")).strip() else 0.3,
            "evidence_strength": min(len(evidences) / 5.0, 1.0),
            "funding_definition": 1.0 if project.get("funding_need_min_norm") and project.get("funding_need_max_norm") else 0.4,
        }

        missing_information = []
        if not str(project.get("partnership_structure", "")).strip():
            missing_information.append("partnership_structure")
        if not skills:
            missing_information.append("team_skill_needs")
        if len(evidences) < 2:
            missing_information.append("validation_evidence")
        if not str(project.get("compliance_readiness", "")).strip():
            missing_information.append("compliance_readiness")

        executive_summary = (
            f"{project.get('project_title', 'This project')} is a {stage} stage initiative in "
            f"{', '.join(self._humanize(item) for item in sectors[:2]) or 'sustainability'} focused on {geography or 'its target geography'}, "
            f"with alignment to {', '.join(self._humanize(item) for item in sdgs[:2]) or 'priority SDGs'}."
        )

        explanation_metadata = {
            "top_strengths": [
                strength
                for strength, condition in [
                    ("clear_problem_statement", quality_indicators["problem_clarity"] >= 0.8),
                    ("well_defined_solution", quality_indicators["solution_specificity"] >= 0.75),
                    ("evidence_present", quality_indicators["evidence_strength"] >= 0.4),
                    ("funding_defined", quality_indicators["funding_definition"] >= 0.9),
                ]
                if condition
            ],
            "top_gaps": missing_information[:4],
            "readiness_storyline": "evidence_led" if len(evidences) >= 4 else "needs_proof_building",
        }

        payload = {
            "normalized_tags": normalized_tags,
            "hidden_needs": hidden_needs,
            "quality_indicators": quality_indicators,
            "missing_information": missing_information,
            "executive_summary": executive_summary,
            "explanation_metadata": explanation_metadata,
        }
        self._write_cache(cache_key, payload)
        return payload
