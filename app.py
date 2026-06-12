import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Inventory & Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Load and cache data
@st.cache_data
def load_data():
    df = pd.read_csv('data1.csv')
    # Convert Date column to datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

@st.cache_data
def load_store_mapping():
    # Store location mapping
    store_mapping = {
        '1AIR': 'Walmart Airdrie',
        '1RED': 'Walmart Red Deer',
        '1WBR': 'Walmart Westbrook Mall',
        '1ESC': 'Walmart South Common Edmonton',
        '1SHV': 'Walmart Shawnessy / Shawville',
        '1MAR': 'Walmart Marlborough Mall',
        'CHKM': 'Chinook Centre',
        'MKML': 'Market Mall',
        'TNTM': 'Pacific Place (T&T)',
        'SCRM': 'Southcentre Mall',
        'CIML': 'Crossiron Mills',
        'BVSQ': 'Bow Valley Square',
        'MARL': 'Marlborough Mall',
        'FTMC': 'Fort McMurray Peter Pond Mall',
        'METR': 'Metropolis at Metrotown Burnaby',
        'CENT': 'Surrey Central City',
        'GUIL': 'Guilford Town Centre',
        'PKPL': 'Park Place Mall',
        'C-WH': 'Warehouse Beltline'
    }
    return store_mapping

