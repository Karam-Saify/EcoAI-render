import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ..ml.embeddings.vector_store import SemanticVectorStore
from ..ml.explainability.llm_enricher import LLMEnricherStub
from ..ml.features.pair_featurizer import PairFeaturizer
from ..ml.matchers.investor_matcher import InvestorMatcher
from ..ml.matchers.volunteer_matcher import VolunteerMatcher
from ..ml.retrievers.activity_retriever import ActivityRetriever
from ..ml.retrievers.grant_retriever import GrantRetriever
from ..ml.scorers.readiness_scorer import ReadinessScorer

logging.basicConfig(level=logging.INFO)


class GlobalMatchingService:
    """
    Orchestrates the singleton ML pipeline state for fast API inference.
    """

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.feature_dir = self.base_dir / "data" / "feature_store"
        self.vector_dir = self.base_dir / "data" / "vectors"

        # Datasets
        self.projects_df = pd.DataFrame()
        self.investors_df = pd.DataFrame()
        self.volunteers_df = pd.DataFrame()
        self.grants_df = pd.DataFrame()
        self.activities_df = pd.DataFrame()

        # Vectors
        self.project_embs = np.array([])
        self.investor_embs = np.array([])
        self.volunteer_embs = np.array([])
        self.grant_embs = np.array([])
        self.activity_embs = np.array([])

        # Modules
        self.vector_store = SemanticVectorStore()
        self.featurizer = PairFeaturizer()
        self.investor_matcher = InvestorMatcher(self.featurizer)
        self.volunteer_matcher = VolunteerMatcher()
        self.grant_retriever = GrantRetriever(self.vector_store)
        self.activity_retriever = ActivityRetriever(self.vector_store)
        self.readiness_scorer = ReadinessScorer()
        self.llm_enricher = LLMEnricherStub(str(self.base_dir / "artifacts" / "model_outputs" / "llm_cache"))

    def load_artifacts(self):
        """Loads feature tables and NPY arrays into RAM."""
        try:
            logging.info("Loading feature store DataFrames...")
            dataset_targets = {
                "projects": "projects_df",
                "investors": "investors_df",
                "volunteers": "volunteers_df",
                "grants": "grants_df",
                "activities": "activities_df",
            }
            for entity, attr_name in dataset_targets.items():
                path = self.feature_dir / f"{entity}_features.parquet"
                if path.exists():
                    setattr(self, attr_name, pd.read_parquet(path))

            logging.info("Loading NPY arrays...")
            vector_targets = {
                "projects": "project_embs",
                "investors": "investor_embs",
                "volunteers": "volunteer_embs",
                "grants": "grant_embs",
                "activities": "activity_embs",
            }
            for entity, attr_name in vector_targets.items():
                path = self.vector_dir / f"{entity}_vectors.npy"
                if path.exists():
                    setattr(self, attr_name, np.load(path))

            logging.info("Successfully loaded ML models and data into RAM.")
        except Exception as exc:
            logging.error(f"Failed to load artifacts: {exc}")

    def _get_project(self, project_id: str) -> dict:
        if self.projects_df.empty:
            return {}
        matches = self.projects_df[self.projects_df["project_id"].astype(str) == str(project_id)]
        return matches.iloc[0].to_dict() if not matches.empty else {}

    def score_readiness(self, project_id: str):
        project = self._get_project(project_id)
        if not project:
            return None
        investor_matches = self.match_investors(project_id, top_k=3)
        volunteer_matches = self.match_volunteers(project_id, top_k=3)
        grant_matches = self.retrieve_grants(project_id, top_k=3)
        activity_matches = self.retrieve_activities(project_id, top_k=3)
        context = self.readiness_scorer.build_context(
            investor_matches=investor_matches,
            volunteer_matches=volunteer_matches,
            grant_matches=grant_matches,
            activity_matches=activity_matches,
        )
        return self.readiness_scorer.score_project(project, context=context)

    def match_investors(self, project_id: str, top_k: int = 10):
        project = self._get_project(project_id)
        if not project or self.investors_df.empty:
            return []

        text = project.get("text_full", "")
        sims = self.vector_store.query_similarity(text, self.investor_embs) if isinstance(text, str) and text else None
        return self.investor_matcher.match(project, self.investors_df, sims, top_k)

    def match_volunteers(self, project_id: str, top_k: int = 10):
        project = self._get_project(project_id)
        if not project or self.volunteers_df.empty:
            return []

        text = project.get("text_full", "")
        sims = self.vector_store.query_similarity(text, self.volunteer_embs) if isinstance(text, str) and text else None
        return self.volunteer_matcher.match(project, self.volunteers_df, sims, top_k)

    def retrieve_grants(self, project_id: str, top_k: int = 5):
        project = self._get_project(project_id)
        if not project or self.grants_df.empty:
            return []

        text = project.get("text_full", "")
        stage = project.get("stage_norm", "")
        return self.grant_retriever.retrieve_grants(text, stage, self.grants_df, self.grant_embs, top_k, project=project)

    def retrieve_activities(self, project_id: str, top_k: int = 5):
        project = self._get_project(project_id)
        if not project or self.activities_df.empty:
            return []

        text = project.get("text_full", "")
        sector = project.get("sector_norm", [])
        return self.activity_retriever.retrieve_precedents(
            text,
            sector,
            self.activities_df,
            self.activity_embs,
            top_k,
            project=project,
        )

    def enrich_project(self, project_id: str):
        project = self._get_project(project_id)
        if not project:
            return None
        return self.llm_enricher.enrich_project(project)

    def get_analytics(self) -> dict:
        sectors = {}
        if not self.projects_df.empty and "sector_norm" in self.projects_df.columns:
            for sector_list in self.projects_df["sector_norm"].dropna():
                for sector in sector_list:
                    label = str(sector).replace("_", " ").title()
                    sectors[label] = sectors.get(label, 0) + 1

        dist = [{"name": key, "val": value} for key, value in sorted(sectors.items(), key=lambda item: item[1], reverse=True)[:8]]

        return {
            "total_projects": len(self.projects_df),
            "total_investors": len(self.investors_df),
            "total_volunteers": len(self.volunteers_df),
            "total_grants": len(self.grants_df),
            "total_activities": len(self.activities_df),
            "sector_distribution": dist,
        }

    def trigger_orchestration_script(self, script_name: str):
        script_path = self.base_dir / "scripts" / script_name
        subprocess.Popen([sys.executable, str(script_path)], cwd=str(self.base_dir))


matching_service = GlobalMatchingService()
