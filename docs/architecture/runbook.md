# Ecowise Platform Runbook

## System Architecture Assumptions
- **Datastore:** Local Pandas + Parquet for caching feature vectors allows rapid dev, built to be easily swapped to `pgvector` out-of-the-box using the existing `SemanticVectorStore` abstraction.
- **True Success Labels:** As specified, since true outcomes are missing, the system uses a heuristic `ReadinessScorer` logic in place of a supervised learner, serving as a reliable v1 fallback.
- **LLM Cost Mitigation:** External enrichment API calls are strictly wrapped in the `llm_enricher.py` stub to cache exact outputs locally to avoid API burn rate.

## Setup Instructions

### Backend (Python 3.10+)
1. `cd backend`
2. `python -m venv venv`
3. `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. `pip install -r requirements.txt`
5. **Ingest Data:** Run the ingestion pipeline to parse the raw outputs.
   `python ../scripts/ingest/load_data.py`
6. **Build Vectors & Features:** 
   `python ../scripts/build_features/feature_pipeline.py`
7. **Run API Server:**
   `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

### Frontend (Node.js 18+)
1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. The React dashboard will be live at `http://localhost:5173`.

## API Usage Examples

**Score Project Readiness:**
```bash
curl -X POST "http://localhost:8000/projects/1/score-readiness"
```

**Match Top 5 Investors:**
```bash
curl -X POST "http://localhost:8000/projects/1/match-investors?top_k=5"
```

**Retrieve Relevant Grants:**
```bash
curl -X POST "http://localhost:8000/projects/1/retrieve-grants"
```
