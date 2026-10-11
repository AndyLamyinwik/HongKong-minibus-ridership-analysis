# Prepared Data Dictionary

## Grain, dates, and units

All analytical tables use `month` as a **reference month**, formatted `YYYY-MM-01`. The target window is `2015-01-01`–`2025-12-01`: 132 consecutive months. A month/mode pair is unique within each measure table. Passenger journeys are published aggregate journeys, not unique people. Monthly totals, daily averages, and month-end fleet/capacity stocks remain separate tables.

| Dataset | SQL table | Target records | Key |
| --- | --- | ---: | --- |
| `monthly_passenger_journeys.csv` | `monthly_passenger_journeys` | 660 | `(month, mode)` |
| `monthly_average_daily_journeys.csv` | `monthly_average_daily_journeys` | 660 | `(month, mode)` |
| `monthly_minibus_fleet.csv` | `monthly_minibus_fleet` | 264 | `(month, mode)` |

CSV integer flags use `0`/`1`; SQLite uses constrained integers. Numeric passenger and kilometre columns are floats in the preparation layer and `REAL` in SQLite; whole-number fleet/capacity columns are integers. Source indicators and dimension fields retain empty strings. Nullable mileage is represented by an empty CSV field and SQL `NULL`; it is never interpreted as zero.

## Passenger series codes

| `mode` | Label and definition | `measurement_basis` | `includes_estimates` |
| --- | --- | --- | ---: |
| `GMB` | Green Minibus: TD's `MODE=PLB`, `TTD_PTO_CODE=GMB` | `reported` | 0 |
| `RMB` | Red Minibus: TD's `MODE=PLB`, `TTD_PTO_CODE=RMB` | `estimated` | 1 |
| `PLB` | Total Public Light Bus: same-month GMB + RMB | `mixed` | 1 |
| `MTR` | MTRC `Local` + `Airport` + `LRT`; includes cross-boundary services in MTR Lines; excludes Tramways and MTR buses | `reported` | 0 |
| `FRANCHISED_BUS` | Contemporaneous KMB, CTB franchises, NWFB, LWB, and NLB; excludes residents' services and MTR buses | `reported` | 0 |

These codes describe the prepared comparison series rather than literal values of the raw `MODE` column. The `transport_modes` dimension stores their labels, definitions, and passenger measurement qualifications. PLB overlaps with GMB and RMB; use only PLB, MTR, and franchised buses in the proposed comparison-group denominator.

## Monthly passenger and average daily tables

The two tables share all metadata fields below but have separate numeric columns and units.

| Field | Type | Definition and constraints |
| --- | --- | --- |
| `month` | Text/date identifier | First day of the reference month; target window only |
| `mode` | Text | One of the five prepared series codes |
| `passenger_journeys_thousands` | Float/REAL | **Monthly table only:** journeys during the month in thousands; required, finite, nonnegative |
| `average_daily_journeys_thousands` | Float/REAL | **Daily table only:** published monthly average daily journeys in thousands per day; required, finite, nonnegative |
| `unit` | Text | `thousand_journeys` in monthly table; `thousand_journeys_per_day` in daily table |
| `measurement_basis` | Text | `reported`, `estimated`, or `mixed` as defined above; not a claim of independently observed accuracy |
| `includes_estimates` | Integer flag | 1 for RMB and PLB passenger series; 0 for GMB, MTR, and franchised buses |
| `is_derived` | Integer flag | 1 for a prepared aggregate (PLB, MTR, franchised buses); 0 for direct GMB/RMB rows |
| `source_id` | Text | `td_table21` for monthly values; `td_table21s` for daily values; foreign key to `source_files` |
| `source_indicator` | Text | Distinct nonblank official tokens from source rows, sorted and joined with `\|`; empty if none; component originals remain in staging |
| `is_provisional` | Integer flag | 1 if any contributing source indicator contains `#`; otherwise 0 |
| `is_revised` | Integer flag | 1 if any contributing source indicator contains `*`; otherwise 0 |
| `component_count` | Integer | Number of distinct source rows contributing to the observation: GMB/RMB 1; PLB 2; MTR 3; bus count follows source grain and merger date |

Monthly bus aggregates have six source components through June 2023 and five from July 2023. Daily bus aggregates have five and four, respectively, because Table 2.1S already combines Citybus franchises. The table pair has the same analytical service boundary despite different component counts. All source target passenger indicators are blank in the preserved snapshot, while RMB still carries its estimation qualification.

## Monthly minibus fleet table

Only GMB and RMB are included. Fleet measurement basis is administrative/reporting provenance; it is distinct from passenger measurement basis.

