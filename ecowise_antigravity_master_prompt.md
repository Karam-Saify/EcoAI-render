# Ecowise — End-to-End Build Prompt for Antigravity

## Role

You are the **Lead AI Platform Engineer, ML Architect, Data Engineer, Product Architect, and Frontend Analytics Lead** for **Ecowise**.

Your job is to build **Ecowise’s end-to-end matching and scoring platform** from raw data to production-grade outputs.

You must work as if this is a serious internal product build for a high-standard impact-tech team with expectations similar to **JP Morgan internal analytics quality**, **McKinsey problem-structuring rigor**, and **BCG digital product polish**.

You are expected to:
- ingest and validate raw data
- normalize and unify entity schemas
- engineer features
- design and implement the matching system
- design and implement the project readiness / success score
- build the retrieval and ranking pipeline
- expose APIs
- build internal dashboards in **React**
- create professional visualizations and KPI panels
- make the code modular, reproducible, and production-oriented
- produce a system that can be extended later to real NGO and government data

---

# 1. Core Product Context

Ecowise is an **AI-powered sustainability coordination and impact matching platform**.

The platform matches:
- projects
- investors / funders
- volunteers / specialists
- grants / funding calls
- later, NGO and government entities

The immediate goal is to build a strong internal engine for:
1. **Project → Investor matching**
2. **Project → Volunteer matching**
3. **Project → Grant / funding-call retrieval**
4. **Project → Similar ecosystem activity retrieval**
5. **Project readiness / success-potential scoring**
6. **Internal analytics dashboards**

This is not a simple recommender system.
This is a **hybrid structured + semantic + retrieval + scoring platform**.

---

# 2. Inputs Provided

I will give you structured raw data files.

Assume the data includes at least the following categories:
- `projects`
- `investors`
- `volunteers`
- `grants`
- `external ecosystem activities` such as IATI or similar donor/project activity records
- optional summary / metadata files

You must build the system from these raw files.

Do **not** assume the schemas are already perfectly aligned.
Do **not** assume all fields are clean.
Do **not** assume all entity types should be treated the same way.

---

# 3. Critical System Principles

## 3.1 Build a hybrid system, not one black-box model
The correct architecture is:
- structured filtering
- feature engineering
- semantic enrichment
- retrieval
- ranking
- scoring
- explainability

Do not build a single opaque end-to-end LLM-only recommender.

## 3.2 Separate matching from success scoring
Matching answers:
- who or what is the best fit

Success / readiness answers:
- how fundable, executable, and partnership-ready a project is

These are separate modules.

## 3.3 Use LLMs only where they add value
Use LLM APIs for:
- taxonomy normalization
- semantic tagging
- missing-field detection
- project quality extraction
- explanation generation
- optional enrichment of sparse text fields

Do not use the LLM as the sole ranking engine.

## 3.4 Design for extensibility
The architecture must later support:
- NGO profiles
- government programs
- user behavior logs
- match acceptance feedback
- milestone completion outcomes
- true supervised learning in later phases

---

# 4. What You Must Deliver

You must build the following end to end.

## 4.1 Data layer
- raw data ingestion
- schema validation
- cleaning and normalization
- canonical taxonomy layer
- feature store outputs
- vector-ready text fields
- audit reports

## 4.2 Model / matching layer
- project-investor matcher
- project-volunteer matcher
- project-grant retriever
- project-activity precedent retriever
- readiness / success-potential scoring engine
- explainability outputs

## 4.3 API layer
- endpoints for search, match, rank, explain, score, and analytics

## 4.4 Frontend layer
- internal professional React dashboard
- investor statistics
- project pipeline metrics
- geography/sector/SDG distributions
- matching performance views
- score distributions
- top patterns and segmentation views

## 4.5 Engineering layer
- modular codebase
- environment configuration
- reproducible pipeline
- tests
- documentation
- setup guide
- sample outputs

---

# 5. Desired Architecture

Build the project as a clean multi-layer system.

