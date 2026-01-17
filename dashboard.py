import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Supply Chain Commander", layout="wide")

st.title("📦 Supply Chain Commander")
st.markdown("Real-time Inventory Optimization & Forecasting System")

# 1. Fetch Data from our own API
# We talk to the FastAPI backend running on port 8000
API_URL = "http://127.0.0.1:8000/inventory/status"

try:
    response = requests.get(API_URL)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        
        # 2. Key Metrics (The "Executive Summary")
        # Count how many items need reordering
        low_stock_count = df[df['recommendation'] == "⚠️ LOW STOCK"].shape[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Products", len(df))
        col2.metric("Low Stock Alerts", low_stock_count, delta_color="inverse")
        col3.metric("System Status", "Online", delta_color="normal")
        
        # 3. The Interactive Table
        st.subheader("Inventory Status")
        
        # Highlight rows based on status
        def highlight_status(val):
            color = '#ffcccb' if val == '⚠️ LOW STOCK' else '#90ee90'
            return f'background-color: {color}'

        # Apply styling
        styled_df = df.style.applymap(highlight_status, subset=['recommendation'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        # 4. Action Button
        # This simulates the "Integrator" role - closing the loop
        if low_stock_count > 0:
            if st.button(f"🚨 Generate Purchase Orders for {low_stock_count} Items"):
                st.success(f"Purchase Orders sent to suppliers for: {', '.join(df[df['recommendation'] == '⚠️ LOW STOCK']['name'].tolist())}")
                st.balloons()
        
    else:
        st.error("Failed to connect to API. Is uvicorn running?")
        
except Exception as e:
    st.error(f"Error: {e}")
    st.info("Make sure your FastAPI server is running! (uvicorn main:app --reload)")