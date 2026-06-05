{{ config(materialized='table') }}

SELECT
    make,

    CASE
        WHEN odometer < 30000 THEN 'Low Mileage'
        WHEN odometer < 80000 THEN 'Medium Mileage'
        ELSE 'High Mileage'
    END AS mileage_segment,

    CASE
        WHEN condition >= 40 THEN 'Excellent'
        WHEN condition >= 25 THEN 'Good'
        ELSE 'Fair'
    END AS condition_segment,

    COUNT(*) AS vehicle_count,

    ROUND(AVG(sellingprice), 2) AS avg_purchase_price,

    ROUND(AVG(gross_profit), 2) AS avg_gpu,

    ROUND(AVG(days_to_sale), 2) AS avg_days_to_sale,

    ROUND(
        AVG(gross_profit) / NULLIF(AVG(sellingprice), 0) * 100,
        2
    ) AS gpu_margin_pct,

    ROUND(AVG(reconditioning_cost), 2) AS avg_reconditioning_cost

FROM analytics.fact_lifecycle

WHERE make IS NOT NULL
GROUP BY
    make,
    mileage_segment,
    condition_segment

HAVING COUNT(*) >= 250

ORDER BY
    avg_gpu DESC
