SELECT
    CAST(year AS INTEGER) AS year,
    make,
    model,
    trim,
    body,
    transmission,
    vin,
    state,
    CAST(condition AS DOUBLE) AS condition,
    CAST(odometer AS DOUBLE) AS odometer,
    color,
    interior,
    seller,
    CAST(mmr AS DOUBLE) AS mmr,
    CAST(sellingprice AS DOUBLE) AS sellingprice,
    saledate
FROM {{ source('raw', 'raw_auction_prices') }}
WHERE vin IS NOT NULL
  AND sellingprice IS NOT NULL