| Field | Type | Definition and constraints |
| --- | --- | --- |
| `month` | Text/date identifier | Reference month; fleet and capacity measured at month-end |
| `mode` | Text | `GMB` or `RMB` |
| `licensed_vehicles` | Integer | TD `NO_FLEET`: licensed vehicles at month-end; required positive whole number for selected GMB/RMB records |
| `passenger_capacity` | Integer | TD `PAX_CAP`: passenger carrying places at month-end; required positive whole number for selected GMB/RMB records |
| `vehicle_km_thousands` | Nullable float/REAL | TD `KM`: monthly operated vehicle-kilometres in thousands; GMB values retained; RMB structurally null |
| `cross_harbour_vehicle_km_thousands` | Nullable float/REAL | TD `KM_CROSS_HARBOUR`: monthly cross-harbour vehicle-kilometres in thousands; structurally null for both minibus modes |
| `fleet_unit` | Text | Constant `vehicles` |
| `capacity_unit` | Text | Constant `passenger_places` |
| `km_unit` | Text | Constant `thousand_vehicle_km`, including rows with null mileage |
| `measurement_basis` | Text | Constant `reported` for licensed-fleet/capacity records, including RMB |
| `source_id` | Text | Constant `td_table22`; foreign key to `source_files` |
| `source_record_id` | Text | Stable snapshot row identifier, e.g. `td_table22:2`; unique |
| `source_row_number` | Integer | Physical CSV row number; header is row 1 and first data record row 2 |
| `source_fleet_text` | Text | Source `NO_FLEET` numeric string after leading/trailing whitespace normalization |
| `source_capacity_text` | Text | Source `PAX_CAP` numeric string after leading/trailing whitespace normalization |
| `source_km_text` | Text | Source `KM` field after whitespace normalization, including empty string for a source blank |
| `source_cross_harbour_km_text` | Text | Source `KM_CROSS_HARBOUR` field after whitespace normalization, including source blanks |
| `fleet_indicator` | Text | Original `NO_FLEET_INDI` |
| `capacity_indicator` | Text | Original `PAX_CAP_INDI` |
| `km_indicator` | Text | Original `KM_INDI` |
| `cross_harbour_km_indicator` | Text | Original `KM_CROSS_HARBOUR_INDI` |
| `is_provisional` | Integer flag | 1 if a selected fleet-row measure indicator contains `#`; otherwise 0 |
| `is_revised` | Integer flag | 1 if a selected fleet-row measure indicator contains `*`; otherwise 0 |

Licensed fleet is not daily operating fleet; capacity is not occupancy. A later journeys-per-licensed-vehicle calculation would be a descriptive proxy. Because RMB patronage estimates already use fleet counts, patronage/fleet associations cannot be treated as independent demand evidence.

## SQLite source components and lineage

`passenger_source_records` preserves the **1,422 target monthly component rows** used by the five passenger series. `daily_source_records` preserves the **1,290 target daily component rows**. They retain source granularity rather than adding overlapping analytical total records. Their analytical value columns retain the same units as the corresponding fact tables.

| Field | Tables | Definition |
| --- | --- | --- |
| `source_record_id` | Both | Primary key formed from source ID and physical CSV row number, e.g. `td_table21:2` |
| `source_id` | Both | Foreign key to the preserved file metadata |
| `source_row_number` | Both | Physical CSV row number, beginning at 2 for first data row |
| `month` | Both | ISO reference month in the target window |
| `source_mode` | Both | Original `MODE`, such as `PLB`, `Railways`, or `Fran_Bus` |
| `operator_code` | Both | Original `TTD_PTO_CODE`, including `GMB`, `RMB`, `MTRC`, `KMB`, `CTB`, `NWFB`, `LWB`, `NLB` |
| `franchise_type` | Monthly only | Original `FRANCHISE_TYPE`; CTB `1`, `2`, or `3` when applicable; empty string elsewhere |
| `rail_category` | Both | Original `RAIL_LINE`: `Local`, `Airport`, `LRT` for MTR components; empty elsewhere |
| `passenger_journeys_thousands` | Monthly only | Parsed source `PAX` in thousands per month |
| `average_daily_journeys_thousands` | Daily only | Parsed source `AVG_DAILY_PAX` in thousands per day |
| `source_numeric_text` | Both | Source numeric field string after leading/trailing whitespace normalization and before conversion |
| `source_indicator` | Both | Original `PAX_INDI` or `AVG_DAILY_PAX_INDI`, including empty string |
| `measurement_basis` | Both | `estimated` for RMB components; `reported` for other selected components |
| `includes_estimates` | Both | 1 for RMB components, otherwise 0 |

Unique source keys are `(month, source_mode, operator_code, franchise_type, rail_category)` for monthly rows and `(month, source_mode, operator_code, rail_category)` for daily rows. `(source_id, source_row_number)` is also unique in each staging table. Empty dimensions are explicit empty strings rather than SQL nulls, so the uniqueness constraints apply consistently.

`passenger_lineage` and `daily_lineage` contain `(month, mode, source_record_id)` as a composite primary key. Each row links a prepared observation to one source component. The target contracts are **1,686 passenger links** and **1,554 daily links**: GMB/RMB source rows contribute once to their own series and again to PLB. This intentional reuse is lineage, not duplicate analytical observations. Composite foreign keys ensure that a link points to the same month in its fact and component record. Fleet observations carry direct row lineage within their own table.

