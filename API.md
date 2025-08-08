# FastAPI Inventory Optimization Service

A RESTful API service that serves inventory analytics data from MongoDB for Tableau Public consumption.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
python3 -m venv api_env
source api_env/bin/activate
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Tableau CSV**: http://localhost:8000/tableau/fact_daily.csv

## 📊 API Endpoints

### Core Endpoints

#### `GET /`
Health check endpoint returning basic service info.

#### `GET /health`
Detailed health check with MongoDB connectivity and collection counts.

#### `GET /tableau/fact_daily.csv`
**Primary endpoint for Tableau Public integration**

Returns denormalized daily inventory facts as CSV format.

**Query Parameters:**
- `start_date` (optional): Start date in YYYY-MM-DD format (default: 2024-01-01)
- `end_date` (optional): End date in YYYY-MM-DD format (default: 2024-03-31)
- `category` (optional): Filter by product category
- `limit` (optional): Limit number of records

**Response Format (CSV):**
```csv
product_id,date,demand,category,price,uom,lead_time_days,safety_stock,reorder_multiplier,inventory_level,stockout_flag,month,reorder_point,recommended_order_qty
product0001,2024-01-01,3,Health & Beauty,21.56,pack,7,11,2.11,55,0,2024-01,91,114
```

**Example Usage:**
```bash
# Get all data
curl "http://localhost:8000/tableau/fact_daily.csv"

# Get January data for Electronics
curl "http://localhost:8000/tableau/fact_daily.csv?start_date=2024-01-01&end_date=2024-01-31&category=Electronics"

# Get sample data (first 100 records)
curl "http://localhost:8000/tableau/fact_daily.csv?limit=100"
```

### Analytics Endpoints

#### `GET /api/products`
Get products catalog with optional category filtering.

**Query Parameters:**
- `category` (optional): Filter by product category

#### `GET /api/categories`
Get list of all product categories.

#### `GET /api/metrics/kpis`
Calculate key performance indicators for the inventory system.

**Query Parameters:**
- `start_date` (optional): Start date for KPI calculation
- `end_date` (optional): End date for KPI calculation

**Response:**
```json
{
    "total_skus": 1000,
    "in_stock_percentage": 99.99,
    "fill_rate": 99.99,
    "stockout_rate": 0.01,
    "date_range": "2024-01-01 to 2024-03-31"
}
```

## 🏗️ Data Schema

The API joins four MongoDB collections to create the denormalized fact table:

### Collections Used:
- **products**: Product catalog with categories, pricing, lead times
- **daily_demand**: Daily demand per product with seasonality
- **inventory_levels**: End-of-day inventory levels
- **reorder_recommendations**: Monthly reorder points and quantities

### Calculated Fields:
- **stockout_flag**: 1 if inventory=0 and demand>0, else 0
- **month**: Extracted from date for recommendation joins

## 🔗 Tableau Integration

### Option 1: Direct CSV Download (Recommended)
1. Use the CSV endpoint directly in Tableau Public
2. Connect to Web Data Connector or upload CSV file
3. Refresh data by re-downloading CSV

### Option 2: Google Sheets Bridge (Future)
1. API syncs data to Google Sheets
2. Tableau Public connects to Google Sheets
3. Automatic refresh through scheduled API calls

## 📈 Tableau Dashboard Structure

### Overview Dashboard
- **KPIs**: Total SKUs, In-Stock %, Fill Rate, Stockout Rate
- **Trends**: Inventory levels over time by category
- **Analysis**: Demand vs inventory correlation

### Replenishment Planning
- **Alerts**: Products below reorder point
- **Recommendations**: Suggested order quantities
- **Lead Time Analysis**: Performance by supplier

### SKU Performance
- **Individual Product Analysis**: Demand patterns, stockout incidents
- **Category Comparison**: Performance metrics by product category
- **Seasonal Trends**: Demand patterns by weekday/month

## 🚀 Deployment

### Google Cloud Run
```bash
# Setup (one-time)
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Create secret for MongoDB URI
echo -n "YOUR_MONGO_URI" | gcloud secrets create MONGO_URI --data-file=-

# Deploy
./deploy.sh
```

### Environment Variables
- `MONGO_URI`: MongoDB connection string (stored in Secret Manager)
- `MONGO_DB`: Database name (default: inventory_demo)

## 🔧 Development

### Adding New Endpoints
1. Add endpoint function to `main.py`
2. Update this documentation
3. Test with `curl` or `/docs` interface

### Database Schema Changes
1. Update aggregation pipeline in `/tableau/fact_daily.csv` endpoint
2. Verify CSV output format matches Tableau expectations
3. Update documentation

### Performance Optimization
- MongoDB indexes are already created for key fields
- Consider adding pagination for large date ranges
- Monitor Cloud Run metrics for scaling needs

## 🛠️ Troubleshooting

### Common Issues
1. **MongoDB Connection Failed**: Check MONGO_URI environment variable
2. **Empty CSV Response**: Verify date range and data exists in collections
3. **Slow API Response**: Check MongoDB indexes and query efficiency

### Monitoring
- Use `/health` endpoint for service monitoring
- Monitor Cloud Run logs for errors
- Track API response times and usage patterns
