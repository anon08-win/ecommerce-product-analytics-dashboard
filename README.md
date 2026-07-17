# E-Commerce Product Analytics Dashboard

> Production-quality analytics project demonstrating product thinking, SQL, Python analytics, dashboarding, and business recommendations for the **Olist Brazilian E-Commerce Dataset**.

## Business Problem

Olist is a Brazilian e-commerce marketplace connecting sellers to customers across multiple states. The business needs visibility into:

- **Revenue performance** and growth trends across regions and categories
- **Customer behavior** including retention, churn, and lifetime value
- **Product performance** to identify winners and underperformers
- **Funnel optimization** to reduce drop-offs between order and delivery
- **Seasonal patterns** to inform inventory and marketing planning

This dashboard provides a single source of truth for product, growth, and business analysts to make data-driven decisions.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                           │
│  Olist Kaggle Dataset (8 CSVs)                         │
│  orders | customers | items | products | sellers |     │
│  payments | reviews | geolocation                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 PROCESSING LAYER                        │
│  src/data_loader.py                                    │
│  - Auto-download + join all tables                     │
│  - Feature engineering (delivery time, RFM, cohorts)   │
│  - Clean analytical dataset at order-item level         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 ANALYTICS LAYER                         │
│  src/analytics.py                                      │
│  - Executive KPIs                                      │
│  - Purchase Funnel                                     │
│  - RFM Segmentation                                    │
│  - Cohort Analysis                                     │
│  - Revenue / Category / State Analytics                │
│  - Pareto (80/20) Analysis                             │
│  - Retention & Churn Risk                              │
│                                                         │
│  sql/analytics_queries.sql                             │
│  - Interview-quality SQL for all metrics               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               INSIGHTS LAYER                            │
│  src/insights.py                                       │
│  - Consulting-style data-driven recommendations        │
│  - Category-specific, actionable insights              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               PRESENTATION LAYER                        │
│  dashboard/app.py (Plotly Dash)                        │
│  - 6-tab professional dashboard                        │
│  - Executive Summary | Product | Customer |            │
│    Revenue | Cohort Analysis | Business Insights       │
│                                                         │
│  notebooks/analytics.py (Matplotlib/Seaborn)           │
│  - Static charts for reports                           │
└─────────────────────────────────────────────────────────┘
```

## Dataset

**Olist Brazilian E-Commerce Dataset** (Kaggle) — 100k+ orders from 2016-2018.

| Table | Records | Description |
|-------|---------|-------------|
| orders | 99,441 | Order metadata (status, timestamps) |
| customers | 99,441 | Customer location data |
| order_items | 112,650 | Item-level order details |
| products | 32,951 | Product categories and attributes |
| sellers | 3,095 | Seller information |
| payments | 103,886 | Payment type, value, installments |
| reviews | 99,224 | Review scores and comments |
| geolocation | 1,000,163 | Zip code coordinates |

## Key KPIs

| Metric | Value |
|--------|-------|
| Total Revenue | Computed from data |
| Total Orders | Computed from data |
| Unique Customers | Computed from data |
| Repeat Customers | Computed from data |
| Average Order Value (AOV) | Revenue / Orders |
| Customer Lifetime Value (CLV) | Revenue / Customers |
| Repeat Purchase Rate | Repeat / Total Customers |
| Monthly Growth (MoM) | Month-over-month % |
| Cancellation Rate | Canceled / Total Orders |
| Average Delivery Time | Days from purchase to delivery |

> All metrics are computed from the actual dataset — no fabricated numbers.

## Dashboard Pages

### 1. Executive Summary
- 8 KPI cards (Revenue, Orders, Customers, AOV, CLV, Repeat Rate, Growth, Cancellation)
- Monthly revenue trend with orders overlay
- Purchase funnel visualization
- Top states and categories by revenue

### 2. Product Analytics
- Category revenue treemap
- Pareto (80/20) analysis
- Best & low performing product tables
- Seasonal revenue trends by year

### 3. Customer Analytics
- RFM segment distribution (bar + pie)
- Customer churn risk analysis
- Order distribution per customer
- Detailed RFM segment table

### 4. Revenue Analytics
- Monthly revenue & AOV trend
- Revenue by state (choropleth + bar)
- Top sellers by revenue
- MoM growth chart

### 5. Cohort Analysis
- Full retention heatmap
- Retention curves by cohort
- Month 1/3/6 retention trends

### 6. Business Insights
- 10 consulting-style insights with recommendations
- Data-driven, category-specific, actionable

## Repository Structure

```
ECommerce-Product-Analytics/
├── data/                          # Auto-downloaded CSV datasets
├── sql/
│   └── analytics_queries.sql      # Interview-quality SQL queries
├── notebooks/
│   └── analytics.py               # Static chart generation
├── dashboard/
│   ├── __init__.py
│   └── app.py                     # Plotly Dash dashboard (6 tabs)
├── reports/                       # Exported CSV analytics
├── screenshots/                   # Dashboard screenshots
├── src/
│   ├── __init__.py
│   ├── data_loader.py             # Data ingestion + joins
│   ├── analytics.py               # All analytics functions
│   └── insights.py                # Business insight generator
├── main.py                        # Entry point
├── requirements.txt
└── README.md
```

## Setup & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch Dashboard

```bash
python main.py
# Dashboard runs at http://localhost:8050
```

### 3. Export Analytics Only (No Dashboard)

```bash
python main.py --export
# CSVs exported to reports/
```

### 4. Generate Static Charts

```bash
python notebooks/analytics.py
# PNGs saved to screenshots/
```

### 5. Run on Custom Port

```bash
python main.py --port 3000
```

## SQL Queries

The `sql/analytics_queries.sql` file contains 9 interview-quality queries:

1. **Executive Revenue KPIs** — Aggregated metrics across all orders
2. **Monthly Revenue Trend** — MoM revenue with growth rate
3. **Purchase Funnel** — Orders → Paid → Delivered → Reviewed
4. **Repeat Purchase Analysis** — One-time vs repeat customer split
5. **RFM Segmentation** — NTILE-based scoring with segment labels
6. **Top Customers** — Top 20 by total spend
7. **Category Performance** — Revenue, AOV, reviews per category
8. **Cohort Retention** — Monthly cohort retention percentages
9. **CLV Distribution** — Customer lifetime value tier breakdown

## Tech Stack

- **Python 3.14+**
- **Pandas** — Data manipulation
- **NumPy** — Numerical operations
- **Plotly** — Interactive visualizations
- **Dash** — Dashboard framework
- **Dash Bootstrap Components** — Layout and styling
- **Matplotlib / Seaborn** — Static charts
- **SQL** — Analytical queries

## Key Insights

All insights are generated from the actual dataset. The dashboard automatically computes:

- Highest revenue category and its contribution
- Biggest funnel drop-off stage with loss quantification
- Best performing RFM customer segment
- At-risk customer count and revenue exposure
- Geographic revenue concentration
- Cancellation rate assessment
- Delivery performance benchmark
- Repeat purchase rate and growth opportunity
- Pareto distribution of category revenue
- Seasonal peak month identification

## Resume Bullet Points

- Built end-to-end analytics pipeline processing 100K+ e-commerce orders across 8 joined tables
- Designed 6-tab interactive dashboard with Plotly Dash serving executive KPIs, RFM segmentation, cohort analysis, and revenue analytics
- Wrote 9 interview-quality SQL queries covering funnel analysis, cohort retention, CLV distribution, and RFM scoring
- Automated consulting-style business insight generation grounded in actual data metrics
- Reduced data preparation time by building modular Python pipeline with auto-download, feature engineering, and analytical dataset construction

<img width="2878" height="1432" alt="image" src="https://github.com/user-attachments/assets/ca94b25f-9ff7-4175-a995-adb36e0fd347" />
<img width="2854" height="886" alt="image" src="https://github.com/user-attachments/assets/0515f712-0468-4c93-b8f8-fe9c6a9e4f5d" />
<img width="2048" height="931" alt="image" src="https://github.com/user-attachments/assets/d24815bd-ae3d-411d-aa17-e62cda5d80e4" />
<img width="2047" height="889" alt="image" src="https://github.com/user-attachments/assets/d3281261-2e62-4381-a92b-89969fbbeed3" />
<img width="2048" height="969" alt="image" src="https://github.com/user-attachments/assets/463c460e-2cba-4018-9b2e-0565530490e6" />
<img width="2048" height="660" alt="image" src="https://github.com/user-attachments/assets/d0efef6c-6e15-43d3-bc85-80135e7f2f61" />
<img width="2048" height="728" alt="image" src="https://github.com/user-attachments/assets/1d3cf3ff-e093-480f-8865-3b4b44da0faa" />
<img width="2048" height="950" alt="image" src="https://github.com/user-attachments/assets/864f8e6f-8d69-48b8-ba72-35e4918f93ff" />