## 5.1 Backend
Preferred:
- Python
- FastAPI or Django + DRF
- PostgreSQL
- pgvector if possible
- SQLAlchemy or Django ORM
- Pydantic schemas
- scikit-learn
- sentence-transformers or embedding API integration
- pandas / numpy
- optional LightGBM or XGBoost

## 5.2 Frontend
Preferred:
- React
- TypeScript
- Vite or Next.js
- Tailwind CSS
- Recharts or ECharts
- TanStack Table
- Zustand or Redux Toolkit if needed
- Axios or fetch client
- clean, premium, executive dashboard design

## 5.3 File and storage strategy
Need support for:
- raw files
- normalized files
- model artifacts
- vectorized outputs
- cached feature tables
- logs
- dashboard API-ready aggregates

---

# 6. Core Data Understanding and Required Entity Design

You must transform the raw data into canonical entity models.

## 6.1 Project entity
Expected fields may include:
- project_id
- title
- archetype
- legal_form
- country
- region
- sector
- sdg_alignment
- stage
- target_beneficiaries
- delivery_model
- funding_need_min
- funding_need_max
- team_skill_needs
- partnership_structure
- compliance_readiness
- credibility_level
- evidence_tokens
- problem_statement
- solution_summary
- realism_score
- validation_flags

## 6.2 Investor entity
Expected fields may include:
- investor_id
- name
- archetype
- domicile_country
- region_focus
- geography_focus
- sector_focus
- sdg_focus
- instrument_set
- stage_preference
- ticket_min
- ticket_max
- reporting_burden
- risk_appetite
- impact_framework
- eligibility_strictness
- credibility_tokens
- thesis_text
- realism_score
- validation_flags

## 6.3 Volunteer entity
Expected fields may include:
- volunteer_id
- full_name
- modality
- role_title
- country
- languages
- sector_preferences
- sdg_preferences
- skill_bundle
- seniority_band
- availability_hours_per_week
- engagement_months
- work_mode
- travel_willingness
- evidence_tokens
- bio_text
- realism_score
- validation_flags

## 6.4 Grant / opportunity entity
Possible fields:
- opportunity_id
- title
- agency / funder
- open_date
- close_date
- description
- funding categories
- applicant eligibility
- award min / max
- cost sharing
- source URL
- enriched keywords / sectors

## 6.5 External activity / ecosystem entity
Possible fields:
- activity_id
- reporting organization
- participating organizations
- recipient countries / regions
- sector names / codes
- project description
- results text
- document counts
- source URL

---

# 7. Canonical Taxonomy Layer

You must create a unified taxonomy so all entities can be compared.

Normalize at least:

## 7.1 Geography
Create standardized fields:
- country_iso
- country_name
- region_name
- geography_scope

## 7.2 Sector
Create controlled sector taxonomy such as:
- agriculture
- water
- waste
- climate_resilience
- renewable_energy
- livelihoods
- education
- health
- governance
- humanitarian_resilience
- circular_economy
- research_policy
- multi-sector

## 7.3 SDGs
Convert all SDG strings to normalized arrays:
- SDG1
- SDG2
- ...
- SDG17

## 7.4 Stage
Normalize stages such as:
- idea
- prototype
- pilot
- scale

## 7.5 Skills
Map free text skills into a controlled skills ontology, grouped into:
- technical skills
- field delivery skills
- donor / proposal skills
- policy / governance skills
- monitoring and evaluation skills
- domain expertise
- design / product / engineering skills

## 7.6 Evidence / credibility tokens
Normalize all evidence tokens into categorical signals:
- concept_note
- prototype_demo
- pilot_results
- audited_report
- impact_report
- results_dashboard
- partner_letter
- research_output
- policy_brief
- implementation_partner
- traction_signal
- certification
- professional_reference
- project_history
- community_reference
- advisory_experience

## 7.7 Readiness maturity
Normalize:
- compliance_readiness
- credibility_level
- reporting_burden
- eligibility_strictness
- risk_appetite

Represent them numerically as well as categorically.

---

# 8. Build the End-to-End Data Pipeline

## 8.1 Ingestion
Create ingestion scripts that:
- load all files
- infer schemas
- validate row counts
- handle malformed records
- produce ingestion logs

