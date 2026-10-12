# Research Plan and Milestones

## Scope and decision

Use **January 2015–December 2025** as the primary historical window. The common monthly source snapshot contains all 132 months for the requested passenger series. This supports annual comparisons, monthly recovery benchmarks, and descriptive examination of persistent changes without assembling a series from different publication vintages.

Phases 1–4, Phase 5A portfolio preparation and Phase 5B-1 GitHub publication are complete. Discovery established source availability; preparation implemented separate monthly measures, SQLite, provenance and validation; research provides reproducible descriptive calculations, independent SQL checks, seven figures and a [findings report](../reports/eda_findings.md). Interactive presentation includes the original five-section Streamlit/Plotly dashboard and the approved static research publication developed in Phases 6A–6B. Phase 6C publishes and verifies the [research website](https://andylamyinwik.github.io/HongKong-minibus-ridership-analysis/) on GitHub Pages. The [preparation report](validation_report.md), [analytical methods](analysis_methodology.md), [dashboard documentation](dashboard.md), [portfolio validation](portfolio_validation.md) and [website deployment record](website_deployment.md) document the work. Phase 5B-2 Streamlit Community Cloud deployment remains separate and requires approval.

## Research questions

| # | Question | Implemented evidence and method | Interpretation limit |
| --- | --- | --- | --- |
| 1 | How did published GMB, RMB, and total PLB passenger journeys change from 2015 to 2025, and did the direction differ between subperiods? | Monthly Table 2.1; complete-year totals, year-on-year changes, and indexed series. | Establish direction from data; RMB remains an estimate. |
| 2 | How did the GMB/RMB composition of minibus patronage change? | GMB and RMB journeys as shares of their combined total; compare annual composition and monthly persistence. | A shift in aggregate composition does not establish that individual passengers switched services. |
| 3 | How did 2020–2022 monthly demand compare with pre-pandemic patterns? | Same-calendar-month comparisons with 2019 and a 2015–2018 monthly baseline; daily rates to account for month length. | Period differences coincide with COVID-19 but do not isolate its causal effect; 2019 is not assumed to be an undisturbed year. |
| 4 | How did PLB's share of the selected transport comparison group change relative to MTR railway services and franchised buses? | Same-period Table 2.1 journeys; PLB / (PLB + MTR railway services + franchised buses), with optional separate GMB and RMB contributions. | This denominator is a selected comparison group, not all travel or the entire public transport market. |
| 5 | How far did published demand in 2023–2025 recover against explicit pre-pandemic benchmarks, and were differences persistent across modes and months? | Ratios and absolute differences against 2019 and the earlier baseline; compare equivalent months and complete years. | Recovery can exceed a benchmark; it is not assumed to mean return to the same travel behaviour. |
| 6 | Did calendar-month patterns or variability change across the three study periods? | Daily rates, profiles normalized to each year's day-weighted daily level, and within-period profile dispersion; no formal seasonal decomposition. | Normalization retains within-year trend and calendar/service effects. The disruption-period profile does not represent ordinary seasonality. |
| 7 | How did licensed GMB/RMB fleet composition and published journeys per licensed vehicle evolve together? | Month-end Table 2.2 fleet and capacity; descriptive fleet shares and a carefully labelled journeys-per-licensed-vehicle proxy. | Licensed vehicles are not deployed vehicles; the ratio is not occupancy or productivity. RMB estimates already use fleet counts, so an association is partly mechanical. |

Questions 1–6 are supported by the verified passenger datasets. Question 7 is implemented as a qualified descriptive extension using monthly GMB/RMB licensed stock; its limitations remain visible in the report and dashboard.

## Measurement and comparison rules

1. **Keep source measures separate.** Table 2.1 `PAX` is a monthly total in thousands. Table 2.1S `AVG_DAILY_PAX` is a daily average in thousands. Table 2.2 fleet/capacity is a month-end stock. Do not concatenate these into one value column without a metric and unit, or compare annual totals with daily averages.
2. **Retain measurement metadata.** Preserve original codes, source filename, retrieval date, revision date, indicator fields, and a method label identifying RMB estimates. Blanks in dimensions and blank indicators have different meanings from missing numeric measurements.
3. **Use stable aggregation boundaries.** Derive PLB as GMB + RMB. Derive MTR railway journeys as `MTRC` with `RAIL_LINE` in `Local`, `Airport`, `LRT`; report those components separately when helpful. Sum applicable `Fran_Bus` rows once, including each Citybus franchise present in that month. Do not count operator totals and components twice.
4. **Avoid publication-vintage stitching.** Use the preserved monthly snapshot for the main series. Annual HTML/PDF publications are validation references, whose older provisional values may differ legitimately. Investigate discrepancies rather than replacing a monthly value with an older annual figure.
5. **Aggregate with the calendar.** Annual passenger totals require all twelve months. Compute annual daily rates from total journeys divided by actual days in the year, or a day-weighted monthly daily average. Never sum daily averages or take an unweighted average across unequal months. Fleet annual summaries must state whether they use December stock or a monthly mean; never sum vehicle stocks over months.
6. **Treat shares consistently.** The main comparison group is PLB + MTR railway services + franchised buses. GMB and RMB are components of PLB and must not be added again to this denominator. Any wider public transport share would need a separate, documented denominator and treatment of estimated taxi figures.

Use 2015–2019, 2020–2022, and 2023–2025 as descriptive pre-pandemic, pandemic-period, and subsequent-period groupings. Retain monthly detail so these broad labels do not conceal timing. Service/network changes, cross-boundary travel, population and visitor changes, and other disruptions may be relevant contextual explanations; independently verify their dates and evidence before adding them to the narrative.

## Tools and data design

| Purpose | Tool | Output and status |
| --- | --- | --- |
| Ingestion and preparation | Python 3.12 (verified), pandas, standard library | Implemented repeatable preparation from byte-preserved raw files |
| SQL modelling and storage | SQLite through Python's `sqlite3` | Implemented schemas, constrained monthly tables, component staging, lineage, metadata, and six SQL views |
| Quality assurance | pytest and pipeline validation | Automated software tests, machine-readable diagnostics, and a preparation report |
| Exploration and statistical summaries | Python scripts and pandas | Implemented endpoint, growth, period, recovery, composition, share, calendar-profile and fleet summaries |
| Visualization | Matplotlib | Seven reproducible PNG figures with units, source notes and estimate annotations |
| Interactive presentation | Streamlit, Plotly, pandas | Five-section local dashboard, file-aware caching, display selectors and automated UI/chart checks |
| Static research publication | HTML/CSS/JavaScript, ECharts, Vite, GitHub Pages | Published editorial website with four interactive charts and expandable methodology |
| Version control and documentation | Git, Markdown, GitHub Actions | Public source repository and tested Pages deployment workflow |

The implemented analytical grain is **one month × one defined transport series × one measure**, with separate monthly passenger and average daily tables and a GMB/RMB month-end fleet table. The five passenger series are `GMB`, `RMB`, `PLB`, `MTR`, and `FRANCHISED_BUS`. Operator/franchise/rail-component records and lineage are retained in SQLite. Source metadata include filenames, URLs, retrieval and revision dates, checksums, original numeric strings, and row numbers; analytical records preserve units, measurement basis, source indicators, and estimate/status flags. See [data_dictionary.md](data_dictionary.md) for the implemented field contract.

## Milestones and acceptance criteria

| Phase | Work | Acceptance criteria |
| --- | --- | --- |
| 1 — Discovery and planning | Inspect official files; document coverage, definitions, quality, and questions; preserve raw sources. | Three foundation documents, authentic raw sources, exact download instructions, and recorded hashes. Complete. |
| 2 — Data preparation and validation | Implement local Python ingestion and SQLite staging; parse dates/codes/flags; define mode mappings; produce validated monthly measures and fleet datasets. | Complete. All 132 target months, keys, units, estimate labels, merger handling, missing-value policies, source reconciliation, and daily-rate checks are covered by automated validation. Annual publications serve as validation references. See the execution report. |
| 3 — Exploratory and statistical analysis | Answer the agreed questions; investigate reference discrepancies; assess benchmark sensitivity, monthly patterns and fleet context; create research figures and findings. | Complete. Numerical claims trace to unrounded outputs; independent SQL/Pandas calculations agree; estimates and limitations remain visible; all input bytes are preserved. |
| 4 — Visualization and presentation | Present the contrasting GMB/RMB trajectories through interactive trends, recovery, shares and fleet context. | Complete. Five Streamlit sections reuse the validated analytical tables, preserve definitions and caveats, and include tested controls, Plotly charts, missing-input guidance and local run instructions. See the dashboard validation record. |
| 5A — Portfolio preparation and final review | Review reproducibility, documentation, source attribution, licensing, visuals and repository organization. | Complete. Fresh installation/reproduction, full software suite, genuine assets, scoped license and future release instructions are documented. Full reproduction after cloning requires the separately downloaded specification PDF and checksum match. |
| 5B-1 — GitHub publication | Publish and inspect the approved public GitHub repository. | Complete. Public `main` contains the approved research assets; the repository and initial 108-file release were verified. |
| 5B-2 — Hosted deployment | Deploy and verify the Streamlit dashboard. | Requires separate approval after publication. Validate the actual cloud build, runtime, controls, downloads and hosted presentation before adding its URL. |
| 6A–6B — Research website | Establish the approved editorial design and complete recovery, shares, fleet and methodology chapters. | Complete. Four SVG charts, reproducible static export, responsive controls and frontend/exporter tests reuse the validated research. |
| 6C — GitHub Pages release | Publish the approved website and update the portfolio. | Complete. Actions build/deploy succeeded; public assets, chart interactions and desktop/mobile presentation were verified. See [website_deployment.md](website_deployment.md). |

## Preparation decisions and next milestones

- The preparation workflow verifies the existing snapshot before processing; later snapshots require a separate provenance decision.
- Required passenger and fleet observations must be present, finite, and valid; structural RMB kilometre blanks and all minibus cross-harbour kilometre blanks remain null.
- PLB, MTR railway, and franchised bus aggregates use explicit component definitions, row-level lineage, and propagated estimate/status metadata.
- Daily-rate reconciliation uses actual calendar days and matching operator boundaries, including combined Citybus franchises. Older annual publication comparisons retain their own vintage and rounding qualifications.
- Phase 3 implements separate analytical scripts and SQL queries from the validated layer, with 2019 and 2015–2018 recovery benchmarks, calendar-day-adjusted profiles and a qualified fleet indicator.
- Phase 4 presents contrasting GMB/RMB trajectories, explicit recovery benchmarks, nonoverlapping comparison-group shares and licensed fleet context. The dashboard preserves the existing research evidence, with visible source and interpretation notes.
- Phase 5A completes repository review, scoped code/data licensing, clean-environment reproduction and portfolio illustrations. Phase 5B-1 publishes the approved repository. Phases 6A–6C deliver and verify the public research website; Phase 5B-2 Streamlit deployment remains a separate milestone requiring approval.
