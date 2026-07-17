"""
Analytics Module - Executive KPIs, Funnel, Customer, Revenue, and Product Analytics.
All metrics are computed from the analytical dataset with zero fabricated numbers.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


# ---------------------------------------------------------------------------
# Executive KPIs
# ---------------------------------------------------------------------------

def compute_executive_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute top-level executive KPIs from the analytical dataset."""
    orders_df = df.drop_duplicates(subset=["order_id"])
    customers_df = df.drop_duplicates(subset=["customer_unique_id"])

    total_revenue = orders_df["revenue"].sum()
    total_orders = orders_df["order_id"].nunique()
    unique_customers = customers_df["customer_unique_id"].nunique()

    repeat_customers = (
        orders_df.groupby("customer_unique_id")["order_id"]
        .nunique()
        .pipe(lambda s: (s > 1).sum())
    )

    aov = total_revenue / total_orders if total_orders else 0
    repeat_purchase_rate = repeat_customers / unique_customers if unique_customers else 0

    # CLV: total revenue / unique customers
    clv = total_revenue / unique_customers if unique_customers else 0

    # Monthly growth: only compare complete months (exclude first and last month
    # which are likely partial). Use median order count as threshold for completeness.
    monthly_orders = orders_df.groupby("order_month").agg(
        revenue=("revenue", "sum"),
        order_count=("order_id", "nunique"),
    ).sort_index()
    if len(monthly_orders) >= 3:
        median_orders = monthly_orders["order_count"].median()
        complete_months = monthly_orders[monthly_orders["order_count"] >= median_orders * 0.5]
        if len(complete_months) >= 2:
            latest_complete = complete_months.iloc[-1]["revenue"]
            prev_complete = complete_months.iloc[-2]["revenue"]
            monthly_growth = ((latest_complete - prev_complete) / prev_complete * 100) if prev_complete else None
        else:
            monthly_growth = None
    else:
        monthly_growth = None

    # Cancellation rate
    cancelled = orders_df[orders_df["order_status_clean"] == "Canceled"].shape[0]
    cancellation_rate = cancelled / total_orders * 100 if total_orders else 0

    # Average delivery time
    delivered = orders_df[orders_df["order_delivered_customer_date"].notna()]
    avg_delivery_days = delivered["delivery_days"].mean() if len(delivered) else 0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": int(total_orders),
        "unique_customers": int(unique_customers),
        "repeat_customers": int(repeat_customers),
        "aov": round(aov, 2),
        "clv": round(clv, 2),
        "repeat_purchase_rate": round(repeat_purchase_rate * 100, 2),
        "monthly_growth_pct": round(monthly_growth, 2) if monthly_growth is not None else None,
        "cancellation_rate": round(cancellation_rate, 2),
        "avg_delivery_days": round(avg_delivery_days, 1),
    }


# ---------------------------------------------------------------------------
# Purchase Funnel
# ---------------------------------------------------------------------------

def compute_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """Build purchase funnel: Orders -> Paid -> Delivered -> Reviewed.
    Only counts reviews on delivered orders to keep the funnel logically consistent."""
    orders_df = df.drop_duplicates(subset=["order_id"])

    total_orders = orders_df["order_id"].nunique()
    paid_orders = orders_df[orders_df["total_payment_value"].notna() & (orders_df["total_payment_value"] > 0)]["order_id"].nunique()
    delivered_orders = orders_df[orders_df["order_status_clean"] == "Delivered"]["order_id"].nunique()
    reviewed_orders = orders_df[
        (orders_df["order_status_clean"] == "Delivered") & (orders_df["review_score"].notna())
    ]["order_id"].nunique()

    funnel = pd.DataFrame({
        "stage": ["Orders", "Paid", "Delivered", "Reviewed"],
        "count": [total_orders, paid_orders, delivered_orders, reviewed_orders],
    })
    funnel["drop_off"] = funnel["count"].diff().fillna(0).abs()
    funnel["drop_off_pct"] = [0.0] + [
        round((funnel.iloc[i - 1]["count"] - funnel.iloc[i]["count"]) / funnel.iloc[i - 1]["count"] * 100, 2)
        if funnel.iloc[i - 1]["count"] > 0 else 0.0
        for i in range(1, len(funnel))
    ]
    funnel["conversion_pct"] = round(funnel["count"] / funnel.iloc[0]["count"] * 100, 2)
    return funnel


# ---------------------------------------------------------------------------
# Monthly Revenue
# ---------------------------------------------------------------------------

