"""
E-Commerce Product Analytics Dashboard
Main entry point - run this to launch the dashboard.

Usage:
    python main.py                # Launch dashboard on port 8050
    python main.py --port 3000    # Launch on custom port
    python main.py --export       # Export analytics to CSV only (no dashboard)
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    parser = argparse.ArgumentParser(description="E-Commerce Product Analytics Dashboard")
    parser.add_argument("--port", type=int, default=8050, help="Port to run dashboard on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--export", action="store_true", help="Export analytics CSVs without launching dashboard")
    parser.add_argument("--debug", action="store_true", default=True, help="Run in debug mode")
    args = parser.parse_args()

    if args.export:
        export_analytics()
        return

    launch_dashboard(args.host, args.port, args.debug)


def export_analytics():
    """Export all analytics to CSV files in reports/."""
    from src.data_loader import build_analytical_dataset
    from src.analytics import (
        compute_executive_kpis, compute_funnel, monthly_revenue,
        revenue_by_category, revenue_by_state, top_sellers,
        rfm_segmentation, rfm_summary, category_performance,
        pareto_analysis, retention_analysis, churn_risk, top_customers,
        best_selling_products, low_performing_products, customer_distribution,
    )
    from pathlib import Path
    import pandas as pd

    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    print("Loading dataset...")
    df = build_analytical_dataset()

    print("Computing analytics...")
    exports = {
        "executive_kpis": pd.DataFrame([compute_executive_kpis(df)]),
        "funnel": compute_funnel(df),
        "monthly_revenue": monthly_revenue(df),
        "revenue_by_category": revenue_by_category(df),
        "revenue_by_state": revenue_by_state(df),
        "top_sellers": top_sellers(df),
        "rfm_summary": rfm_summary(rfm_segmentation(df)),
        "category_performance": category_performance(df),
        "pareto_analysis": pareto_analysis(df),
        "retention": retention_analysis(df),
        "customer_distribution": customer_distribution(df),
        "churn_risk": churn_risk(df),
        "top_customers": top_customers(df),
        "best_products": best_selling_products(df),
        "low_products": low_performing_products(df),
    }

    for name, data in exports.items():
        path = reports_dir / f"{name}.csv"
        data.to_csv(path, index=False)
        print(f"  Exported {name} -> {path}")

    print(f"\nAll reports exported to {reports_dir}/")


def launch_dashboard(host: str, port: int, debug: bool):
    """Launch the Dash dashboard."""
    from dashboard.app import app
    print(f"\n{'='*60}")
    print(f"  E-Commerce Product Analytics Dashboard")
    print(f"  Running at http://{host}:{port}")
    print(f"{'='*60}\n")
    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    main()
