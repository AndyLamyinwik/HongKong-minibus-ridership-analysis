# Data Preparation and Validation Methodology

## Scope and source preservation

The preparation workflow reads the Transport Department snapshot preserved during Phase 1 and selects **January 2015–December 2025**, a fixed window of 132 consecutive reference months. Table 2.1 provides monthly passenger journeys; Table 2.1S provides average daily passenger journeys; Table 2.2 supplies minibus operating statistics. The revision-date CSV and data specification PDF provide source metadata and definitions. Source URLs, attribution, reuse terms, discovery findings, and exact retrieval instructions remain in [data_sources.md](data_sources.md).

The original five files under `data/raw/` are never edited or resaved. `config/sources.json` fixes their filenames, formats, expected byte sizes, SHA-256 hashes, retrieval date (`2026-10-11`), and revision date (`2026-09-21`). Hash and revision verification precede transformation. A changed or missing source cannot silently become a new study snapshot. The generated inspection file describes the entire preserved statistical source files, including observations outside the study window; analytical outputs include only the target window.

## Loading and type rules

CSV fields are initially read as text so that blank dimensions, official indicators, and numeric representations are preserved. Leading/trailing whitespace is stripped for parsing; the byte-preserved raw file remains the exact source record. Exact header order and source key uniqueness are checked. Duplicate source keys cause a failure and are never silently dropped. The source date is six-digit `YYYYMM`; it must parse to a valid calendar month. Output `month` uses ISO `YYYY-MM-01`, with the first day serving as a month identifier rather than a daily observation. The revision date is separate from the reference month and retrieval date.

Required passenger values convert to finite, nonnegative numeric values without changing their published scale. Monthly `PAX` remains thousands of journeys; daily `AVG_DAILY_PAX` remains thousands of journeys per day. Licensed fleet and passenger capacity must be positive whole numbers for the selected GMB/RMB records and are stored as integers. Available PLB mileage remains thousands of vehicle-kilometres. Source numeric text after whitespace normalization is retained in SQLite source records or the fleet table, allowing every transformed value to be inspected against its source representation.

Passenger components are summed with Python `Decimal` using their retained source numeric text, then stored as floating-point values in Pandas and SQLite `REAL` fields. No rounding is applied to the analytical values. Source text preserves the published representation, while reconciliation tolerances account for floating-point storage.

Blank, `N.A.`, and `-` tokens are interpreted in context; none becomes zero. Required measurements cannot be missing or nonnumeric. A malformed or unsupported token causes an understandable validation failure. Empty franchise, railway, and bus-subtype dimensions indicate that those dimensions do not apply; they remain empty strings so source composite keys are explicit. Official indicators are kept separately from values. No interpolation, extrapolation, forward filling, averaging across gaps, or insertion of analytical observations is performed.

## Series definitions and aggregation

| Output code | Table 2.1 selection and derivation | Passenger measurement basis |
| --- | --- | --- |
| `GMB` | `MODE=PLB`, `TTD_PTO_CODE=GMB`; one row per month | `reported` |
| `RMB` | `MODE=PLB`, `TTD_PTO_CODE=RMB`; one row per month | `estimated` |
| `PLB` | Same-month GMB + RMB, only when both required components are valid | `mixed` |
| `MTR` | Sum `MTRC` with `RAIL_LINE=Local`, `Airport`, and `LRT` exactly once | `reported` |
| `FRANCHISED_BUS` | Sum all contemporaneous `MODE=Fran_Bus` components: KMB, applicable CTB franchises, NWFB when present, LWB, and NLB | `reported` |

MTR `Local` includes cross-boundary services under TD's MTR Lines definition. Hong Kong Tramways and MTR buses are outside the MTR railway comparator. Residents' bus services are outside franchised buses. PLB is a derived total whose components remain available; any later comparison-group denominator must use PLB, MTR, and franchised buses without also adding GMB or RMB.

Table 2.1 franchised bus records include six components per month through June 2023 and five from July 2023. CTB franchise `1` and NWFB end after June; CTB franchise `3` begins in July; CTB franchise `2` continues. These boundaries are explicitly validated against the 1 July 2023 franchise merger rather than inferred from row counts. Table 2.1S already combines CTB franchises, with five operator records before the merger and four afterwards. Monthly-to-daily source checks therefore sum the monthly CTB franchises before matching the combined daily CTB observation. No franchise total is added again to its components.

The same five analytical series are prepared separately from Table 2.1S. Their values remain daily averages, rather than being multiplied by calendar days and inserted into the monthly table. Passenger measurement-basis labels propagate to the daily layer, including RMB's estimation qualification. `is_derived` and `component_count` identify aggregates; lineage tables record the exact source rows used for every monthly and daily observation.

