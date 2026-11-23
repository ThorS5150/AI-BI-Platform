# 04 Data Source

## Origin
Self-generated dataset (generator script CarSales_Generator), synthetic. No real customer or sales data.

## File
- `demand_forecasting_quebec_daily_2020_2025.csv`, approx. 57 MB
- 407,712 rows, daily granularity, 2020-01-01 to 2025-12-31
- 50 dealers in 17 cities (Quebec), 32 models, 9 brands
- Loaded unchanged into Databricks as `platform.bronze_sales_raw`

In the project, the file is not in the repo (`data/raw/` is in `.gitignore`). The generator is in the forecasting project.

## Fields
| Field | Type | Description |
|---|---|---|
| date | date | Sales date, daily |
| year, month, week_of_year, day_of_week, is_weekend | int, string, boolean | Calendar fields |
| dealer_id | string | Dealer |
| city, region | string | Dealer location (Quebec) |
| brand, model, vehicle_category, fuel_type, transmission | string | Vehicle attributes |
| base_price, discount, final_price | int | List price, discount as amount in CAD, final price |
| promotion_type | string | Promotion type |
| inventory_available | int | Stock |
| online_leads, test_drives_booked | int | Sales activity |
| units_sold | int | Units sold (target variable for forecasting) |
| revenue | int | Revenue in CAD = final_price × units_sold |

## Key
The dataset has no `sale_id`. The unique key is the combination `(date, dealer_id, model)`. Checked: 407,712 unique keys for 407,712 rows.

## Known properties
- 91,416 rows (22 %) with `units_sold = 0`. These are days without sales, not errors.
- The dataset contains a yearly macro factor from the generator. As a result, sales fall clearly in 2025. This is caused by the synthetic data and must be mentioned when interpreting the results.