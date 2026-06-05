{{ config(materialized='table') }}

SELECT
    state,
    COUNT(*) AS vehicle_count,
    ROUND(AVG(gross_profit), 2) AS avg_gpu,
    ROUND(AVG(days_to_sale), 2) AS avg_days_to_sale,
    ROUND(AVG(reconditioning_cost), 2) AS avg_reconditioning_cost,
    ROUND(AVG(financing_attach) * 100, 2) AS finance_attach_pct,
    ROUND(AVG(warranty_attach) * 100, 2) AS warranty_attach_pct
FROM analytics.fact_lifecycle
GROUP BY state
HAVING COUNT(*) > 100
ORDER BY avg_gpu DESC
