# Ecowise Implementation Phases

## Phase 1: Canonical Core
- Normalize all source families into a shared schema for geography, SDGs, sectors, stages, skills, evidence, instruments, and funding ranges.
- Rebuild the feature store so matching and analytics consume canonical fields instead of raw strings.
- Align semantic text generation with canonical fields for projects, investors, volunteers, grants, and external activities.
- Load project and activity artifacts into the runtime service layer.
- Expose the missing volunteer and external activity retrieval endpoints.

## Phase 2: Matching Intelligence
- Strengthen hard filters for investor, volunteer, grant, and precedent matching.
- Expand the readiness score into a fuller sub-score framework with blockers and risk flags tied to real normalized evidence.
- Add reusable aggregate match tables and explanation-ready metadata.
- Integrate the LLM enrichment layer beyond stubs with strict JSON outputs and stable caching.
- Prepare trainable rerankers and offline evaluation datasets for LightGBM / XGBoost.

## Phase 3: Executive Product
- Replace mock analytics with backend-generated aggregates for counts, distributions, clusters, and graph edges.
- Connect the premium dashboard surfaces to the real analytics endpoints.
- Build the final three-page executive experience: Executive Overview, Entity Intelligence, and Matching & Clusters.
- Add production persistence with PostgreSQL and pgvector, operational setup, and test coverage.
- Package sample outputs, setup instructions, and validation docs for a reproducible internal platform release.
