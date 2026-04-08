import pandas as pd


class TextComposer:
    """
    Composes semantically rich text from canonicalized fields so structured and
    semantic retrieval stay aligned.
    """

    @staticmethod
    def _join_tokens(value) -> str:
        if isinstance(value, list):
            return ", ".join(str(item).replace("_", " ") for item in value if str(item).strip())
        if value is None:
            return ""
        return str(value)

    def compose_project_text(self, row: pd.Series) -> str:
        parts = [
            f"Project Title: {row.get('project_title', '')}",
            f"Geography: {row.get('country_norm', '')} / {str(row.get('region_norm', '')).replace('_', ' ')}",
            f"Sector Focus: {self._join_tokens(row.get('sector_norm', []))}",
            f"SDG Alignment: {self._join_tokens(row.get('sdg_labels', row.get('sdg_norm', [])))}",
            f"Development Stage: {row.get('stage_norm', '')}",
            f"Team Skill Needs: {self._join_tokens(row.get('team_skill_needs_norm', []))}",
            f"Evidence Signals: {self._join_tokens(row.get('evidence_tokens_norm', []))}",
            f"Delivery Model: {self._join_tokens(row.get('delivery_model_norm', []))}",
            f"Target Beneficiaries: {self._join_tokens(row.get('beneficiary_norm', []))}",
            f"Problem Statement: {row.get('problem_statement', '')}",
            f"Solution Summary: {row.get('solution_summary', '')}",
        ]
        return ". ".join(part for part in parts if part and not part.endswith(": ")).strip()

    def compose_investor_text(self, row: pd.Series) -> str:
        parts = [
            f"Investor Name: {row.get('name', '')}",
            f"Domicile: {row.get('domicile_country_norm', '')}",
            f"Geography Focus: {self._join_tokens(row.get('geography_focus_norm', []))}",
            f"Region Focus: {self._join_tokens(row.get('region_focus_norm', []))}",
            f"Target Sectors: {self._join_tokens(row.get('sector_norm', []))}",
            f"Target SDGs: {self._join_tokens(row.get('sdg_labels', row.get('sdg_norm', [])))}",
            f"Stage Preference: {self._join_tokens(row.get('stage_norm', []))}",
            f"Instruments: {self._join_tokens(row.get('instrument_norm', []))}",
            f"Impact Framework: {row.get('impact_framework', '')}",
            f"Thesis: {row.get('thesis_text', '')}",
        ]
        return ". ".join(part for part in parts if part and not part.endswith(": ")).strip()

    def compose_volunteer_text(self, row: pd.Series) -> str:
        parts = [
            f"Volunteer Name: {row.get('full_name', '')}",
            f"Role: {row.get('role_title', '')}",
            f"Country: {row.get('country_norm', '')}",
            f"Languages: {self._join_tokens(row.get('language_norm', []))}",
            f"Preferred Sectors: {self._join_tokens(row.get('sector_norm', []))}",
            f"Preferred SDGs: {self._join_tokens(row.get('sdg_labels', row.get('sdg_norm', [])))}",
            f"Skills: {self._join_tokens(row.get('skills_norm', []))}",
            f"Work Mode: {row.get('work_mode_norm', '')}",
            f"Travel Willingness: {row.get('travel_willingness_norm', '')}",
            f"Availability Hours: {row.get('availability_hours_norm', '')}",
            f"Bio: {row.get('bio_text', '')}",
        ]
        return ". ".join(part for part in parts if part and not part.endswith(": ")).strip()

    def compose_grant_text(self, row: pd.Series) -> str:
        parts = [
            f"Grant Title: {row.get('title', '')}",
            f"Funder: {row.get('funder_name', '')}",
            f"Instruments: {self._join_tokens(row.get('instrument_norm', []))}",
            f"Funding Categories: {self._join_tokens(row.get('funding_categories_norm', []))}",
            f"Applicant Types: {self._join_tokens(row.get('applicant_types_norm', []))}",
            f"Relevant Sectors: {self._join_tokens(row.get('sector_norm', []))}",
            f"Description: {row.get('description', '')}",
        ]
        return ". ".join(part for part in parts if part and not part.endswith(": ")).strip()

    def compose_activity_text(self, row: pd.Series) -> str:
        parts = [
            f"Organization: {row.get('ngo_name', row.get('reporting_org_name', ''))}",
            f"Activity Title: {row.get('title', '')}",
            f"Countries: {self._join_tokens(row.get('recipient_country_norm', []))}",
            f"Regions: {self._join_tokens(row.get('recipient_region_norm', []))}",
            f"Sectors: {self._join_tokens(row.get('sector_norm', []))}",
            f"Keywords: {self._join_tokens(row.get('matched_keywords_norm', []))}",
            f"Description: {row.get('description', '')}",
            f"Results: {row.get('results_text', '')}",
        ]
        return ". ".join(part for part in parts if part and not part.endswith(": ")).strip()

    def build_embeddings_corpus(self, df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
        df_out = df.copy()
        if df_out.empty:
            df_out["text_full"] = ""
            return df_out

        if entity_type == "project":
            df_out["text_full"] = df_out.apply(self.compose_project_text, axis=1)
        elif entity_type == "investor":
            df_out["text_full"] = df_out.apply(self.compose_investor_text, axis=1)
        elif entity_type == "volunteer":
            df_out["text_full"] = df_out.apply(self.compose_volunteer_text, axis=1)
        elif entity_type == "grant":
            df_out["text_full"] = df_out.apply(self.compose_grant_text, axis=1)
        elif entity_type == "activity":
            df_out["text_full"] = df_out.apply(self.compose_activity_text, axis=1)
        else:
            df_out["text_full"] = df_out.astype(str).apply(lambda row: " ".join(row), axis=1)

        return df_out
