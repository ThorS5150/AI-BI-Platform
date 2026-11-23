# 05 Data Model (Gold, Star Schema)

## Fact table
`gold_fact_sales`
- date_key, dealer_key, model_key
- units_sold, base_price, discount, final_price, revenue
- inventory_available, online_leads, test_drives_booked, promotion_type

Key: The dataset has no `sale_id`. The unique key is the combination `(date, dealer_id, model)`, checked with 407,712 unique keys for 407,712 rows.

## Dimensions
- `gold_dim_date`: date_key (yyyymmdd), date, year, month, week_of_year, day_of_week, is_weekend (2,192 rows)
- `gold_dim_dealer`: dealer_key, dealer_id, location_key (50 rows)
- `gold_dim_location`: location_key, city, region (17 cities)
- `gold_dim_model`: model_key, model, brand, vehicle_category, fuel_type, transmission (32 rows)

## Decisions
- **Geography separated:** `city` and `region` are in `dim_location`, not in `dim_dealer`. Several dealers share one city. `dim_dealer` references the location via `location_key`.
- **Product attributes in `dim_model`:** brand, vehicle_category, fuel_type and transmission depend uniquely on the model (checked: 0 models with several values). A separate `dim_brand` is not worth it for 9 brands.
- **Unique dealer location:** Each dealer has exactly one city and one region (checked: 0 cases of conflict).

## Granularity
One row per dealer, model and day.