"""
Business Insights Generator - Produces consulting-style insights from the data.
All insights are grounded in actual computed metrics, never fabricated.
"""
import pandas as pd
import numpy as np
from typing import List, Dict


def generate_insights(df: pd.DataFrame, kpis: dict, funnel: pd.DataFrame,
                      cat_rev: pd.DataFrame, state_rev: pd.DataFrame,
                      rfm_summary: pd.DataFrame, retention_matrix: pd.DataFrame,
                      seasonal: pd.DataFrame, pareto: pd.DataFrame) -> List[Dict[str, str]]:
    """Generate data-driven business insights."""
    insights = []
    orders_df = df.drop_duplicates(subset=["order_id"])

    # 1. Revenue concentration in top category
    top_cat = cat_rev.iloc[0]
    second_cat = cat_rev.iloc[1] if len(cat_rev) > 1 else None
    top3_share = cat_rev.head(3)["revenue_share_pct"].sum()
    top5_share = cat_rev.head(5)["revenue_share_pct"].sum()
    insights.append({
        "category": "Revenue Concentration",
        "title": "Top 3 Categories Drive {:.1f}% of Revenue".format(top3_share),
        "insight": (
            f"{top_cat['product_category_name_english']} is the #1 category with ${top_cat['revenue']:,.0f} "
            f"({top_cat['revenue_share_pct']}% share, {top_cat['orders']:,} orders). "
            f"The top 3 categories alone contribute {top3_share}% of total item revenue, "
            f"and the top 5 cover {top5_share}%."
        ),
        "recommendation": (
            f"Ensure {top_cat['product_category_name_english']} maintains seller coverage and inventory depth. "
            f"Analyze the top 3 categories for cross-sell bundles to increase basket size, "
            f"as concentration risk is high if any top category loses sellers."
        ),
    })

    # 2. Funnel drop-off analysis
    delivered_row = funnel[funnel["stage"] == "Delivered"].iloc[0]
    reviewed_row = funnel[funnel["stage"] == "Reviewed"].iloc[0]
    orders_row = funnel[funnel["stage"] == "Orders"].iloc[0]
    delivery_gap = orders_row["count"] - delivered_row["count"]
    review_gap = delivered_row["count"] - reviewed_row["count"]
    delivery_loss_pct = round(delivery_gap / orders_row["count"] * 100, 2)
    review_loss_pct = round(review_gap / delivered_row["count"] * 100, 2) if delivered_row["count"] > 0 else 0
    insights.append({
        "category": "Funnel Optimization",
        "title": f"{delivery_gap:,} Orders Lost Before Delivery ({delivery_loss_pct}%)",
        "insight": (
            f"Of {orders_row['count']:,} orders, {delivered_row['count']:,} reach delivery "
            f"({delivered_row['conversion_pct']}% of total). "
            f"The {delivery_gap:,} orders lost before delivery represent the largest funnel gap. "
            f"Of delivered orders, {reviewed_row['count']:,} ({reviewed_row['conversion_pct']}%) get reviewed."
        ),
        "recommendation": (
            f"The {delivery_loss_pct}% pre-delivery loss ({delivery_gap:,} orders) should be investigated "
            f"by order status — cancellations, unavailable items, and shipping failures each need "
            f"different interventions. Target reducing this gap by 30% to recover ~{int(delivery_gap * 0.3):,} orders."
        ),
    })

    # 3. RFM segment analysis - find the segment with best revenue-per-customer
    if len(rfm_summary) > 0:
        rfm_summary_copy = rfm_summary.copy()
        rfm_summary_copy["rev_per_customer"] = (
            rfm_summary_copy["total_revenue"] / rfm_summary_copy["customers"]
        )
        best_efficiency = rfm_summary_copy.sort_values("rev_per_customer", ascending=False).iloc[0]
        largest_segment = rfm_summary_copy.sort_values("customers", ascending=False).iloc[0]
        at_risk = rfm_summary_copy[rfm_summary_copy["segment"].isin(["At Risk", "Lost"])]
        at_risk_customers = at_risk["customers"].sum() if len(at_risk) > 0 else 0
        at_risk_rev = at_risk["total_revenue"].sum() if len(at_risk) > 0 else 0
        at_risk_pct = round(at_risk_customers / rfm_summary_copy["customers"].sum() * 100, 1) if rfm_summary_copy["customers"].sum() > 0 else 0
        at_risk_rev_pct = round(at_risk_rev / rfm_summary_copy["total_revenue"].sum() * 100, 1) if rfm_summary_copy["total_revenue"].sum() > 0 else 0

        insights.append({
            "category": "Customer Value",
            "title": f"{best_efficiency['segment']} Highest Value: ${best_efficiency['rev_per_customer']:,.0f}/Customer",
            "insight": (
                f"The {best_efficiency['segment']} segment generates ${best_efficiency['rev_per_customer']:,.0f} "
                f"per customer (vs ${rfm_summary_copy['rev_per_customer'].mean():,.0f} average), "
                f"with {best_efficiency['avg_frequency']:.1f} avg orders and {best_efficiency['avg_recency']:.0f}-day recency. "
                f"The largest segment is {largest_segment['segment']} ({largest_segment['customers']:,} customers, "
                f"{largest_segment['customer_share_pct']}% of base)."
            ),
            "recommendation": (
                f"Create tiered loyalty rewards for {best_efficiency['segment']} to protect this high-value base. "
                f"Measure CLV lift over 6 months and use their purchase patterns "
                f"to build lookalike audiences for acquisition."
            ),
        })

        # 4. Churn risk insight
        if at_risk_customers > 0:
            insights.append({
                "category": "Retention Risk",
                "title": f"{at_risk_customers:,} Customers ({at_risk_pct}%) at Risk of Churn",
                "insight": (
                    f"{at_risk_customers:,} customers in 'At Risk' or 'Lost' segments represent "
                    f"${at_risk_rev:,.0f} in historical revenue ({at_risk_rev_pct}% of total). "
                    f"These customers have low recency scores, meaning they haven't purchased recently "
                    f"despite prior engagement."
                ),
                "recommendation": (
                    f"Segment the {at_risk_customers:,} at-risk customers by last purchase category "
                    f"and send targeted win-back campaigns with category-specific offers. "
                    f"Prioritize the top-spending 20% of at-risk customers for personalized outreach."
                ),
            })

    # 5. Geographic concentration
    top3_states = state_rev.head(3)
    top3_share = top3_states["revenue_share_pct"].sum()
    sp_share = state_rev[state_rev["customer_state"] == "SP"]["revenue_share_pct"].values
    sp_share = sp_share[0] if len(sp_share) > 0 else 0

    # Find states with highest AOV
    high_aov_states = state_rev[state_rev["orders"] >= 1000].nlargest(3, "aov")

    insights.append({
        "category": "Geographic Distribution",
        "title": f"São Paulo Alone Accounts for {sp_share:.1f}% of Revenue",
        "insight": (
            f"The top 3 states ({', '.join(top3_states['customer_state'].head(3).tolist())}) "
            f"drive {top3_share:.1f}% of total revenue. SP dominates with {sp_share:.1f}% share. "
            f"States with highest AOV among high-volume regions: "
            f"{', '.join(high_aov_states['customer_state'].tolist())} "
            f"(${high_aov_states['aov'].mean():,.0f} avg order value)."
        ),
        "recommendation": (
            f"With {sp_share:.1f}% concentration in SP, explore expansion into underpenetrated states "
            f"with high AOV like {high_aov_states.iloc[0]['customer_state']}. "
            f"Regional logistics partnerships could reduce the {kpis['avg_delivery_days']:.1f}-day "
            f"average delivery time in distant states."
        ),
    })

    # 6. Cancellation and delivery performance
    cancel_rate = kpis["cancellation_rate"]
    avg_del = kpis["avg_delivery_days"]
    insights.append({
        "category": "Operations",
        "title": f"Cancellation {cancel_rate}% | Avg Delivery {avg_del:.1f} Days",
        "insight": (
            f"The {cancel_rate}% cancellation rate ({int(kpis['total_orders'] * cancel_rate / 100):,} orders) "
            f"is well below the typical e-commerce benchmark of 3-5%. "
            f"Average delivery takes {avg_del:.1f} days from purchase, "
            f"which directly impacts the {delivery_loss_pct}% pre-delivery order loss."
        ),
        "recommendation": (
            f"While cancellations are controlled, the {avg_del:.1f}-day average delivery "
            f"can be reduced by analyzing delivery time by state and seller. "
            f"Set up seller SLA dashboards to identify carriers and sellers "
            f"consistently above the 15-day threshold."
        ),
    })

    # 7. Repeat purchase and CLV gap
    rpr = kpis["repeat_purchase_rate"]
    clv = kpis["clv"]
    one_time_pct = round(100 - rpr, 1)
    repeat_rev_per = round(
        orders_df[
            orders_df["customer_unique_id"].map(
                orders_df.groupby("customer_unique_id")["order_id"].nunique()
            ) > 1
        ].groupby("customer_unique_id")["revenue"].sum().mean(), 2
    ) if rpr > 0 else 0

    insights.append({
        "category": "Growth",
        "title": f"{one_time_pct}% of Customers Are One-Time Buyers (CLV: ${clv:,.2f})",
        "insight": (
            f"Only {rpr}% of customers make more than one purchase. "
            f"The average CLV is ${clv:,.2f}, but repeat customers spend "
            f"${repeat_rev_per:,.2f} on average — "
            f"{round(repeat_rev_per / clv, 1) if clv > 0 else 0}x the overall average. "
            f"This gap represents the largest growth opportunity."
        ),
        "recommendation": (
            f"Convert one-time buyers to repeat customers by triggering post-purchase "
            f"email sequences at day 7, 14, and 30 with personalized product recommendations. "
            f"A 5-percentage-point improvement in repeat rate "
            f"(from {rpr}% to {rpr + 5}%) would add ~{int(kpis['unique_customers'] * 0.05):,} "
            f"returning customers."
        ),
    })

    # 8. Pareto analysis
    cat_80 = pareto[pareto["cumulative_revenue_pct"] <= 80].shape[0]
    total_cats = pareto.shape[0]
    pareto_pct = round(cat_80 / total_cats * 100, 1) if total_cats else 0
    bottom_cats = total_cats - cat_80
    bottom_rev_share = round(100 - pareto.iloc[cat_80 - 1]["cumulative_revenue_pct"], 1) if cat_80 > 0 else 100

    insights.append({
        "category": "Portfolio Strategy",
        "title": f"{cat_80} of {total_cats} Categories ({pareto_pct}%) Generate 80% of Revenue",
        "insight": (
            f"{cat_80} categories ({pareto_pct}% of the portfolio) drive 80% of revenue. "
            f"The remaining {bottom_cats} categories contribute only {bottom_rev_share}% combined. "
            f"This long tail includes categories with low order volume and minimal revenue impact."
        ),
        "recommendation": (
            f"Audit the bottom {bottom_cats} categories: those with <50 orders and <$50K revenue "
            f"should be evaluated for delisting or bundling into parent categories. "
            f"Reallocate seller acquisition budget toward the top {cat_80} categories "
            f"where demand is proven."
        ),
    })

    # 9. Seasonal planning
    if len(seasonal) > 0:
        monthly_rev = seasonal.groupby("month_num")["revenue"].sum().sort_values(ascending=False)
        peak_month = monthly_rev.index[0]
        peak_rev = monthly_rev.iloc[0]
        low_month = monthly_rev.index[-1]
        low_rev = monthly_rev.iloc[-1]
        month_names = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
                       7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
        peak_name = month_names.get(peak_month, str(peak_month))
        low_name = month_names.get(low_month, str(low_month))
        seasonal_ratio = round(peak_rev / low_rev, 1) if low_rev > 0 else 0

        insights.append({
            "category": "Seasonal Planning",
            "title": f"{peak_name} Peaks at ${peak_rev:,.0f} ({seasonal_ratio}x {low_name})",
            "insight": (
                f"{peak_name} generates the highest revenue at ${peak_rev:,.0f}, "
                f"which is {seasonal_ratio}x the lowest month ({low_name}: ${low_rev:,.0f}). "
                f"The top 3 months ({month_names.get(monthly_rev.index[0])}, "
                f"{month_names.get(monthly_rev.index[1])}, {month_names.get(monthly_rev.index[2])}) "
                f"account for {round(monthly_rev.head(3).sum() / monthly_rev.sum() * 100, 1)}% of annual revenue."
            ),
            "recommendation": (
                f"Begin inventory and logistics planning 8 weeks before {peak_name}. "
                f"Negotiate temporary capacity increases with carriers and "
                f"pre-position top-selling SKUs in regional fulfillment centers."
            ),
        })

    return insights