## Estimates, flags, and missing fleet mileage

RMB patronage is estimated even when its official indicator is empty. TD's method uses surveys, licensed vehicle counts, and other parameters rather than regular operator returns. RMB passenger rows therefore carry `measurement_basis=estimated` and `includes_estimates=1`; PLB carries `mixed` and `1`. GMB, MTR, and franchised buses carry `reported` and `0`. Here, “reported” describes publication provenance, not an independent audit or a census of unique travellers. No uncertainty intervals are fabricated.

The official `#` and `*` indicators mean provisional and revised respectively. Distinct nonblank indicators from contributing rows are sorted and joined with `|`; aggregate provisional/revised flags indicate whether any component carries the corresponding symbol. An empty indicator does not prove accuracy or rule out future revisions. Source staging keeps each component's indicator, including its empty string.

The fleet output selects only Table 2.2 GMB/RMB rows. Their licensed vehicles and passenger places are reported administrative month-end stocks, including RMB fleet observations; the RMB passenger estimate label does not turn its licensed fleet into an estimate. GMB operating kilometres are retained where published. RMB operating kilometres and all minibus cross-harbour kilometres are structurally blank in this snapshot and remain null. CSV null mileage is an empty field; SQLite stores SQL `NULL`. No comparable GMB/RMB mileage-based measure is created. Licensed vehicles are not observed daily deployment, and passenger capacity is not passenger journeys.

## Quality gates and reconciliation

Automated checks cover source hashes and schemas, source dates and composite keys, required numeric values, valid indicators, exactly 132 continuous months, the required five passenger codes, unique month/mode keys, units, negative/nonfinite values, estimate propagation, fleet completeness, component counts, source reconciliation, historical bus boundaries, and SQLite integrity and foreign keys. Required failed checks block publication of validated datasets. Software tests exercise both correct fixtures and deliberately invalid input; synthetic fixtures are confined to tests.

Monthly passenger aggregates are checked against their exact source components, and fleet values against the selected original records. Daily reconciliation checks monthly totals against the corresponding published daily value multiplied by the actual number of days in that month, including leap years. The preserved Table 2.1S daily values carry enough decimal precision for a strict arithmetic tolerance of **`1e-7` thousand journeys** (0.0001 journey), below Table 2.1's finest published quantum of one journey. This tolerance absorbs floating-point representation error without accepting discrepancies as large as a published monthly rounding unit. It is an arithmetic consistency check: the daily series is derived from related reported totals, so agreement does not independently corroborate measurement accuracy.

Operator/component checks reconcile 1,290 compatible monthly/daily keys after combining CTB franchises. A separate aggregate check reconciles the five analytical series for all 132 months. Nine selected 2024/2025 annual minibus totals from the already verified annual/December reference publications are transcribed in `config/reference_values.csv` and used only as validation comparisons. Their integer-thousand presentation allows **0.5 thousand journeys** of rounding difference. Larger differences receive a warning with source vintage and status information; current CSV observations are never modified to match an older publication. Annual sums calculated for these checks are validation diagnostics, not additional annual analytical datasets or interpreted research findings. These selected references do not constitute a full annual-publication audit of every year and mode.

SQLite constraints enforce analytical month/mode primary keys, component uniqueness, foreign keys, permitted units, valid measurement labels, and nonnegative numeric values. Database loading occurs in a transaction, and the file is inspected before the validated outputs are published. The SQL views expose consistently defined inputs, lineage, fleet context, and reconciliation fields for later analysis; they calculate no growth, shares, recovery, or fleet-normalized research results.

## Outputs and reproducibility

The output contracts are 660 monthly passenger observations, 660 separate average daily observations, and 264 GMB/RMB fleet observations, each spanning `2015-01-01` to `2025-12-01`. The database also preserves 1,422 selected monthly source components, 1,290 daily source components, source-file metadata, transport definitions, and lineage. See [data_dictionary.md](data_dictionary.md) for fields and SQL views, and [validation_report.md](validation_report.md) for the actual run results.

Run `python scripts/prepare_data.py` and then `python -m pytest -q` from the repository root after installing the pinned dependencies as described in the [README](../README.md). The pipeline writes machine-readable `validation_summary.json`, `source_inspection.json`, and the readable validation report. A failed attempt returns a nonzero exit code and records diagnostics; previously validated datasets can remain available, so the current report must be checked before use. The pipeline reproduces the preserved source snapshot locally. A future official download is a different snapshot unless its hashes and revision metadata match.
