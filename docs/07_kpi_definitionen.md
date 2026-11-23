# 07 KPI Definitions

Status: 2026-11-19. This catalog is the only set of KPIs the agent's `kpi_tool` may use. Free-form SQL goes through `sql_tool` (read-only).

Source: `gold_fact_sales`, joined to `gold_dim_date`, `gold_dim_dealer`, `gold_dim_location` and `gold_dim_model` where needed. Column names as in docs/05.

| KPI | Definition | Columns | Unit | Owner |
|---|---|---|---|---|
| Revenue | SUM(revenue) | revenue | CAD | Project author |
| Units sold | SUM(units_sold) | units_sold | units | Project author |
| Average revenue per unit | Revenue / Units sold | revenue, units_sold | CAD per unit | Project author |
| Revenue, prior year | Revenue of the year before the selected year | revenue, dim_date.year | CAD | Project author |
| Revenue growth YoY | Revenue (selected year) / Revenue (prior year) - 1 | revenue, dim_date.year | % | Project author |
| Average discount per unit | SUM(discount × units_sold) / SUM(units_sold) | discount, units_sold | CAD per unit | Project author |
| Lead-to-test-drive rate | SUM(test_drives_booked) / SUM(online_leads) | online_leads, test_drives_booked | % | Project author |
| Days of inventory | Average inventory_available / average units sold per day | inventory_available, units_sold, dim_date | days | Project author |
| Share of zero-sales rows | Rows with units_sold = 0 / all rows | units_sold | % | Project author |

## Rules
- Ratios are computed from sums, never as the average of row-level ratios.
- Date filters use `dim_date`. Years are calendar years.
- Division by zero returns NULL, not 0.
- The `kpi_tool` accepts only these KPIs and the dimensions and date filters they support.

## Units of the base columns
- `discount` is an amount in CAD per unit. The weighted average above therefore uses `discount × units_sold`.
- `revenue` is defined as `final_price × units_sold`.

## Checks
Run on the Silver rows (407,712):
- Revenue check `revenue == final_price × units_sold`: 0 failures.
- Price check `final_price == base_price - discount`: 0 failures.

## Change log
- 2026-11-19: Catalog defined (9 KPIs). Column names corrected: the earlier draft used `revenue_cad`, `units` and `fact_sales`, which do not exist in the Gold layer.
- 2026-11-19: `discount` confirmed as CAD amount per unit. Discount KPI changed to a unit-weighted average.
- 2026-11-19: Revenue and price checks run on all 407,712 Silver rows, 0 failures each.