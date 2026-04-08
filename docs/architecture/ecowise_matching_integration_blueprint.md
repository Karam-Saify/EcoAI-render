# Ecowise Matching Integration Blueprint

## 1. Goal

Build a robust end-to-end system where:

1. Data is created or updated from the website.
2. Canonical entities are stored in the operational database.
3. Matching and graph-weight jobs are triggered automatically.
4. The ML service computes scores, predictions, and graph edges.
5. Results are persisted back into the database.
6. The website reads only persisted results from the application API.

This keeps the system reliable, explainable, and recoverable.

## 2. System Boundaries

### 2.1 Source of truth

`Ecowise` Go backend and Postgres are the source of truth for:

1. Users and roles
2. Profiles
3. Projects
4. Government issues
5. Issue solutions
6. Skills
7. Sectors
8. Geography fields
9. Workflow states

### 2.2 ML boundary

The Python `EcoAI` backend is the ML and inference service for:

1. Feature generation
2. Embeddings
3. Ranking and prediction
4. Graph weighting
5. Explainability payload generation
6. Retraining pipeline

### 2.3 Frontend boundary

`Ecowise-web` should never call the ML service directly.

The frontend should only call Go application APIs that return:

1. Persisted match results
2. Persisted graph edges
3. Job status
4. Explanations

## 3. Canonical Entities for Matching

Before inference, normalize these entities:

1. `project`
2. `platform_user`
3. `organization_profile`
4. `individual_profile`
5. `government_profile`
6. `government_issue`
7. `issue_solution`
8. `skill`
9. `project_required_skill`
10. `sustainability_sector`

Each entity must expose:

1. Stable primary key
2. Created and updated timestamps
3. Status
4. Geography
5. Sector or category
6. Human-authored text fields
7. Normalized fields for ML use

## 4. Database Additions

### 4.1 `outbox_event`

Purpose: durable event log written in the same transaction as business updates.

Fields:

1. `id`
2. `event_type`
3. `entity_type`
4. `entity_id`
5. `payload_json`
6. `dedupe_key`
7. `status`
8. `created_at`
9. `processed_at`
10. `error_message`

Indexes:

1. `(status, created_at)`
2. `(entity_type, entity_id)`
3. unique `(dedupe_key)`

### 4.2 `ml_inference_job`

Purpose: track every inference attempt.

Fields:

1. `id`
2. `job_type`
3. `entity_type`
4. `entity_id`
5. `requested_by_event_id`
6. `feature_snapshot_id`
7. `model_name`
8. `model_version`
9. `feature_schema_version`
10. `status`
11. `attempt_count`
12. `priority`
13. `started_at`
14. `finished_at`
15. `error_message`
16. `created_at`

Indexes:

1. `(status, priority, created_at)`
2. `(entity_type, entity_id, created_at)`

### 4.3 `entity_feature_snapshot`

Purpose: preserve the exact inference input for reproducibility.

Fields:

1. `id`
2. `entity_type`
3. `entity_id`
4. `feature_schema_version`
5. `source_updated_at`
6. `features_json`
7. `text_payload`
8. `embedding_ref`
9. `created_at`

Indexes:

1. `(entity_type, entity_id, created_at desc)`

### 4.4 `graph_edge`

Purpose: persist graph relationships and their weights for UI use.

Fields:

1. `id`
2. `source_entity_type`
3. `source_entity_id`
4. `target_entity_type`
5. `target_entity_id`
6. `edge_type`
7. `weight`
8. `confidence`
9. `rank`
10. `explanation_json`
11. `model_name`
12. `model_version`
13. `status`
14. `created_at`
15. `updated_at`

Indexes:

1. `(source_entity_type, source_entity_id)`
2. `(target_entity_type, target_entity_id)`
3. `(edge_type, weight desc)`

### 4.5 `model_registry`

Purpose: track active and historical models.

Fields:

1. `id`
2. `model_name`
3. `model_version`
4. `artifact_uri`
5. `feature_schema_version`
6. `training_run_id`
7. `status`
8. `metrics_json`
9. `created_at`
10. `activated_at`

### 4.6 `match_feedback`

Purpose: collect product signals for retraining and evaluation.

Fields:

1. `id`
2. `entity_type`
3. `entity_id`
4. `matched_entity_type`
5. `matched_entity_id`
6. `feedback_type`
7. `feedback_value`
8. `source_user_id`
9. `source_workflow`
10. `context_json`
11. `created_at`

Examples of `feedback_type`:

1. `proposal_accepted`
2. `proposal_upvoted`
3. `interest_created`
4. `match_saved`
5. `match_viewed`
6. `match_rejected`

## 5. Keep and Extend Existing `match_result`

The existing `match_result` table remains the primary persisted ranking result.

Extend it by adding:

1. `matched_entity_type`
2. `feature_schema_version`
3. `computed_at`
4. `expires_at`
5. `confidence_score`
6. `rank`
7. `inference_job_id`

`explanation_json` should contain:

1. Top positive factors
2. Top negative factors
3. Factor contributions
4. Confidence
5. Recommended next action

## 6. Event-Driven Flow

The robust flow should be:

1. User action hits `Ecowise-web`
2. Frontend sends request to Go API
3. Go API validates and writes canonical DB data
4. Same DB transaction writes an `outbox_event`
5. Outbox worker reads pending events
6. Worker normalizes entity data and writes `entity_feature_snapshot`
7. Worker creates `ml_inference_job`
8. Python ML service consumes the job
9. ML service computes:
   1. match results
   2. graph weights
   3. explanations
   4. confidence values
10. ML service writes results back to Postgres
11. Go API serves the latest persisted results
12. Frontend refreshes and renders results
13. User actions on results create `match_feedback`

## 7. Job Types

Define these initial job types:

1. `project_match_refresh`
2. `issue_match_refresh`
3. `solution_support_prediction`
4. `graph_edge_refresh`
5. `entity_embedding_refresh`
6. `feature_snapshot_refresh`
7. `full_recompute`

## 8. Job Status Lifecycle

Use these statuses:

1. `pending`
2. `running`
3. `succeeded`
4. `failed`
5. `retry_scheduled`
6. `stale`
7. `cancelled`

Rules:

1. Jobs must be idempotent.
2. Failed jobs must retain the error message.
3. Repeated entity updates should mark older unfinished jobs as `stale` when appropriate.

## 9. API Contract

### 9.1 Operational APIs in Go

1. `POST /api/v1/projects/:id/refresh-matches`
2. `POST /api/v1/issues/:id/refresh-matches`
3. `GET /api/v1/projects/:id/matches`
4. `GET /api/v1/issues/:id/matches`
5. `GET /api/v1/entities/:type/:id/graph`
6. `GET /api/v1/jobs/:id`
7. `POST /api/v1/match-feedback`

### 9.2 Internal worker or ML APIs

Keep these internal only:

1. `POST /internal/inference/run`
2. `POST /internal/embeddings/rebuild`
3. `POST /internal/features/rebuild`
4. `POST /internal/training/run`

## 10. Feature Engineering Strategy

Do not start with a pure black-box model.

Use a hybrid stack:

1. deterministic business features
2. semantic embeddings
3. learned ranker on top

### 10.1 Deterministic features

Examples:

1. sector overlap
2. geography overlap
3. skill overlap
4. stage or funding fit
5. profile completeness
6. credibility signals
7. recency
8. urgency alignment
9. delivery capacity

### 10.2 Semantic features

Use embeddings for:

1. project to organization similarity
2. issue to solution similarity
3. project to donor or investor relevance
4. project to precedent retrieval

### 10.3 First learned model

Use a gradient-boosted model first:

1. LightGBM
2. XGBoost