## 8.2 Profiling
Generate a data profiling report:
- record counts
- null rates
- distinct values
- outlier numeric fields
- duplication rates
- suspicious text repetition
- malformed category distributions

## 8.3 Cleaning
Perform:
- whitespace cleanup
- lowercase normalization where needed
- delimiter normalization
- token splitting for SDGs, sectors, skills, instruments, evidence tokens
- date parsing
- numeric coercion
- country normalization
- de-duplication
- missing value strategies

## 8.4 Canonical transformation
Produce normalized tables:
- `projects_canonical`
- `investors_canonical`
- `volunteers_canonical`
- `grants_canonical`
- `activities_canonical`

## 8.5 Feature tables
Produce:
- `project_features`
- `investor_features`
- `volunteer_features`
- `grant_features`
- `activity_features`
- `pair_features_project_investor`
- `pair_features_project_volunteer`

## 8.6 Embedding preparation
Create text fields for semantic embedding:
- project_text_full
- investor_text_full
- volunteer_text_full
- grant_text_full
- activity_text_full

Each should be carefully composed from the most informative fields.

---

# 9. LLM Enrichment Layer

Build a dedicated enrichment module using an LLM API.

## 9.1 Required LLM tasks

### Project enrichment
For each project, derive:
- normalized sector tags
- normalized SDG tags
- normalized skill needs
- likely partner types needed
- problem clarity score
- solution specificity score
- implementation readiness score
- measurability score
- stakeholder articulation score
- risk articulation score
- missing information checklist
- short executive summary
- one-line investment thesis summary
- one-line implementation thesis summary

### Investor enrichment
For each investor:
- normalized thesis categories
- investment instrument categories
- likely project-fit archetypes
- intensity of reporting burden
- likely excluded project types
- likely strong-fit delivery models

### Volunteer enrichment
For each volunteer:
- normalized skill ontology mapping
- stakeholder-fit roles
- field suitability
- remote suitability
- leadership / execution suitability

### Grant enrichment
For each grant:
- eligibility class
- likely relevant sectors
- likely relevant project stages
- likely relevant countries / regions
- funding style
- submission complexity
- likely fit score dimensions

### Activity enrichment
For each activity:
- sector tags
- implementing organization type
- partnership pattern
- aid / implementation theme
- relevance to future Ecowise projects

## 9.2 LLM output format
All LLM outputs must be strict JSON.
Do not allow unstructured text outputs in the pipeline.

## 9.3 LLM caching
Cache every LLM response locally so repeated runs are stable and cost-efficient.

---

# 10. Matching System Design

Build three major matching engines.

## 10.1 Project → Investor Matching Engine

### Step A: hard filtering
Filter investors by:
- geography compatibility
- sector compatibility
- stage compatibility
- funding overlap
- instrument compatibility
- baseline compliance fit

### Step B: pair feature generation
Generate pair features such as:
- sector exact match
- sector semantic similarity
- SDG overlap count
- stage compatibility score
- budget overlap ratio
- geography compatibility score
- delivery model fit
- compliance readiness vs eligibility strictness
- credibility vs reporting burden suitability
- evidence strength fit
- text embedding cosine similarity between project and investor thesis
- LLM-inferred archetype compatibility

### Step C: final ranking
Implement:
- v1 weighted scoring
- v2 trainable ranking model

Preferred first learned model:
- LightGBM ranker or XGBoost ranker
Alternative:
- weighted composite ranker if labels are not yet available

### Step D: explanations
Return:
- total match score
- top contributing factors
- disqualifying issues
- rationale text for why this investor is suitable
- recommendations to improve project-investor fit

---

## 10.2 Project → Volunteer Matching Engine

### Step A: hard filtering
Filter by:
- work mode compatibility
- geography / remote compatibility
- basic sector fit
- minimum availability threshold
- engagement duration threshold

### Step B: pair feature generation
Include:
- skill overlap score
- sector overlap score
- SDG overlap score
- language compatibility
- geography compatibility
- seniority fit
- work mode compatibility
- travel willingness fit
- availability fit
- engagement duration fit
- evidence fit
- semantic similarity of project needs vs volunteer bio and role profile

