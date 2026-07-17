-- =============================================================================
-- Executive Revenue KPIs
-- =============================================================================
SELECT
    COUNT(DISTINCT o.order_id)                           AS total_orders,
    COUNT(DISTINCT o.customer_id)                        AS total_customers,
    ROUND(SUM(p.payment_value), 2)                       AS total_revenue,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT c.customer_unique_id), 2) AS customer_lifetime_value,
    ROUND(
        SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) * 100.0
        / COUNT(DISTINCT o.order_id), 2
    )                                                    AS cancellation_rate_pct,
    ROUND(AVG(
        EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) / 86400.0
    ), 1)                                                AS avg_delivery_days
FROM olist_orders o
JOIN olist_customers c       ON o.customer_id = c.customer_id
LEFT JOIN olist_order_payments p ON o.order_id = p.order_id
WHERE o.order_status != 'canceled';


-- =============================================================================
-- Monthly Revenue Trend
-- =============================================================================
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp)::DATE AS month,
    COUNT(DISTINCT o.order_id)                            AS orders,
    COUNT(DISTINCT o.customer_id)                         AS customers,
    ROUND(SUM(p.payment_value), 2)                        AS revenue,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS aov,
    ROUND(
        (SUM(p.payment_value) - LAG(SUM(p.payment_value))
            OVER (ORDER BY DATE_TRUNC('month', o.order_purchase_timestamp)))
        / NULLIF(LAG(SUM(p.payment_value))
            OVER (ORDER BY DATE_TRUNC('month', o.order_purchase_timestamp)), 0) * 100
    , 2)                                                 AS revenue_mom_pct
FROM olist_orders o
JOIN olist_order_payments p ON o.order_id = p.order_id
WHERE o.order_status != 'canceled'
GROUP BY 1
ORDER BY 1;


-- =============================================================================
-- Purchase Funnel
-- =============================================================================
SELECT
    'Orders'   AS stage, COUNT(DISTINCT order_id) AS count FROM olist_orders
UNION ALL
SELECT
    'Paid'     AS stage, COUNT(DISTINCT order_id) AS count
    FROM olist_order_payments WHERE payment_value > 0
UNION ALL
SELECT
    'Delivered' AS stage, COUNT(DISTINCT order_id) AS count
    FROM olist_orders WHERE order_status = 'delivered'
UNION ALL
SELECT
    'Reviewed'  AS stage, COUNT(DISTINCT order_id) AS count
    FROM olist_order_reviews WHERE review_score IS NOT NULL
ORDER BY count DESC;


-- =============================================================================
-- Repeat Purchase Analysis
-- =============================================================================
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(p.payment_value)       AS total_spend
    FROM olist_orders o
    JOIN olist_customers c       ON o.customer_id = c.customer_id
    JOIN olist_order_payments p  ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
)
SELECT
    CASE WHEN order_count = 1 THEN 'One-time' ELSE 'Repeat' END AS customer_type,
    COUNT(*)                                                      AS customers,
    ROUND(AVG(total_spend), 2)                                    AS avg_spend,
    ROUND(SUM(total_spend), 2)                                    AS total_revenue,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)           AS share_pct
FROM customer_orders
GROUP BY 1;


-- =============================================================================
-- RFM Segmentation
-- =============================================================================
WITH rfm AS (
    SELECT
        c.customer_unique_id,
        EXTRACT(DAY FROM MAX(o.order_purchase_timestamp) - MIN(o.order_purchase_timestamp)) AS recency_days,
        COUNT(DISTINCT o.order_id)  AS frequency,
        SUM(p.payment_value)        AS monetary
    FROM olist_orders o
    JOIN olist_customers c       ON o.customer_id = c.customer_id
    JOIN olist_order_payments p  ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
),
scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)      AS m_score
    FROM rfm
)
SELECT
    *,
    r_score + f_score + m_score AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3                   THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2                   THEN 'New Customers'
        WHEN r_score <= 2 AND f_score >= 3                   THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2                   THEN 'Lost'
        ELSE 'Need Attention'
    END AS segment
FROM scored
ORDER BY rfm_total DESC;


-- =============================================================================
-- Top Customers by Revenue
-- =============================================================================
SELECT
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    COUNT(DISTINCT o.order_id)                   AS orders,
    ROUND(SUM(p.payment_value), 2)               AS total_spend,
    ROUND(AVG(p.payment_value), 2)               AS avg_order_value,
    MIN(o.order_purchase_timestamp)::DATE        AS first_purchase,
    MAX(o.order_purchase_timestamp)::DATE        AS last_purchase
