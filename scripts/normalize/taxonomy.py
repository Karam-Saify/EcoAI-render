import re
from typing import Callable

import pandas as pd

try:
    from app.core.geography import region_name as geography_region_name
except ModuleNotFoundError:
    geography_region_name = None


SDG_NAME_MAP = {
    1: "no_poverty",
    2: "zero_hunger",
    3: "good_health_and_well_being",
    4: "quality_education",
    5: "gender_equality",
    6: "clean_water_and_sanitation",
    7: "affordable_and_clean_energy",
    8: "decent_work_and_economic_growth",
    9: "industry_innovation_and_infrastructure",
    10: "reduced_inequalities",
    11: "sustainable_cities_and_communities",
    12: "responsible_consumption_and_production",
    13: "climate_action",
    14: "life_below_water",
    15: "life_on_land",
    16: "peace_justice_and_strong_institutions",
    17: "partnerships_for_the_goals",
}

SDG_KEYWORD_MAP = {
    "poverty": 1,
    "hunger": 2,
    "health": 3,
    "well being": 3,
    "education": 4,
    "gender": 5,
    "water": 6,
    "sanitation": 6,
    "energy": 7,
    "economic growth": 8,
    "decent work": 8,
    "industry": 9,
    "innovation": 9,
    "infrastructure": 9,
    "inequalities": 10,
    "cities": 11,
    "communities": 11,
    "consumption": 12,
    "production": 12,
    "climate": 13,
    "oceans": 14,
    "below water": 14,
    "land": 15,
    "justice": 16,
    "institutions": 16,
    "peace": 16,
    "partnerships": 17,
}

COUNTRY_CODE_MAP = {
    "lebanon": "LB",
    "lb": "LB",
    "jordan": "JO",
    "jo": "JO",
    "uganda": "UG",
    "ug": "UG",
    "kenya": "KE",
    "ke": "KE",
    "tanzania": "TZ",
    "tz": "TZ",
    "syria": "SY",
    "sy": "SY",
    "palestine": "PS",
    "ps": "PS",
    "europe": "EU",
    "global": "GLOBAL",
}

REGION_ALIAS_MAP = {
    "mena": "middle_east_and_north_africa",
    "middle east": "middle_east",
    "middle east and north africa": "middle_east_and_north_africa",
    "east africa": "east_africa",
    "sub saharan africa": "sub_saharan_africa",
    "north africa": "north_africa",
}

SECTOR_ALIAS_MAP = {
    "renewable": "renewable_energy",
    "energy": "energy",
    "climate": "climate_action",
    "climate resilience": "climate_resilience",
    "livelihood": "livelihoods",
    "m&e": "monitoring_and_evaluation",
    "monitoring & evaluation": "monitoring_and_evaluation",
}


def _snake_case(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
    return re.sub(r"_+", "_", cleaned).strip("_")


def _title_case_token(value: str) -> str:
    token = _snake_case(value)
    return token.replace("_", " ").title() if token else ""


def _coerce_delimited_tokens(text_item, *, preserve_case: bool = False) -> list[str]:
    if isinstance(text_item, list):
        values = text_item
    elif isinstance(text_item, str):
        values = re.split(r"[,;/|]+", text_item)
    else:
        return []

    cleaned = []
    for value in values:
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "-", "n/a"}:
            continue
        cleaned.append(text if preserve_case else _snake_case(text))
    return cleaned


def normalize_text_to_list(text_item):
    return _coerce_delimited_tokens(text_item)


def normalize_label_list(text_item) -> list[str]:
    return [_title_case_token(token) for token in _coerce_delimited_tokens(text_item)]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for value in values:
        if value and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def extract_sdg_tags(sdg_item):
    raw_text = " ".join(_coerce_delimited_tokens(sdg_item, preserve_case=True)).lower()
    clean_sdgs = set()

    for match in re.finditer(r"(sdg\s*-?\s*|goal\s*-?\s*)?(\d{1,2})", raw_text, re.IGNORECASE):
        value = int(match.group(2))
        if 1 <= value <= 17:
            clean_sdgs.add(f"SDG{value}")

    for keyword, sdg_num in SDG_KEYWORD_MAP.items():
        if keyword in raw_text:
            clean_sdgs.add(f"SDG{sdg_num}")

    return sorted(clean_sdgs, key=lambda item: int(item.replace("SDG", "")))


def expand_sdg_labels(sdgs) -> list[str]:
    labels = []
    for sdg in extract_sdg_tags(sdgs):
        number = int(sdg.replace("SDG", ""))
        labels.append(f"{sdg}_{SDG_NAME_MAP[number]}")
    return labels


