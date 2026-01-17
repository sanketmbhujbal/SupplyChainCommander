from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
import os
from dotenv import load_dotenv # pip install python-dotenv

# Load variables from .env file
load_dotenv()

# 1. Connect to DB
# Get the secret safely
DB_URL = os.getenv("DB_URL")

app = FastAPI(title="Supply Chain Commander", version="1.0")

engine = create_engine(DB_URL)

# 2. Define the Output Format (Pydantic Model)
# This ensures our API always returns clean, structured JSON
class ProductStatus(BaseModel):
    product_id: int
    name: str
    current_stock: int
    predicted_demand_next_7_days: int
    recommendation: str
    reorder_quantity: int

@app.get("/")
def home():
    return {"message": "Supply Chain AI is Live! Go to /docs for the dashboard."}

@app.get("/inventory/status", response_model=list[ProductStatus])
def get_inventory_status():
    """
    Compares Current Stock vs. AI Forecasts to generate reorder recommendations.
    """
    print("⏳ Calculating inventory status...")
    
    with engine.connect() as conn:
        # A. Get Current Stock
        stock_query = """
        SELECT p.product_id, p.name, i.stock_level 
        FROM products p
        JOIN current_inventory i ON p.product_id = i.product_id
        """
        stock_df = pd.read_sql(stock_query, conn)
        
        # B. Get Forecasts (Next 7 Days)
        # We sum the predicted demand for the upcoming week
        forecast_query = """
        SELECT product_id, SUM(predicted_demand) as demand_7_days
        FROM demand_forecasts
        WHERE forecast_date >= CURRENT_DATE 
          AND forecast_date <= CURRENT_DATE + INTERVAL '7 days'
        GROUP BY product_id
        """
        forecast_df = pd.read_sql(forecast_query, conn)
    
    # C. Merge Data (The "Full Stack" Logic)
    # This combines the 'Now' (Stock) with the 'Future' (Forecast)
    merged_df = pd.merge(stock_df, forecast_df, on="product_id", how="left")
    
    # Handle products with no forecast (fill with 0)
    merged_df['demand_7_days'] = merged_df['demand_7_days'].fillna(0).astype(int)
    
    results = []
    
    # D. Apply Business Rules
    for _, row in merged_df.iterrows():
        stock = row['stock_level']
        demand = row['demand_7_days']
        
        # LOGIC: If we don't have enough stock to cover next week's demand...
        if stock < demand:
            status = "⚠️ LOW STOCK"
            # Reorder enough to cover demand + buffer (e.g. 10 units)
            reorder = (demand - stock) + 10 
        else:
            status = "✅ Healthy"
            reorder = 0
            
        results.append({
            "product_id": row['product_id'],
            "name": row['name'],
            "current_stock": stock,
            "predicted_demand_next_7_days": demand,
            "recommendation": status,
            "reorder_quantity": reorder
        })
        
    return results