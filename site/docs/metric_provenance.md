# Website metric provenance

The website presents the existing validated historical analysis. Its deterministic [exporter](../scripts/export_data.py) reads preserved analytical tables and verifies their relationships before writing [`public/data/research.json`](../public/data/research.json). It does not rerun the preparation or analysis pipelines. The browser reads that asset and formats its values using the established definitions.

Scope is **January 2015–December 2025**, 132 consecutive months and eleven complete calendar years. The source snapshot was retrieved on **11 October 2026** and records a dataset revision date of **21 September 2026**. Later official downloads may contain a different vintage.

## Original homepage

| Website field or view | Authoritative table and column | Rule and qualification |
| --- | --- | --- |
| `kpis.plb_change_pct` | `endpoint_comparison.csv`: PLB, `change_2015_2025_pct` | `100 × (2025 annual journeys / 2015 annual journeys − 1)`; displayed −19.51%; PLB includes estimates |
| `kpis.gmb_change_pct` | Same table/column, GMB | Same endpoint rule; displayed −11.17% |
| `kpis.rmb_change_pct` | Same table/column, RMB | Same endpoint rule; displayed −58.00%; estimated |
| `kpis.rmb_recovery_2019_pct` | `recovery_2019.csv`: RMB, `recovery_pct` | `100 × 2025 RMB annual journeys / 2019 RMB annual journeys`; displayed 49.18%; estimated |
| `annual[].journeys_thousands` | `annual_ridership.csv`: `passenger_journeys_thousands`, year × GMB/RMB | Existing complete-year flow; display in millions divides by 1,000 |
| `annual[].index_2015` | The same annual journey column | `100 × annual journeys / the same mode's 2015 annual journeys`; matches the existing dashboard trend definition |
| `narrative.gmb_share_2015_pct`, `gmb_share_2025_pct` | `annual_minibus_composition.csv`: GMB, `share_of_plb_pct` in the stated year | GMB / PLB × 100; displayed 82.21% and 90.72% |
| `narrative.gmb_change_2023_2025_pct`, `rmb_change_2023_2025_pct` | `trend_segments.csv`: `2023_to_2025`, `change_pct` for each mode | Existing endpoint interval, verified against annual flows; GMB +4.00%, estimated RMB −11.90% |

The exporter cross-checks endpoint totals and recovery ratios against all five modes in the annual ridership output. The original `annual` array contains only the two minibus components, 22 observations. The fleet chapter reuses these annual flows rather than storing another passenger series.

`measurement_basis`, `includes_estimates`, `is_provisional` and `is_revised` accompany the annual observations. GMB is reported; RMB is estimated. Blank official source flags do not establish finality or remove the RMB estimation qualification.

## Chapter one: recovery

`recovery[]` copies five rows from [`recovery_2019.csv`](../../analysis/outputs/recovery_2019.csv), retaining `mode`, `recovery_pct`, `measurement_basis` and `includes_estimates`. The exporter verifies each ratio against `baseline_2019_journeys_thousands`, `journeys_2025_thousands`, the annual journey output and the endpoint comparison.

| Service | 2025 as a percentage of own 2019 annual journeys | Basis |
| --- | --- | --- |
| Green Minibuses | 91.88% | Reported |
| Red Minibuses | 49.18% | Estimated |
| Public Light Bus total | 85.03% | GMB + estimated RMB |
| MTR railway services | 101.99% | Reported; changing service coverage |
| Franchised buses | 91.63% | Reported; contemporaneous franchises |

The formula is **2025 annual journeys / the same mode's 2019 annual journeys × 100**. A value of 100% equals the benchmark; values above 100% are permitted. These are five separate ratios with their own denominators. PLB overlaps GMB and RMB and must not be added to its components. Recovery bars are not market shares.

The native mode selector highlights the selected service and exposes the corresponding value. It does not alter the benchmark or recalculate recovery. The 2019 benchmark is distinct from the 2015 trend index; the original report also documents sensitivity to a 2015–2018 mean baseline.

## Chapter two: comparison-group share and minibus composition

[`annual_market_share.csv`](../../analysis/outputs/annual_market_share.csv) supplies 44 year × component records. The four components are **GMB, RMB, MTR railway services and franchised buses**. For each year:

```text
group journeys = GMB + RMB + MTR railway services + franchised buses
component share (%) = component annual journeys / group annual journeys × 100
PLB subtotal (%) = GMB share + RMB share
```

