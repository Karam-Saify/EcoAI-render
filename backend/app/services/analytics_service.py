import logging
from collections import Counter
from typing import Any, Dict, List

import numpy as np
from sklearn.manifold import TSNE

from ..core.geography import coerce_country_code, country_coordinates, country_name, region_coordinates, region_name

logger = logging.getLogger(__name__)


class GlobalAnalyticsService:
    def __init__(self, matching_service):
        self.ms = matching_service
        self._cached_overview = None
        self._cached_entities = None
        self._cached_clusters = None
        self._cached_match_snapshot = None

    @staticmethod
    def _humanize(token: str) -> str:
        return str(token).replace("_", " ").title()

    @staticmethod
    def _truncate(text: str, limit: int = 42) -> str:
        text = str(text or "").strip()
        if len(text) <= limit:
            return text
        return f"{text[: limit - 1].rstrip()}..."

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            if isinstance(value, str) and not value.strip():
                return default
            if np.isnan(value):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _country_code(value: Any) -> str:
        return coerce_country_code(value)

    def _display_country(self, value: Any) -> str:
        label = country_name(value)
        return label or self._humanize(value or "unknown")

    def _display_region(self, value: Any) -> str:
        label = region_name(value)
        return label or self._humanize(value or "unknown")

    @staticmethod
    def _to_list(value) -> List[str]:
        if value is None:
            return []
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split("|") if item.strip()]
        return []

    def _display_name(self, row: dict, entity_type: str) -> str:
        if entity_type == "project":
            return self._truncate(row.get("project_title", "Untitled Project"), 44)
        if entity_type == "investor":
            return self._truncate(row.get("name", "Unknown Investor"), 40)
        if entity_type == "volunteer":
            return self._truncate(row.get("full_name", "Unknown Volunteer"), 34)
        if entity_type == "grant":
            return self._truncate(row.get("title", "Untitled Grant"), 42)
        if entity_type == "precedent":
            return self._truncate(
                row.get("reporting_org_name") or row.get("ngo_name") or row.get("title") or "Historical Precedent",
                42,
            )
        return self._truncate(str(row.get("name", "Unknown")))

    def _primary_sector(self, row: dict, fallback_column: str = "sector_norm") -> str:
        items = self._to_list(row.get(fallback_column))
        if items:
            return self._humanize(items[0])
        keyword_items = self._to_list(row.get("matched_keywords_norm"))
        if keyword_items:
            return self._humanize(keyword_items[0])
        return "General"

    def _top_sectors(self, df, column: str, top_k: int = 8) -> List[Dict[str, Any]]:
        counts = {}
        if df.empty or column not in df.columns:
            return []
        for items in df[column].dropna():
            for item in self._to_list(items):
                counts[item] = counts.get(item, 0) + 1
        return [
            {"name": self._humanize(name), "val": val}
            for name, val in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:top_k]
        ]

    def _build_regional_stack(self) -> List[Dict[str, Any]]:
        rows = {}

        def add(region_value, label):
            region = str(region_value or "").strip() or "Unknown"
            rows.setdefault(region, {"region": region, "Projects": 0, "Investors": 0, "Volunteers": 0, "NGOs": 0})
            rows[region][label] += 1

        for _, row in self.ms.projects_df.iterrows():
            add(self._display_region(row.get("region_norm")), "Projects")

        for _, row in self.ms.investors_df.iterrows():
            regions = self._to_list(row.get("region_focus_norm"))
            if regions:
                for region in regions:
                    add(self._display_region(region), "Investors")
            else:
                add("Unknown", "Investors")

        for _, row in self.ms.volunteers_df.iterrows():
            add(self._display_country(row.get("country_iso2") or row.get("country_norm")), "Volunteers")

        for _, row in self.ms.activities_df.iterrows():
            regions = self._to_list(row.get("recipient_region_norm"))
            if regions:
                for region in regions:
                    add(self._display_region(region), "NGOs")
            else:
                countries = self._to_list(row.get("recipient_country_norm"))
                add(self._display_country(countries[0]) if countries else "Unknown", "NGOs")

        data = list(rows.values())
        data.sort(key=lambda row: row["Projects"] + row["Investors"] + row["Volunteers"] + row["NGOs"], reverse=True)
        return data[:10]

    @staticmethod
    def _overlap_ratio(left, right) -> float:
        left_set = set(left)
        right_set = set(right)
        if not left_set or not right_set:
            return 0.0
        return len(left_set & right_set) / min(len(left_set), len(right_set))

    @staticmethod
    def _range_fit(min_need, max_need, min_offer, max_offer) -> float:
        min_need = float(min_need or 0)
        max_need = float(max_need or 0)
        min_offer = float(min_offer or 0)
        max_offer = float(max_offer) if max_offer not in (None, 0) else float("inf")
        if max_need <= 0:
            return 0.5
        overlap_min = max(min_need, min_offer)
        overlap_max = min(max_need, max_offer)
        overlap = max(0.0, overlap_max - overlap_min)
        denom = max(max_need - min_need, 1.0)
        return min(overlap / denom, 1.0)

    def _compute_match_snapshot(self) -> Dict[str, Any]:
        if self._cached_match_snapshot is not None:
            return self._cached_match_snapshot

        project_count = len(self.ms.projects_df)
        snapshot = {
            "coverage": [
                {"entity": "Investors", "matched_projects": 0, "avg_top_score": 0.0},
                {"entity": "Volunteers", "matched_projects": 0, "avg_top_score": 0.0},
                {"entity": "Grants", "matched_projects": 0, "avg_top_score": 0.0},
                {"entity": "Precedents", "matched_projects": 0, "avg_top_score": 0.0},
            ],
            "total_matches": 0,
            "avg_match_score": 0.0,
        }
        if project_count == 0:
            self._cached_match_snapshot = snapshot
            return snapshot

        project_embs = self.ms.project_embs if isinstance(self.ms.project_embs, np.ndarray) else np.array([])
        investor_embs = self.ms.investor_embs if isinstance(self.ms.investor_embs, np.ndarray) else np.array([])
        volunteer_embs = self.ms.volunteer_embs if isinstance(self.ms.volunteer_embs, np.ndarray) else np.array([])
        grant_embs = self.ms.grant_embs if isinstance(self.ms.grant_embs, np.ndarray) else np.array([])
        activity_embs = self.ms.activity_embs if isinstance(self.ms.activity_embs, np.ndarray) else np.array([])

        inv_sim = project_embs @ investor_embs.T if project_embs.size and investor_embs.size else np.zeros((project_count, 0))
        vol_sim = project_embs @ volunteer_embs.T if project_embs.size and volunteer_embs.size else np.zeros((project_count, 0))
        grant_sim = project_embs @ grant_embs.T if project_embs.size and grant_embs.size else np.zeros((project_count, 0))
        act_sim = project_embs @ activity_embs.T if project_embs.size and activity_embs.size else np.zeros((project_count, 0))

        top_scores = {"Investors": [], "Volunteers": [], "Grants": [], "Precedents": []}
        matched_projects = {"Investors": 0, "Volunteers": 0, "Grants": 0, "Precedents": 0}

        for p_idx, (_, project) in enumerate(self.ms.projects_df.iterrows()):
            p_sector = self._to_list(project.get("sector_norm"))
            p_sdg = self._to_list(project.get("sdg_norm"))
            p_skills = self._to_list(project.get("team_skill_needs_norm"))
            p_country = str(project.get("country_iso2", ""))
            p_region = str(project.get("region_norm", ""))
            p_stage = str(project.get("stage_norm", ""))
            p_min = project.get("funding_need_min_norm", project.get("funding_need_min", 0))
            p_max = project.get("funding_need_max_norm", project.get("funding_need_max", 0))

            investor_best = 0.0
            for i_idx, (_, investor) in enumerate(self.ms.investors_df.iterrows()):
                sector_fit = self._overlap_ratio(p_sector, self._to_list(investor.get("sector_norm")))
                stage_fit = 1.0 if p_stage in self._to_list(investor.get("stage_norm")) else 0.0
                geo_fit = max(
                    self._overlap_ratio([p_country], self._to_list(investor.get("geography_focus_norm"))),
                    self._overlap_ratio([p_region], self._to_list(investor.get("region_focus_norm"))),
                )
                budget_fit = self._range_fit(
                    p_min,
                    p_max,
                    investor.get("ticket_min_norm", investor.get("ticket_min", 0)),
                    investor.get("ticket_max_norm", investor.get("ticket_max", 0)),
                )
                semantic = float(inv_sim[p_idx, i_idx]) if inv_sim.shape[1] > i_idx else 0.0
                score = semantic * 0.45 + sector_fit * 0.20 + stage_fit * 0.10 + geo_fit * 0.15 + budget_fit * 0.10
                investor_best = max(investor_best, score)
            top_scores["Investors"].append(investor_best * 100)
            if investor_best >= 0.58:
                matched_projects["Investors"] += 1

            volunteer_best = 0.0
            for v_idx, (_, volunteer) in enumerate(self.ms.volunteers_df.iterrows()):
                skill_fit = self._overlap_ratio(p_skills, self._to_list(volunteer.get("skills_norm")))
                sdg_fit = self._overlap_ratio(p_sdg, self._to_list(volunteer.get("sdg_norm")))
                sector_fit = self._overlap_ratio(p_sector, self._to_list(volunteer.get("sector_norm")))
                geo_fit = 1.0 if str(volunteer.get("country_iso2", "")) == p_country else 0.6 if str(volunteer.get("work_mode_norm", "")) in {"remote", "hybrid"} else 0.3
                semantic = float(vol_sim[p_idx, v_idx]) if vol_sim.shape[1] > v_idx else 0.0
                score = semantic * 0.35 + skill_fit * 0.25 + sdg_fit * 0.10 + sector_fit * 0.10 + geo_fit * 0.20
                volunteer_best = max(volunteer_best, score)
            top_scores["Volunteers"].append(volunteer_best * 100)
            if volunteer_best >= 0.48:
                matched_projects["Volunteers"] += 1

            grant_best = 0.0
            for g_idx, (_, grant) in enumerate(self.ms.grants_df.iterrows()):
                semantic = float(grant_sim[p_idx, g_idx]) if grant_sim.shape[1] > g_idx else 0.0
                sector_fit = self._overlap_ratio(p_sector, self._to_list(grant.get("sector_norm")))
                budget_fit = self._range_fit(
                    p_min,
                    p_max,
                    grant.get("award_floor_norm", 0),
                    grant.get("award_ceiling_norm", 0),
                )
                score = semantic * 0.60 + sector_fit * 0.20 + budget_fit * 0.20
                grant_best = max(grant_best, score)
            top_scores["Grants"].append(grant_best * 100)
            if grant_best >= 0.42:
                matched_projects["Grants"] += 1

            activity_best = 0.0
            for a_idx, (_, activity) in enumerate(self.ms.activities_df.iterrows()):
                semantic = float(act_sim[p_idx, a_idx]) if act_sim.shape[1] > a_idx else 0.0
                sector_fit = self._overlap_ratio(p_sector, self._to_list(activity.get("sector_norm")))
                geo_fit = self._overlap_ratio([p_country], self._to_list(activity.get("recipient_country_norm")))
                results_fit = 1.0 if bool(activity.get("results_present")) else 0.35
                score = semantic * 0.55 + sector_fit * 0.15 + geo_fit * 0.20 + results_fit * 0.10
                activity_best = max(activity_best, score)
            top_scores["Precedents"].append(activity_best * 100)
            if activity_best >= 0.50:
                matched_projects["Precedents"] += 1

        coverage = []
        total_matches = 0
        all_scores = []
        for label in ["Investors", "Volunteers", "Grants", "Precedents"]:
            total_matches += matched_projects[label]
            all_scores.extend(top_scores[label])
            coverage.append(
                {
                    "entity": label,
                    "matched_projects": matched_projects[label],
                    "avg_top_score": round(float(np.mean(top_scores[label])) if top_scores[label] else 0.0, 1),
                }
            )

        snapshot = {
            "coverage": coverage,
            "total_matches": total_matches,
            "avg_match_score": round(float(np.mean(all_scores)) if all_scores else 0.0, 1),
        }
        self._cached_match_snapshot = snapshot
        return snapshot

    def get_executive_overview(self) -> Dict[str, Any]:
        if self._cached_overview is not None:
            return self._cached_overview

        match_snapshot = self._compute_match_snapshot()
        self._cached_overview = {
            "entity_composition": [
                {"name": "Projects", "value": len(self.ms.projects_df)},
                {"name": "Investors", "value": len(self.ms.investors_df)},
                {"name": "Volunteers", "value": len(self.ms.volunteers_df)},
                {"name": "NGOs", "value": len(self.ms.activities_df)},
            ],
            "top_kpis": {
                "total_investors": len(self.ms.investors_df),
                "total_projects": len(self.ms.projects_df),
                "total_volunteers": len(self.ms.volunteers_df),
                "total_ngos": len(self.ms.activities_df),
                "total_matches": match_snapshot["total_matches"],
                "avg_match_score": match_snapshot["avg_match_score"],
            },
            "regional_distribution": self._build_regional_stack(),
            "top_sectors": self._top_sectors(self.ms.projects_df, "sector_norm"),
            "match_coverage": match_snapshot["coverage"],
            "stage_distribution": self._build_stage_distribution(),
        }
        return self._cached_overview

    def _build_stage_distribution(self) -> List[Dict[str, Any]]:
        counts = {}
        if self.ms.projects_df.empty:
            return []
        for stage in self.ms.projects_df.get("stage_norm", []):
            counts[str(stage)] = counts.get(str(stage), 0) + 1
        return [
            {"name": self._humanize(name), "val": val}
            for name, val in sorted(counts.items(), key=lambda item: item[1], reverse=True)
        ]

    def _build_investor_matrix(self) -> List[List[int]]:
        matrix = [[0] * 3 for _ in range(3)]
        label_map = {"low": 0, "moderate": 1, "medium": 1, "high": 2}
        if self.ms.investors_df.empty:
            return matrix
        for _, row in self.ms.investors_df.iterrows():
            risk = label_map.get(str(row.get("risk_appetite", "")).strip().lower(), 1)
            burden = label_map.get(str(row.get("reporting_burden", "")).strip().lower(), 1)
            matrix[risk][burden] += 1
        return matrix

    def _build_project_heatmap(self) -> Dict[str, Any]:
        if self.ms.projects_df.empty or "sector_norm" not in self.ms.projects_df.columns:
            return {"yAxis": [], "xAxis": [], "data": []}

        combos = {}
        sectors = set()
        stages = set()
        for _, row in self.ms.projects_df.iterrows():
            stage = str(row.get("stage_norm", "unknown"))
            for sector in self._to_list(row.get("sector_norm")):
                combos[(sector, stage)] = combos.get((sector, stage), 0) + 1
                sectors.add(sector)
                stages.add(stage)

        sectors = sorted(sectors)
        stages = sorted(stages)
        data = []
        for y_idx, sector in enumerate(sectors):
            for x_idx, stage in enumerate(stages):
                data.append([x_idx, y_idx, combos.get((sector, stage), 0)])

        return {
            "yAxis": [self._humanize(sector) for sector in sectors],
            "xAxis": [self._humanize(stage) for stage in stages],
            "data": data,
        }

    def _build_skill_gap(self) -> List[Dict[str, Any]]:
        demand = {}
        supply = {}
        for _, row in self.ms.projects_df.iterrows():
            for skill in self._to_list(row.get("team_skill_needs_norm")):
                demand[skill] = demand.get(skill, 0) + 1
        for _, row in self.ms.volunteers_df.iterrows():
            for skill in self._to_list(row.get("skills_norm")):
                supply[skill] = supply.get(skill, 0) + 1

        keys = sorted(set(demand) | set(supply), key=lambda key: demand.get(key, 0) + supply.get(key, 0), reverse=True)[:10]
        return [{"skill": self._humanize(key), "demand": demand.get(key, 0), "supply": supply.get(key, 0)} for key in keys]

    def _build_funding_histogram(self) -> List[Dict[str, Any]]:
        bins = [
            ("0-50k", 0, 50000),
            ("50k-150k", 50000, 150000),
            ("150k-500k", 150000, 500000),
            ("500k-1m", 500000, 1000000),
            ("1m+", 1000000, float("inf")),
        ]
        counts = {label: 0 for label, _, _ in bins}
        for _, row in self.ms.projects_df.iterrows():
            value = float(row.get("funding_need_max_norm", row.get("funding_need_max", 0)) or 0)
            for label, low, high in bins:
                if low <= value < high:
                    counts[label] += 1
                    break
        return [{"band": label, "count": counts[label]} for label, _, _ in bins]

    def _build_top_geographies(self) -> List[Dict[str, Any]]:
        counts = {}
        for _, row in self.ms.projects_df.iterrows():
            country = self._display_country(row.get("country_iso2") or row.get("country_norm"))
            counts[country] = counts.get(country, 0) + 1
        return [{"name": name, "val": val} for name, val in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:8]]

    def _build_activity_geography_map(self) -> Dict[str, Any]:
        points: Dict[str, Dict[str, Any]] = {}
        sector_totals: Counter[str] = Counter()
        unlocated_activities = 0

        def get_point(place_id: str, name: str, code: str, place_type: str, coordinates: Dict[str, float] | None) -> Dict[str, Any]:
            existing = points.get(place_id)
            if existing is not None:
                return existing

            point = {
                "id": place_id,
                "code": code,
                "name": name,
                "place_type": place_type,
                "lat": coordinates["lat"] if coordinates else None,
                "lon": coordinates["lon"] if coordinates else None,
                "activity_count": 0,
                "project_count": 0,
                "volunteer_count": 0,
                "investor_count": 0,
                "results_count": 0,
                "sector_counts": Counter(),
                "organization_counts": Counter(),
            }
            points[place_id] = point
            return point

        for _, row in self.ms.activities_df.iterrows():
            primary_sector = self._primary_sector(row)
            organization = str(row.get("reporting_org_name") or row.get("ngo_name") or "Unknown Organization").strip()
            sector_totals[primary_sector] += 1

            country_targets = []
            for raw_country in self._to_list(row.get("recipient_country_norm")):
                code = self._country_code(raw_country)
                name = self._display_country(raw_country)
                if code and name:
                    country_targets.append((f"country:{code}", code, name, country_coordinates(code)))

            targets = country_targets
            if not targets:
                region_targets = []
                for raw_region in self._to_list(row.get("recipient_region_norm")):
                    normalized_code = str(raw_region).strip()
                    name = self._display_region(raw_region)
                    if name and name.lower() != "unknown":
                        region_targets.append(
                            (
                                f"region:{normalized_code or name.lower().replace(' ', '-')}",
                                normalized_code,
                                name,
                                region_coordinates(normalized_code),
                            )
                        )
                targets = region_targets

            if not targets:
                unlocated_activities += 1
                continue

            seen_ids = set()
            for place_id, code, name, coordinates in targets:
                if place_id in seen_ids:
                    continue
                seen_ids.add(place_id)
                point = get_point(place_id, name, code, "country" if place_id.startswith("country:") else "region", coordinates)
                point["activity_count"] += 1
                point["results_count"] += 1 if bool(row.get("results_present")) else 0
                point["sector_counts"][primary_sector] += 1
                point["organization_counts"][organization] += 1

        for _, row in self.ms.projects_df.iterrows():
            code = self._country_code(row.get("country_iso2") or row.get("country_norm"))
            if not code:
                continue
            point = get_point(f"country:{code}", self._display_country(code), code, "country", country_coordinates(code))
            point["project_count"] += 1

        for _, row in self.ms.volunteers_df.iterrows():
            code = self._country_code(row.get("country_iso2") or row.get("country_norm"))
            if not code:
                continue
            point = get_point(f"country:{code}", self._display_country(code), code, "country", country_coordinates(code))
            point["volunteer_count"] += 1

        for _, row in self.ms.investors_df.iterrows():
            code = self._country_code(row.get("domicile_country_iso2") or row.get("domicile_country_norm"))
            if not code:
                continue
            point = get_point(f"country:{code}", self._display_country(code), code, "country", country_coordinates(code))
            point["investor_count"] += 1

        prepared_points = []
        mapped_locations = 0
        top_activity_location = {"name": "No geography", "count": 0}
        top_ecosystem_location = {"name": "No geography", "count": 0}

        for point in points.values():
            sector_counts = point.pop("sector_counts")
            org_counts = point.pop("organization_counts")
            ecosystem_total = point["activity_count"] + point["project_count"] + point["volunteer_count"] + point["investor_count"]
            point["ecosystem_total"] = ecosystem_total
            point["is_mappable"] = point["lat"] is not None and point["lon"] is not None
            point["dominant_sector"] = sector_counts.most_common(1)[0][0] if sector_counts else "General"
            point["sector_breakdown"] = [{"name": name, "value": value} for name, value in sector_counts.most_common(6)]
            point["sector_counts"] = dict(sector_counts)
            point["sample_organizations"] = [name for name, _ in org_counts.most_common(3)]

            if point["is_mappable"]:
                mapped_locations += 1
            if point["activity_count"] > top_activity_location["count"]:
                top_activity_location = {"name": point["name"], "count": point["activity_count"]}
            if ecosystem_total > top_ecosystem_location["count"]:
                top_ecosystem_location = {"name": point["name"], "count": ecosystem_total}
            prepared_points.append(point)

        prepared_points.sort(key=lambda item: (item["activity_count"], item["ecosystem_total"], item["name"]), reverse=True)

        return {
            "points": prepared_points,
            "filters": {
                "sectors": [name for name, _ in sector_totals.most_common()],
                "layers": ["activity_count", "ecosystem_total", "project_count", "volunteer_count", "investor_count"],
                "place_types": ["country", "region"],
            },
            "summary": {
                "tracked_activities": len(self.ms.activities_df),
                "mapped_locations": mapped_locations,
                "distinct_places": len(prepared_points),
                "unlocated_activities": unlocated_activities,
                "top_activity_location": top_activity_location,
                "top_ecosystem_location": top_ecosystem_location,
            },
        }

    def get_entity_intelligence(self) -> Dict[str, Any]:
        if self._cached_entities is not None:
            return self._cached_entities

        self._cached_entities = {
            "investor_risk_reporting_matrix": self._build_investor_matrix(),
            "project_sector_stage_heatmap": self._build_project_heatmap(),
            "skill_demand_supply": self._build_skill_gap(),
            "funding_histogram": self._build_funding_histogram(),
            "top_project_geographies": self._build_top_geographies(),
            "project_stage_distribution": self._build_stage_distribution(),
            "activity_geography_map": self._build_activity_geography_map(),
        }
        return self._cached_entities

    def _sample_project_rows(self, limit: int = 12, max_per_sector: int = 2) -> List[Dict[str, Any]]:
        if self.ms.projects_df.empty:
            return []

        sector_counts = {}
        rows = [row.to_dict() for _, row in self.ms.projects_df.iterrows()]
        for row in rows:
            for sector in self._to_list(row.get("sector_norm")) or ["general"]:
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

        ordered_sectors = [sector for sector, _ in sorted(sector_counts.items(), key=lambda item: item[1], reverse=True)]
        selected_ids = set()
        selected_rows = []
        per_sector_counts = {}

        for sector in ordered_sectors:
            for row in rows:
                project_id = str(row.get("project_id"))
                if project_id in selected_ids:
                    continue
                sectors = self._to_list(row.get("sector_norm"))
                if sector in sectors and per_sector_counts.get(sector, 0) < max_per_sector:
                    selected_rows.append(row)
                    selected_ids.add(project_id)
                    per_sector_counts[sector] = per_sector_counts.get(sector, 0) + 1
                    if len(selected_rows) >= limit:
                        return selected_rows

        for row in rows:
            project_id = str(row.get("project_id"))
            if project_id not in selected_ids:
                selected_rows.append(row)
                selected_ids.add(project_id)
                if len(selected_rows) >= limit:
                    break
        return selected_rows

    def _build_semantic_map(self) -> List[Dict[str, Any]]:
        logger.info("Computing semantic cluster coordinates...")
        points = []
        labelled_embeddings = []
        datasets = [
            ("Project", self.ms.projects_df, self.ms.project_embs, 36, "project"),
            ("Investor", self.ms.investors_df, self.ms.investor_embs, 26, "investor"),
            ("Volunteer", self.ms.volunteers_df, self.ms.volunteer_embs, 26, "volunteer"),
            ("Precedent", self.ms.activities_df, self.ms.activity_embs, 36, "precedent"),
        ]

        for label, df, emb_array, take, entity_type in datasets:
            if df.empty or not isinstance(emb_array, np.ndarray) or emb_array.size == 0:
                continue
            count = min(len(df), len(emb_array), take)
            if count <= 0:
                continue
            indices = np.linspace(0, min(len(df), len(emb_array)) - 1, num=count, dtype=int)
            for idx in indices:
                row = df.iloc[int(idx)].to_dict()
                recipient_regions = self._to_list(row.get("recipient_region_norm"))
                recipient_countries = self._to_list(row.get("recipient_country_norm"))
                display_region = (
                    self._display_region(row.get("region_norm"))
                    if row.get("region_norm")
                    else self._display_region(recipient_regions[0])
                    if recipient_regions
                    else self._display_country(row.get("country_iso2") or row.get("country_norm"))
                    if row.get("country_iso2") or row.get("country_norm")
                    else self._display_country(recipient_countries[0])
                    if recipient_countries
                    else "Global"
                )
                labelled_embeddings.append(
                    {
                        "type": label,
                        "name": self._display_name(row, entity_type),
                        "sector": self._primary_sector(row),
                        "region": display_region,
                        "embedding": emb_array[int(idx)],
                    }
                )

        if not labelled_embeddings:
            return points

        matrix = np.vstack([item["embedding"] for item in labelled_embeddings])
        perplexity = min(28, max(5, len(matrix) // 10))
        coords = TSNE(n_components=2, perplexity=perplexity, random_state=42, init="random").fit_transform(matrix)

        for idx, item in enumerate(labelled_embeddings):
            points.append(
                {
                    "id": idx,
                    "x": float(coords[idx][0]),
                    "y": float(coords[idx][1]),
                    "type": item["type"],
                    "name": item["name"],
                    "sector": item["sector"],
                    "region": item["region"],
                }
            )
        return points

    def _build_match_landscape(self) -> Dict[str, Any]:
        project_rows = self._sample_project_rows(limit=16, max_per_sector=3)
        if not project_rows:
            return {
                "corridors": [],
                "network": {"nodes": [], "edges": [], "summary": {"projects": 0, "connections": 0, "avg_score": 0.0}},
                "project_panels": [],
                "signal": {"lead_sector": "No Sector", "fit_index": 0.0, "narrative": "No projects available for match analysis."},
            }

        corridor_book = {}
        network_nodes = {}
        network_edges = []
        project_panels = []
        edge_scores = []
        relation_mix = {"investor": 0, "volunteer": 0, "grant": 0, "precedent": 0}

        network_project_ids = {str(row.get("project_id")) for row in project_rows[:8]}
        thresholds = {"investor": 68.0, "volunteer": 60.0, "grant": 55.0, "precedent": 56.0}

        def register_corridor_score(bucket: dict, key: str, score: float):
            bucket.setdefault(f"{key}_scores", [])
            bucket[f"{key}_scores"].append(float(score))

        def register_node(node_id: str, name: str, group: str, value: float, subtitle: str, score: float | None = None):
            existing = network_nodes.get(node_id)
            payload = {
                "id": node_id,
                "name": name,
                "group": group,
                "value": round(float(value), 1),
                "subtitle": subtitle,
            }
            if score is not None:
                payload["score"] = round(float(score), 1)
            if existing is None or payload["value"] > existing.get("value", 0):
                network_nodes[node_id] = payload

        def maybe_add_relation(project_row: dict, relation_type: str, match: dict | None):
            if not match:
                return None

            if relation_type == "investor":
                score = self._safe_float(match.get("total_score"))
                node_id = f"investor:{match.get('investor_id')}"
                register_node(node_id, self._truncate(match.get("investor_name", "Unknown Investor"), 30), "investor", max(26.0, score), match.get("rationale", "Investor fit"), score=score)
                label = "Investor"
            elif relation_type == "volunteer":
                score = self._safe_float(match.get("total_score"))
                node_id = f"volunteer:{match.get('volunteer_id')}"
                register_node(node_id, self._truncate(match.get("name", "Unknown Volunteer"), 28), "volunteer", max(24.0, score), match.get("rationale", "Volunteer fit"), score=score)
                label = "Volunteer"
            elif relation_type == "grant":
                score = self._safe_float(match.get("relevance_score"))
                node_id = f"grant:{match.get('grant_id')}"
                register_node(node_id, self._truncate(match.get("title", "Grant Opportunity"), 32), "grant", max(22.0, score), match.get("funder", "Grant fit"), score=score)
                label = "Grant"
            else:
                score = self._safe_float(match.get("relevance_score"))
                node_id = f"precedent:{match.get('activity_id')}"
                register_node(node_id, self._truncate(match.get("reporting_org", "Historical Precedent"), 32), "precedent", max(22.0, score), match.get("rationale", "Precedent fit"), score=score)
                label = "Precedent"

            if score < thresholds[relation_type]:
                return None

            relation_mix[relation_type] += 1
            edge_scores.append(score)
            network_edges.append(
                {
                    "source": f"project:{project_row.get('project_id')}",
                    "target": node_id,
                    "value": round(score, 1),
                    "relation": label,
                    "rationale": match.get("rationale", f"{label} fit"),
                }
            )
            return {"name": network_nodes[node_id]["name"], "score": round(score, 1), "rationale": match.get("rationale", "")}

        for project_row in project_rows:
            project_id = str(project_row.get("project_id"))
            project_title = self._display_name(project_row, "project")
            sector = self._primary_sector(project_row)
            stage = self._humanize(project_row.get("stage_norm", "unknown"))

            investor_matches = self.ms.match_investors(project_id, top_k=2)
            volunteer_matches = self.ms.match_volunteers(project_id, top_k=2)
            grant_matches = self.ms.retrieve_grants(project_id, top_k=1)
            precedent_matches = self.ms.retrieve_activities(project_id, top_k=1)

            top_investor = investor_matches[0] if investor_matches else None
            top_volunteer = volunteer_matches[0] if volunteer_matches else None
            top_grant = grant_matches[0] if grant_matches else None
            top_precedent = precedent_matches[0] if precedent_matches else None

            bucket = corridor_book.setdefault(
                sector,
                {
                    "sector": sector,
                    "projects": 0,
                    "sample_projects": [],
                    "investor_scores": [],
                    "volunteer_scores": [],
                    "grant_scores": [],
                    "precedent_scores": [],
                },
            )
            bucket["projects"] += 1
            if len(bucket["sample_projects"]) < 3:
                bucket["sample_projects"].append(project_title)
            if top_investor:
                register_corridor_score(bucket, "investor", self._safe_float(top_investor.get("total_score")))
            if top_volunteer:
                register_corridor_score(bucket, "volunteer", self._safe_float(top_volunteer.get("total_score")))
            if top_grant:
                register_corridor_score(bucket, "grant", self._safe_float(top_grant.get("relevance_score")))
            if top_precedent:
                register_corridor_score(bucket, "precedent", self._safe_float(top_precedent.get("relevance_score")))

            if project_id not in network_project_ids:
                continue

            register_node(f"project:{project_id}", project_title, "project", 42.0, f"{sector} | {stage}")
            investor_panel = maybe_add_relation(project_row, "investor", top_investor)
            volunteer_panel = maybe_add_relation(project_row, "volunteer", top_volunteer)
            grant_panel = maybe_add_relation(project_row, "grant", top_grant)
            precedent_panel = maybe_add_relation(project_row, "precedent", top_precedent)

            project_panels.append(
                {
                    "project_id": project_id,
                    "project_title": project_title,
                    "sector": sector,
                    "stage": stage,
                    "country": self._display_country(project_row.get("country_iso2") or project_row.get("country_norm")),
                    "investor": investor_panel,
                    "volunteer": volunteer_panel,
                    "grant": grant_panel,
                    "precedent": precedent_panel,
                }
            )

        corridors = []
        for sector, bucket in corridor_book.items():
            avg_investor = round(float(np.mean(bucket["investor_scores"])) if bucket["investor_scores"] else 0.0, 1)
            avg_volunteer = round(float(np.mean(bucket["volunteer_scores"])) if bucket["volunteer_scores"] else 0.0, 1)
            avg_grant = round(float(np.mean(bucket["grant_scores"])) if bucket["grant_scores"] else 0.0, 1)
            avg_precedent = round(float(np.mean(bucket["precedent_scores"])) if bucket["precedent_scores"] else 0.0, 1)
            fit_index = round(avg_investor * 0.35 + avg_volunteer * 0.20 + avg_grant * 0.25 + avg_precedent * 0.20, 1)
            corridors.append(
                {
                    "sector": sector,
                    "projects": bucket["projects"],
                    "avg_investor_score": avg_investor,
                    "avg_volunteer_score": avg_volunteer,
                    "avg_grant_score": avg_grant,
                    "avg_precedent_score": avg_precedent,
                    "fit_index": fit_index,
                    "sample_projects": bucket["sample_projects"],
                }
            )

        corridors.sort(key=lambda item: (item["fit_index"], item["projects"]), reverse=True)
        lead_corridor = corridors[0] if corridors else None

        match_network = {
            "nodes": list(network_nodes.values()),
            "edges": network_edges,
            "summary": {
                "projects": len(network_project_ids),
                "connections": len(network_edges),
                "avg_score": round(float(np.mean(edge_scores)) if edge_scores else 0.0, 1),
                "investor_edges": relation_mix["investor"],
                "volunteer_edges": relation_mix["volunteer"],
                "grant_edges": relation_mix["grant"],
                "precedent_edges": relation_mix["precedent"],
            },
        }

        signal = {
            "lead_sector": lead_corridor["sector"] if lead_corridor else "No Sector",
            "fit_index": lead_corridor["fit_index"] if lead_corridor else 0.0,
            "narrative": (
                f"{lead_corridor['sector']} is the strongest current corridor because sampled projects in this space show the best combined investor, volunteer, grant, and precedent support."
                if lead_corridor
                else "No corridor signal available yet."
            ),
        }

        return {
            "corridors": corridors[:8],
            "network": match_network,
            "project_panels": project_panels[:6],
            "signal": signal,
        }

    def get_cluster_data(self) -> Dict[str, Any]:
        if self._cached_clusters is not None:
            return self._cached_clusters

        semantic_map = self._build_semantic_map()
        match_landscape = self._build_match_landscape()

        self._cached_clusters = {
            "umap_nodes": semantic_map,
            "semantic_map": semantic_map,
            "match_corridors": match_landscape["corridors"],
            "match_network": match_landscape["network"],
            "ecosystem_graph": match_landscape["network"],
            "project_match_panels": match_landscape["project_panels"],
            "cluster_signal": match_landscape["signal"],
        }
        return self._cached_clusters
