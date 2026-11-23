# 10 Forecast Concept

Status: 2026-11-20. Notebooks 01 to 04 done. Notebook 05 (batch scoring) pending.

## Goal
Forecast weekly units sold per dealer and vehicle model for the next 12 weeks. The forecast is stored in a Gold table. The agent's `forecast_tool` reads that table with SQL. The model does not run live.

## Scope
- Target: `units_sold` per dealer-model series and week.
- Series: 186 dealer-model combinations. The assortment is fixed over time: the number of active combinations is 186 in every year from 2020 to 2025.
- History: 2020 to 2025, 313 weeks per series, complete (no gaps inside the active span).
- Aggregates per model and per dealer are sums of these series, so they stay consistent with the base forecast.
- Out of scope for now: price forecasting, real-time scoring.

## Data
Source: `workspace.default.gold_fact_sales`, joined to `gold_dim_date`.

Weekly table `gold_weekly_sales`:
- dealer_key, model_key, week_start (Monday), units_sold, revenue, avg_discount_per_unit, inventory_available (weekly average)

Aggregation rules:
- Weeks start on Monday, taken from `dim_date`.
- Ratios are computed from sums, as in docs/07.
- Weeks outside a series' active span are not filled. No zero weeks are inserted there. Checked: no gaps inside any span.
- Partial weeks are excluded: the week starting 2019-12-30 (only 2020 days, Jan 1 to 5) and the week starting 2025-12-29 (only Dec 29 to 31). Usable range: week_start 2020-01-06 to 2025-12-22.
- Checked on 2026-11-19: 186 series, 58,404 rows, units in weekly table equal units in fact table (996,844).

## Series structure
Checked on the Gold data (2026-11-19):
- Dealer-model-weeks with rows: 58,404. This equals 186 series x about 313 weeks.
- Gaps inside active spans: 0.
- Average active combinations per year: 186 in every year, 2020 to 2025.

Consequences:
- Every series has a full history. A global LightGBM model across the 186 series is feasible.
- The 186 combinations are the dealer's assortment. A combination that is not in the data is not offered, not zero demand.
- The feature "weeks since series start" is not needed in this version, because all series start in 2020.

## Validation
Temporal split only. Random splits leak future information into training.
- Training: 2020-01 to 2024-12
- Validation for the number of boosting rounds: 2024 (early stopping). The test year is not used for tuning.
- Test: 2025-01 to 2025-12. The first test week is 2025-01-06 (Monday). The week starting 2024-12-30 belongs to 2024.

The test year contains the macro-driven decline described in docs/04. It is a hard test. A model that only fits past seasonality will fail here.

Observed yearly level (units per active combination per month): 2020 51, 2021 96, 2022 61, 2023 73, 2024 96, 2025 70. The test year follows a peak year, so the model has to predict a drop.

Two evaluation horizons, both reported:
- **One-step-ahead:** Each week of 2025 is predicted from the actual weeks before it. Used to compare models fairly.
- **12-week rolling origin:** Origins every 4 weeks in 2025. From each origin, the next 12 weeks are predicted without new actuals. This is the production case.

Metrics, computed per series and then aggregated:
- WAPE = sum(|actual - forecast|) / sum(actual). Primary metric.
- MAE, for reference.
- Reported at three levels: dealer-model, model, dealer.

## Models
1. **Baseline:** 8-week moving average of units_sold per series. Every model must beat it.
2. **LightGBM:** one global model across all 186 series, objective Poisson (units are counts; predictions are expected values, not whole units). One model serves both horizons: each training row is an origin plus a horizon h from 1 to 12. Features:
   - lags: 1 to 8 weeks (lag_1 is the origin week), and 52 weeks (`lag52_target`, the same week last year)
   - rolling mean over 4 and 8 weeks, calculated from past weeks only (`roll4`, `roll8`)
   - horizon `h`
   - calendar: week of year, month, quarter
   - holidays: Quebec public holidays per week, using the `holidays` package with province "QC" (verified: `holidays` 0.109 in Databricks)
   - dealer attributes from `gold_dim_dealer` and `gold_dim_location`: city, region
   - model attributes from `gold_dim_model`: brand, vehicle_category, fuel_type, transmission
   - Parameters: learning_rate 0.05, num_leaves 63, min_data_in_leaf 200, feature_fraction 0.9, bagging_fraction 0.8, seed 42. Best iteration: 191.
3. **N-BEATS:** comparison model only, not production (decided 2026-11-19). Not evaluated yet.

No feature may use values from the week it predicts or later.

