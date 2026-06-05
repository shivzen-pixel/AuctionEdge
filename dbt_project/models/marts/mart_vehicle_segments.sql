{{ config(materialized='table') }}

SELECT
    make,
    CASE
        WHEN odometer < 30000 THEN 'Low Mileage'
        WHEN odometer < 80000 THEN 'Medium Mileage'
        ELSE 'High Mileage'
    END AS mileage_segment,

    COUNT(*) AS vehicle_count,

    ROUND(AVG(gross_profit),2) AS avg_gpu,
    ROUND(AVG(days_to_sale),2) AS avg_days_to_sale,
    ROUND(AVG(reconditioning_cost),2) AS avg_reconditioning_cost

FROM analytics.fact_lifecycle

GROUP BY
    make,
    mileage_segment

HAVING COUNT(*) > 250

ORDER BY avg_gpu DESC