### Step C: final ranking
Preferred:
- weighted scoring or boosted tabular ranking model

### Step D: explanations
Return:
- match score
- skill-fit explanation
- operational-fit explanation
- any constraints or limitations

---

## 10.3 Project → Grant / Activity Retrieval Engine

This is a retrieval task, not a standard pairwise recommender.

### Build a hybrid retriever
Combine:
- metadata filtering
- keyword retrieval
- embedding retrieval
- reranking

### Retrieval targets
1. grants / funding calls
2. similar external implementation activities
3. similar donor / implementation precedents

### Features for grant ranking
- topical similarity
- geography fit
- stage fit
- award-size fit
- eligibility compatibility
- description semantic similarity
- due-date urgency or current relevance

### Features for activity ranking
- sector similarity
- country / region relevance
- beneficiary similarity
- delivery model similarity
- text similarity
- partner structure similarity

### Outputs
Return:
- ranked relevant grants
- ranked relevant external activities
- evidence-backed explanation
- extracted lessons / precedent patterns

---

# 11. Project Readiness / Success-Potential Score

Do **not** falsely build a “true success prediction” model unless real outcome labels exist.

Instead build a strong and transparent:

## 11.1 Readiness / Success-Potential Score

This score should evaluate:
- project clarity
- evidence maturity
- credibility
- compliance readiness
- funding attractiveness
- implementation feasibility
- partnerability
- grant fit
- volunteer fit
- ecosystem precedent strength

### Example component groups

#### A. Documentation and evidence
- evidence token strength
- presence of outputs / pilot results / audited materials

#### B. Operational readiness
- stage maturity
- delivery model maturity
- implementation partner presence
- compliance readiness

#### C. Fundability
- investor universe fit
- funding range realism
- reporting burden tolerance
- SDG / sector attractiveness

#### D. Execution readiness
- volunteer skill coverage
- operational skills match
- partnership structure strength

#### E. External relevance
- similarity to real grants
- similarity to real ecosystem activities
- geography-theme relevance

## 11.2 Score design
Build:
- base composite weighted score
- explainable sub-scores
- risk flags
- opportunity flags
- missing critical components
- top next actions

## 11.3 Future-proofing
Design the score module so it can later be upgraded to a supervised model when actual platform outcomes exist.

---

# 12. Candidate Models You Must Implement or Prepare

## 12.1 Baseline models
Implement:
- rules-based filter
- weighted composite scorer
- cosine semantic similarity
- hybrid retrieval ranker

## 12.2 Preferred learned models
Prepare or implement:
- logistic regression baseline
- random forest baseline
- LightGBM / XGBoost ranking model for match reranking
- gradient boosted model for readiness scoring if pseudo-labels are created

## 12.3 Vector / semantic layer
Implement:
- text embeddings
- cosine similarity search
- vector index using pgvector or local vector store

## 12.4 Weak supervision option
If no human labels exist, create pseudo-labeling logic from high-confidence rules to train a first reranker.

---

# 13. Evaluation Requirements

You must not build blindly.
You must evaluate the system.

## 13.1 Matching evaluation
Evaluate:
- precision@k
- recall@k where possible
- manual sanity review sets
- sector-based quality slices
- geography-based quality slices
- stage-based quality slices

## 13.2 Readiness score evaluation
If no true labels exist:
- validate via rubric consistency
- perform monotonic sanity checks
- ensure score behaves correctly when evidence or fit signals are improved

## 13.3 Retrieval evaluation
For grants and activity retrieval:
- qualitative relevance review
- top-k semantic relevance
- metadata coverage checks

## 13.4 Explainability evaluation
Check whether explanations are:
- consistent with score factors
- not hallucinated
- grounded in structured inputs

---

# 14. API Requirements

Build clean APIs.

## 14.1 Core endpoints

### Data
- `GET /health`
- `POST /ingest`
- `POST /normalize`
- `POST /rebuild-features`