def normalize_stage(stage_raw):
    stage_raw = _snake_case(stage_raw)
    if any(token in stage_raw for token in ["idea", "concept", "pre_seed"]):
        return "idea"
    if any(token in stage_raw for token in ["prototype", "mvp", "alpha"]):
        return "prototype"
    if any(token in stage_raw for token in ["pilot", "beta", "early_stage"]):
        return "pilot"
    if any(token in stage_raw for token in ["scale", "growth", "series", "expansion"]):
        return "scale"
    return "unknown"


def normalize_sector_list(text_item) -> list[str]:
    sectors = []
    for token in _coerce_delimited_tokens(text_item):
        sector = SECTOR_ALIAS_MAP.get(token.replace("_", " "), token)
        sectors.append(_snake_case(sector))
    return _dedupe(sectors)


def normalize_skill_list(text_item) -> list[str]:
    return _dedupe(_coerce_delimited_tokens(text_item))


def normalize_evidence_list(text_item) -> list[str]:
    return _dedupe(_coerce_delimited_tokens(text_item))


def normalize_instrument_list(text_item) -> list[str]:
    return _dedupe(_coerce_delimited_tokens(text_item))


def normalize_country_name(value) -> str:
    if value is None:
        return ""
    token = str(value).strip()
    if not token or token.lower() in {"nan", "none", "-", "n/a"}:
        return ""
    if token.isupper() and len(token) in {2, 3} and token.lower() in COUNTRY_CODE_MAP:
        token = next(
            (name for name, code in COUNTRY_CODE_MAP.items() if code == COUNTRY_CODE_MAP[token.lower()] and len(name) > 2),
            token,
        )
    return _title_case_token(token)


def normalize_country_code(value) -> str:
    token = _snake_case(value)
    return COUNTRY_CODE_MAP.get(token, token.upper() if len(token) in {2, 3} else "")


def normalize_country_list(value) -> list[str]:
    codes = []
    for token in _coerce_delimited_tokens(value, preserve_case=True):
        code = normalize_country_code(token)
        if code:
            codes.append(code)
    return _dedupe(codes)


def normalize_region(value) -> str:
    token = _snake_case(value).replace("_", " ")
    if not token:
        return ""
    if token.isdigit() and geography_region_name is not None:
        mapped = geography_region_name(token)
        if mapped:
            return _snake_case(mapped)
    return _snake_case(REGION_ALIAS_MAP.get(token, token))


def normalize_region_list(value) -> list[str]:
    return _dedupe([normalize_region(token) for token in _coerce_delimited_tokens(value, preserve_case=True)])


