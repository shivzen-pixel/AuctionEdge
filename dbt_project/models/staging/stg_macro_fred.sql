{{ config(materialized='view') }}

SELECT
    CAST(date AS DATE) AS date,
    series_id,
    series_name,
    CAST(value AS DOUBLE) AS value
FROM {{ source('raw', 'raw_macro_fred') }}