### Project-level inference
- `POST /projects/{id}/match-investors`
- `POST /projects/{id}/match-volunteers`
- `POST /projects/{id}/retrieve-grants`
- `POST /projects/{id}/retrieve-activities`
- `POST /projects/{id}/score-readiness`
- `POST /projects/{id}/full-analysis`

### Search / browse
- `GET /projects`
- `GET /investors`
- `GET /volunteers`
- `GET /grants`
- `GET /activities`

### Dashboards / analytics
- `GET /analytics/overview`
- `GET /analytics/projects`
- `GET /analytics/investors`
- `GET /analytics/volunteers`
- `GET /analytics/grants`
- `GET /analytics/geography`
- `GET /analytics/sectors`
- `GET /analytics/sdgs`
- `GET /analytics/readiness-distribution`
- `GET /analytics/matching-quality`

## 14.2 Response design
Responses must include:
- compact summary
- detailed structured breakdown
- explanation objects
- score factors
- traceable entity ids

---

# 15. Internal Dashboard Requirements

Build a **React internal dashboard** with a premium executive look.

This dashboard is not a toy admin screen.
It should feel like:
- institutional internal analytics
- consulting-grade insight presentation
- high-end portfolio intelligence UI

The visual language should be:
- minimal
- dark or neutral professional palette
- sharp typography hierarchy
- dense but readable
- premium cards
- elegant filters
- polished interactions
- no clutter
- dashboard-first

## 15.1 Main dashboard pages

### A. Executive Overview
Show:
- total projects
- total investors
- total volunteers
- total grants
- total activities
- readiness score distribution
- top sectors
- top countries
- top SDGs
- match coverage rates

### B. Projects Intelligence
Show:
- projects by country
- projects by sector
- projects by stage
- funding need distribution
- evidence maturity distribution
- compliance readiness distribution
- readiness score histogram
- top projects by readiness
- projects with largest funding gaps
- projects with weakest execution readiness

### C. Investors Intelligence
Show:
- investor count by region
- investor count by geography focus
- sector distribution
- instrument mix
- stage preference mix
- ticket-size range distribution
- risk appetite distribution
- reporting burden distribution
- impact framework distribution
- top archetypes

### D. Volunteers Intelligence
Show:
- volunteers by country
- volunteers by sector preference
- skill cluster map
- work mode split
- seniority distribution
- availability distribution
- engagement duration distribution
- language distribution
- high-value scarce skills
- volunteer supply vs project demand mismatch

### E. Grants Intelligence
Show:
- grants by sector
- grants by region / geography
- open vs closed vs evergreen
- award-size distributions
- eligibility complexity
- current most relevant grants
- project-grant fit summaries

### F. Ecosystem Activity Intelligence
Show:
- external activities by geography
- external activities by sector
- donor / reporting organization concentration
- partner network signals
- thematic clusters
- precedent density by country and sector

### G. Matching Analytics
Show:
- top matched investors per project
- top matched volunteers per project
- strongest fit dimensions
- weak fit dimensions
- average match score by sector
- average match score by geography
- score spread analysis
- top reasons for disqualification
- top readiness blockers

---

# 16. Dashboard Charting Expectations

The dashboard should include highly professional visualizations.

Use:
- KPI cards
- distribution histograms
- stacked bar charts
- grouped bar charts
- treemaps
- heatmaps
- geographic choropleth or region maps where reasonable
- Sankey-style flow diagrams if useful
- scatterplots for funding/readiness relationships
- radar charts only if truly useful
- ranked tables with filters
- segmentation matrices

Suggested analysis views:
- investor count by sector x geography
- project stage x readiness heatmap
- skill demand vs volunteer supply gap matrix
- funding need x investor ticket overlap plot
- sector x SDG density
- region x instrument preference
- top grant relevance panels
- country x external activity precedent density

Build dashboards so they can filter by:
- country
- region
- sector
- SDG
- stage
- entity archetype
- legal form
- work mode
- seniority
- risk appetite
- instrument type

---

# 17. Frontend UX and Visual Quality Standard

The UI must feel premium and executive.
Reference expectations:
- large clean spacing
- premium card treatment
- refined shadows or borders
- precise grid layout
- readable data density
- highly polished tables
- visible drill-down paths
- consulting-style section titles
- insight-first layout, not widget-first chaos

