"""
Data Loader - Downloads and joins the Olist Brazilian E-Commerce Dataset.
Produces a single analytical DataFrame ready for downstream analytics.
"""
import os
import ssl
import zipfile
import urllib.request
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CSV_URLS = {
    "olist_orders_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_orders_dataset.csv",
    "olist_customers_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_customers_dataset.csv",
    "olist_order_items_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_order_items_dataset.csv",
    "olist_products_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_products_dataset.csv",
    "olist_sellers_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_sellers_dataset.csv",
    "olist_order_payments_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_order_reviews_dataset.csv",
    "olist_geolocation_dataset.csv": "https://raw.githubusercontent.com/Kaaykun/OlistAnalysis/master/data/csv/olist_geolocation_dataset.csv",
}

FALLBACK_URL = "https://github.com/Kaaykun/OlistAnalysis/archive/refs/heads/master.zip"

CATEGORY_NAMES = {
    "pc_gamer": "PC Gaming",
    "portateis_cozinha_e_preparadores_de_alimentos": "Kitchen Appliances",
    "la_cuisine": "Kitchen & Dining",
    "cama_mesa_banho": "Bed & Table & Bath",
    "beleza_saude": "Health & Beauty",
    "esporte_lazer": "Sports & Leisure",
    "informatica_acessorios": "Computers & Accessories",
    "moveis_decoracao": "Furniture & Decor",
    "utilidades_domesticas": "Home Utilities",
    "automotivo": "Automotive",
    "brinquedos": "Toys",
    "cool_stuff": "Cool Stuff",
    "ferramentas_jardim": "Garden Tools",
    "telefonia": "Telephony",
    "bebes": "Baby Products",
    "livros_interesse_geral": "Books",
    "perfumaria": "Perfumery",
    "relogios_presentes": "Watches & Gifts",
    "papelaria": "Stationery",
    "bolsas_acessorios": "Bags & Accessories",
    "eletroportateis": "Small Appliances",
    "construcao_ferramentas_construcao": "Construction Tools",
    "construcao_ferramentas_iluminacao": "Lighting Tools",
    "construcao_ferramentas_jardim": "Garden Construction Tools",
    "construcao_ferramentas_seguranca": "Security Tools",
    "malas_acessorios": "Luggage & Accessories",
    "climatizacao": "Climate Control",
    "casa_construcao": "Home Construction",
    "eletrodomesticos_2": "Home Appliances (2)",
    "eletrodomesticos": "Home Appliances",
    "artigos_de_festas": "Party Supplies",
    "artigos_de_natal": "Christmas Supplies",
    "fashion_bolsas_acessorios": "Fashion Bags & Accessories",
    "fashion_calcados": "Fashion Shoes",
    "fashion_roupa_feminina": "Women's Fashion",
    "fashion_roupa_infantil": "Children's Fashion",
    "fashion_roupa_masculina": "Men's Fashion",
    "frutas_vegetais": "Fruits & Vegetables",
    "casa_forno_banheiro": "Kitchen & Bathroom",
    "audio": "Audio",
    "image": "Imaging & Video",
    "tablets_impressao_imagem": "Tablets & Printing",
    "sinalizacao_e_seguranca": "Signage & Security",
    "fashion_underwear_e_moda_praia": "Underwear & Beach Fashion",
}

STATUS_MAP = {
    "delivered": "Delivered",
    "shipped": "Shipped",
    "canceled": "Canceled",
    "unavailable": "Unavailable",
    "invoiced": "Invoiced",
    "processing": "Processing",
    "created": "Created",
    "approved": "Approved",
}


def _download_file(url: str, dest: Path) -> bool:
    """Download a single CSV file. Tries curl first, then urllib with SSL workaround."""
    # Try curl (handles SSL natively on macOS)
    try:
        result = subprocess.run(
            ["curl", "-sL", "-o", str(dest), "--max-time", "30", url],
            capture_output=True, timeout=35,
        )
        if result.returncode == 0 and dest.exists() and dest.stat().st_size > 100:
            return True
    except Exception:
        pass
    # Fallback: urllib with unverified SSL context
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=30) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        return dest.exists() and dest.stat().st_size > 100
    except Exception:
        return False


def _download_zip_and_extract() -> None:
    """Download the full zip archive and extract CSVs into data/."""
    zip_path = DATA_DIR / "olist.zip"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        subprocess.run(
            ["curl", "-sL", "-o", str(zip_path), "--max-time", "60", FALLBACK_URL],
            capture_output=True, timeout=70,
        )
        if not zip_path.exists() or zip_path.stat().st_size < 1000:
            raise Exception("Zip download failed")
        with zipfile.ZipFile(zip_path, "r") as z:
            for name in z.namelist():
                if name.endswith(".csv") and "olist_" in name:
                    basename = os.path.basename(name)
                    if basename not in [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]:
                        with z.open(name) as src, open(DATA_DIR / basename, "wb") as dst:
                            dst.write(src.read())
        zip_path.unlink(missing_ok=True)
    except Exception as e:
        print(f"  Warning: Could not download zip archive: {e}")


