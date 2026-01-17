import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- UPDATED SECTION ---
# Dynamic Dates: End "yesterday" so we predict "tomorrow"
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=365 * 2) # 2 years of history
# -----------------------

days = (end_date - start_date).days
date_range = [start_date + timedelta(days=x) for x in range(days)]

# 2. Define Products with different "behaviours"
products = [
    {"id": 1, "name": "Winter Jacket", "sku": "WIN-001", "base_price": 120.00, "type": "seasonal_winter"},
    {"id": 2, "name": "Beach Towel", "sku": "SUM-002", "base_price": 25.00, "type": "seasonal_summer"},
    {"id": 3, "name": "AA Batteries", "sku": "GEN-003", "base_price": 15.00, "type": "steady"},
    {"id": 4, "name": "Smart Home Hub", "sku": "TEC-004", "base_price": 200.00, "type": "trending"}
]

sales_data = []

# 3. Generate Daily Sales with Logic
for date in date_range:
    month = date.month
    day_of_year = date.timetuple().tm_yday
    
    for p in products:
        base_demand = 50 # Average daily sales
        noise = np.random.normal(0, 10) # Random fluctuation (standard deviation 10)
        
        # LOGIC: Adjust demand based on Product Type
        if p["type"] == "seasonal_winter":
            # Sine wave peaking in winter (Months 12 and 1)
            seasonality = 40 * np.cos((month - 1) * 2 * np.pi / 12) 
            demand = base_demand + seasonality + noise
            
        elif p["type"] == "seasonal_summer":
             # Sine wave peaking in summer (Months 6 and 7)
            seasonality = 40 * np.cos((month - 7) * 2 * np.pi / 12)
            demand = base_demand + seasonality + noise
            
        elif p["type"] == "trending":
            # Linear growth: Sales increase by 0.1 units every day
            trend = 0.1 * (date - start_date).days
            demand = 20 + trend + noise # Starts lower (20) but grows
            
        else: # "steady"
            demand = base_demand + noise

        # Clean up: demand can't be negative
        final_qty = max(0, int(demand))
        
        # Only record if a sale happened
        if final_qty > 0:
            sales_data.append({
                "product_id": p["id"],
                "transaction_date": date.strftime("%Y-%m-%d"),
                "quantity_sold": final_qty,
                "total_amount": round(final_qty * p["base_price"], 2)
            })

# 4. Convert to DataFrames
df_products = pd.DataFrame(products)
df_sales = pd.DataFrame(sales_data)

# 5. Save to CSV (so we can inspect before DB load)
df_products.to_csv("products.csv", index=False)
df_sales.to_csv("sales_transactions.csv", index=False)

print(f"Generated {len(df_sales)} sales transactions.")
print("Files saved: products.csv, sales_transactions.csv")