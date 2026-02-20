import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Brazilian E-Commerce Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Brazilian E-Commerce Dashboard")

# ================= LOAD DATA ================= #
@st.cache_data
def load_data():
    base_path = os.path.join(os.path.dirname(__file__), "E-Commerce Public Dataset")
    
    orders = pd.read_csv(os.path.join(base_path, "orders_dataset.csv"), parse_dates=[
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ])
    
    order_items = pd.read_csv(os.path.join(base_path, "order_items_dataset.csv"))
    products = pd.read_csv(os.path.join(base_path, "products_dataset.csv"))
    customers = pd.read_csv(os.path.join(base_path, "customers_dataset.csv"))
    geolocation = pd.read_csv(os.path.join(base_path, "geolocation_dataset.csv"))
    category_translation = pd.read_csv(
        os.path.join(base_path, "product_category_name_translation.csv")
    )
    
    return orders, order_items, products, customers, geolocation, category_translation


orders, order_items, products, customers, geolocation, category_translation = load_data()

# ================= SIDEBAR FILTER ================= #
st.sidebar.header("📅 Filter by Order Date")

orders_clean = orders[
    (orders["order_status"] == "delivered") &
    (orders["order_delivered_customer_date"].notna())
].copy()

min_date = orders_clean["order_purchase_timestamp"].min().date()
max_date = orders_clean["order_purchase_timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    
    orders_filtered = orders_clean[
        (orders_clean["order_purchase_timestamp"].dt.date >= start_date) &
        (orders_clean["order_purchase_timestamp"].dt.date <= end_date)
    ].copy()
else:
    orders_filtered = orders_clean.copy()

st.markdown(f"**Selected Period:** {start_date} to {end_date}")

# ================= IMPORTANT PART ================= #

valid_order_ids = orders_filtered["order_id"].unique()

order_items_filtered = order_items[
    order_items["order_id"].isin(valid_order_ids)
].copy()

# ================= MERGING ================= #

customer_orders = pd.merge(
    customers, 
    orders_filtered, 
    on="customer_id", 
    how="inner"
)

items_product = pd.merge(
    order_items_filtered, 
    products, 
    on="product_id", 
    how="inner"
)

items_product = pd.merge(
    items_product,
    category_translation,
    on="product_category_name",
    how="left"
)

orders_items_product = pd.merge(
    orders_filtered,
    items_product,
    on="order_id",
    how="inner"
)

# ================= OVERVIEW ================= #
st.header("📌 Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Customers", customer_orders["customer_unique_id"].nunique())
col2.metric("Total Orders", customer_orders["order_id"].nunique())

total_revenue = orders_items_product["price"].sum()
col3.metric("Total Revenue (R$)", f"{total_revenue:,.2f}")

# ================= TOP 10 CATEGORY ================= #
st.header("🛒 Product Analysis")

product_summary = orders_items_product.groupby(
    "product_category_name_english"
).agg(
    quantity_sold=("order_item_id", "count"),
    total_revenue=("price", "sum")
).reset_index()

top_products = product_summary.sort_values(
    "total_revenue",
    ascending=False
).head(10)

fig1 = px.bar(
    top_products,
    x="product_category_name_english",
    y="total_revenue",
    text="total_revenue",
    labels={
        "product_category_name_english": "Product Category",
        "total_revenue": "Revenue (R$)"
    },
    title="Top 10 Product Categories by Revenue"
)

fig1.update_traces(
    texttemplate="R$ %{text:,.0f}",
    textposition="outside"
)

fig1.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig1, use_container_width=True)

# ================= CUSTOMER GEOGRAPHY ================= #
st.header("🌎 Customer Geography Analysis")

geolocation_silver = geolocation.groupby(
    ['geolocation_zip_code_prefix', 'geolocation_city', 'geolocation_state']
)[['geolocation_lat', 'geolocation_lng']].median().reset_index()

customers_geo = pd.merge(
    customer_orders,
    geolocation_silver,
    left_on="customer_zip_code_prefix",
    right_on="geolocation_zip_code_prefix",
    how="left"
).drop_duplicates(subset="order_id")

fig_map = px.scatter_mapbox(
    customers_geo,
    lat="geolocation_lat",
    lon="geolocation_lng",
    hover_name="customer_city",
    hover_data=["customer_state"],
    zoom=3,
    height=600
)

fig_map.update_layout(mapbox_style="open-street-map")
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")
st.markdown("Interactive dashboard with dynamic date filtering.")