def normalize_numeric(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    if cleaned in {"", "-", ".", "-."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _apply_if_present(df: pd.DataFrame, column: str, fn: Callable) -> pd.Series:
    if column in df.columns:
        return df[column].apply(fn)
    return pd.Series([""] * len(df), index=df.index)


def build_project_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    canon = df.copy()
    canon["project_title"] = canon.get("project_title", canon.get("title", "")).astype(str).str.strip()
    canon["country_norm"] = _apply_if_present(canon, "country", normalize_country_name)
    canon["country_iso2"] = _apply_if_present(canon, "country", normalize_country_code)
    canon["region_norm"] = _apply_if_present(canon, "region", normalize_region)
    canon["sector_norm"] = _apply_if_present(canon, "sector", normalize_sector_list)
    canon["sdg_norm"] = _apply_if_present(canon, "sdg_alignment", extract_sdg_tags)
    canon["sdg_labels"] = _apply_if_present(canon, "sdg_alignment", expand_sdg_labels)
    canon["stage_norm"] = _apply_if_present(canon, "stage", normalize_stage)
    canon["team_skill_needs_norm"] = _apply_if_present(canon, "team_skill_needs", normalize_skill_list)
    canon["evidence_tokens_norm"] = _apply_if_present(canon, "evidence_tokens", normalize_evidence_list)
    canon["beneficiary_norm"] = _apply_if_present(canon, "target_beneficiaries", normalize_text_to_list)
    canon["delivery_model_norm"] = _apply_if_present(canon, "delivery_model", normalize_text_to_list)
    canon["funding_need_min_norm"] = _apply_if_present(canon, "funding_need_min", normalize_numeric)
    canon["funding_need_max_norm"] = _apply_if_present(canon, "funding_need_max", normalize_numeric)
    return canon


def build_investor_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    canon = df.copy()
    canon["name"] = canon.get("name", "").astype(str).str.strip()
    canon["domicile_country_norm"] = _apply_if_present(canon, "domicile_country", normalize_country_name)
    canon["domicile_country_iso2"] = _apply_if_present(canon, "domicile_country", normalize_country_code)
    canon["geography_focus_norm"] = _apply_if_present(canon, "geography_focus", normalize_country_list)
    canon["region_focus_norm"] = _apply_if_present(canon, "region_focus", normalize_region_list)
    canon["sector_norm"] = _apply_if_present(canon, "sector_focus", normalize_sector_list)
    canon["sdg_norm"] = _apply_if_present(canon, "sdg_focus", extract_sdg_tags)
    canon["sdg_labels"] = _apply_if_present(canon, "sdg_focus", expand_sdg_labels)
    canon["stage_norm"] = _apply_if_present(
        canon, "stage_preference", lambda col: [normalize_stage(x) for x in normalize_text_to_list(col)]
    )
    canon["instrument_norm"] = _apply_if_present(canon, "instrument_set", normalize_instrument_list)
    canon["ticket_min_norm"] = _apply_if_present(canon, "ticket_min", normalize_numeric)
    canon["ticket_max_norm"] = _apply_if_present(canon, "ticket_max", normalize_numeric)
    canon["credibility_tokens_norm"] = _apply_if_present(canon, "credibility_tokens", normalize_evidence_list)
    return canon


def build_volunteer_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    canon = df.copy()
    canon["full_name"] = canon.get("full_name", "").astype(str).str.strip()
    canon["country_norm"] = _apply_if_present(canon, "country", normalize_country_name)
    canon["country_iso2"] = _apply_if_present(canon, "country", normalize_country_code)
    canon["language_norm"] = _apply_if_present(canon, "languages", normalize_text_to_list)
    canon["sector_norm"] = _apply_if_present(canon, "sector_preferences", normalize_sector_list)
    canon["sdg_norm"] = _apply_if_present(canon, "sdg_preferences", extract_sdg_tags)
    canon["sdg_labels"] = _apply_if_present(canon, "sdg_preferences", expand_sdg_labels)
    canon["skills_norm"] = _apply_if_present(canon, "skill_bundle", normalize_skill_list)
    canon["work_mode_norm"] = _apply_if_present(canon, "work_mode", _snake_case)
    canon["travel_willingness_norm"] = _apply_if_present(canon, "travel_willingness", _snake_case)
    canon["evidence_tokens_norm"] = _apply_if_present(canon, "evidence_tokens", normalize_evidence_list)
    canon["availability_hours_norm"] = _apply_if_present(canon, "availability_hours_per_week", normalize_numeric)
    canon["engagement_months_norm"] = _apply_if_present(canon, "engagement_months", normalize_numeric)
    return canon


def build_grant_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    canon = df.copy()
    canon["funder_name"] = canon.get("agency_name", canon.get("top_agency_name", "")).astype(str).str.strip()
    canon["instrument_norm"] = _apply_if_present(canon, "funding_instruments", normalize_instrument_list)
    canon["sector_norm"] = _apply_if_present(canon, "funding_categories", normalize_sector_list)
    canon["funding_categories_norm"] = _apply_if_present(canon, "funding_categories", normalize_text_to_list)
    canon["applicant_types_norm"] = _apply_if_present(canon, "applicant_types", normalize_text_to_list)
    canon["award_ceiling_norm"] = _apply_if_present(canon, "award_ceiling", normalize_numeric)
    canon["award_floor_norm"] = _apply_if_present(canon, "award_floor", normalize_numeric)
    canon["status_norm"] = _apply_if_present(canon, "status", _snake_case)
    return canon


def build_activity_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    canon = df.copy()
    canon["ngo_name"] = canon.get("reporting_org_name", "").astype(str).str.strip()
    canon["sector_norm"] = _apply_if_present(canon, "sector_names", normalize_sector_list)
    canon["matched_keywords_norm"] = _apply_if_present(canon, "matched_keywords", normalize_text_to_list)
    canon["recipient_country_norm"] = _apply_if_present(canon, "recipient_countries", normalize_country_list)
    canon["recipient_region_norm"] = _apply_if_present(canon, "recipient_regions", normalize_region_list)
    canon["participating_orgs_norm"] = _apply_if_present(canon, "participating_orgs", normalize_text_to_list)
    canon["results_present"] = canon.get("results_text", "").astype(str).str.strip().ne("")
    return canon


ENTITY_CANONICALIZERS = {
    "projects": build_project_canonical,
    "investors": build_investor_canonical,
    "volunteers": build_volunteer_canonical,
    "grants": build_grant_canonical,
    "activities": build_activity_canonical,
}


def build_entity_canonical(entity_name: str, df: pd.DataFrame) -> pd.DataFrame:
    canonicalizer = ENTITY_CANONICALIZERS.get(entity_name)
    if canonicalizer is None:
        return df
    return canonicalizer(df)


if __name__ == "__main__":
    print("Taxonomy normalization helpers are ready.")
