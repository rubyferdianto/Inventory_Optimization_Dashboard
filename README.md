# Inventory Optimization Dashboard

An end-to-end inventory analytics service using MongoDB Atlas and FastAPI deployed on Google Cloud Run, designed for Tableau Public consumption.

## Overview

This project provides a complete inventory optimization solution:
- **Data**: Synthetic inventory datasets (products, daily demand, inventory levels, reorder recommendations)
- **Database**: MongoDB Atlas with TLS-enabled secure connection
- **API**: FastAPI service with multiple endpoints for analytics and Tableau integration
- **Deployment**: Google Cloud Run (containerized) with Secret Manager for secure credential storage
- **Visualization**: Tableau Public via CSV endpoint

**Data Flow**: MongoDB Atlas → FastAPI (Cloud Run) → Tableau Public (CSV)

## Architecture

```
MongoDB Atlas (Cloud Database)
       ↓
FastAPI Service (Google Cloud Run)
       ↓
Tableau Public Dashboard
```

## Repository Structure

- `main.py` — FastAPI service with endpoints for Tableau and analytics
- `requirements.txt` — Python dependencies (FastAPI, pymongo, pandas, certifi, etc.)
- `Dockerfile` — Container image configuration for Cloud Run deployment
- `.dockerignore` — Optimized builds (excludes unnecessary files)
- `deploy.sh` — Automated deployment script to Cloud Run
- `API.md` — Detailed endpoint documentation and examples
- `Init-JSON-data.ipynb` — Jupyter notebook for generating synthetic data
- `.env.example` — Template for local environment configuration
- `.gitignore` — Git ignore rules for security and clean repository

## Current Deployment Status

### Production Service (Google Cloud Run)
- **Service URL**: https://inventory-api-610111719715.us-central1.run.app
- **MongoDB Database**: `inventory_demo` on MongoDB Atlas cluster
- **Authentication**: Secret Manager for secure credential storage

### Quick Access Links
- **Health Check**: https://inventory-api-610111719715.us-central1.run.app/health
- **API Documentation**: https://inventory-api-610111719715.us-central1.run.app/docs
- **Tableau CSV Endpoint**: https://inventory-api-610111719715.us-central1.run.app/tableau/fact_daily.csv

### MongoDB Connection Details
The service connects to MongoDB Atlas using:
- **Cluster**: `cluster0.thisg0i.mongodb.net`
- **Database**: `inventory_demo`
- **Authentication**: Username/password stored in Google Secret Manager
- **Connection**: TLS-enabled with certificate validation via `certifi`

To find your MongoDB URI:
1. **MongoDB Atlas Dashboard**: Log into your MongoDB Atlas account
2. **Connect**: Click "Connect" on your cluster
3. **Application**: Choose "Connect your application"  
4. **Connection String**: Copy the connection string format:
   ```
   mongodb+srv://<username>:<password>@cluster0.thisg0i.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
   ```

## Local Development Setup

### Prerequisites
- Python 3.8+ installed
- MongoDB Atlas account and cluster
- Git for version control

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd Inventory_Optimization_Dashboard

# Create virtual environment
python3 -m venv api_env
source api_env/bin/activate  # On Windows: api_env\Scriptsctivate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy template and configure
cp .env.example .env
# Edit .env with your MongoDB connection details
```

Required environment variables:
- `MONGO_URI`: Your MongoDB Atlas connection string
- `MONGO_DB`: Database name (default: `inventory_demo`)

### 3. Run Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access points:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Tableau CSV**: http://localhost:8000/tableau/fact_daily.csv

## Production Deployment to Google Cloud Run

### Prerequisites
- Google Cloud CLI installed and authenticated
- Google Cloud project with billing enabled
- MongoDB Atlas cluster configured

### Automated Deployment

```bash
# One-command deployment
./deploy.sh
```

The deployment script:
- Sets up Google Cloud project (`thermal-setup-458600-q8`)
- Enables required services (Cloud Build, Cloud Run, Secret Manager)
- Creates MongoDB URI secret in Secret Manager
- Builds container image with Cloud Build
- Deploys to Cloud Run in `us-central1` region
- Configures environment variables and secrets

### Manual Deployment (Alternative)

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable services
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# Create secret (first time only)
printf "%s" "YOUR_MONGO_URI" | gcloud secrets create MONGO_URI --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/inventory-api
gcloud run deploy inventory-api \
  --image gcr.io/YOUR_PROJECT_ID/inventory-api \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars ENVIRONMENT=production,MONGO_DB=inventory_demo \
  --set-secrets MONGO_URI=MONGO_URI:latest
```

### Update Secrets

```bash
# Update MongoDB URI in Secret Manager
printf "%s" "NEW_MONGO_URI" | gcloud secrets versions add MONGO_URI --data-file=-

# Redeploy to pick up new secret
./deploy.sh
```

## API Endpoints

