"""
FastAPI service for Inventory Optimization Dashboard
Serves MongoDB data for Tableau Public consumption
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import os
from datetime import datetime, date
from typing import Optional, List
import json
from dotenv import load_dotenv
import certifi

# Load environment variables (ENV_FILE takes precedence, then ENVIRONMENT)
env_file = os.environ.get("ENV_FILE")
if env_file and os.path.exists(env_file):
    load_dotenv(env_file)
else:
    env = os.environ.get("ENVIRONMENT", "").lower()
    if env == "staging" and os.path.exists(".env.staging"):
        load_dotenv(".env.staging")
    else:
        load_dotenv()

app = FastAPI(
    title="Inventory Optimization API",
    description="API for serving inventory analytics data to Tableau",
    version="1.0.0"
)

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("MONGO_DB", "inventory_demo")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")

client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client[DB_NAME]

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Inventory Optimization API",
        "database": DB_NAME,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check with MongoDB connectivity"""
    try:
        # Test MongoDB connection
        client.admin.command('ping')
        
        # Get collection counts
        counts = {}
        for collection in ["products", "daily_demand", "inventory_levels", "reorder_recommendations"]:
            counts[collection] = db[collection].count_documents({})
        
        return {
            "status": "healthy",
            "mongodb": "connected",
            "database": DB_NAME,
            "collections": counts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/tableau/fact_daily.csv")
async def get_daily_facts_csv(
    start_date: Optional[str] = Query("2024-01-01", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query("2024-03-31", description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    limit: Optional[int] = Query(None, description="Limit number of records")
):
    """
    Returns denormalized daily facts as CSV for Tableau consumption.
    Joins products, daily_demand, inventory_levels, and reorder_recommendations.
    """
    try:
        # Build MongoDB aggregation pipeline
        match_stage = {
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        pipeline = [
            {"$match": match_stage},
            # Join with inventory_levels
            {
                "$lookup": {
                    "from": "inventory_levels",
                    "let": {"prod_id": "$product_id", "date_val": "$date"},
                    "pipeline": [
                        {"$match": {"$expr": {"$and": [
                            {"$eq": ["$product_id", "$$prod_id"]},
                            {"$eq": ["$date", "$$date_val"]}
                        ]}}}
                    ],
                    "as": "inventory"
                }
            },
            # Join with products
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            # Join with reorder_recommendations (by month)
            {
                "$lookup": {
                    "from": "reorder_recommendations",
                    "let": {"prod_id": "$product_id", "month": {"$substr": ["$date", 0, 7]}},
                    "pipeline": [
                        {"$match": {"$expr": {"$and": [
                            {"$eq": ["$product_id", "$$prod_id"]},
                            {"$eq": [{"$substr": ["$date", 0, 7]}, "$$month"]}
                        ]}}}
                    ],
                    "as": "recommendation"
                }
            },
            # Unwind arrays
            {"$unwind": "$inventory"},
            {"$unwind": "$product"},
            {"$unwind": {"path": "$recommendation", "preserveNullAndEmptyArrays": True}},
            # Project final structure
            {
                "$project": {
                    "date": 1,
                    "product_id": 1,
                    "category": "$product.category",
                    "price": "$product.price",
                    "uom": "$product.uom",
                    "lead_time_days": "$product.lead_time_days",
                    "safety_stock": "$product.safety_stock",
                    "reorder_multiplier": "$product.reorder_multiplier",
                    "demand": 1,
                    "inventory_level": "$inventory.inventory_level",
                    "stockout_flag": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$inventory.inventory_level", 0]},
                                {"$gt": ["$demand", 0]}
                            ]},
                            1, 0
                        ]
                    },
                    "month": {"$substr": ["$date", 0, 7]},
                    "reorder_point": {"$ifNull": ["$recommendation.reorder_point", None]},
                    "recommended_order_qty": {"$ifNull": ["$recommendation.recommended_order_qty", None]}
                }
            }
        ]
        
        # Add category filter if specified
        if category:
            pipeline.insert(1, {"$match": {"product.category": category}})
        
        # Add limit if specified
        if limit:
            pipeline.append({"$limit": limit})
        
        # Execute aggregation
        cursor = db.daily_demand.aggregate(pipeline)
        data = list(cursor)
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found for the specified criteria")
        
        # Convert to DataFrame and then to CSV
        df = pd.DataFrame(data)
        
        # Remove MongoDB _id field if present
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)
        
        # Convert to CSV
        csv_content = df.to_csv(index=False)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory_daily_facts.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")

@app.get("/api/products")
async def get_products(category: Optional[str] = Query(None, description="Filter by category")):
    """Get products catalog"""
    try:
        filter_criteria = {}
        if category:
            filter_criteria["category"] = category
        
        products = list(db.products.find(filter_criteria, {"_id": 0}))
        return {"products": products, "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@app.get("/api/categories")
async def get_categories():
    """Get all product categories"""
    try:
        categories = db.products.distinct("category")
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@app.get("/api/metrics/kpis")
async def get_kpis(
    start_date: Optional[str] = Query("2024-01-01", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query("2024-03-31", description="End date (YYYY-MM-DD)")
):
    """Calculate key performance indicators"""
    try:
        # Total SKUs
        total_skus = db.products.count_documents({})
        
        # Stockout analysis
        stockout_pipeline = [
            {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
            {
                "$lookup": {
                    "from": "inventory_levels",
                    "let": {"prod_id": "$product_id", "date_val": "$date"},
                    "pipeline": [
                        {"$match": {"$expr": {"$and": [
                            {"$eq": ["$product_id", "$$prod_id"]},
                            {"$eq": ["$date", "$$date_val"]}
                        ]}}}
                    ],
                    "as": "inventory"
                }
            },
            {"$unwind": "$inventory"},
            {
                "$project": {
                    "product_id": 1,
                    "date": 1,
                    "demand": 1,
                    "inventory_level": "$inventory.inventory_level",
                    "stockout": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$inventory.inventory_level", 0]},
                                {"$gt": ["$demand", 0]}
                            ]},
                            1, 0
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_days": {"$sum": 1},
                    "stockout_days": {"$sum": "$stockout"},
                    "total_demand": {"$sum": "$demand"},
                    "unfulfilled_demand": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$stockout", 1]},
                                "$demand", 0
                            ]
                        }
                    }
                }
            }
        ]
        
        stockout_result = list(db.daily_demand.aggregate(stockout_pipeline))
        
        if stockout_result:
            result = stockout_result[0]
            fill_rate = ((result["total_demand"] - result["unfulfilled_demand"]) / result["total_demand"] * 100) if result["total_demand"] > 0 else 100
            stockout_rate = (result["stockout_days"] / result["total_days"] * 100) if result["total_days"] > 0 else 0
        else:
            fill_rate = 0
            stockout_rate = 0
        
        return {
            "total_skus": total_skus,
            "in_stock_percentage": round(100 - stockout_rate, 2),
            "fill_rate": round(fill_rate, 2),
            "stockout_rate": round(stockout_rate, 2),
            "date_range": f"{start_date} to {end_date}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating KPIs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

