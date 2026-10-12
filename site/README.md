# Hong Kong Minibus Research — Static Website

An editorial research website for **Hong Kong Minibus Ridership: A Decade in Transition (2015–2025)**. The approved homepage introduces **“One Industry. Two Different Futures.”** through four verified findings and an interactive annual Green / Red Minibus comparison. Four subsequent chapters examine recovery, comparison-group shares, fleet context and methodology.

**[Explore the published research website](https://andylamyinwik.github.io/hong-kong-minibus-ridership-analysis/)** — verified on GitHub Pages on 12 October 2026.

The site uses warm paper, deep ink, jade and muted coral, with self-hosted Instrument Serif and DM Sans. Its [design system](docs/design-system.md) describes the visual and accessibility rules. [Metric provenance](docs/metric_provenance.md) maps every numerical view to the existing analytical tables. The [validation record](docs/validation.md) records implementation checks, build results and browser evidence.

## Local development

Use Node.js **22.12 or later** and **pnpm 11.25.0**. Package versions and transitive dependencies are pinned in `package.json` and `pnpm-lock.yaml`.

From the repository root:

```powershell
cd site
pnpm install --frozen-lockfile
pnpm dev
```

Open **http://127.0.0.1:5173/hong-kong-minibus-ridership-analysis/**. The development server binds to the local computer and requires that port to be available. Stop it with Ctrl+C when finished.

To test and preview the production build, from `site/`:

```powershell
pnpm test
pnpm build
pnpm preview
```

Open **http://127.0.0.1:4173/hong-kong-minibus-ridership-analysis/**. Serve `dist/` over HTTP; opening `index.html` with `file://` prevents the data fetch from working in normal browser security settings.

Dependency installation requires network access. The production website reads its bundled static files over HTTP. It is independent of the existing Streamlit application and Python runtime.

## Reading experience

The website is one scrolling publication. The original hero, finding strip, annual trend chart and research introduction retain the approved homepage design. Overview, Research and Methodology remain working primary navigation anchors. A research contents navigation leads to Recovery, Landscape, Fleet and Methods.

| Section | Evidence and useful interactions |
| --- | --- |
| Annual minibus trends | GMB and estimated RMB, switching between own **2015 = 100** and absolute **million journeys**; native year selector and complete annual table |
| The uneven recovery | Five service comparisons against each service's **2019 annual journeys = 100%**; an annotated horizontal bar chart, a native mode selector and accessible comparison table |
| A changing transport landscape | Four nonoverlapping comparison-group components; all-mode and minibus-detail views, a native year selector, PLB subtotal and full share table; an inline comparison highlights GMB's increased share within PLB |
| Fleet size and passenger demand | GMB/RMB selection, December stock versus annual journey indices, and an alternative annual vehicle-day proxy view; a native year selector and supporting stock/proxy table |
| Methodology and sources | Six native expandable explanations covering scope, metrics, transport boundaries, fleet interpretation, validation/revisions and estimation limits; links to the complete published documentation |

There are **four ECharts visualizations**, all rendered as SVG: the preserved annual trend chart and three chapter charts. Calendar-day-adjusted profiles and their qualifications remain in the complete findings report.

Tooltips expose values in their original units, while labeled native controls and tables provide keyboard and touch alternatives. The market-share **Minibus detail** view changes the visible components and vertical range to **0–20%**; it retains the original four-mode denominator. Fleet comparisons use one common index axis, with original stock, journey and proxy units retained in tooltips and tables.

Loading states reserve chart space and display em dashes rather than zero-valued findings. Empty, invalid and unavailable data receive explanatory messages; retry is available for a failed download. Reduced-motion preferences disable chart animation and animated scrolling. Mobile layouts wrap controls and legends, shorten plotted labels where necessary, retain estimate qualifications and allow wide tables to scroll within bounded regions.

## Technology and file structure

The site uses HTML5, CSS and JavaScript ES modules with **Apache ECharts 6.1.0** and **Vite 8.3.4**. The build bundles required line/bar chart components, the SVG renderer and locally served fonts. ECharts and zrender have separate vendor chunks for caching.

```text
site/
  index.html                    Semantic publication and chapter copy
  package.json                  Development, test and build commands
  pnpm-lock.yaml                Locked dependency graph
  vite.config.js                Relative build paths and vendor chunks
  src/
    main.js                     Loading, rendering and native interactions
    data.js                     Runtime contracts and display formatting
    chart.js                    Preserved indexed / absolute annual chart
    research-charts.js          Recovery, comparison-group and fleet charts
    research-data.js            Runtime contracts for the new chapter data
    research.js                 Chapter rendering and native interactions
    style.css                   Responsive editorial layouts
  public/
    data/research.json          Verified static research asset
    favicon.svg                 Original vector project mark
    licenses/                   Dependency and font attribution texts
  scripts/export_data.py        Deterministic export and stale-file check
  tests/                        Source agreement, contracts and presentation
  docs/
    design-system.md            Visual and interaction specification
    metric_provenance.md        Source columns, formulas and interpretation
    validation.md               Implementation checks and browser evidence
```

`node_modules/`, `dist/`, development caches and local QA artifacts are ignored. The original Python, SQL, Streamlit, raw/processed data, reports and analytical figures remain in their existing locations.

## Reproducible static data

The exporter reads validated [`analysis/outputs/`](../analysis/outputs/) tables, preserved monthly fleet records and source/definition files. It writes only `public/data/research.json`. Python **3.10 or later** and the standard library are sufficient for the exporter and its isolated contract tests.

From the repository root:

```powershell
python site/scripts/export_data.py --check
python site/tests/export_data_test.py
```

`--check` verifies that the bundled JSON exactly matches a fresh deterministic export without writing files. The contract tests use isolated copies of the inputs. To regenerate the asset after an intentional, validated research update:

```powershell
python site/scripts/export_data.py
```

The static asset contains:

- 22 GMB/RMB annual observations, the four original KPIs and narrative values.
- Five 2025 recovery percentages with measurement qualifications.
- 44 annual comparison-group component shares, 11 PLB subtotals and 11 group denominators.
- 22 annual fleet/proxy observations and two endpoint summaries; their stock inputs are checked against all 264 preserved monthly fleet records before export.
- Source URLs, snapshot/revision dates, units, estimation flags and SHA-256 hashes for 17 analytical input and definition files.

The snapshot was retrieved on **11 October 2026**, with a recorded dataset revision of **21 September 2026**. It covers **132 months per mode**, January 2015 through December 2025. The extended asset preserves the original annual/KPI interface and reuses those annual journey values in the fleet chapter rather than duplicating the passenger series.

The exporter copies and cross-checks existing analytical results. Display indices, subtotals, percentage-point differences and endpoint formatting follow existing documented definitions. Values remain unrounded in JSON. Percentage/index displays use two decimals; the original annual table displays millions to three decimals. [Metric provenance](docs/metric_provenance.md) gives the precise columns and formulas.

For original analytical tests, use the pinned Python environment and follow the [full reproduction prerequisites](../docs/data_reuse.md#download-the-dictionary-for-full-local-reproduction). Frontend/exporter tests and the production website do not require the official specification PDF. Final test counts and preservation checks appear in the [validation record](docs/validation.md).

## Interpretation

RMB journeys are estimates. PLB totals and all comparison-group denominators include that component. The source provides no quantified confidence interval. Annual totals sum twelve monthly flows from one consistent vintage; historical values may be revised.

Recovery uses each mode's own 2019 annual journeys, while trend indices use 2015. Shares cover the explicitly defined comparison group, rather than all Hong Kong transport. MTR service coverage changed, and preparation accounts for the July 2023 Citybus/NWFB merger without double-counting franchises.

Licensed stocks are administrative records, not daily deployed fleets. The annual journey proxy divides annual flow by calendar-day-weighted month-end stocks, rather than December stock alone. It does not measure occupancy, utilization or operational productivity. RMB estimation already uses fleet information, limiting independent interpretation of passenger/fleet associations. The site describes aggregate historical patterns without identifying causes or individual passenger switching.

See the original [research findings](../reports/eda_findings.md), [analytical methodology](../docs/analysis_methodology.md), [data dictionary](../docs/data_dictionary.md), [source inventory](../docs/data_sources.md) and [revision investigation](../reports/reference_discrepancies.md) for full context.

## Static hosting compatibility and release status

`vite.config.js` uses `base: '/hong-kong-minibus-ridership-analysis/'`. Generated scripts, CSS, fonts and the favicon use the project-site path; licenses and JSON resolve beneath the publication homepage. Navigation uses anchors within the same HTML document. The production build and repository-path verification are covered by the [validation record](docs/validation.md).

The research publication is deployed on GitHub Pages. The [GitHub Pages workflow](../.github/workflows/deploy-site.yml) checks the deterministic data export, runs exporter/frontend tests and builds the site before uploading only `site/dist/`. A separate dependent job deploys that artifact to the `github-pages` environment. [Deployment configuration and verification](../docs/website_deployment.md) record the successful release and maintenance steps.

## Rights and attribution

Original website code follows the repository's [MIT license](../LICENSE). Hong Kong Transport Department source data retains its original rights and [DATA.GOV.HK terms](https://data.gov.hk/en/terms-and-conditions). This independent study does not imply government endorsement.

ECharts uses Apache-2.0; zrender uses BSD-3-Clause; tslib uses 0BSD. Instrument Serif and DM Sans use SIL Open Font License 1.1. Unchanged dependency licenses, font licenses and required copyright notices are retained in [`public/licenses/`](public/licenses/), copied into the production build and linked from the footer.
