import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(
    page_title="Brazilian E-Commerce Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Brazilian E-Commerce Dashboard")

# Load Data
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
    
    return orders, order_items, products, customers, geolocation

orders, order_items, products, customers, geolocation = load_data()

# Sidebar Filter
st.sidebar.title("Filter Options")
selected_states = st.sidebar.multiselect(
    "Select Customer States",
    options=customers['customer_state'].unique(),
    default=[]
)

# Data Cleaning & Merge
orders = orders[orders["order_status"] == "delivered"].copy()
orders["status_ketepatan"] = np.where(
    orders["order_delivered_customer_date"] < orders["order_estimated_delivery_date"],
    "On Time", "Late"
)

# Merge customers + orders
customer_orders = pd.merge(customers, orders, on="customer_id", how="inner")

# Merge order_items + products
items_product = pd.merge(order_items, products, on="product_id", how="inner")

# Merge orders + items_product
orders_items_product = pd.merge(orders, items_product, on="order_id", how="inner")

# Apply Filter
if selected_states:
    customer_orders = customer_orders[customer_orders["customer_state"].isin(selected_states)]
    orders_items_product = orders_items_product[orders_items_product["customer_id"].isin(customer_orders["customer_id"])]

# ------------------ OVERVIEW ------------------ #
st.header("📌 Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Total Customers", customer_orders["customer_id"].nunique())
col2.metric("Total Orders", customer_orders["order_id"].nunique())
col3.metric("Total Revenue (R$)", round(orders_items_product["price"].sum(),2))

# ------------------ TOP 10 PRODUCT REVENUE ------------------ #
st.header("🛒 Product Analysis")
product_summary = orders_items_product.groupby("product_id").agg({
    "order_item_id":"count",
    "price":"mean"
}).rename(columns={"order_item_id":"quantity_sold"}).reset_index()
product_summary["total_revenue"] = product_summary["quantity_sold"] * product_summary["price"]
top_products = product_summary.sort_values("total_revenue", ascending=False).head(10)

fig1 = px.bar(
    top_products,
    x="product_id",
    y="total_revenue",
    color="total_revenue",
    color_continuous_scale=px.colors.sequential.Blues,
    text="quantity_sold",
    labels={"product_id":"Product ID", "total_revenue":"Revenue R$"},
    title="Top 10 Product Revenue"
)
st.plotly_chart(fig1, use_container_width=True)

# ------------------ CUSTOMER GEOGRAPHY ------------------ #
st.header("🌎 Customer Geography Analysis")

# Median geolocation per zip code
geolocation_silver = geolocation.groupby(
    ['geolocation_zip_code_prefix', 'geolocation_city', 'geolocation_state']
)[['geolocation_lat','geolocation_lng']].median().reset_index()

customers_geo = pd.merge(
    customer_orders,
    geolocation_silver,
    left_on="customer_zip_code_prefix",
    right_on="geolocation_zip_code_prefix",
    how="left"
).drop_duplicates(subset="order_id")

# Map
st.subheader("Customer Map")
fig_map = px.scatter_mapbox(
    customers_geo,
    lat="geolocation_lat",
    lon="geolocation_lng",
    hover_name="customer_city",
    hover_data=["customer_state","order_id"],
    color_discrete_sequence=["blue"],
    zoom=3,
    height=600
)
fig_map.update_layout(mapbox_style="open-street-map")
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

# Histogram Top 10 Cities
st.subheader("Top 10 Cities with Most Customers")
top_cities = customers_geo.groupby('customer_city')['customer_id'] \
               .nunique().sort_values(ascending=False).head(10)
fig_hist = px.bar(
    top_cities[::-1],
    x=top_cities.values[::-1],
    y=top_cities.index[::-1],
    orientation='h',
    labels={"x":"Number of Customers", "y":"City"},
    text=top_cities[::-1],
    title="Top 10 Cities by Customer Count"
)
st.plotly_chart(fig_hist, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("This dashboard was created using **Streamlit** and Brazilian E-Commerce Public Dataset by Olist.")
