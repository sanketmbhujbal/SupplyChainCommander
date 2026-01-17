import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv # pip install python-dotenv

# Load variables from .env file
load_dotenv()

# 1. Connect to DB
# Get the secret safely
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL)

def init_db():
    print("⏳ Connecting to Database...")
    
    # 2. THE SCHEMA (DDL - Data Definition Language)
    # We drop tables if they exist so you can re-run this script safely (Idempotency)
    schema_sql = """
    DROP TABLE IF EXISTS demand_forecasts;
    DROP TABLE IF EXISTS current_inventory;
    DROP TABLE IF EXISTS sales_transactions;
    DROP TABLE IF EXISTS products;

    CREATE TABLE products (
        product_id INT PRIMARY KEY,
        sku VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100),
        type VARCHAR(50),
        base_price DECIMAL(10, 2)
    );

    CREATE TABLE sales_transactions (
        transaction_id SERIAL PRIMARY KEY,
        product_id INT REFERENCES products(product_id),
        transaction_date DATE NOT NULL,
        quantity_sold INT NOT NULL,
        total_amount DECIMAL(10, 2)
    );

    CREATE TABLE current_inventory (
        inventory_id SERIAL PRIMARY KEY,
        product_id INT REFERENCES products(product_id),
        stock_level INT NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE demand_forecasts (
        forecast_id SERIAL PRIMARY KEY,
        product_id INT REFERENCES products(product_id),
        forecast_date DATE NOT NULL,
        predicted_demand INT NOT NULL,
        confidence_interval_lower INT,  -- <--- NEW COLUMN
        confidence_interval_upper INT,  -- <--- NEW COLUMN
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(schema_sql))
        conn.commit()
    print("✅ Schema created successfully.")

def load_data():
    print("⏳ Loading data from CSVs...")
    
    # Read the CSVs we generated earlier
    try:
        df_products = pd.read_csv("products.csv")
        df_sales = pd.read_csv("sales_transactions.csv")
        
        # Rename columns to match SQL table exactly if needed
        # (Our CSV headers: 'id', 'name', 'sku'... SQL expects: 'product_id', 'name'...)
        df_products = df_products.rename(columns={"id": "product_id"})
        
        # Write to SQL
        # if_exists='append' means "add to the table we just created"
        # index=False means "don't upload the pandas row number as a column"
        df_products.to_sql('products', engine, if_exists='append', index=False)
        print(f"   -> Loaded {len(df_products)} products.")
        
        df_sales.to_sql('sales_transactions', engine, if_exists='append', index=False)
        print(f"   -> Loaded {len(df_sales)} sales transactions.")
        
        # Initialize Inventory (Mock Data)
        # Let's assume we start with 50 units of everything
        inventory_data = []
        for pid in df_products['product_id']:
            inventory_data.append({"product_id": pid, "stock_level": 50})
        
        df_inv = pd.DataFrame(inventory_data)
        df_inv.to_sql('current_inventory', engine, if_exists='append', index=False)
        print(f"   -> Initialized inventory for {len(df_inv)} items.")
        
        print("✅ ETL Process Complete!")
        
    except FileNotFoundError:
        print("❌ Error: CSV files not found. Did you run 'generate_mock_data.py'?")

if __name__ == "__main__":
    init_db()
    load_data()