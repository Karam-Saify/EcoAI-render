import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.metrics.pairwise import cosine_similarity

class PairFeaturizer:
    """
    Computes heuristic overlap rules and semantic similarities between pairs.
    E.g., Project <-> Investor overlap scores for LightGBM/XGBoost downstream.
    """
    
    def __init__(self):
        pass

    def _coerce_sequence(self, value) -> List[str]:
        if value is None:
            return []
        if isinstance(value, np.ndarray):
            return [str(item) for item in value.tolist() if str(item).strip()]
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split("|") if item.strip()]
        return []
        
    def _safe_overlap(self, list_a: List[str], list_b: List[str]) -> float:
        list_a = self._coerce_sequence(list_a)
        list_b = self._coerce_sequence(list_b)
        if not list_a or not list_b: return 0.0
        set_a, set_b = set(list_a), set(list_b)
        overlap = len(set_a.intersection(set_b))
        return overlap / min(len(set_a), len(set_b)) 

    def _budget_fit(self, req_min: float, req_max: float, available_min: float, available_max: float) -> float:
        """Computes overlap ratio of required vs available funding ranges."""
        try:
            overlap_min = max(req_min, available_min)
            overlap_max = min(req_max, available_max)
            overlap = max(0, overlap_max - overlap_min)
            req_range = max(1, req_max - req_min)
            return min(overlap / req_range, 1.0)
        except:
            return 0.0

    def compute_project_investor_features(self, project: dict, investor: dict, sem_sim: float = 0.0) -> Dict[str, float]:
        """Calculates precise numerical features for model ranking."""
        
        # Sector and SDG Overlaps
        sector_ol = self._safe_overlap(project.get('sector_norm', []), investor.get('sector_norm', []))
        sdg_ol = self._safe_overlap(project.get('sdg_norm', []), investor.get('sdg_norm', []))
        
        # Stage Fit
        stage_fit = 1.0 if project.get('stage_norm', '') in investor.get('stage_norm', []) else 0.0
        
        # Budget Match
        p_min = project.get('funding_need_min_norm', project.get('funding_need_min', 0)) or 0
        p_max = project.get('funding_need_max_norm', project.get('funding_need_max', 0)) or 0
        i_min = investor.get('ticket_min_norm', investor.get('ticket_min', 0)) or 0
        i_max = investor.get('ticket_max_norm', investor.get('ticket_max', float('inf')))
        i_max = float('inf') if i_max in (None, 0) else i_max
        budget_fit = self._budget_fit(p_min, p_max, i_min, i_max)
        
        # Credibility & Risk
        risk_map = {'low': 0.2, 'moderate': 0.5, 'medium': 0.5, 'high': 1.0}
        p_cred = risk_map.get(str(project.get('credibility_level', 'moderate')).lower(), 0.5)
        # Default investor risk appetite to high (1.0) if missing
        i_risk = risk_map.get(str(investor.get('risk_appetite', 'high')).lower(), 1.0)
        # If project is low cred, and investor is low risk appetite, score drops
        risk_penalty = max(0, p_cred - i_risk) 
        
        return {
            'sector_overlap_score': sector_ol,
            'sdg_overlap_score': sdg_ol,
            'stage_compatibility': stage_fit,
            'budget_overlap_ratio': budget_fit,
            'semantic_cosine_sim': sem_sim,
            'risk_alignment_score': 1.0 - risk_penalty
        }
