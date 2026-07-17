"""
Analytics Notebook - Standalone analysis and chart generation.
Run cells individually or use `jupyter notebook notebooks/analytics.ipynb`.
This script generates all charts as static PNGs in reports/ and screenshots/.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from src.data_loader import build_analytical_dataset
from src.analytics import *

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "screenshots"
REPORTS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (14, 7),
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.3,
})
sns.set_style("whitegrid")
sns.set_palette("Blues_d")


def run_all():
    print("Loading dataset...")
    df = build_analytical_dataset()

    print("Computing analytics...")
    kpis = compute_executive_kpis(df)
    funnel = compute_funnel(df)
    monthly = monthly_revenue(df)
    cat_rev = revenue_by_category(df)
    state_rev = revenue_by_state(df)
    rfm_df = rfm_segmentation(df)
    rfm_sum = rfm_summary(rfm_df)
    pareto = pareto_analysis(df)
    retention = retention_analysis(df)
    seasonal = seasonal_trends(df)

    # ---- KPI Summary ----
    print("\n=== Executive KPIs ===")
    for k, v in kpis.items():
        print(f"  {k}: {v}")

    # ---- Funnel ----
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(funnel["stage"], funnel["count"], color=sns.color_palette("Blues_d", len(funnel)))
    for bar, count, pct in zip(bars, funnel["count"], funnel["conversion_pct"]):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                f"{count:,} ({pct}%)", va="center", fontsize=11)
    ax.set_xlabel("Orders")
    ax.set_title("Purchase Funnel")
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "funnel.png")
    plt.close()

    # ---- Monthly Revenue ----
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.bar(monthly["order_month_str"], monthly["revenue"], color="#1A73E8", alpha=0.7, label="Revenue")
    ax1.set_ylabel("Revenue ($)", color="#1A73E8")
    ax1.set_xlabel("Month")
    ax2 = ax1.twinx()
    ax2.plot(monthly["order_month_str"], monthly["aov"], color="#EA4335", linewidth=2, marker="o", label="AOV")
    ax2.set_ylabel("AOV ($)", color="#EA4335")
    ax1.set_title("Monthly Revenue & Average Order Value")
    ax1.tick_params(axis="x", rotation=45)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "monthly_revenue.png")
    plt.close()

    # ---- Revenue by Category ----
    fig, ax = plt.subplots(figsize=(12, 8))
    top_cats = cat_rev.head(15)
    ax.barh(top_cats["product_category_name_english"], top_cats["revenue"], color="#34A853")
    ax.set_xlabel("Revenue ($)")
    ax.set_title("Top 15 Categories by Revenue")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "revenue_by_category.png")
    plt.close()

    # ---- RFM Segments ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    sns.barplot(data=rfm_sum, x="segment", y="customers", ax=axes[0], palette="Set2")
    axes[0].set_title("Customers by RFM Segment")
    axes[0].tick_params(axis="x", rotation=30)
    axes[1].pie(rfm_sum["total_revenue"], labels=rfm_sum["segment"], autopct="%1.1f%%",
                colors=sns.color_palette("Set2", len(rfm_sum)))
    axes[1].set_title("Revenue Share by Segment")
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "rfm_segments.png")
    plt.close()

    # ---- Pareto ----
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(pareto["categories_pct"], pareto["revenue"], color="#1A73E8", alpha=0.6, width=2)
    ax1.set_xlabel("% of Categories")
    ax1.set_ylabel("Revenue ($)", color="#1A73E8")
    ax2 = ax1.twinx()
    ax2.plot(pareto["categories_pct"], pareto["cumulative_revenue_pct"], color="#EA4335", linewidth=2, linestyle="--")
    ax2.axhline(y=80, color="#FBBC04", linestyle=":", linewidth=1.5, label="80%")
    ax2.set_ylabel("Cumulative %", color="#EA4335")
    ax2.legend()
    ax1.set_title("Pareto (80/20) Analysis")
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "pareto.png")
    plt.close()

    # ---- Retention Curve ----
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(retention["months_since_first"], retention["retention_pct"], marker="o",
            color="#1A73E8", linewidth=2)
    ax.fill_between(retention["months_since_first"], retention["retention_pct"], alpha=0.1, color="#1A73E8")
    ax.set_xlabel("Months Since First Purchase")
    ax.set_ylabel("Retention %")
    ax.set_title("Customer Retention Curve")
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "retention_curve.png")
    plt.close()

    # ---- Seasonal ----
    fig, ax = plt.subplots(figsize=(12, 6))
    for year, group in seasonal.groupby("order_year"):
        ax.plot(group["month_name"], group["revenue"], marker="o", linewidth=2, label=str(year))
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue ($)")
    ax.set_title("Seasonal Revenue by Year")
    ax.legend(title="Year")
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "seasonal.png")
    plt.close()

    # ---- Revenue by State ----
    fig, ax = plt.subplots(figsize=(12, 7))
    top_states = state_rev.head(20)
    ax.bar(top_states["customer_state"], top_states["revenue"], color="#1A73E8")
    ax.set_xlabel("State")
    ax.set_ylabel("Revenue ($)")
    ax.set_title("Revenue by Customer State")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "revenue_by_state.png")
    plt.close()

    # ---- Cohort Heatmap ----
    cohort = cohort_analysis(df)
    fig, ax = plt.subplots(figsize=(14, max(8, len(cohort) * 0.4)))
    sns.heatmap(cohort.iloc[:, :12], annot=True, fmt=".1f", cmap="Blues",
                linewidths=0.5, ax=ax, cbar_kws={"label": "Retention %"})
    ax.set_title("Monthly Cohort Retention Matrix")
    ax.set_xlabel("Months Since First Purchase")
    ax.set_ylabel("Cohort Month")
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "cohort_heatmap.png")
    plt.close()

    # Export KPIs to CSV
    pd.DataFrame([kpis]).to_csv(REPORTS_DIR / "executive_kpis.csv", index=False)
    funnel.to_csv(REPORTS_DIR / "funnel.csv", index=False)
    monthly.to_csv(REPORTS_DIR / "monthly_revenue.csv", index=False)
    cat_rev.to_csv(REPORTS_DIR / "revenue_by_category.csv", index=False)
    state_rev.to_csv(REPORTS_DIR / "revenue_by_state.csv", index=False)
    rfm_sum.to_csv(REPORTS_DIR / "rfm_summary.csv", index=False)
    pareto.to_csv(REPORTS_DIR / "pareto_analysis.csv", index=False)
    retention.to_csv(REPORTS_DIR / "retention_curve.csv", index=False)
    seasonal.to_csv(REPORTS_DIR / "seasonal_trends.csv", index=False)

    print(f"\nAll charts saved to {SCREENSHOTS_DIR}/")
    print(f"All reports saved to {REPORTS_DIR}/")
    print("Done!")


if __name__ == "__main__":
    run_all()
