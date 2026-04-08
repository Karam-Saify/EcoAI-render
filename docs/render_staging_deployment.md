# Render Staging Deployment

This project is now prepared for a branch-based staging deployment on Render.

## Services to create

1. `ecowise-web-staging`
   - Repo: `Ecowise-web`
   - Blueprint file: `Ecowise-web/render.yaml`
   - Important env:
     - `VITE_API_URL=https://<your-ecowise-api-staging>.onrender.com`

2. `ecowise-api-staging`
   - Repo: `Ecowise`
   - Blueprint file: `render.yaml`
   - Important env:
     - `DATABASE_URL`
     - `JWT_SECRET`
     - `ALLOWED_ORIGINS=https://<your-frontend-staging>.onrender.com,http://localhost:5173`

3. `ecowise-ml-staging`
   - Repo: root `EcoAI` repo
   - Blueprint file: `render.yaml`
   - Root dir: `backend`
   - Important env:
     - `ECOWISE_DATABASE_URL`

## Recommended order

1. Create a separate staging Postgres database on Render.
2. Deploy `ecowise-api-staging` and point `DATABASE_URL` to the staging database.
3. Deploy `ecowise-ml-staging` and point `ECOWISE_DATABASE_URL` to the same staging database.
4. Deploy `ecowise-web-staging` and set `VITE_API_URL` to the Go API staging URL.
5. Update `ALLOWED_ORIGINS` on the Go API to match the final frontend staging URL.

## Branch workflow

Create the same feature branch name in each repo so review is easy:

- `feature/staging-review`

Use that branch when creating the Render services so production stays untouched.

## Verification checklist

1. Open the frontend staging URL.
2. Confirm `/health` returns `ok` on the Go API staging URL.
3. Confirm `/health` returns `healthy` on the ML staging URL.
4. Register or log in through the staging frontend.
5. Create or update a project/issue/solution.
6. Confirm records appear in:
   - `ecowise.outbox_event`
   - `ecowise.entity_feature_snapshot`
   - `ecowise.ml_inference_job`
   - `ecowise.match_result`
   - `ecowise.graph_edge`

## Notes

- Use a staging database, never production, for branch previews.
- The frontend can be reviewed immediately after deployment.
- The full matching display in the UI still depends on read APIs serving persisted `match_result` and `graph_edge`.
