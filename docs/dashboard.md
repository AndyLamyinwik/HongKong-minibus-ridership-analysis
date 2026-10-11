# Interactive Historical Transport Dashboard

The dashboard presents **One Industry, Two Different Futures: The Diverging Trajectories of Hong Kong's Green and Red Minibuses**. It uses the existing, validated January 2015–December 2025 analytical tables and the conclusions in [the research report](../reports/eda_findings.md). Running the dashboard does not require rerunning preparation or analysis.

## Run locally

Python **3.12** is the verified runtime. From the repository root, create an environment and install the pinned requirements:

```text
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS/Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
```

Open [the local dashboard](http://127.0.0.1:8501). Stop it with `Ctrl+C` in the terminal. If that port is already occupied, select another port in the command. Commands assume the repository root; application data paths resolve relative to the entry point, independently of the working directory.

## Navigation and visual story

| Section | Analytical question and interactive presentation |
| --- | --- |
| Executive Overview | How did the two minibus categories diverge? Four fixed study KPIs, an annual GMB/RMB chart with an absolute/indexed switch, recent changes and minibus composition. |
| Ridership Trends | How do long-term direction and monthly detail differ? Mode selection, inclusive year bounds, monthly/annual views, total/indexed journeys and selected annual endpoints. |
| COVID-19 Recovery | How far did each mode return to its own 2019 benchmark? Mode selection, 2025 recovery bars, paired 2019/2025 totals and the full annual recovery path. |
| Market Share & Industry Structure | How did comparison-group shares and minibus composition change? Monthly/annual frequency, year bounds, stacked area/line views and a separate GMB/RMB composition chart. |
| Fleet & Ridership Relationships | How did licensed stocks and demand relative to stock evolve? GMB/RMB selection, year bounds, monthly/annual frequency, stock and journey/vehicle-day proxy charts, and endpoint changes. |

Every section includes its question, evidence, interpretation and relevant qualifications. **Sources & methodology** is expandable below each section, with official download links, snapshot dates, definitions and formulas. The sidebar retains a short estimation reminder. Selected source records can be downloaded as CSV; original field names and source units are retained in these downloads. Plotly charts support hover, legend toggling, zoom, reset, full-screen viewing and PNG export.

The overview's four KPIs refer to the complete study window: PLB, GMB and RMB percentage changes in annual journeys from 2015 to 2025, and RMB's 2025 annual total as a percentage of 2019. The recovery comparison retains 2019/2025 regardless of other pages' date controls. Findings beside the filtered trend, share and fleet views state the selected annual endpoints explicitly. The recovery page's minibus finding is labelled as the full study result even if a different mode is selected.

## Display definitions

The [Phase 3 analytical methodology](analysis_methodology.md) remains authoritative. The dashboard selects existing annual/monthly tables rather than aggregating a filtered time series into a new annual definition.

- **Absolute journeys:** monthly or annual source thousands divided by 1,000 to display millions. These frequencies are labelled separately.
- **Annual index:** a mode's annual journeys divided by its own 2015 annual journeys × 100.
- **Monthly index:** average daily journeys divided by the same mode's same-calendar-month average daily journeys in 2015 × 100. All twelve 2015 points equal 100. This is a display transformation using the existing daily-rate field, with calendar-day adjustment; it is not the Phase 3 within-year seasonality index. Both trend baselines are fixed before filtering.
- **Recovery:** existing annual journeys / the same mode's 2019 annual journeys × 100. The headline uses 2025; 100% is a benchmark rather than an upper limit.
- **Share within selected public transport modes:** the stored four-component share using GMB + RMB + MTR railway services + franchised buses. PLB is a subtotal, never an extra additive component. Annual shares use annual flow totals. Legend visibility does not change the denominator.
- **Minibus composition:** existing GMB/RMB shares of PLB. Its denominator differs from the transport-share chart.
- **Fleet stock:** month-end licensed vehicles; annual stock displays **December**, explicitly distinct from the arithmetic mean of month-end stocks.
- **Fleet indicator:** monthly average daily journeys × 1,000 / licensed vehicles; annual journeys × 1,000 / Σ(month-end licensed vehicles × calendar days). The precomputed annual weighted indicator is used unchanged.
- **Endpoint change:** 100 × (end / start − 1), using the stated annual endpoints. Share differences are expressed in **percentage points**, not percentage change. A single selected year compares the same endpoint with itself.

## Application structure and data contract

```text
dashboard/app.py                         # Five sections, controls and file-aware caching
src/hk_minibus/dashboard/
    __init__.py
    data.py                             # Local loading, schema and consistency checks
    metrics.py                          # Pure filtering, display units and fixed indices
    charts.py                           # Plotly figure functions
    components.py                       # Shared UI, source notes and methodology
.streamlit/config.toml                  # Restrained light theme
tests/test_dashboard_*.py               # Data, metric, chart and Streamlit app checks
```

`data.py` reads these twelve existing CSVs from `analysis/outputs/`: `monthly_ridership`, `annual_ridership`, `endpoint_comparison`, `recovery_2019`, `annual_recovery`, `monthly_market_share`, `annual_market_share`, `annual_minibus_composition`, `minibus_composition`, `annual_fleet`, `fleet_normalized`, and `trend_segments`. It also requires `analysis/outputs/analysis_summary.json` and `config/sources.json`. No additional dataset copies are created. The two research Markdown reports are optional downloadable supporting documents.

Required input checks cover complete monthly/year/mode keys, units, finite measurements, estimate/status metadata, successful analysis status, annual/monthly agreement and cross-table consistency. The checks verify the included calculation contracts without publishing replacement outputs. Missing, malformed or inconsistent data produce an explanatory error instead of a partial historical chart. Empty mode selections produce guidance. `st.cache_data` uses relative file names, sizes and nanosecond modification times as its input signature, so a changed required file invalidates the cached dataset.

The code reads only local historical files; it contains no credentials or machine-specific absolute paths. Streamlit and Plotly are pinned together with the existing preparation, analysis and test environment in [requirements.txt](../requirements.txt). Theme and appearance use native controls and a small shared stylesheet; the application's responsive layout and chart sizing use Streamlit/Plotly capabilities.

## Interpretation limits

RMB journeys remain estimates, without published confidence intervals or a complete estimation-parameter history. PLB and every transport-share denominator inherit that estimated component. The preserved source snapshot has a single vintage, while older provisional annual references differ; specific revision reasons remain unresolved. MTR includes changing service coverage and cross-boundary railway journeys. Journeys count trips rather than unique travellers. Shares describe the selected comparison group rather than all Hong Kong public transport, and recovery ratios do not establish causes or passenger switching.

Licensed vehicles are administrative stocks rather than daily deployment. The fleet-normalized indicator does not measure occupancy, utilization or operational productivity. RMB demand estimation itself uses fleet information, creating a partly mechanical relationship. These qualifications remain visible in the relevant dashboard views and in the shared methodology.

## Verification

Run the complete suite, including the earlier preparation and research tests:

In a new checkout, first complete the [official specification download/checksum prerequisite](data_reuse.md#download-the-dictionary-for-full-local-reproduction). Preparation tests verify all five manifest files; dashboard startup itself does not need the PDF.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp analysis/.pytest-tmp-dashboard -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
```

The workspace test directory avoids restricted system temporary/cache paths in some Windows environments. Streamlit AppTest creates a local socket pair; the test process needs permission for loopback sockets. The application server also needs loopback access. [Streamlit's AppTest documentation](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest) explains the simulated UI checks; [Plotly configuration documentation](https://plotly.com/python/configuration-options/) describes the chart controls.

The [Phase 4 validation record](dashboard_validation.md) distinguishes automated checks from browser interactions and records the tested environment and any remaining limits.