def _ensure_datasets() -> None:
    """Make sure all required CSV files exist in data/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = {f for f in os.listdir(DATA_DIR) if f.endswith(".csv")}
    missing = [name for name in CSV_URLS if name not in existing]
    if not missing:
        return
    print(f"  Downloading {len(missing)} missing dataset files...")
    for name in missing:
        dest = DATA_DIR / name
        ok = _download_file(CSV_URLS[name], dest)
        if ok:
            print(f"    Downloaded {name}")
        else:
            print(f"    Failed: {name}")
    still_missing = [name for name in CSV_URLS if name not in {f for f in os.listdir(DATA_DIR) if f.endswith(".csv")}]
    if still_missing:
        print("  Trying zip archive fallback...")
        _download_zip_and_extract()


def load_orders() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv", parse_dates=[
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ])
    return df


def load_customers() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")


def load_order_items() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv", parse_dates=["shipping_limit_date"])
    return df


def load_products() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
    df["product_category_name_english"] = df["product_category_name"].map(CATEGORY_NAMES).fillna(df["product_category_name"])
    return df


def load_sellers() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")


def load_payments() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")


def load_reviews() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "olist_order_reviews_dataset.csv", parse_dates=["review_creation_date", "review_answer_timestamp"])
    return df


def load_geolocation() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_geolocation_dataset.csv")


def build_analytical_dataset() -> pd.DataFrame:
    """Join all tables into a single analytical DataFrame at the order-item level."""
    _ensure_datasets()

    print("  Loading raw tables...")
    orders = load_orders()
    customers = load_customers()
    items = load_order_items()
    products = load_products()
    sellers = load_sellers()
    payments = load_payments()
    reviews = load_reviews()

    # Aggregate payments per order (handle split payments)
    pay_agg = (
        payments.groupby("order_id")
        .agg(
            total_payment_value=("payment_value", "sum"),
            payment_installments=("payment_installments", "max"),
            primary_payment_type=("payment_type", lambda x: x.mode().iloc[0] if len(x) > 0 else "unknown"),
        )
        .reset_index()
    )

    # Aggregate reviews per order (take most recent review)
    reviews_sorted = reviews.sort_values("review_creation_date", ascending=False)
    rev_agg = (
        reviews_sorted.groupby("order_id")
        .first()
        .reset_index()[["order_id", "review_score", "review_comment_title", "review_comment_message"]]
    )

    # Merge everything together
    print("  Joining tables...")
    df = (
        items
        .merge(orders, on="order_id", how="inner")
        .merge(customers, on="customer_id", how="inner")
        .merge(products, on="product_id", how="left")
        .merge(sellers, on="seller_id", how="left")
        .merge(pay_agg, on="order_id", how="left")
        .merge(rev_agg, on="order_id", how="left")
    )

    # Derived columns
    df["order_status_clean"] = df["order_status"].map(STATUS_MAP).fillna(df["order_status"])

    # Revenue
    df["revenue"] = df["total_payment_value"].fillna(df["price"] + df["freight_value"])

    # Delivery time in days
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400.0

    # Estimated delivery time
    df["estimated_delivery_days"] = (
        df["order_estimated_delivery_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400.0

    # Delivery delay
    df["delivery_delay_days"] = df["delivery_days"] - df["estimated_delivery_days"]

    # Order date components
    df["order_date"] = df["order_purchase_timestamp"].dt.date
    df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M")
    df["order_week"] = df["order_purchase_timestamp"].dt.to_period("W")
    df["order_year"] = df["order_purchase_timestamp"].dt.year
    df["order_quarter"] = df["order_purchase_timestamp"].dt.quarter

    # Customer tenure (days since first purchase)
    customer_first = df.groupby("customer_unique_id")["order_purchase_timestamp"].min().rename("first_purchase_date")
    df = df.merge(customer_first, on="customer_unique_id", how="left")
    df["customer_tenure_days"] = (df["order_purchase_timestamp"] - df["first_purchase_date"]).dt.total_seconds() / 86400.0

    # Is repeat customer
    customer_order_count = df.groupby("customer_unique_id")["order_id"].nunique().rename("customer_order_count")
    df = df.merge(customer_order_count, on="customer_unique_id", how="left")
    df["is_repeat_customer"] = df["customer_order_count"] > 1

    print(f"  Analytical dataset ready: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def get_category_lookup() -> dict:
    """Return product_category_name -> English name mapping."""
    return CATEGORY_NAMES.copy()


if __name__ == "__main__":
    df = build_analytical_dataset()
    print("\nDataset summary:")
    print(f"  Date range: {df['order_purchase_timestamp'].min()} to {df['order_purchase_timestamp'].max()}")
    print(f"  Unique customers: {df['customer_unique_id'].nunique():,}")
    print(f"  Unique orders: {df['order_id'].nunique():,}")
    print(f"  Total revenue: ${df['revenue'].sum():,.2f}")
    print(f"  Columns: {list(df.columns)}")