def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly revenue, order count, and AOV. Flags incomplete months."""
    orders_df = df.drop_duplicates(subset=["order_id"])
    monthly = (
        orders_df.groupby("order_month")
        .agg(
            revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_unique_id", "nunique"),
        )
        .reset_index()
    )
    monthly["order_month_str"] = monthly["order_month"].astype(str)
    monthly["aov"] = round(monthly["revenue"] / monthly["orders"], 2)

    # Mark incomplete months (fewer than half the median order count)
    median_orders = monthly["orders"].median()
    monthly["is_complete"] = monthly["orders"] >= (median_orders * 0.5)

    # MoM only between consecutive complete months
    monthly["revenue_mom_pct"] = np.nan
    complete = monthly[monthly["is_complete"]].index
    for i in range(1, len(complete)):
        prev_idx = complete[i - 1]
        curr_idx = complete[i]
        prev_rev = monthly.loc[prev_idx, "revenue"]
        if prev_rev > 0:
            monthly.loc[curr_idx, "revenue_mom_pct"] = round(
                (monthly.loc[curr_idx, "revenue"] - prev_rev) / prev_rev * 100, 2
            )

    return monthly


# ---------------------------------------------------------------------------
# Revenue by Category
# ---------------------------------------------------------------------------

def revenue_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue and order count by product category.
    Revenue is computed at the order-item level (each item's revenue contribution)."""
    cat = (
        df.groupby("product_category_name_english")
        .agg(
            revenue=("revenue", "sum"),
            items=("order_item_id", "count"),
            orders=("order_id", "nunique"),
            avg_price=("price", "mean"),
            unique_customers=("customer_unique_id", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    cat["revenue_share_pct"] = round(cat["revenue"] / cat["revenue"].sum() * 100, 2)
    cat["avg_price"] = round(cat["avg_price"], 2)
    return cat


# ---------------------------------------------------------------------------
# Revenue by State
# ---------------------------------------------------------------------------

def revenue_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue and customer count by customer state."""
    state = (
        df.groupby("customer_state")
        .agg(
            revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_unique_id", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    state["revenue_share_pct"] = round(state["revenue"] / state["revenue"].sum() * 100, 2)
    state["aov"] = round(state["revenue"] / state["orders"], 2)
    return state


# ---------------------------------------------------------------------------
# Top Sellers
# ---------------------------------------------------------------------------

def top_sellers(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Top N sellers by revenue."""
    sellers = (
        df.groupby("seller_id")
        .agg(
            revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
            products=("product_id", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(n)
    )
    return sellers


# ---------------------------------------------------------------------------
# Seasonal Trends
# ---------------------------------------------------------------------------

def seasonal_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly seasonal pattern across years."""
    orders_df = df.drop_duplicates(subset=["order_id"])
    orders_df = orders_df.copy()
    orders_df["month_num"] = orders_df["order_purchase_timestamp"].dt.month
    orders_df["month_name"] = orders_df["order_purchase_timestamp"].dt.strftime("%b")

    seasonal = (
        orders_df.groupby(["order_year", "month_num", "month_name"])
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
        .reset_index()
        .sort_values(["order_year", "month_num"])
    )
    return seasonal


# ---------------------------------------------------------------------------
# RFM Segmentation
# ---------------------------------------------------------------------------

def rfm_segmentation(df: pd.DataFrame) -> pd.DataFrame:
    """Compute RFM scores and segments for each customer."""
    orders_df = df.drop_duplicates(subset=["order_id"]).copy()
    reference_date = orders_df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    rfm = (
        orders_df.groupby("customer_unique_id")
        .agg(
            recency=("order_purchase_timestamp", lambda x: (reference_date - x.max()).days),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
            first_purchase=("order_purchase_timestamp", "min"),
            last_purchase=("order_purchase_timestamp", "max"),
        )
        .reset_index()
    )

    # Quintile scoring (5 = best)
    rfm["R_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

    # Segment assignment
    def segment(row):
        if row["R_score"] >= 4 and row["F_score"] >= 4 and row["M_score"] >= 4:
            return "Champions"
        elif row["R_score"] >= 3 and row["F_score"] >= 3:
            return "Loyal Customers"
        elif row["R_score"] >= 4 and row["F_score"] <= 2:
            return "New Customers"
        elif row["R_score"] >= 3 and row["F_score"] <= 2:
            return "Potential Loyalists"
        elif row["R_score"] <= 2 and row["F_score"] >= 3:
            return "At Risk"
        elif row["R_score"] <= 2 and row["F_score"] <= 2:
            return "Lost"
        else:
            return "Need Attention"

    rfm["segment"] = rfm.apply(segment, axis=1)
    rfm["tenure_days"] = (rfm["last_purchase"] - rfm["first_purchase"]).dt.days
    return rfm


def rfm_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """Aggregate RFM by segment."""
    summary = (
        rfm.groupby("segment")
        .agg(
            customers=("customer_unique_id", "count"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_revenue=("monetary", "sum"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    summary["customer_share_pct"] = round(summary["customers"] / summary["customers"].sum() * 100, 2)
    summary["revenue_share_pct"] = round(summary["total_revenue"] / summary["total_revenue"].sum() * 100, 2)
    summary["avg_recency"] = round(summary["avg_recency"], 1)
    summary["avg_frequency"] = round(summary["avg_frequency"], 2)
    summary["avg_monetary"] = round(summary["avg_monetary"], 2)
    summary["total_revenue"] = round(summary["total_revenue"], 2)
    return summary


# ---------------------------------------------------------------------------
# Cohort Analysis
# ---------------------------------------------------------------------------

def cohort_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly cohort retention matrix."""
    orders_df = df.drop_duplicates(subset=["order_id"]).copy()
    orders_df["order_month_dt"] = orders_df["order_purchase_timestamp"].dt.to_period("M")

    # First purchase month per customer
    first_purchase = (
        orders_df.groupby("customer_unique_id")["order_month_dt"]
        .min()
        .reset_index()
        .rename(columns={"order_month_dt": "cohort_month"})
    )
    orders_df = orders_df.merge(first_purchase, on="customer_unique_id", how="left")

    # Cohort period (month index from first purchase)
    orders_df["cohort_index"] = (
        orders_df["order_month_dt"].astype(int) - orders_df["cohort_month"].astype(int)
    )

    # Cohort size
    cohort_data = orders_df.groupby(["cohort_month", "cohort_index"])["customer_unique_id"].nunique().reset_index()
    cohort_data.columns = ["cohort_month", "cohort_index", "customers"]

    cohort_pivot = cohort_data.pivot(index="cohort_month", columns="cohort_index", values="customers")
    cohort_pivot = cohort_pivot.sort_index()

    cohort_sizes = cohort_pivot[0]
    retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100

    return retention_matrix


# ---------------------------------------------------------------------------
# Category Performance
# ---------------------------------------------------------------------------

def category_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Detailed category performance metrics."""
    cat = (
        df.groupby("product_category_name_english")
        .agg(
            revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
            items=("order_item_id", "count"),
            avg_price=("price", "mean"),
            avg_freight=("freight_value", "mean"),
            avg_review=("review_score", "mean"),
            unique_customers=("customer_unique_id", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    cat["revenue_share_pct"] = round(cat["revenue"] / cat["revenue"].sum() * 100, 2)
    cat["avg_price"] = round(cat["avg_price"], 2)
    cat["avg_freight"] = round(cat["avg_freight"], 2)
    cat["avg_review"] = round(cat["avg_review"], 2)
    cat["items_per_order"] = round(cat["items"] / cat["orders"], 2)
    return cat


# ---------------------------------------------------------------------------
# Pareto Analysis
# ---------------------------------------------------------------------------

def pareto_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """80/20 analysis on categories: what % of categories drive 80% of revenue."""
    cat = revenue_by_category(df)
    cat = cat.sort_values("revenue", ascending=False).reset_index(drop=True)
    cat["cumulative_revenue"] = cat["revenue"].cumsum()
    cat["cumulative_revenue_pct"] = round(cat["cumulative_revenue"] / cat["revenue"].sum() * 100, 2)
    cat["category_rank"] = range(1, len(cat) + 1)
    cat["categories_pct"] = round(cat["category_rank"] / len(cat) * 100, 2)
    return cat


# ---------------------------------------------------------------------------
# Retention Analysis
# ---------------------------------------------------------------------------

def retention_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly retention rate for repeat customers."""
    orders_df = df.drop_duplicates(subset=["order_id"]).copy()
    customer_orders = (
        orders_df.groupby("customer_unique_id")["order_purchase_timestamp"]
        .apply(list)
        .reset_index()
    )

    retention_records = []
    for _, row in customer_orders.iterrows():
        dates = sorted(row["order_purchase_timestamp"])
        if len(dates) < 2:
            continue
        first = dates[0]
        for d in dates[1:]:
            months_diff = (d.year - first.year) * 12 + (d.month - first.month)
            retention_records.append({
                "customer_unique_id": row["customer_unique_id"],
                "months_since_first": months_diff,
            })

    if not retention_records:
        return pd.DataFrame(columns=["months_since_first", "retained_customers", "retention_pct"])

    ret_df = pd.DataFrame(retention_records)
    total_with_second = ret_df["customer_unique_id"].nunique()

    retention = (
        ret_df.groupby("months_since_first")["customer_unique_id"]
        .nunique()
        .reset_index()
        .rename(columns={"customer_unique_id": "retained_customers"})
    )
    retention["retention_pct"] = round(retention["retained_customers"] / total_with_second * 100, 2)
    return retention


# ---------------------------------------------------------------------------
# Product Performance
# ---------------------------------------------------------------------------

def best_selling_products(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Top N products by total revenue."""
    prod = (
        df.groupby(["product_id", "product_category_name_english"])
        .agg(
            revenue=("revenue", "sum"),
            units_sold=("order_item_id", "count"),
            orders=("order_id", "nunique"),
            avg_price=("price", "mean"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(n)
    )
    prod["avg_price"] = round(prod["avg_price"], 2)
    return prod


def low_performing_products(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Bottom N products (by revenue) that have at least 5 orders."""
    prod = (
        df.groupby(["product_id", "product_category_name_english"])
        .agg(
            revenue=("revenue", "sum"),
            units_sold=("order_item_id", "count"),
            orders=("order_id", "nunique"),
            avg_price=("price", "mean"),
            avg_review=("review_score", "mean"),
        )
        .reset_index()
    )
    prod = prod[prod["orders"] >= 5].sort_values("revenue", ascending=True).head(n)
    prod["avg_price"] = round(prod["avg_price"], 2)
    prod["avg_review"] = round(prod["avg_review"], 2)
    return prod


# ---------------------------------------------------------------------------
# Customer Distribution
# ---------------------------------------------------------------------------

def customer_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of customers by order count."""
    orders_df = df.drop_duplicates(subset=["order_id"])
    customer_orders = orders_df.groupby("customer_unique_id")["order_id"].nunique().reset_index()
    customer_orders.columns = ["customer_unique_id", "order_count"]
    dist = customer_orders["order_count"].value_counts().reset_index()
    dist.columns = ["order_count", "num_customers"]
    dist = dist.sort_values("order_count")
    dist["cumulative_customers_pct"] = round(dist["num_customers"].cumsum() / dist["num_customers"].sum() * 100, 2)
    return dist


# ---------------------------------------------------------------------------
# Churn Risk
# ---------------------------------------------------------------------------

def churn_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Identify customers at churn risk (no purchase in last 90 days of dataset)."""
    orders_df = df.drop_duplicates(subset=["order_id"]).copy()
    reference_date = orders_df["order_purchase_timestamp"].max()

    customer_last = (
        orders_df.groupby("customer_unique_id")["order_purchase_timestamp"]
        .max()
        .reset_index()
        .rename(columns={"purchase_timestamp": "last_purchase"})
    )
    customer_last["days_since_last"] = (reference_date - customer_last["order_purchase_timestamp"]).dt.days

    def risk_level(days):
        if days <= 30:
            return "Active"
        elif days <= 90:
            return "Warm"
        elif days <= 180:
            return "Cooling"
        else:
            return "At Risk"

    customer_last["risk_level"] = customer_last["days_since_last"].apply(risk_level)

    risk_summary = (
        customer_last.groupby("risk_level")
        .agg(customers=("customer_unique_id", "count"))
        .reset_index()
        .sort_values("customers", ascending=False)
    )
    risk_summary["share_pct"] = round(risk_summary["customers"] / risk_summary["customers"].sum() * 100, 2)
    return risk_summary


# ---------------------------------------------------------------------------
# Top Customers
# ---------------------------------------------------------------------------

def top_customers(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Top N customers by total spend."""
    orders_df = df.drop_duplicates(subset=["order_id"])
    cust = (
        orders_df.groupby("customer_unique_id")
        .agg(
            total_spend=("revenue", "sum"),
            orders=("order_id", "nunique"),
            avg_order_value=("revenue", "mean"),
            first_purchase=("order_purchase_timestamp", "min"),
            last_purchase=("order_purchase_timestamp", "max"),
            city=("customer_city", "first"),
            state=("customer_state", "first"),
        )
        .reset_index()
        .sort_values("total_spend", ascending=False)
        .head(n)
    )
    cust["total_spend"] = round(cust["total_spend"], 2)
    cust["avg_order_value"] = round(cust["avg_order_value"], 2)
    return cust
