import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Brazilian E-Commerce Public Dataset Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Brazilian E-Commerce Public Dataset Dashboard")

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
    payments = pd.read_csv(os.path.join(base_path, "order_payments_dataset.csv"))
    reviews = pd.read_csv(os.path.join(base_path, "order_reviews_dataset.csv"), parse_dates=[
        "review_creation_date", "review_answer_timestamp"
    ])
    customers = pd.read_csv(os.path.join(base_path, "customers_dataset.csv"))
    sellers = pd.read_csv(os.path.join(base_path, "sellers_dataset.csv"))
    geolocation = pd.read_csv(os.path.join(base_path, "geolocation_dataset.csv"))
    category_translation = pd.read_csv(os.path.join(base_path, "product_category_name_translation.csv"))
    
    return orders, order_items, products, payments, reviews, customers, sellers, geolocation, category_translation

orders, order_items, products, payments, reviews, customers, sellers, geolocation, category_translation = load_data()

# Sidebar Filter
st.sidebar.title("Filter Options")
selected_states = st.sidebar.multiselect(
    "Select Customer States", options=customers['customer_state'].unique(), default=[]
)

# Data Cleaning & Merge
orders = orders[orders["order_status"] == "delivered"].copy()

# Tambah status ketepatan
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

# Merge payments + reviews
payments_reviews = pd.merge(payments, reviews, on="order_id", how="left")
payments_reviews["indikator_komentar"] = payments_reviews["review_comment_message"].notna().astype(int)

# Merge customer_orders + payments_reviews
full_data = pd.merge(customer_orders, payments_reviews, on="order_id", how="left")

# Apply Filter
if selected_states:
    customer_orders = customer_orders[customer_orders["customer_state"].isin(selected_states)]
    orders_items_product = orders_items_product[orders_items_product["customer_id"].isin(customer_orders["customer_id"])]
    full_data = full_data[full_data["customer_id"].isin(customer_orders["customer_id"])]

# Overview
col1, col2, col3 = st.columns(3)

col1.metric("Total Customers", customer_orders["customer_id"].nunique())
col2.metric("Total Orders", customer_orders["order_id"].nunique())
col3.metric("Total Revenue (R$)", round(full_data["payment_value"].sum(),2))

# Product Analysis
st.header("🛒 Product Analysis")
product_summary = orders_items_product.groupby("product_id").agg({
    "order_item_id":"count",
    "price":"mean"
}).rename(columns={"order_item_id":"quantity_sold"}).reset_index()

product_summary["total_revenue"] = product_summary["quantity_sold"] * product_summary["price"]
top_products = product_summary.sort_values("total_revenue", ascending=False).head(10)

colors_top = px.colors.sequential.Blues_r
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

# Payment Analysis
st.header("💳 Payment Analysis")
payment_summary = full_data.groupby("payment_type").agg({
    "order_id":"nunique",
    "payment_value":["min","max","mean"]
}).reset_index()
payment_summary.columns = ["payment_type","total_orders","min_payment","max_payment","avg_payment"]

# Bar chart
fig2 = px.bar(
    payment_summary,
    x="payment_type",
    y="total_orders",
    color="total_orders",
    color_continuous_scale=px.colors.sequential.Teal,
    text="total_orders",
    labels={"total_orders":"Total Orders","payment_type":"Payment Type"},
    title="Payment Method Distribution"
)
st.plotly_chart(fig2, use_container_width=True)

# Delivery Status Analysis
orders_filtered = orders.copy()
if selected_states:
    orders_filtered = orders[orders["customer_id"].isin(customer_orders["customer_id"])]
st.header("📦 Delivery Status Analysis")
delivery_counts = orders_filtered["status_ketepatan"].value_counts().reset_index()
delivery_counts.columns = ["status","count"]

col_del1, col_del2 = st.columns(2)

fig3 = go.Figure(data=[go.Pie(
    labels=delivery_counts['status'],
    values=delivery_counts['count'],
    hole=0.5,
    marker_colors=["#1f77b4","#aec7e8"], 
    textinfo="label+percent"
)])
fig3.update_layout(title="Delivery On-Time vs Late")
col_del1.plotly_chart(fig3, use_container_width=True)

# Insight
on_time = delivery_counts.loc[delivery_counts['status']=="On Time","count"].values[0]
late = delivery_counts.loc[delivery_counts['status']=="Late","count"].values[0]
insight_text = f"Total On Time: {on_time}\nTotal Late: {late}\nPersentase Tepat Waktu: {round(on_time/(on_time+late)*100,2)}%"
col_del2.markdown("**Delivery Insights**")
col_del2.info(insight_text)

# Customer Geography Analysis
st.header("🌎 Customer Geography Analysis")
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

st.subheader("Customer Map")
fig4 = px.scatter_mapbox(
    customers_geo,
    lat="geolocation_lat",
    lon="geolocation_lng",
    hover_name="customer_city",
    hover_data=["customer_state","order_id"],
    color_discrete_sequence=["blue"],
    zoom=3,
    height=600
)
fig4.update_layout(mapbox_style="open-street-map")
fig4.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig4, use_container_width=True)

# Review Analysis
st.header("⭐ Review Analysis")
reviews_summary = full_data.groupby("review_score").agg({
    "order_id":"count"
}).reset_index().rename(columns={"order_id":"count"})

fig6 = px.bar(
    reviews_summary,
    x="review_score",
    y="count",
    color="review_score",
    color_continuous_scale=px.colors.sequential.Blues,
    text="count",
    labels={"review_score":"Review Score","count":"Total Orders"},
    title="Review Score Distribution"
)
st.plotly_chart(fig6, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("This dashboard was created using **Streamlit** and Brazilian E-Commerce Public Dataset by Olist.")
