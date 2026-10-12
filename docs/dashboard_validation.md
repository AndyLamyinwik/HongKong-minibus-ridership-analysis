# Phase 4 Dashboard Validation Record

Verified on **11 October 2026**. This is the completed Phase 4 execution record. The later [Phase 5A portfolio validation](portfolio_validation.md) records final packaging and layout review. Phase 5B-1 published the source repository, and Phase 6C verified the separate [GitHub Pages research website](website_deployment.md). The Streamlit dashboard remains a local presentation of the preserved historical research; its Community Cloud deployment is unverified and requires separate approval.

## Environment and complete suite

| Component | Verified version |
| --- | --- |
| Python | 3.12.14, Windows |
| Streamlit | 1.65.0 |
| Plotly | 7.1.0 |
| pandas | 3.0.1 |
| NumPy | 2.5.4 |
| pytest | 9.0.2 |

The final complete test run returned **201 passed in 84.74 seconds**, with no failures. `python -m pip check` returned **No broken requirements found**. All installed preparation, analysis, dashboard and test dependencies are pinned in `requirements.txt`.

After a final stylesheet adjustment for medium-width KPI cards, the **26 application tests passed again in 8.52 seconds**. Actual browser inspection confirmed a two-column KPI layout at the normal sidebar-open width, with all four percentage values fully visible; wide screens retain four columns and narrow screens use one. This last change affected presentation only.

| Test group | Passed | Evidence covered |
| --- | ---: | --- |
| Existing preparation, database and analytical tests | 84 | Earlier ingestion, validation, storage, analytical formulas and independent SQL agreement |
| Dashboard data contracts and display metrics | 61 | Required files, malformed/incomplete inputs, keys, units, estimates/status fields, successful analysis metadata, cross-table agreement, fixed indices, inclusive filtering and endpoint helpers |
| Plotly charts | 30 | Trace values and units, recovery above 100%, denominator preservation, no additive PLB, fleet summaries, empty/malformed inputs, no input mutation, bounded period shading, single-year shares and legend spacing |
| Streamlit AppTest | 26 | Actual entry point, all five sections, four KPIs, mode/year/frequency/measure controls, filtered chart values, empty selections, controlled unavailable-input error, single-year comparisons and working-directory independence |

The final test command used a fresh workspace fixture directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp analysis/.pytest-tmp-phase4-confirm -p no:cacheprovider --tb=short
```

The Windows sandbox blocks local socket pairs; a diagnostic traceback located an initial AppTest startup block in Python's asyncio/socket initialization, before application execution. Tests and the local server were then run with loopback permission. Disposable test directories and earlier stopped server processes were removed. This environment restriction is distinct from a dashboard application failure.

## Headline agreement with Phase 3

The dashboard reads the values from existing analytical tables. Automated checks verify their calculations and the displayed two-decimal rounding against the research report.

| Displayed finding | Verified dashboard value | Existing table |
| --- | --- | --- |
| PLB annual journey change, 2015–2025 | −19.51% | `endpoint_comparison.csv` |
| GMB annual journey change, 2015–2025 | −11.17% | `endpoint_comparison.csv` |
| Estimated RMB annual journey change, 2015–2025 | −58.00% | `endpoint_comparison.csv` |
| RMB 2025 journeys as a percentage of 2019 | 49.18% | `recovery_2019.csv` |
| GMB share of PLB journeys in 2025 | 90.72%; +8.51 pp since 2015 | `annual_minibus_composition.csv` |
| GMB/RMB change from 2023 to 2025 | +4.00% / −11.90% | `trend_segments.csv` |
| GMB/PLB/MTR/bus 2025 recovery against 2019 | 91.88% / 85.03% / 101.99% / 91.63% | `recovery_2019.csv` |
| Combined PLB comparison-group share | 16.99% in 2015 → 14.32% in 2025; −2.67 pp | `annual_market_share.csv` |
| December GMB/RMB licensed vehicles | 3,203 / 1,141 in 2015 → 3,360 / 693 in 2025 | `annual_fleet.csv` |

Research results are not embedded as constants in the application. This validation document records rounded examples of the checked snapshot. Metric definitions remain those in [the research methodology](analysis_methodology.md), with the fixed 2015 display indices documented in [the dashboard guide](dashboard.md).

## Actual browser verification

The final application was started on the local loopback interface and inspected in the Codex in-app browser. Browser checks complemented the simulated Streamlit tests:

- Navigated all five main sections and verified their titles, charts, narrative and source notes.
- Selected RMB only, changed to annual indexed trends, and moved the year range to 2023–2025; the baseline remained 2015. Cleared all selected modes and verified readable guidance.
- Switched among the recovery benchmark, 2019/2025 volume and annual recovery-path tabs. Confirmed the 100% reference and MTR's value above it.
- Switched transport shares between monthly/annual frequency and area/line presentation. Selected 2025 alone and verified a meaningful single-year share view.
- Switched fleet frequency and the licensed-stock/journey-indicator tabs, with the annual weighting definition visible.
- Opened Sources & methodology and verified official links, service definitions, formula text, estimation/revision qualifications and supporting report controls.
- Inspected wide, medium and narrow layouts. The observed narrow content viewport was **390 × 844 CSS pixels**, with document width equal to viewport width. Opening content and KPI cards reflowed vertically; the two-mode trend and five-mode recovery charts retained readable axes and separate wrapped legends. The medium-width KPI row uses two columns to prevent value truncation when the sidebar is open.

An independent visual review checked saved desktop overview, desktop trend and mobile opening captures. The main review additionally checked the final mobile chart spacing after a legend/axis overlap was corrected. Browser sizing was restored after testing. The final local preview is available at [127.0.0.1:8501](http://127.0.0.1:8501) while its local server runs.

## Preservation and remaining limits

SHA-256 checks before and after dashboard work confirmed that **all 73 protected earlier files** remained byte-for-byte unchanged: raw and prepared data, source configuration, SQL, analytical tables/figures, research reports, earlier Python modules and earlier tests. The dashboard adds presentation code and tests; README, the project plan and dependencies were updated for the completed stage. No historical datasets were regenerated or copied for presentation.

No known functional failures remain in the verified environment. Setup was exercised on Windows/Python 3.12; the documented macOS/Linux commands and other browser engines were not executed. The browser checks cover representative controls and narrow layouts, rather than an exhaustive device or screen-reader audit. The underlying analytical limits remain: estimated RMB volumes, vintage revisions, changing MTR coverage, a selected transport denominator, descriptive recovery comparisons and licensed-stock proxies.

Phase 5A completed the licensing, attribution, clean-environment, portfolio-image and repository reviews recorded in [portfolio_validation.md](portfolio_validation.md). GitHub source publication and the separate static research website release are complete. Streamlit Community Cloud deployment and hosted verification remain pending approval.
