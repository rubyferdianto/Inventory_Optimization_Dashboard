# Inventory Optimization Dashboard

An end-to-end inventory analytics service using MongoDB Atlas and a FastAPI API deployed on Google Cloud Run, designed for Tableau Public consumption.

## Overview

- Data: Synthetic inventory datasets (products, daily demand, inventory levels, reorder recommendations)
- DB: MongoDB Atlas
- API: FastAPI + Uvicorn
- Deploy: Google Cloud Run (containerized with Dockerfile)
- Viz: Tableau Public via CSV endpoint

Data flow:
MongoDB Atlas → FastAPI (Cloud Run) → Tableau Public (CSV)

## Repository Contents

- `main.py` — FastAPI service with endpoints for Tableau and analytics
- `requirements.txt` — Python dependencies (FastAPI, pymongo, pandas, certifi, etc.)
- `Dockerfile` — Container image for Cloud Run
- `.dockerignore` — Slimmer builds (excludes venv, data, notebooks, etc.)
- `deploy.sh` — One-command deployment to Cloud Run
- `API.md` — Endpoint details and examples
- `Init-JSON-data.ipynb` — Optional notebook to generate/import synthetic data
- `data/` — Optional local assets (not used by the API)

Removed (no longer needed for Cloud Run): local start/stop scripts, ngrok, Railway, and other helper files.

## Local Development (optional)

1) Create a virtual environment and install deps

```bash
python3 -m venv api_env
source api_env/bin/activate
pip install -r requirements.txt
```

2) Configure environment (local only)

- Create `.env` with your MongoDB settings:
  - `MONGO_URI` (SRV or standard URI)
  - `MONGO_DB` (default: `inventory_demo`)

Notes:
- The app auto-loads env files in this order:
  - If `ENV_FILE` is set, that file is loaded
  - Else if `ENVIRONMENT=production` and `.env.production` exists, it’s loaded
  - Else `.env` is loaded

3) Run locally

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Docs:    http://localhost:8000/docs
# Health:  http://localhost:8000/health
# Tableau: http://localhost:8000/tableau/fact_daily.csv
```

## Deploy to Google Cloud Run (recommended)

Prereqs:
- gcloud CLI installed and logged in
- Billing enabled on project
- MongoDB Atlas project and database created

One-command deploy (uses `deploy.sh`):

```bash
./deploy.sh
```

What `deploy.sh` does:
- Sets project ID to `thermal-setup-458600-q8` (update in the script if needed)
- Enables Cloud Build, Cloud Run, Secret Manager
- Creates/uses Secret Manager secret `MONGO_URI`
- Builds the container with Cloud Build and deploys to Cloud Run (region `us-central1`)
- Sets env vars `ENVIRONMENT=production`, `MONGO_DB=inventory_demo`

Manual deploy (alternative):

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/inventory-api
gcloud run deploy inventory-api \
  --image gcr.io/YOUR_PROJECT_ID/inventory-api \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars ENVIRONMENT=production,MONGO_DB=inventory_demo \
  --set-secrets MONGO_URI=MONGO_URI:latest
```

After deploy, get the URL:

```bash
gcloud run services describe inventory-api --region us-central1 --format='value(status.url)'
```

Use these endpoints:
- Health: {SERVICE_URL}/health
- Docs: {SERVICE_URL}/docs
- Tableau CSV: {SERVICE_URL}/tableau/fact_daily.csv

## Current Deployment (Cloud Run)

Service URL:
- https://inventory-api-610111719715.us-central1.run.app

Quick links:
- Health: https://inventory-api-610111719715.us-central1.run.app/health
- Docs: https://inventory-api-610111719715.us-central1.run.app/docs
- Tableau CSV: https://inventory-api-610111719715.us-central1.run.app/tableau/fact_daily.csv

Update MongoDB URI (Secret Manager):
```bash
# Add a new version to the existing secret
printf "%s" "YOUR_NEW_MONGO_URI" | gcloud secrets versions add MONGO_URI --data-file=-
# (Re)deploy or roll new revision to pick up changes
./deploy.sh
```

## Environment, TLS, and MongoDB Atlas

- Cloud Run does NOT read `.env` files. Set env via `--set-env-vars` or Secret Manager.
- The app uses `certifi` and configures `pymongo` with `tlsCAFile=certifi.where()` to avoid TLS handshake issues.
- For SRV URIs (`mongodb+srv://`), `dnspython` is used via `pymongo[srv]` (already included).

Network access:
- Ensure your Cloud Run service has outbound internet access to Atlas.
- If you attach a Serverless VPC Connector with egress = “all-traffic”, configure Cloud NAT for public egress; otherwise Atlas won’t be reachable.
- Easiest: no VPC connector, or egress = “private-ranges-only”.
- In Atlas, temporarily allow `0.0.0.0/0` to validate connectivity, then restrict to a static egress IP (Cloud NAT) for production.

Quick checks (CLI):

```bash
gcloud run services describe inventory-api --region us-central1 \
  --format='value(spec.template.metadata.annotations."run.googleapis.com/vpc-access-connector")'

gcloud run services describe inventory-api --region us-central1 \
  --format='value(spec.template.metadata.annotations."run.googleapis.com/vpc-access-egress")'
```

## API Endpoints (summary)

- `GET /` — Basic service info
- `GET /health` — Health with MongoDB connectivity and collection counts
- `GET /tableau/fact_daily.csv` — Denormalized daily facts for Tableau
  - Query params: `start_date`, `end_date`, `category`, `limit`
- `GET /api/products` — Product catalog (optional `category`)
- `GET /api/categories` — List of categories
- `GET /api/metrics/kpis` — KPI calculations (fill rate, stockout %, etc.)

## Security

- Never commit secrets. `.env*` are for local only.
- On Cloud Run, use Secret Manager for `MONGO_URI`.
- Use a read-only MongoDB user for analytics/API.

## Troubleshooting

- TLS handshake errors to Atlas:
  - Keep `certifi` in requirements (already present)
  - Ensure outbound internet from Cloud Run (see VPC connector notes)
  - Verify Atlas network access allowlist
- Empty CSV:
  - Confirm date range and data availability in MongoDB
- Slow queries:
  - Consider indexes on `product_id`, `date` fields in collections

## Tableau Public

Use the Cloud Run CSV endpoint directly in Tableau Public:

- CSV URL: `{SERVICE_URL}/tableau/fact_daily.csv`
- Optional filters via query params, e.g.:
  `{SERVICE_URL}/tableau/fact_daily.csv?start_date=2024-01-01&end_date=2024-01-31&category=Electronics&limit=1000`

---

For more detailed endpoint docs and examples, see `API.md`.