| Static field | Source and verification |
| --- | --- |
| `market_share.annual[].share_pct` for four components | Copy `share_pct`; check `passenger_journeys_thousands` against annual journeys and `comparison_group_journeys_thousands` against the four-component sum |
| `market_share.denominators[].journeys_thousands` | Copy the common annual `comparison_group_journeys_thousands`; verify that each component has the same positive denominator |
| `market_share.annual[]` PLB rows | Derive eleven GMB + RMB share subtotals, set `is_subtotal=true`, `measurement_basis=mixed` and `includes_estimates=true`; verify against PLB annual flows / group total |
| `market_share.endpoints.plb_share_2015_pct` | Read the verified 2015 PLB subtotal; displayed 16.99% |
| `market_share.endpoints.plb_share_2025_pct` | Read the verified 2025 PLB subtotal; displayed 14.32% |
| `market_share.endpoints.plb_share_change_pp` | 2025 subtotal minus 2015 subtotal; displayed −2.67 percentage points |
| GMB composition comparison | Existing `narrative` fields from `annual_minibus_composition.csv`; denominator is PLB, not the four-mode group |

The export contains 44 component shares plus eleven explicitly marked subtotals, not 55 denominator components. Each year's four component shares sum to 100%. PLB is excluded from the component list and the plotted share series.

The all-mode line chart plots the four component shares on a 0–50% axis. **Minibus detail** plots GMB and RMB on a 0–20% axis while retaining the original four-mode denominator and percentages. It does not renormalize the two minibus shares to 100%. The year selector and table expose the group total and PLB subtotal separately.

Annual shares divide annual flows; they are not an average of monthly share percentages. Every denominator contains estimated RMB journeys, including when its numerator is reported. This comparison group does not describe all Hong Kong public transport. Internal GMB/PLB composition has a different denominator and cannot show individual passenger switching.

### Transport boundaries

MTR railway services combine **MTR Lines, Airport Express and Light Rail**. MTR Lines include cross-boundary services. Hong Kong Tramways and MTR buses are excluded. Network/service coverage changed, so the comparison follows the published series rather than a constant railway network.

Each contemporaneous franchised-bus component is counted once. Through June 2023, monthly Table 2.1 includes Citybus franchises 1 and 2 plus NWFB. From July 2023, Citybus franchise 3 replaces franchise 1 and NWFB, while franchise 2 continues. KMB, LWB and NLB remain included. Table 2.1S combines the Citybus franchises before its daily operator records are reconciled. Residents' services and MTR buses are outside the franchised-bus comparator. Preparation validates the 1 July 2023 merger boundary without adding old and new franchise totals together.

## Chapter three: licensed stock, journeys and the vehicle-day proxy

[`annual_fleet.csv`](../../analysis/outputs/annual_fleet.csv) supplies 22 annual GMB/RMB records. The exporter checks them against all 264 reported observations in [`monthly_minibus_fleet.csv`](../../data/processed/monthly_minibus_fleet.csv).

| Static field | Source column or formula | Meaning |
| --- | --- | --- |
| `fleet.annual[].december_licensed_vehicles` | `december_licensed_vehicles`, checked against that year's December monthly record | Reported administrative stock in vehicles |
| `fleet.annual[].licensed_vehicle_days_proxy` | `licensed_vehicle_days_proxy`, checked against `Σ(month-end licensed_vehicles × calendar days in month)` | Calendar-day-weighted licensed stock proxy, not an observed daily operating fleet |
| `fleet.annual[].journeys_per_licensed_vehicle_day_proxy` | `average_daily_journeys_per_licensed_vehicle` | Existing annual proxy: `annual_passenger_journeys_thousands × 1,000 / licensed_vehicle_days_proxy` |
| `fleet.annual[].index_stock_2015` | `100 × December stock / own December 2015 stock` | Relative change in the stated stock snapshot |
| `fleet.annual[].index_proxy_2015` | `100 × annual proxy / own 2015 annual proxy` | Relative change in the existing vehicle-day indicator |
| Annual journey comparison | Reuse `annual[].index_2015` and `journeys_thousands` | Complete-year flow, independent of the choice of stock snapshot |
| `fleet.endpoints[].stock_change_pct` | `100 × (December 2025 stock / December 2015 stock − 1)` | Same endpoint calculation used by dashboard fleet comparisons |
| `fleet.endpoints[].proxy_change_pct` | `100 × (2025 annual proxy / 2015 annual proxy − 1)` | Same endpoint rule used by dashboard `fleet_endpoints` |

