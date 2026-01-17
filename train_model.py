import pandas as pd
from sqlalchemy import create_engine, text
from prophet import Prophet
import os
from dotenv import load_dotenv # pip install python-dotenv

# Load variables from .env file
load_dotenv()

# 1. Connect to DB
# Get the secret safely
DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL)

def train_and_predict():
    print("⏳ Fetching data from Database...")
    products_df = pd.read_sql("SELECT product_id, name FROM products", engine)
    
    for index, row in products_df.iterrows():
        p_id = row['product_id']
        p_name = row['name']
        print(f"\nTraining model for: {p_name} (ID: {p_id})...")
        
        # 1. Fetch Sales Data
        query = f"""
            SELECT transaction_date as ds, SUM(quantity_sold) as y
            FROM sales_transactions 
            WHERE product_id = {p_id}
            GROUP BY transaction_date
            ORDER BY transaction_date
        """
        df = pd.read_sql(query, engine)
        
        if len(df) < 5: # Lowered threshold for testing
            print(f"   ⚠️ Not enough data ({len(df)} rows). Skipping.")
            continue
            
        # 2. Train Prophet
        m = Prophet(daily_seasonality=False, yearly_seasonality=True)
        m.fit(df)
        
        # 3. Predict NEXT 60 Days (Make range wider to catch 'Today')
        future = m.make_future_dataframe(periods=60) 
        forecast = m.predict(future)
        
        # 4. Ensure last_sale_date is a Pandas Timestamp, not a Python date
        last_sale_date = pd.to_datetime(df['ds'].max())

        # Filter: Keep only future predictions
        future_forecast = forecast[forecast['ds'] > last_sale_date].copy()
        
        if future_forecast.empty:
            print("   ⚠️ Forecast DataFrame is empty! Logic error.")
            continue

        # 5. Prepare and Save
        upload_df = future_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        upload_df.columns = ['forecast_date', 'predicted_demand', 'confidence_interval_lower', 'confidence_interval_upper']
        upload_df['product_id'] = p_id
        
        # Clean negatives and round
        upload_df['predicted_demand'] = upload_df['predicted_demand'].apply(lambda x: max(0, int(round(x))))
        
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM demand_forecasts WHERE product_id = {p_id}"))
            conn.commit()
            
        upload_df.to_sql('demand_forecasts', engine, if_exists='append', index=False)
        print(f"   ✅ Saved {len(upload_df)} days of forecasts (From {upload_df['forecast_date'].min()} to {upload_df['forecast_date'].max()})")

if __name__ == "__main__":
    train_and_predict()