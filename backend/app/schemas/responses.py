from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ReadinessResponse(BaseModel):
    total_score: float
    sub_scores: Dict[str, float]
    risk_flags: List[str]
    missing_criticals: List[str]
    improvement_plan: str
    blockers: List[str] = []
    improvement_suggestions: List[str] = []
    context_signals: Optional[Dict[str, float]] = None

class MatchFactor(BaseModel):
    sector_overlap_score: float
    sdg_overlap_score: float
    stage_compatibility: float
    budget_overlap_ratio: float
    semantic_cosine_sim: float
    risk_alignment_score: float

class MatchResult(BaseModel):
    id: str
    name: str
    total_score: float
    rationale: str
    factor_contributions: Optional[Dict[str, float]] = None
    improvement: Optional[str] = None

class RetrievalResult(BaseModel):
    id: str
    title: str
    relevance_score: float
    semantic_confidence: float
    rationale: str
    funder: Optional[str] = None
    application_complexity: Optional[str] = None

class MatchListResponse(BaseModel):
    matches: List[MatchResult]

class RetrievalListResponse(BaseModel):
    results: List[RetrievalResult]

class ActivityRetrievalResult(BaseModel):
    id: str
    title: str
    relevance_score: float
    semantic_confidence: float
    rationale: str
    reporting_org: Optional[str] = None
    description_snippet: Optional[str] = None

class ActivityRetrievalListResponse(BaseModel):
    results: List[ActivityRetrievalResult]

class EnrichmentResponse(BaseModel):
    normalized_tags: Dict[str, Any]
    hidden_needs: List[str]
    quality_indicators: Dict[str, float]
    missing_information: List[str]
    executive_summary: str
    explanation_metadata: Dict[str, Any]

class PipelineStatus(BaseModel):
    status: str
    message: str
    
class SectorDistribution(BaseModel):
    name: str
    val: int

class AnalyticsOverview(BaseModel):
    total_projects: int
    total_investors: int
    total_volunteers: int
    total_grants: int
    total_activities: int
    sector_distribution: List[SectorDistribution]