| Service | December 2015 vehicles | December 2025 vehicles | December stock change | Annual proxy change, 2015–2025 |
| --- | --- | --- | --- | --- |
| Green Minibuses | 3,203 | 3,360 | +4.90% | −16.00% |
| Red Minibuses | 1,141 | 693 | −39.26% | −30.77% |

The exporter also checks annual calendar days, arithmetic mean month-end stock, day-weighted mean stock and the annual journey numerator. Leap days are included. It does not use December stock in place of the annual vehicle-day denominator or average twelve monthly journey/vehicle ratios into the annual proxy.

The **Stock & journeys** view indexes two different measures to their own 2015 values: December licensed stock and full-year journeys. A shared index axis compares relative movement without mixing their original units. The **Vehicle-day proxy** view indexes the existing annual proxy to its own 2015 value. Tooltips, year values and the table preserve the original units and denominator.

Both GMB and RMB stock records are **reported**. RMB's passenger input and resulting proxy are **estimated**; `stock_measurement_basis` and `proxy_measurement_basis` retain that distinction. Licensed stock is not daily deployment. The indicator does not measure occupancy, utilization or operational productivity. RMB estimation already uses fleet information, so passenger/fleet associations are partly mechanical. Comparable RMB mileage is unavailable and is not inferred.

## Methodology, reconciliation and revisions

The website's six expandable explanations condense the existing methods and link to the full documentation. Its validation account describes complete/unique month-mode keys, units, estimation metadata, the GMB + RMB = PLB identity, four-component shares summing to 100%, calendar-adjusted daily/monthly reconciliation and agreement between separate SQL and Pandas calculations.

The monthly snapshot remains internally consistent. Six selected comparisons with older provisional annual minibus references fall outside the documented rounding tolerance. Publication updates are the best-supported explanation; specific reasons remain unresolved. The site retains the current vintage rather than changing observations to match an older publication. Reconciliation establishes internal consistency rather than independently auditing passenger-count accuracy. Cross-vintage sensitivity is not an uncertainty interval for RMB estimates.

The full report also examines calendar-day-adjusted profiles. Their limited years and residual within-year trends require additional interpretation, so those details remain in the linked report rather than another chapter chart.

## Input hashes and compact static layer

`provenance.input_sha256` records these 17 files:

| Input | Role |
| --- | --- |
| `analysis/outputs/annual_ridership.csv` | Complete-year journey flows and estimate/status labels |
| `analysis/outputs/endpoint_comparison.csv` | Original endpoint findings and recovery cross-checks |
| `analysis/outputs/recovery_2019.csv` | Five recovery comparisons |
| `analysis/outputs/annual_minibus_composition.csv` | Minibus composition and GMB endpoint shares |
| `analysis/outputs/trend_segments.csv` | Recent endpoint interval and narrative values |
| `analysis/outputs/analysis_summary.json` | Successful analysis status and fixed research scope |
| `config/sources.json` | Publisher, source snapshot and revision metadata |
| `src/hk_minibus/dashboard/metrics.py` | Existing display/index/endpoint definitions |
| `docs/analysis_methodology.md` | Analytical rules and interpretation |
| `reports/eda_findings.md` | Authoritative research narrative |
| `analysis/outputs/annual_market_share.csv` | Four-component annual shares |
| `analysis/outputs/annual_fleet.csv` | Annual stock summaries and existing proxy |
| `data/processed/monthly_minibus_fleet.csv` | Reported stock and calendar-weighting reconciliation |
| `docs/data_dictionary.md` | Prepared field, unit and mode definitions |
| `docs/data_sources.md` | Verified official source inventory |
| `reports/reference_discrepancies.md` | Annual reference and revision investigation |
| `src/hk_minibus/dashboard/charts.py` | Existing chart measurement and interpretation conventions |

The shipped JSON retains the original annual/KPI interface and adds recovery, comparison-group and fleet records. The full five-mode annual journey table and 264 monthly fleet records are used during export validation; they are not duplicated as full arrays in the website asset. Original analytical files are read without modification.

To verify the exact bundled asset, from the repository root:

```powershell
python site/scripts/export_data.py --check
python site/tests/export_data_test.py
```

All exported numerical values retain full precision. Rounding occurs only for presentation. Final frontend, exporter, analytical and browser checks are recorded in [validation.md](validation.md).
