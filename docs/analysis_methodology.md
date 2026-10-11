# Phase 3 Analytical Methodology and Output Dictionary

## Inputs, scope and preservation

The analysis reads the validated Phase 2 CSVs and opens `data/processed/transport.sqlite` with SQLite's read-only mode and `PRAGMA query_only`. It does not rebuild the preparation layer. Scope is January 2015–December 2025: 132 months, five passenger series and two minibus fleet series. Source vintage, units, estimation qualifications and row-level provenance are defined in the [prepared data dictionary](data_dictionary.md) and [source inventory](data_sources.md).

Before analysis, the runner verifies official raw-file hashes, the successful Phase 2 validation status, CSV/database equality, complete month/mode keys, numeric validity, units and estimation labels. It confirms that SQLite validation metadata equals the Phase 2 JSON. Hashes of every preserved raw and processed file, including the database, and the two source configuration files are recorded before execution and checked again before analytical outputs are replaced.

The [annual reference investigation](../reports/reference_discrepancies.md) examines all six exceptions using official notes and publication values. Updates to older provisional figures are the best-supported interpretation; specific revision reasons remain unresolved. The current, internally consistent monthly snapshot is retained. Annual endpoint sensitivity changes neither the direction of the main decade results nor the GMB/RMB recovery ranking. Cross-vintage differences are not uncertainty estimates for RMB measurement.

## Calculation rules

| Measure | Definition | Interpretation |
| --- | --- | --- |
| Annual journeys | Sum all twelve monthly journey totals, in thousands | A flow; monthly daily averages and fleet stocks are not summed into it |
| Absolute change | Current journeys − baseline journeys | Thousands of journeys, retaining the sign |
| Year-over-year change | 100 × (current / previous − 1) | Annual complete years or the same calendar month one year earlier; first in-window year has no growth benchmark |
| Endpoint change | 100 × (2025 / 2015 − 1) | A decade comparison, not an annualized growth rate |
| Recovery index | 100 × annual journeys / that mode's 2019 annual journeys | 100 means equal journey volume; values above 100 are permitted |
| Alternative recovery | 100 × 2025 annual journeys / mean annual journeys in 2015–2018 | Sensitivity to the choice of historical benchmark; no claim that either baseline is undisturbed |
| Period mean annual journeys | Period journey sum / number of complete years | Comparable scale for five-year and three-year groups |
| Period daily rate | Period journey sum / actual number of calendar days | Day-weighted rate in thousands; leap days included |
| Comparison-group share | 100 × component journeys / (GMB + RMB + MTR + franchised bus journeys) | Four nonoverlapping components; PLB share is GMB share + RMB share |
| Annual share | Ratio of annual totals | Not an unweighted mean of monthly percentages |
| Minibus composition | 100 × GMB or RMB journeys / PLB journeys | Shares within minibus patronage, not licensed fleet composition |
| Change contribution | Component absolute change / PLB absolute change × 100 | Signed decomposition; can exceed 100 or be negative when changes offset; not a market share |
| Monthly fleet-normalized indicator | Daily journeys in thousands × 1,000 / month-end licensed vehicles | Individual journeys per licensed vehicle per day, using administrative stock |
| Annual fleet-normalized indicator | Annual journeys in thousands × 1,000 / Σ(month-end vehicles × month days) | Licensed vehicle-days proxy; month-end stocks stand in for their month's stock |

Units remain explicit in field names. Displayed million-journey values divide thousand-journey values by 1,000. Percentages and percentage-point differences are distinguished. Undefined ratios remain missing. Values are not rounded in analytical CSVs; reports and figures round only their display.

The comparison group is a defined subset of Hong Kong transport, not the entire public transport market. Prepared MTR and bus aggregates appear once; their raw operator components are not added again. MTR includes cross-boundary services under the MTR Lines definition, and preparation explicitly handles the July 2023 Citybus/NWFB merger. RMB remains estimated, PLB includes estimated RMB, and every comparison-group denominator contains estimated journeys even where a numerator is reported. Blank status flags do not imply measurement certainty.

## Periods, troughs and calendar profiles

The pre-pandemic period is 2015–2019, disruption is 2020–2022, and post-pandemic is 2023–2025. These are descriptive groupings, not causal treatment assignments. `trend_segments` also uses explicit endpoint intervals: 2015→2019, 2019→2022, 2022→2025, 2023→2025 and 2015→2025; annual increase/decrease counts refer only to transitions within each stated interval.

The runner identifies the lowest published monthly total and lowest average daily rate separately for each mode over the entire window. Those minima can occur in different months because month length differs. Same-calendar-month daily comparisons against 2019 are available in the monthly and minima outputs. If two months have an equal minimum, the first chronological observation is reported; this is a deterministic convention rather than a unique-minimum assertion.

The `seasonality` table stores, for every period/mode/calendar month:

- The arithmetic mean monthly total and mean average daily rate across the available years.
- A mean normalized daily index: each monthly daily rate / its year's annual journeys-per-calendar-day × 100, then average the corresponding calendar month equally across years.
- Population standard deviation (`ddof=0`) of those daily rates and coefficient of variation (`100 × SD / mean`). These summarize the observed years and do not estimate sampling error.

Daily rates remove month-length differences. Within-year normalization reduces between-year level differences but does not detrend each year. Ongoing recovery/decline, movable calendar effects, service changes and sharp demand interruptions can influence these profiles. Each calendar month has five pre-period observations and three in each subsequent period. The disruption profile is particularly unsuitable as evidence of stable recurring seasonality. No statistical-significance claim, causal model or confidence interval is inferred from these descriptive profiles. RMB estimation uncertainty is not quantified by their dispersion.

## Fleet interpretation