## Tracking and registry
- MLflow experiment `/Users/<user>/ai-bi-forecast` (Databricks requires an absolute workspace path).
- Run `lgbm_poisson_v1`: parameters, WAPE at all three levels for both horizons, baseline WAPE for comparison.
- Registered model `workspace.platform.demand_forecast_lgbm` (Unity Catalog needs a three-part name; schema `platform` is the project schema).
- Alias `champion` points to the version in use.
- The model is logged without an explicit signature and without `input_example`. The input example check failed on the categorical columns. Predictions through the alias match the local model exactly (max. deviation 0.0). This is recorded as a known limit (see Risks).

## Batch scoring
- Forecast horizon: 12 weeks from the last available week.
- Output table `gold_forecast_weekly`: dealer_key, model_key, week_start, forecast_units (double, expected value), forecast_units_rounded (integer, rounded to whole units), model_version, run_id, created_at.
- Dashboards and agent answers show `forecast_units_rounded`. Totals and error metrics use `forecast_units`, because rounding each row separately biases sums, especially for low-volume combinations.
- The table is rewritten on each run. A history of forecasts is not kept in this version.

## Notebooks
1. `01_weekly_sales`: build `gold_weekly_sales`, check the number of series (186) and the week index. Done.
2. `02_baseline`: moving-average baseline, WAPE on the test year at all three levels. Done.
3. `03_train_lgbm`: features, training, MLflow logging. Done. Panel: 666,252 rows.
4. `04_evaluate`: compare models per level, register the champion if it beats the baseline. Done. Criteria met, model registered, alias `champion` set and verified.
5. `05_batch_score`: write `gold_forecast_weekly`. Pending.

## Acceptance criteria
- LightGBM WAPE on the 2025 test set is lower than the baseline WAPE, at the model level and at the dealer-model level.
- Results are reported as they are. If LightGBM does not beat the baseline, the document says so, and the baseline stays as the forecast.

Result: met at both horizons and all three levels (see below).

## Baseline results (02_baseline, 2026-11-19)
8-week moving average, test year 2025.

| Horizon | Dealer-model WAPE | Model WAPE | Dealer WAPE |
|---|---|---|---|
| One-step-ahead | 0.3235 | 0.2622 | 0.2708 |
| 12-week rolling origin | 0.3412 | 0.2873 | 0.2935 |

## LightGBM results (03_train_lgbm, 2026-11-20)
Test year 2025, same origins as the baseline.

| Horizon | Level | Baseline WAPE | LightGBM WAPE | Difference |
|---|---|---|---|---|
| One-step-ahead | Dealer-model | 0.3235 | 0.2772 | −0.046 |
| One-step-ahead | Model | 0.2622 | 0.1932 | −0.069 |
| One-step-ahead | Dealer | 0.2708 | 0.2045 | −0.066 |
| 12-week rolling origin | Dealer-model | 0.3412 | 0.3214 | −0.020 |
| 12-week rolling origin | Model | 0.2873 | 0.2450 | −0.042 |
| 12-week rolling origin | Dealer | 0.2935 | 0.2546 | −0.039 |

The gain is smaller at 12 weeks, especially at dealer-model level. Accuracy falls with the horizon for both models.

## Resolved checks
- **Listing check (2026-11-19):** The number of active dealer-model combinations is 186 in every year. The 2025 decline is therefore not a listing effect. Units per active combination fell by about 27 % from 2024 to 2025 (96 to 70 per month). The decline is a demand effect.
- **Forecast level:** Dealer-model series (186) as the base. Model and dealer totals are sums of these series.
- **Holidays package (2026-11-19):** `holidays` 0.109 is installed in Databricks. Restart the Python session after installing (`dbutils.library.restartPython()`).
- **Week index (2026-11-20):** The test start 2025-01-01 is not a Monday. The first test week is found with `searchsorted`, which gives 2025-01-06.
- **Model registry (2026-11-20):** Registered as `workspace.platform.demand_forecast_lgbm`. Alias `champion` loads and predicts identically to the training model.

## Open decisions
- **Baseline strength:** The 8-week moving average is weak for a seasonal series. A seasonal naive baseline (lag 52) would show how much of the gain comes from seasonality. Not decided yet.
- **Input signature:** Add a signature and an input example, with categorical columns handled explicitly, before using the registry for serving. Not decided yet.

## Risks
- The 2025 decline is caused by a macro factor that is not in the data. The model will not predict it. This is a limit, not a bug.
- 22 % of the daily rows have zero sales (docs/06). At weekly level this is smaller, but low-volume combinations may still show many low weeks.
- One test year and one training run. Results may change with another test year or another seed.
- Yearly levels vary strongly (2020: 51, 2021: 96). A model trained on 2020 to 2024 may learn these swings as seasonality and not as trend.
- The registered model has no signature. The alias works, but the input check of MLflow reports a warning for categorical columns.