Prefer ranking or calibrated classification before deep learning.

## 11. Prediction Targets

Define targets clearly.

Initial targets:

1. probability an organization is a strong match for a project
2. probability an individual is a strong contributor match
3. probability a proposal will receive strong support
4. probability an edge is important enough to display in the graph

Training labels should come from product behavior:

1. accepted proposal
2. upvote
3. contributor interest
4. shortlist or save
5. successful collaboration outcome later

## 12. Graph Weighting Design

Do not reuse match score directly as graph weight.

Use a separate edge formula:

`edge_weight = a*semantic_similarity + b*feature_fit + c*behavior_signal + d*confidence - e*staleness`

Store:

1. raw weight
2. normalized weight
3. confidence
4. explanation
5. model version

This makes graph rendering stable and explainable.

## 13. Reliability Rules

To make the system robust:

1. All business writes must be transactional.
2. Outbox events must be written in the same transaction as entity updates.
3. Inference must be asynchronous.
4. Results must be persisted before UI reads them.
5. Previous results must remain readable if a new inference job fails.
6. Model outputs must always include version metadata.
7. Every inference input must be reproducible from a stored snapshot.
8. Jobs must retry with backoff.
9. Failed jobs must land in a visible failure state, not disappear.
10. Critical APIs must have timeouts and circuit breakers.

## 14. Rollout Phases

### Phase 1

1. Add orchestration tables
2. Add outbox pattern
3. Persist heuristic match scores in `match_result`
4. Serve persisted results through Go APIs

### Phase 2

1. Add embeddings
2. Add `entity_feature_snapshot`
3. Add semantic similarity to rankings
4. Add explainability payloads

### Phase 3

1. Train first gradient-boosted ranker
2. Register model in `model_registry`
3. Add `confidence_score`
4. Add shadow evaluation against heuristic baseline

### Phase 4

1. Add `graph_edge`
2. Compute graph weights from hybrid scoring
3. Expose graph APIs for frontend consumption

### Phase 5

1. Add `match_feedback`
2. Add retraining pipeline
3. Add offline and online evaluation dashboards

## 15. Minimum Testing Requirements

### 15.1 Database and workflow tests

1. entity update writes outbox event
2. duplicate event does not duplicate final result
3. failed inference leaves prior result intact
4. stale jobs do not overwrite newer results

### 15.2 ML tests

1. feature schema validation
2. prediction output schema validation
3. explanation payload validation
4. model version written correctly

### 15.3 API tests

1. fetch matches by entity
2. fetch graph edges
3. submit feedback
4. job status polling

### 15.4 UI tests

1. loading state while results pending
2. fallback state when no results available
3. explanation panel rendering
4. stale-result badge when latest job not complete

## 16. Recommended Ownership by Repo

### `Ecowise`

1. canonical entities
2. DB schema
3. outbox and inference job tables
4. read APIs for matches and graph
5. feedback write APIs

### `EcoAI`

1. feature generation
2. embeddings
3. ranking model
4. graph weight computation
5. model registry integration
6. retraining scripts

### `Ecowise-web`

1. render persisted matches
2. render graph edges
3. show explainability
4. show refresh and stale states
5. submit feedback actions

## 17. Immediate Build Order

This is the best execution order:

1. Add orchestration tables in Postgres
2. Add Go outbox write logic
3. Add outbox worker and `ml_inference_job`
4. Define stable JSON feature payload contract
5. Connect Python service to consume jobs
6. Persist results into `match_result`
7. Expose `GET /matches` APIs in Go
8. Render match results in frontend
9. Add `graph_edge`
10. Render graph from persisted edges
11. Add `match_feedback`
12. Add retraining pipeline

## 18. Non-Negotiables

1. No direct frontend to ML calls
2. No synchronous user-facing dependency on model execution
3. No ML result without version metadata
4. No hidden failures
5. No graph rendered from transient in-memory model results
6. No retraining without feedback logging