Annual fleet outputs distinguish the arithmetic mean of twelve month-end stocks, December stock, and a day-weighted mean of month-end stocks. Vehicle stocks are never summed and called fleet size. The annual indicator's licensed vehicle-days denominator is a reproducible stock proxy; actual daily operating fleets are unavailable. It does not measure occupancy, operational productivity or vehicle utilization. RMB passenger estimation already uses fleet information, so passenger/fleet relationships are partly mechanical. Unsupported mileage is neither filled nor extrapolated.

## Outputs and traceability

All generated numerical tables are in `analysis/outputs/`. Numeric field suffixes retain their units; `measurement_basis`, `includes_estimates` and annual source flags accompany key outputs. Tables lacking repeated metadata, such as signed change decompositions and calendar profiles, retain `mode` and inherit the prepared mode definitions. The summary records source hashes, SQL hashes, scope, checks and figure-to-table provenance.

| Table | Grain / rows | Principal fields |
| --- | --- | --- |
| `monthly_ridership` | Month × five modes / 660 | Prepared journey fields; daily rates; year, period, calendar month/days; annual daily baseline; within-year index; YoY and same-month 2019 daily recovery |
| `monthly_yoy` | Month × five modes / 660 | Current/prior-year journeys, absolute and percentage change |
| `annual_ridership` | Year × five modes / 55 | Annual journeys; absolute/percentage YoY; basis, estimate and propagated provisional/revised flags |
| `monthly_market_share` | Month × four components / 528 | Mode journeys, comparison-group denominator, share percentage, numerator basis/estimate label |
| `annual_market_share` | Year × four components / 44 | Same fields calculated from annual totals |
| `minibus_composition` | Month × GMB/RMB / 264 | Component journeys, PLB journeys, share of PLB |
| `annual_minibus_composition` | Year × GMB/RMB / 22 | Annual component and PLB totals and composition |
| `annual_recovery` | Year × five modes / 55 | Annual journeys, own 2019 baseline, recovery index |
| `recovery_2019` | Five modes / 5 | 2019/2025 totals, absolute difference, recovery/change percentage, basis/estimate label |
| `endpoint_comparison` | Five modes / 5 | 2015/2019/2025 totals, decade change, both recovery benchmarks, basis/estimate label |
| `period_summary` | Period × five modes / 15 | Years/months/days, total flow, mean annual flow, weighted daily rate, basis/estimate label |
| `monthly_minima` | Mode × two measures / 10 | Metric, month, value and unit, same-month daily recovery, measurement basis |
| `seasonality` | Period × mode × calendar month / 180 | Observation count; raw/daily means; normalized index; population SD and CV |
| `seasonality_ranges` | Period × five modes / 15 | Peak/trough calendar month and index, range in index points |
| `fleet_normalized` | Month × GMB/RMB / 264 | Daily rate, licensed vehicles, journeys per licensed vehicle, passenger basis/estimate label |
| `annual_fleet` | Year × GMB/RMB / 22 | Three fleet-stock summaries; annual passenger flow/days; vehicle-days proxy; annual normalized indicator; passenger basis/estimate label |
| `trend_segments` | Explicit interval × five modes / 25 | Endpoint years/flows, absolute/percentage change, counts of annual increases/decreases/unchanged transitions |
| `minibus_change_contributions` | Explicit interval × GMB/RMB / 10 | Component/PLB absolute changes and signed contribution percentage |
| `annual_reference_comparisons` | Selected published reference / 9 | Official URL/vintage/flag, current/reference/difference, tolerance, relative difference, endpoint sensitivity in percentage points |

Six independently executed SQL results are exported under `analysis/outputs/sql/`. Query definitions and units are documented in [sql/analysis/README.md](../sql/analysis/README.md). The generated [findings report](../reports/eda_findings.md) draws all numerical claims from these tables; its renderer makes narrative calculations reviewable. Seven PNG figures are saved in `analysis/figures/` with explicit units, estimate qualifications, comparison boundaries and source notes.

## Checks and reproducibility

Pandas calculations and separate SQL queries are compared for annual totals and growth, monthly YoY, annual/monthly shares, 2019 recovery and fleet normalization. Numeric reconciliation permits at most `1e-7` thousand journeys (0.0001 journey) for flow arithmetic and `1e-9` percentage points for percentage fields. Text, metadata and missingness must agree. Other gates verify twelve months per annual total, GMB + RMB = PLB, share totals of 100%, denominator boundaries, calendar weighting, recovery baseline 100, calendar-profile grain, normalized annual baseline 100, fleet scaling, CSV round-trips, actual PNG output and unchanged inputs.

The runner builds analytical artifacts in a temporary directory and validates them before replacing prior analysis files with rollback protection. It writes `analysis_summary.json` containing passed checks and unresolved limitations. An unsuccessful run exits nonzero with a readable error. Existing Phase 2 artifacts are not replaced by this runner.

From the repository root with the verified Python 3.12 runtime, after the [specification download/checksum prerequisite](data_reuse.md#download-the-dictionary-for-full-local-reproduction):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\analyze_data.py
.\.venv\Scripts\python.exe -m pytest -q --basetemp analysis/.pytest-tmp-run -p no:cacheprovider
```

The test command uses an ignored, disposable workspace directory for fixtures and disables pytest's optional cache. This avoids the temporary-directory and cache permission errors encountered in the Windows execution environment. Pytest recreates its `--basetemp` directory; this path is reserved for software fixtures, not project datasets. The full verified run passed 84 tests, including the existing 52 preparation tests and 32 new analytical/query tests.

The Phase 2 preparation command remains available separately. Regenerating its unchanged input snapshot is unnecessary for Phase 3 execution. Dependency versions are pinned, and analytical execution requires only the preserved local inputs.
