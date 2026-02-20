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

# ------------------ LOAD DATA ------------------ #
@st.cache_data
def load_data():
    # Ganti base_path sesuai folder dataset Streamlit
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

# ------------------ CLEANING ------------------ #

# Fokus hanya pada orders delivered
orders = orders[orders["order_status"] == "delivered"].copy()

# Buat indikator ketepatan waktu
orders["status_ketepatan"] = np.where(
    orders["order_delivered_customer_date"] < orders["order_estimated_delivery_date"],
    "On Time",
    "Late"
)

# Fill missing product info
products = products.drop(columns=[
    "product_name_lenght",
    "product_description_lenght",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
])

products["product_category_name"] = products["product_category_name"].fillna("outro")
products["product_photos_qty"] = products["product_photos_qty"].fillna(0)

# ------------------ SIDEBAR FILTER ------------------ #
st.sidebar.title("Filter Options")

# Filter tanggal opsional
min_date = orders["order_purchase_timestamp"].min().date()
max_date = orders["order_purchase_timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select Order Date Range (Optional)",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    orders = orders[
        (orders["order_purchase_timestamp"].dt.date >= start_date) &
        (orders["order_purchase_timestamp"].dt.date <= end_date)
    ]
    st.markdown(f"**Selected Period:** {start_date} to {end_date}")

# ------------------ MERGING DATA ------------------ #

# Customers + Orders
customer_orders = pd.merge(customers, orders, on="customer_id", how="inner")

# Order Items + Products
items_product = pd.merge(order_items, products, on="product_id", how="inner")
items_product = pd.merge(
    items_product,
    category_translation,
    on="product_category_name",
    how="left"
)

# Orders + Items + Category
orders_items_product = pd.merge(
    orders,
    items_product,
    on="order_id",
    how="inner"
)

# ------------------ OVERVIEW ------------------ #
st.header("📌 Overview")
col1, col2, col3 = st.columns(3)

col1.metric("Total Customers", customer_orders["customer_unique_id"].nunique())
col2.metric("Total Orders", customer_orders["order_id"].nunique())
col3.metric("Total Revenue (R$)", f"{orders_items_product['price'].sum():,.2f}")

# ------------------ TOP 10 PRODUCT CATEGORY ------------------ #
st.header("🛒 Product Category Analysis")

product_summary = orders_items_product.groupby("product_category_name_english").agg(
    quantity_sold=("order_item_id", "count"),
    total_revenue=("price", "sum")
).reset_index()

top_products = product_summary.sort_values("total_revenue", ascending=False).head(10)

fig1 = px.bar(
    top_products,
    x="product_category_name_english",
    y="total_revenue",
    color="total_revenue",
    color_continuous_scale=px.colors.sequential.Blues,
    text="total_revenue",
    labels={"product_category_name_english": "Product Category",
            "total_revenue": "Revenue (R$)"},
    title="Top 10 Product Categories by Revenue"
)

fig1.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
fig1.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig1, use_container_width=True)

# ------------------ CUSTOMER GEOGRAPHY ------------------ #
st.header("🌎 Customer Geography Analysis")

# Median lat/lng per ZIP
geolocation_silver = geolocation.groupby(
    ['geolocation_zip_code_prefix', 'geolocation_city', 'geolocation_state']
)[['geolocation_lat', 'geolocation_lng']].median().reset_index()

# Gabungkan dengan customer_orders
customers_geo = pd.merge(
    customer_orders,
    geolocation_silver,
    left_on="customer_zip_code_prefix",
    right_on="geolocation_zip_code_prefix",
    how="left"
).drop_duplicates(subset="order_id")

# Map
st.subheader("Customer Distribution Map")
fig_map = px.scatter_mapbox(
    customers_geo,
    lat="geolocation_lat",
    lon="geolocation_lng",
    hover_name="customer_city",
    hover_data=["customer_state"],
    color_discrete_sequence=["blue"],
    zoom=3,
    height=600
)
fig_map.update_layout(mapbox_style="open-street-map")
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

# Top 10 Cities
st.subheader("Top 10 Cities with Most Customers")
top_cities = customers_geo.groupby('customer_city')['customer_unique_id'].nunique().sort_values(ascending=False).head(10)

fig_hist = px.bar(
    top_cities[::-1],
    x=top_cities.values[::-1],
    y=top_cities.index[::-1],
    orientation='h',
    labels={"x":"Number of Customers", "y":"City"},
    text=top_cities[::-1],
    title="Top 10 Cities by Customer Count"
)
fig_hist.update_traces(textposition="outside")
st.plotly_chart(fig_hist, use_container_width=True)

# ------------------ FOOTER ------------------ #
st.markdown("---")
st.markdown("This dashboard was created using **Streamlit** and Brazilian E-Commerce Public Dataset by Olist.")