FROM olist_orders o
JOIN olist_customers c       ON o.customer_id = c.customer_id
JOIN olist_order_payments p  ON o.order_id = p.order_id
GROUP BY c.customer_unique_id, c.customer_city, c.customer_state
ORDER BY total_spend DESC
LIMIT 20;


-- =============================================================================
-- Category Performance
-- =============================================================================
SELECT
    pr.product_category_name   AS category,
    COUNT(DISTINCT o.order_id)  AS orders,
    COUNT(oi.order_id)          AS items_sold,
    ROUND(SUM(p.payment_value), 2) AS revenue,
    ROUND(AVG(oi.price), 2)     AS avg_item_price,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(
        SUM(p.payment_value) * 100.0 / SUM(SUM(p.payment_value)) OVER (), 2
    ) AS revenue_share_pct
FROM olist_order_items oi
JOIN olist_orders o           ON oi.order_id = o.order_id
JOIN olist_products pr        ON oi.product_id = pr.product_id
JOIN olist_order_payments p   ON o.order_id = p.order_id
LEFT JOIN olist_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status != 'canceled'
GROUP BY pr.product_category_name
ORDER BY revenue DESC;


-- =============================================================================
-- Cohort Retention (PostgreSQL / BigQuery style)
-- =============================================================================
WITH first_purchase AS (
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', MIN(o.order_purchase_timestamp))::DATE AS cohort_month
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
),
customer_cohort AS (
    SELECT
        fp.customer_unique_id,
        fp.cohort_month,
        DATE_TRUNC('month', o.order_purchase_timestamp)::DATE AS order_month,
        EXTRACT(MONTH FROM AGE(o.order_purchase_timestamp, fp.cohort_month))::INT AS month_index
    FROM first_purchase fp
    JOIN olist_orders o
        ON o.customer_id IN (
            SELECT customer_id FROM olist_customers
            WHERE customer_unique_id = fp.customer_unique_id
        )
)
SELECT
    cc.cohort_month,
    cs.cohort_size,
    cc.month_index,
    COUNT(DISTINCT cc.customer_unique_id) AS active_customers,
    ROUND(COUNT(DISTINCT cc.customer_unique_id) * 100.0 / cs.cohort_size, 2) AS retention_pct
FROM customer_cohort cc
JOIN cohort_size cs ON cc.cohort_month = cs.cohort_month
GROUP BY cc.cohort_month, cs.cohort_size, cc.month_index
ORDER BY cc.cohort_month, cc.month_index;


-- =============================================================================
-- Average Order Value by State
-- =============================================================================
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id)                              AS orders,
    COUNT(DISTINCT c.customer_unique_id)                    AS customers,
    ROUND(SUM(p.payment_value), 2)                          AS revenue,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS aov,
    ROUND(
        SUM(p.payment_value) * 100.0 / SUM(SUM(p.payment_value)) OVER (), 2
    )                                                       AS revenue_share_pct
FROM olist_orders o
JOIN olist_customers c       ON o.customer_id = c.customer_id
JOIN olist_order_payments p  ON o.order_id = p.order_id
WHERE o.order_status != 'canceled'
GROUP BY c.customer_state
ORDER BY revenue DESC;


-- =============================================================================
-- Customer Lifetime Value Distribution
-- =============================================================================
WITH customer_clv AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id)  AS orders,
        SUM(p.payment_value)        AS clv,
        MIN(o.order_purchase_timestamp)::DATE AS first_purchase,
        MAX(o.order_purchase_timestamp)::DATE AS last_purchase
    FROM olist_orders o
    JOIN olist_customers c       ON o.customer_id = c.customer_id
    JOIN olist_order_payments p  ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
)
SELECT
    CASE
        WHEN clv < 50    THEN 'Under $50'
        WHEN clv < 100   THEN '$50 - $100'
        WHEN clv < 250   THEN '$100 - $250'
        WHEN clv < 500   THEN '$250 - $500'
        ELSE '$500+'
    END AS clv_tier,
    COUNT(*)              AS customers,
    ROUND(AVG(orders), 2) AS avg_orders,
    ROUND(AVG(clv), 2)    AS avg_clv,
    ROUND(SUM(clv), 2)    AS total_revenue,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM customer_clv
GROUP BY 1
ORDER BY MIN(clv);
