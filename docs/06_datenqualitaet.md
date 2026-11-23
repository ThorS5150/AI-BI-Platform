# 06 Data Quality

## Check rules and results (Silver)

Checked with Great Expectations 1.25.0 (ephemeral context, Spark data source), suite `silver_sales_suite`.

| Rule | GX expectation | Result |
|---|---|---|
| date is not null | expect_column_values_to_not_be_null | passed |
| dealer_id is not null | expect_column_values_to_not_be_null | passed |
| model is not null | expect_column_values_to_not_be_null | passed |
| units_sold is not null | expect_column_values_to_not_be_null | passed |
| units_sold >= 0 | expect_column_values_to_be_between (min 0) | passed |
| (date, dealer_id, model) is unique | expect_compound_columns_to_be_unique | passed |

Overall result: 6 of 6 passed.

## Additional PySpark checks (not in GX)

| Rule | Result |
|---|---|
| revenue = final_price × units_sold | 0 deviations |
| base_price − discount = final_price | 0 deviations |

GX has no suitable standard rule for calculations between columns. These checks therefore run as counts in the Silver notebook.

## Observations without error status

- 91,416 of 407,712 rows (22 %) have `units_sold = 0`. These are days without sales. They are kept and marked with `is_zero_sales`.
- `sale_id` does not exist in the dataset. The key is the combination `(date, dealer_id, model)`.
- No duplicates on the key, no negative sales values.
- Period 2025-03-31 to 2025-04-21: weekly sales fall to 840 to 1,333 units (before: 3,200 to 3,600). From 2025-04-28 they recover (3,016, then 3,600 to 3,900 in May).
- In the same period, inventory (sum of `inventory_available` per week) falls from 1,757 to about 1,110 and rises again from 2025-04-28 (1,607, then 1,827 in May).
- Finding: The sales drop fits a supply shortage rather than a drop in demand. The cause is not directly confirmed in the dataset.
- Impact: In these weeks, sales show only part of the demand (censored demand). The forecast learns these weeks as demand. See docs/10, Risks.

## Rows per layer

| Layer | Rows |
|---|---|
| Bronze | 407,712 |
| Silver | 407,712 |
| Gold (fact_sales) | 407,712 |

The suite is stored as `data/eval/silver_sales_suite.json`.

## Open
- Add checks for Gold (keys of the fact table against the dimensions)
- Detect censored demand during supply shortages and account for it in the forecast (docs/10)