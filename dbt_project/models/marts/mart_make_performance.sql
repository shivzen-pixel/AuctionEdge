{{ config(materialized='table') }}

SELECT
    make,
    COUNT(*) AS vehicle_count,
    ROUND(AVG(gross_profit), 2) AS avg_gpu,
    ROUND(AVG(days_to_sale), 2) AS avg_days_to_sale,
    ROUND(AVG(reconditioning_cost), 2) AS avg_reconditioning_cost
FROM analytics.fact_lifecycle
WHERE make IS NOT NULL
GROUP BY make
HAVING COUNT(*) > 500
ORDER BY avg_gpu DESC