For every main page:
- top summary area
- filters row
- primary visual insights
- secondary deeper diagnostics
- ranked table
- insight callouts

Also provide:
- empty states
- loading states
- error states
- export buttons where reasonable
- responsive layout for laptop screens
- no visual mess

---

# 18. Required Outputs from the System

For each project, the system should be able to output:

## 18.1 Investor match result
- top N ranked investors
- match score
- structured factor contributions
- explanation
- blockers / concerns
- improvement suggestions

## 18.2 Volunteer match result
- top N ranked volunteers
- skills fit
- operational fit
- availability fit
- explanation
- blockers

## 18.3 Grant retrieval result
- top N relevant grants
- fit rationale
- eligibility risks
- application complexity notes

## 18.4 Activity precedent result
- top N similar ecosystem activities
- relevance reason
- precedent patterns
- potential partner implications

## 18.5 Readiness score result
- total readiness score
- component sub-scores
- risk flags
- missing critical fields
- improvement plan

---

# 19. Folder Structure You Should Produce

Use a professional structure such as:

```text
ecowise/
  backend/
    app/
      api/
      core/
      models/
      schemas/
      services/
      repositories/
      ml/
        pipelines/
        features/
        embeddings/
        matchers/
        scorers/
        retrievers/
        explainability/
      analytics/
      tasks/
    tests/
    requirements.txt
    pyproject.toml

  frontend/
    src/
      app/
      components/
      features/
        dashboard/
        projects/
        investors/
        volunteers/
        grants/
        analytics/
      hooks/
      lib/
      services/
      types/
      pages/
    package.json

  data/
    raw/
    interim/
    processed/
    feature_store/
    vectors/

  artifacts/
    reports/
    model_outputs/
    charts/
    logs/

  docs/
    architecture/
    api/
    dashboards/
    methodology/

  scripts/
    ingest/
    normalize/
    enrich/
    build_features/
    run_matching/
    build_dashboards/
```

---

# 20. Required Engineering Quality

You must produce:
- clean modular code
- proper typing where possible
- strong naming
- comments only where useful
- environment configuration files
- sample env template
- reproducible commands
- tests for critical logic
- deterministic outputs where possible
- documentation for every major module

---

# 21. Build Sequence You Must Follow

## Phase 1
- inspect raw data
- build canonical schemas
- generate profiling reports
- normalize and clean data

## Phase 2
- create feature engineering pipeline
- create text composition pipeline
- build embeddings
- build vector search

## Phase 3
- implement investor matcher
- implement volunteer matcher
- implement grant/activity retrieval
- implement readiness scorer

## Phase 4
- expose APIs
- test endpoints
- produce example outputs

## Phase 5
- build React dashboard
- connect APIs
- build analytics panels
- create premium visuals

## Phase 6
- validate outputs
- document limitations
- provide runbook

---

# 22. Non-Negotiable Deliverables

At the end, I expect:

1. full codebase  
2. normalized data pipeline  
3. feature engineering pipeline  
4. LLM enrichment pipeline  
5. matching modules  
6. readiness scoring module  
7. retrieval module  
8. API endpoints  
9. React internal dashboard  
10. documentation  
11. setup instructions  
12. example outputs and screenshots  
13. explanation of assumptions and limitations  

---

# 23. Constraints and Honesty Requirements

- Be explicit when labels do not exist
- Do not fake a supervised “success model” if the dataset lacks real outcomes
- Implement a readiness score when true success labels are missing
- Keep all scoring explainable
- Prefer robust simple systems over flashy but fragile ones
- Make the system ready for future user interaction logging and learning

---

# 24. Final Mission

Build Ecowise as a serious internal matching intelligence platform.

It must combine:
- structured scoring
- semantic reasoning
- retrieval
- explainability
- analytics
- premium dashboarding

From raw data to model output to dashboards, build the full system with strong engineering discipline and professional product quality.

Do not give a lightweight prototype.
Give a modular, extensible, professional end-to-end build.