## Source and quality metadata

`source_files` has one record for each of the five preserved files:

| Field | Definition |
| --- | --- |
| `source_id` | Primary key: `td_table21`, `td_table21s`, `td_table22`, `td_revision`, or `td_dictionary` |
| `filename` | Unique preserved raw filename |
| `source_url` | Official resource download URL |
| `publisher` | Transport Department, HKSAR Government, via DATA.GOV.HK |
| `retrieved_on` | Snapshot retrieval date, `2026-10-11` |
| `revision_date` | Dataset's reported revision date, `2026-09-21` |
| `sha256` | Verified 64-character file SHA-256 digest |
| `size_bytes` | Verified raw file size |
| `file_format` | `CSV` or `PDF` |

`transport_modes` uses `mode` as its primary key and stores `label`, `measurement_basis`, `includes_estimates`, and `definition`. Passenger fact tables reference the qualified mode definition. Fleet tables deliberately retain their separate reported basis for RMB licensing counts.

`metadata` is a key/value table for preparation scope and run metadata. `validation_checks` uses `check_id` as its primary key and stores `status` (`pass`, `fail`, `warning`), `severity` (`error`, `warning`, `info`), a readable `message`, and structured `details_json`. The generated `validation_summary.json` records the run's checks and diagnostics outside the database, including duplicate-key checks. `source_inspection.json` records source-level schemas, coverage, input/prepared numeric types, missingness, and symbols/indicators. The readable execution results are in [validation_report.md](validation_report.md). Metadata and diagnostics are not passenger observations.

The SQLite metadata keys record `pipeline_version`, `study_start_month`, `study_end_month`, `comparison_group`, `source_manifest_sha256`, `annual_reference_config_sha256`, and `raw_reuse_terms_url`. The two configuration hashes identify the preparation input contract and the separately transcribed reference values; they are distinct from raw source-file hashes.

The validation JSON uses the following top-level fields:

| Field | Meaning |
| --- | --- |
| `pipeline_version` | Preparation package version |
| `status` | `passed`, `passed_with_warnings`, or `failed` |
| `outputs_published` | Boolean indicating whether this run published validated CSV/SQLite outputs |
| `publication_state` | `published`, `not_published`, or `rollback_incomplete`; identifies whether replacement completed and whether any previous files require recovery |
| `study_window` | Start/end reference month and expected month count |
| `check_counts` | Counts of `pass`, `warning`, and `fail` results |
| `record_counts` | Row counts for analytical, component staging, and lineage frames |
| `source_files` | Verified file provenance records matching the source metadata table |
| `source_inspection` | Source inspection content also exported separately on a successful run |
| `checks` | Ordered check objects with `check_id`, `status`, `severity`, `message`, and `details` |
| `error` | Execution diagnostic, or JSON `null` when no execution error occurred |

The independent `source_inspection.json` is keyed by source ID. For statistical CSVs it records filename/format, record count, exact columns and source key, monthly coverage, numeric-field types and unavailable/zero/negative counts, status counts, blank source dimensions, and mode/operator codes. Revision metadata and the PDF have their own format-appropriate records. A failed preparation attempt can leave the last successful inspection/analytical artifacts in place; `outputs_published` and the current report identify what the current run produced.

## SQL views

| View | Grain and purpose |
| --- | --- |
| `v_monthly_comparison_group` | Monthly PLB, MTR, and franchised bus observations with labels and definitions; exposes the intended later share denominator without calculating shares |
| `v_monthly_minibus_journeys` | Monthly GMB, RMB, and PLB observations with labels; preserves estimates and units |
| `v_monthly_minibus_fleet_context` | Month × GMB/RMB; joins monthly passenger values to fleet/capacity/mileage, retaining separate passenger/fleet basis, units, flags, and source references; no ratios calculated |
| `v_passenger_source_lineage` | One monthly analytical observation × one contributing source record; displays aggregate/component values, source dimensions, original strings/flags, and file provenance |
| `v_daily_reconciliation_inputs` | Month × five passenger series; exposes monthly and daily values with units, actual calendar days, component counts, and source flags |
| `v_monthly_passenger_wide` | One row per month; pivots five monthly values into `gmb_journeys_thousands`, `rmb_journeys_thousands`, `plb_journeys_thousands`, `mtr_journeys_thousands`, and `franchised_bus_journeys_thousands` for later queries |

The long-form fact tables remain the authoritative analytical records, including their quality metadata. The wide view is a convenience pivot, and its mode qualifications still apply. SQL definitions are in [`sql/schema.sql`](../sql/schema.sql) and [`sql/views.sql`](../sql/views.sql). All views expose preparation inputs; growth rates, market shares, recovery indices, seasonality, and interpretation belong to subsequent analysis.
