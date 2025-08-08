# Inventory Optimization Dashboard

An end-to-end inventory analytics solution using synthetic supply chain data, MongoDB Atlas, and Tableau Public visualizations via Google Cloud Run API.

## Project Overview

This project generates comprehensive synthetic inventory data and provides analytics infrastructure for inventory optimization insights through Tableau dashboards.

### Components:
1. **Data Generation** - Python notebook creates realistic supply chain datasets (1000 products, 90 days)
2. **Database** - MongoDB Atlas stores products, demand, inventory levels, and reorder recommendations  
3. **API Service** - FastAPI on Google Cloud Run exposes data for Tableau consumption
4. **Visualization** - Tableau Public dashboards for inventory optimization analytics

## Quick Start

### Prerequisites
- Python 3.9+ with VS Code + Jupyter extensions
- MongoDB Atlas account (or local MongoDB)
- Google Cloud Platform account (for deployment)

### Setup Environment
1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd Inventory_Optimization_Dashboard
   cp .env.example .env
   # Edit .env with your MongoDB connection string
   ```

2. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pymongo python-dotenv
   ```

3. **Generate and import data:**
   - Open `Init-JSON-data.ipynb` in VS Code
   - Select the `.venv` Python kernel
   - Run all cells to generate synthetic data and import to MongoDB

## Data Schema

### Collections Generated:
- **products** (1,000 records) - Product catalog with categories, pricing, lead times, safety stock
- **daily_demand** (91,000 records) - Daily demand per product with weekday seasonality  
- **inventory_levels** (91,000 records) - End-of-day inventory following reorder policy simulation
- **reorder_recommendations** (3,000 records) - Monthly reorder points and recommended quantities

### Key Metrics Available:
- Inventory turnover by category
- Stockout rates and fill rates
- Days on hand (DOH) analysis  
- Reorder point optimization
- Lead time performance
- Demand forecasting accuracy

## Architecture for Tableau Integration

### Planned Data Flow:
```
MongoDB Atlas → FastAPI (Cloud Run) → Google Sheets → Tableau Public
```

### API Endpoints (Planned):
- `GET /tableau/fact_daily.csv` - Denormalized daily facts for Tableau
- `POST /tableau/sync/google-sheets` - Sync data to Google Sheets
- `GET /api/products` - Product catalog
- `GET /api/metrics/kpis` - Key performance indicators

### Tableau Dashboard Structure:
1. **Overview Dashboard**
   - KPIs: In-Stock %, Stockout Days, Avg DOH, Turnover
   - Inventory trends and stockout analysis by category
   
2. **Replenishment Planning**  
   - Products below reorder point
   - Recommended order quantities
   - Lead time analysis

3. **SKU Performance Drilldown**
   - Individual product demand vs inventory
   - Stockout incidents timeline
   - Performance details by product

## File Structure
```
├── Init-JSON-data.ipynb          # Data generation notebook
├── environment.md                # Setup instructions
├── .env.example                  # Environment template
├── .gitignore                    # Git exclusions
├── data/inventory/               # Generated JSONL files
│   ├── products.jsonl
│   ├── daily_demand.jsonl
│   ├── inventory_levels.jsonl
│   └── reorder_recommendations.jsonl
└── README.md                     # This file
```

## Security Notes
- MongoDB credentials stored in `.env` (git-ignored)
- Uses read-only database user for API access
- Connection strings loaded from environment variables
- No hardcoded credentials in source code

## Next Steps
1. ✅ Data generation and MongoDB import completed
2. 🚧 Build FastAPI service for Tableau data access
3. 🚧 Deploy API to Google Cloud Run  
4. 🚧 Create Tableau Public dashboards
5. 🚧 Setup automated data refresh pipeline

## Data Quality & Characteristics
- **Reproducible** - Fixed random seed (42) for consistent results
- **Realistic** - Category-based pricing and demand patterns
- **Seasonal** - Weekday demand variations (higher Mon/Thu, lower weekends)
- **Business Logic** - Proper reorder point policy with lead time considerations
- **Scale** - 1000 products × 90 days = 91K daily records

## Architecture Decisions

### Why No Spark SQL (Current Scale)
**Decision**: Use MongoDB directly instead of Spark SQL for data processing.

**Rationale**:
- **Dataset Size**: 91K records (~12.7 MB) - well within MongoDB's optimal range
- **Query Performance**: MongoDB aggregation pipeline handles joins and analytics efficiently at this scale
- **Infrastructure Complexity**: Spark adds unnecessary overhead for small-medium datasets
- **Cost Efficiency**: Single MongoDB instance vs. distributed Spark cluster
- **Development Speed**: Direct MongoDB queries vs. Spark SQL setup and maintenance

**Performance Comparison** (Current Scale):
```
MongoDB Aggregation: ~10-50ms query response
Spark SQL Setup: Would add 2-5 seconds overhead per query
```

**When to Consider Spark SQL** (Future Scaling):
- **Data Volume**: >100 GB daily processing or >10M daily records
- **Complex ETL**: Multi-source data transformation pipelines
- **Historical Analysis**: Years of inventory data requiring distributed computing
- **ML Pipelines**: Large-scale feature engineering and model training
- **Data Lake Integration**: Processing Parquet/Delta files from object storage

**Migration Path** (If Needed):
```
Current: MongoDB → FastAPI → Tableau
Future:  MongoDB → Spark SQL → Delta Lake → Tableau
         (When dataset exceeds 100GB or requires complex ML)
```

**Cost-Benefit Analysis**:
- **Current**: ~$50/month (MongoDB Atlas + Cloud Run)
- **With Spark**: ~$500-2000/month (Databricks/EMR cluster)
- **Break-even Point**: 10M+ daily records or complex analytics requirements

This architecture decision prioritizes simplicity and cost-effectiveness while maintaining scalability options for future growth.

## Contributing
See `environment.md` for detailed setup instructions including MongoDB configuration and Cloud Run deployment steps.