### Core Endpoints
- `GET /` — Basic service information
- `GET /health` — Health check with MongoDB connectivity and collection counts
- `GET /docs` — Interactive API documentation (Swagger UI)

### Data Endpoints
- `GET /tableau/fact_daily.csv` — **Primary endpoint for Tableau Public**
  - Returns denormalized daily facts as CSV
  - Query parameters: `start_date`, `end_date`, `category`, `limit`
  - Joins products, daily_demand, inventory_levels, and reorder_recommendations

### Analytics Endpoints
- `GET /api/products` — Product catalog with optional category filter
- `GET /api/categories` — List of all product categories
- `GET /api/metrics/kpis` — Key performance indicators (fill rate, stockout %, etc.)

### Example API Calls

```bash
# Health check
curl https://inventory-api-610111719715.us-central1.run.app/health

# Get CSV for Tableau with filters
curl "https://inventory-api-610111719715.us-central1.run.app/tableau/fact_daily.csv?start_date=2024-01-01&end_date=2024-01-31&category=Electronics&limit=1000"

# Get product categories
curl https://inventory-api-610111719715.us-central1.run.app/api/categories

# Get KPIs for date range
curl "https://inventory-api-610111719715.us-central1.run.app/api/metrics/kpis?start_date=2024-01-01&end_date=2024-03-31"
```

## Tableau Public Integration

### Using the CSV Endpoint
1. **Open Tableau Public**
2. **Connect to Data** → **Web Data Connector**
3. **Enter URL**: `https://inventory-api-610111719715.us-central1.run.app/tableau/fact_daily.csv`
4. **Optional Filters**: Add query parameters for date range, category, or limit

### CSV Data Structure
The `/tableau/fact_daily.csv` endpoint provides denormalized data with:
- **Date Information**: `date`, `month`
- **Product Details**: `product_id`, `category`, `price`, `uom`, `lead_time_days`, `safety_stock`
- **Demand & Inventory**: `demand`, `inventory_level`, `stockout_flag`
- **Recommendations**: `reorder_point`, `recommended_order_qty`

### Sample Dashboard Elements
- **KPI Cards**: Fill rate, stockout percentage, total SKUs
- **Time Series**: Daily demand and inventory levels
- **Category Analysis**: Performance by product category
- **Reorder Alerts**: Products requiring restocking
- **Stockout Analysis**: Frequency and impact of stockouts

## Technical Details

### Environment Configuration
The application supports flexible environment loading:
1. `ENV_FILE` environment variable (highest priority)
2. `ENVIRONMENT=staging` → loads `.env.staging`
3. Default → loads `.env`

### MongoDB & TLS Configuration
- Uses `certifi` package for TLS certificate validation
- Configured with `tlsCAFile=certifi.where()` for MongoDB Atlas
- Supports both SRV (`mongodb+srv://`) and standard connection strings
- Uses `pymongo[srv]` for DNS resolution

### Security Considerations
- **Credentials**: Never commit `.env` files - use Secret Manager for production
- **Database Access**: Use read-only MongoDB user for analytics
- **Network Access**: Configure MongoDB Atlas IP allowlist appropriately
- **TLS**: All connections use TLS encryption

### Performance & Optimization
- **Indexes**: Ensure MongoDB has indexes on `product_id` and `date` fields
- **Aggregation**: Uses MongoDB aggregation pipelines for efficient joins
- **Caching**: Consider adding Redis caching for frequently accessed data
- **Monitoring**: Use Cloud Run metrics and MongoDB Atlas monitoring

## Troubleshooting

### Common Issues

#### TLS Handshake Errors to MongoDB Atlas
- Ensure `certifi` is in requirements.txt ✓
- Verify outbound internet access from Cloud Run
- Check MongoDB Atlas network access allowlist
- Confirm TLS configuration in connection string

#### Empty CSV Response
- Verify date range parameters match data in MongoDB
- Check MongoDB collections have data for specified date range
- Validate category names if using category filter

#### Cloud Run Deployment Issues
- Verify Google Cloud project has billing enabled
- Check IAM permissions for Cloud Build and Cloud Run
- Ensure Secret Manager secret `MONGO_URI` exists and is accessible

#### MongoDB Connection Issues
- Test connection string format and credentials
- Verify MongoDB Atlas cluster is running
- Check IP allowlist includes Cloud Run egress IPs (or use 0.0.0.0/0 temporarily)

### Debug Commands

```bash
# Check Cloud Run service status
gcloud run services describe inventory-api --region us-central1

# View Cloud Run logs
gcloud logs tail --service inventory-api

# Test Secret Manager access
gcloud secrets versions access latest --secret="MONGO_URI"

# Check service health
curl https://inventory-api-610111719715.us-central1.run.app/health
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -am 'Add your feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Create a Pull Request

## License

This project is for educational and demonstration purposes. Please ensure you comply with all service terms when using MongoDB Atlas, Google Cloud Run, and Tableau Public.

---

For detailed API documentation with examples, see [API.md](API.md).