# Main application
def main():
    # Header
    st.markdown('<div class="main-header">📊 Inventory & Sales Dashboard</div>', unsafe_allow_html=True)
    
    # Load data
    try:
        df = load_data()
        store_mapping = load_store_mapping()
    except FileNotFoundError:
        st.error("❌ data1.csv file not found! Please make sure the file exists in the same directory.")
        st.info("📁 Expected file: data1.csv")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date filter
    if 'Date' in df.columns and not df['Date'].isna().all():
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        if len(date_range) == 2:
            mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
            df = df[mask]
    
    # Product filter
    if 'Product' in df.columns:
        all_products = ['All'] + sorted(df['Product'].dropna().unique().tolist())
        selected_product = st.sidebar.selectbox("Select Product", all_products)
        if selected_product != 'All':
            df = df[df['Product'] == selected_product]
    
    # Store filter (extract store code from 'From' column)
    if 'From' in df.columns:
        df['Store_Code'] = df['From'].apply(lambda x: str(x).split('/')[0] if pd.notna(x) else 'Unknown')
        df['Store_Name'] = df['Store_Code'].map(store_mapping).fillna('Other/Unknown')
        
        all_stores = ['All'] + sorted(df['Store_Name'].unique().tolist())
        selected_store = st.sidebar.selectbox("Select Store", all_stores)
        if selected_store != 'All':
            df = df[df['Store_Name'] == selected_store]
    
    # Status filter
    if 'Status' in df.columns:
        all_statuses = ['All'] + sorted(df['Status'].dropna().unique().tolist())
        selected_status = st.sidebar.selectbox("Select Status", all_statuses)
        if selected_status != 'All':
            df = df[df['Status'] == selected_status]
    
    # Create two dataframes: Sales and Inventory movements
    df_sales = df[df['To'] == 'Partners/Customers'].copy() if 'To' in df.columns else pd.DataFrame()
    df_inventory = df[df['To'] != 'Partners/Customers'].copy() if 'To' in df.columns else df.copy()
    
    # Key Metrics Row
    st.subheader("📈 Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_transactions = len(df)
        st.metric("Total Transactions", f"{total_transactions:,}")
    
    with col2:
        total_units = df['Quantity'].sum() if 'Quantity' in df.columns else 0
        st.metric("Total Units Moved", f"{total_units:,}")
    
    with col3:
        total_sales_units = df_sales['Quantity'].sum() if not df_sales.empty else 0
        st.metric("Units Sold to Customers", f"{total_sales_units:,}")
    
    with col4:
        unique_products = df['Product'].nunique() if 'Product' in df.columns else 0
        st.metric("Unique Products", f"{unique_products:,}")
    
    with col5:
        unique_stores = df['Store_Name'].nunique() if 'Store_Name' in df.columns else 0
        st.metric("Active Stores", f"{unique_stores:,}")
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Sales Analysis", 
        "🏪 Store Performance", 
        "📦 Product Analysis",
        "📅 Time Series Analysis",
        "📋 Raw Data"
    ])
    
    # Tab 1: Sales Analysis
    with tab1:
        st.subheader("Sales to Customers Analysis")
        
        if not df_sales.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top selling products
                st.write("**Top 10 Selling Products**")
                top_products = df_sales.groupby('Product')['Quantity'].sum().sort_values(ascending=False).head(10)
                fig = px.bar(
                    x=top_products.values, 
                    y=top_products.index,
                    orientation='h',
                    title="Top Products by Units Sold",
                    labels={'x': 'Units Sold', 'y': 'Product'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Sales by store
                st.write("**Sales by Store**")
                store_sales = df_sales.groupby('Store_Name')['Quantity'].sum().sort_values(ascending=False).head(10)
                fig = px.pie(
                    values=store_sales.values,
                    names=store_sales.index,
                    title="Sales Distribution by Store"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Daily sales trend
            if 'Date' in df_sales.columns:
                st.write("**Daily Sales Trend**")
                daily_sales = df_sales.groupby(df_sales['Date'].dt.date)['Quantity'].sum().reset_index()
                daily_sales.columns = ['Date', 'Units Sold']
                fig = px.line(
                    daily_sales,
                    x='Date',
                    y='Units Sold',
                    title="Daily Sales Volume",
                    markers=True
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data found (To = 'Partners/Customers')")
    
    # Tab 2: Store Performance
    with tab2:
        st.subheader("Store Performance Analysis")
        
        if 'Store_Name' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Store inventory movement
                st.write("**Store Inventory Movement**")
                store_movement = df.groupby('Store_Name')['Quantity'].sum().sort_values(ascending=False).head(15)
                fig = px.bar(
                    x=store_movement.index,
                    y=store_movement.values,
                    title="Total Inventory Movement by Store",
                    labels={'x': 'Store', 'y': 'Total Units'}
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Transaction count by store
                st.write("**Transaction Count by Store**")
                store_transactions = df.groupby('Store_Name').size().sort_values(ascending=False).head(15)
                fig = px.bar(
                    x=store_transactions.index,
                    y=store_transactions.values,
                    title="Number of Transactions by Store",
                    labels={'x': 'Store', 'y': 'Number of Transactions'},
                    color=store_transactions.values,
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Store detailed table
            st.write("**Store Performance Summary**")
            store_summary = df.groupby('Store_Name').agg({
                'Quantity': ['sum', 'mean', 'count'],
                'Product': 'nunique'
            }).round(2)
            store_summary.columns = ['Total Units', 'Avg Units/Transaction', 'Transactions', 'Unique Products']
            store_summary = store_summary.sort_values('Total Units', ascending=False)
            st.dataframe(store_summary, use_container_width=True)
        else:
            st.info("Store information not available")
    
    # Tab 3: Product Analysis
    with tab3:
        st.subheader("Product Performance Analysis")
        
        if 'Product' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Product movement
                st.write("**Top Products by Total Movement**")
                product_movement = df.groupby('Product')['Quantity'].sum().sort_values(ascending=False).head(15)
                fig = px.bar(
                    x=product_movement.values,
                    y=product_movement.index,
                    orientation='h',
                    title="Top 15 Products by Total Units Moved",
                    labels={'x': 'Total Units', 'y': 'Product'}
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Sales vs Non-sales for top products
                st.write("**Sales vs Inventory Movement**")
                if not df_sales.empty:
                    top_products_list = product_movement.head(10).index.tolist()
                    comparison_df = pd.DataFrame()
                    for product in top_products_list:
                        sales_qty = df_sales[df_sales['Product'] == product]['Quantity'].sum()
                        inventory_qty = df_inventory[df_inventory['Product'] == product]['Quantity'].sum()
                        comparison_df.loc[product, 'Sales to Customers'] = sales_qty
                        comparison_df.loc[product, 'Inventory Movement'] = inventory_qty
                    
                    fig = px.bar(
                        comparison_df,
                        title="Sales vs Inventory Movement - Top Products",
                        labels={'value': 'Units', 'variable': 'Type', 'index': 'Product'}
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No sales data available for comparison")
            
            # Product details table
            st.write("**Product Summary Details**")
            product_summary = df.groupby('Product').agg({
                'Quantity': ['sum', 'mean', 'count'],
                'Status': lambda x: x.mode().iloc[0] if not x.empty else 'N/A',
                'From': 'nunique'
            }).round(2)
            product_summary.columns = ['Total Units', 'Avg Units/Transaction', 'Transactions', 'Most Common Status', 'Unique Locations']
            product_summary = product_summary.sort_values('Total Units', ascending=False)
            st.dataframe(product_summary, use_container_width=True)
        else:
            st.info("Product information not available")
    
    # Tab 4: Time Series Analysis
    with tab4:
        st.subheader("Time Series Analysis")
        
        if 'Date' in df.columns and not df['Date'].isna().all():
            col1, col2 = st.columns(2)
            
            with col1:
                # Time period selector
                time_period = st.selectbox(
                    "Select Time Period",
                    ['Day', 'Week', 'Month']
                )
            
            with col2:
                # Metric selector
                metric = st.selectbox(
                    "Select Metric",
                    ['Quantity', 'Transaction Count']
                )
            
            # Prepare time series data
            if time_period == 'Day':
                df['Time_Period'] = df['Date'].dt.date
            elif time_period == 'Week':
                df['Time_Period'] = df['Date'].dt.to_period('W').astype(str)
            else:
                df['Time_Period'] = df['Date'].dt.to_period('M').astype(str)
            
            if metric == 'Quantity':
                time_series = df.groupby('Time_Period')['Quantity'].sum().reset_index()
                y_label = 'Total Units Moved'
            else:
                time_series = df.groupby('Time_Period').size().reset_index(name='Quantity')
                y_label = 'Number of Transactions'
            
            fig = px.line(
                time_series,
                x='Time_Period',
                y='Quantity',
                title=f"{metric} Over Time ({time_period})",
                markers=True
            )
            fig.update_layout(
                xaxis_title="Time Period",
                yaxis_title=y_label,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Inventory type breakdown over time
            st.write("**Inventory Movement Type Over Time**")
            if 'To' in df.columns:
                df['Movement_Type'] = df['To'].apply(
                    lambda x: 'Sales to Customers' if x == 'Partners/Customers' 
                    else 'Inter-Warehouse' if 'Inter-warehouse' in str(x)
                    else 'Stock Adjustment' if 'adjustment' in str(x).lower()
                    else 'Other'
                )
                
                # Resample by month for cleaner view
                df['Month'] = df['Date'].dt.to_period('M').astype(str)
                movement_by_month = df.groupby(['Month', 'Movement_Type'])['Quantity'].sum().reset_index()
                
                fig = px.area(
                    movement_by_month,
                    x='Month',
                    y='Quantity',
                    color='Movement_Type',
                    title="Inventory Movement Type Distribution Over Time",
                    labels={'Quantity': 'Total Units', 'Month': 'Month'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Date information not available for time series analysis")
    
    # Tab 5: Raw Data
    with tab5:
        st.subheader("Raw Data Viewer")
        
        # Search and filter
        search_term = st.text_input("🔍 Search across all columns", "")
        if search_term:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            display_df = df[mask]
            st.info(f"Found {len(display_df)} rows containing '{search_term}'")
        else:
            display_df = df
        
        # Show number of rows
        st.write(f"Showing {len(display_df)} rows out of {len(df)} total")
        
        # Display dataframe
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            csv_full = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Full Data (CSV)",
                csv_full,
                f"inventory_data_full_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        
        with col2:
            if not df_sales.empty:
                csv_sales = df_sales.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Sales Data Only (CSV)",
                    csv_sales,
                    f"sales_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: gray;'>Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()