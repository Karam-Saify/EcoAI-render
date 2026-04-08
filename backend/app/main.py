from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from .core.config import settings
from .services.matching_service import matching_service
from .services.analytics_service import GlobalAnalyticsService
from .services.job_orchestration_service import ml_job_orchestration_service
from .schemas.responses import (
    ActivityRetrievalListResponse,
    AnalyticsOverview,
    EnrichmentResponse,
    MatchListResponse,
    PipelineStatus,
    ReadinessResponse,
    RetrievalListResponse,
)

analytics_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global analytics_service
    worker_task = None
    # Startup: Load ML artifacts
    matching_service.load_artifacts()
    analytics_service = GlobalAnalyticsService(matching_service)
    if settings.ML_WORKER_ENABLED:
        worker_task = asyncio.create_task(ml_job_orchestration_service.run_forever())
    yield
    # Shutdown logic if any
    ml_job_orchestration_service.stop()
    if worker_task:
        await worker_task

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

# Allow React app to fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.VERSION}

@app.post("/projects/{project_id}/score-readiness", response_model=ReadinessResponse)
def score_project_readiness(project_id: str):
    res = matching_service.score_readiness(project_id)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return res

@app.get("/projects/{project_id}/enrich", response_model=EnrichmentResponse)
def enrich_project_endpoint(project_id: str):
    res = matching_service.enrich_project(project_id)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return res

@app.post("/projects/{project_id}/match-investors", response_model=MatchListResponse)
def match_investors_endpoint(project_id: str, top_k: int = 10):
    res = matching_service.match_investors(project_id, top_k)
    # Mapping dict output to Pydantic models
    matches = []
    for r in res:
        matches.append({
            "id": r["investor_id"],
            "name": r["investor_name"],
            "total_score": r["total_score"],
            "rationale": r["rationale"],
            "factor_contributions": r["factor_contributions"],
            "improvement": r["improvement"]
        })
    return {"matches": matches}

@app.post("/projects/{project_id}/retrieve-grants", response_model=RetrievalListResponse)
def match_grants_endpoint(project_id: str, top_k: int = 5):
    res = matching_service.retrieve_grants(project_id, top_k)
    results = []
    for r in res:
         results.append({
             "id": r["grant_id"],
             "title": r["title"],
             "relevance_score": r["relevance_score"],
             "semantic_confidence": r["semantic_confidence"],
             "rationale": r["rationale"],
             "funder": r["funder"],
             "application_complexity": r["application_complexity"]
         })
    return {"results": results}

@app.post("/projects/{project_id}/match-volunteers", response_model=MatchListResponse)
def match_volunteers_endpoint(project_id: str, top_k: int = 10):
    res = matching_service.match_volunteers(project_id, top_k)
    matches = []
    for r in res:
        matches.append({
            "id": r["volunteer_id"],
            "name": r["name"],
            "total_score": r["total_score"],
            "rationale": r["rationale"],
            "factor_contributions": {
                "skill_fit": r["skill_fit"],
                "operational_fit": r["operational_fit"],
            },
            "improvement": f"Targeted at {r['expertise_level']} support level",
        })
    return {"matches": matches}

@app.post("/projects/{project_id}/retrieve-activities", response_model=ActivityRetrievalListResponse)
def retrieve_activities_endpoint(project_id: str, top_k: int = 5):
    res = matching_service.retrieve_activities(project_id, top_k)
    results = []
    for r in res:
        results.append({
            "id": r["activity_id"],
            "title": r.get("reporting_org", "Historical Activity"),
            "relevance_score": r["relevance_score"],
            "semantic_confidence": r["semantic_confidence"],
            "rationale": r["rationale"],
            "reporting_org": r.get("reporting_org"),
            "description_snippet": r.get("description_snippet"),
        })
    return {"results": results}

@app.get("/api/v2/analytics/overview")
def get_v2_analytics_overview():
    return analytics_service.get_executive_overview()

@app.get("/api/v2/analytics/entities")
def get_v2_entity_intelligence():
    return analytics_service.get_entity_intelligence()

@app.get("/api/v2/analytics/clusters")
def get_v2_network_clusters():
    return analytics_service.get_cluster_data()

@app.get("/api/v1/analytics/overview", response_model=AnalyticsOverview)
def get_analytics_overview():
    return matching_service.get_analytics()

@app.post("/api/v1/pipeline/ingest", response_model=PipelineStatus)
def trigger_data_ingest():
    matching_service.trigger_orchestration_script("ingest/load_data.py")
    return {"status": "started", "message": "Triggered generic ingestion."}

@app.post("/api/v1/pipeline/rebuild-features", response_model=PipelineStatus)
def trigger_data_rebuild():
    matching_service.trigger_orchestration_script("build_features/feature_pipeline.py")
    return {"status": "started", "message": "Rebuilding local feature models."}

@app.post("/api/v1/pipeline/process-ml-jobs")
def process_ml_jobs_once():
    processed = ml_job_orchestration_service.run_once()
    return {"status": "ok", "processed_jobs": processed}

@app.get("/api/v1/pipeline/ml-worker-status")
def get_ml_worker_status():
    return ml_job_orchestration_service.get_status()
