# Website validation record

The Phase 6A record below preserves the approved homepage checks. The [Phase 6B record](#phase-6b--complete-research-publication) documents the completed publication and its current local verification.

## Phase 6A — Approved homepage

Validated locally on **12 October 2026**. The scope is the design system and functional static homepage. The checks below describe observed results in the local environment; they do not claim testing of a hosted production service.

### Automated checks

| Check | Result |
| --- | --- |
| Deterministic research export, read-only `--check` | Passed; the static JSON exactly matches the existing research inputs |
| Website Node test suite | **47 passed, 0 failed**: 10 source/data agreement tests and 37 validation/presentation tests |
| Existing Python / SQL / Streamlit test suite | **201 passed, 0 failed**, 91.16 seconds in the existing local verification environment |
| Existing environment dependency check | `pip check`: no broken requirements |
| Original published files | All **107** files excluding the permitted `.gitignore` change remain byte-identical to published commit `75df532bfc829bfc25b1e3e26f0121907bbcd21b` |
| Production build | `pnpm build` completed successfully using Vite 8.3.4; no chunk-size warnings after separate ECharts / zrender bundling |
| Data and public assets | Research JSON, favicon and all eight notice files copied byte-for-byte into the build |
| Runtime asset references | 21 HTML/CSS/JS/data references resolved to local build files beneath a repository-style URL prefix |
| Font assets | All ten generated font assets match their original dependency files; only the appropriate supported font format is requested by the browser |
| Credentials and private paths | Pattern checks and source review found no credentials or private absolute paths in the checked website/build text files; this is a scoped review, not a claim of universal secret detection |

The Node tests check exact source agreement and unrounded metrics, annual completeness, own-service 2015 indices, absolute unit conversion, rounded KPI values, source hashes, estimation flags, stale definitions, malformed data, both tooltip views, chronological sorting, mobile endpoint labels, reduced-motion configuration and color-independent series cues.

Tests reject empty or missing observations, duplicate annual keys, missing years, invalid service names, non-finite values, invalid baselines, inconsistent indices, incorrect estimate flags, missing KPIs and missing source vintage. Additional isolated exporter checks exercised malformed inputs, reconciliation failure, deterministic export and rejection of stale/missing assets without modifying the original research files.

Run from `site/`:

```powershell
pnpm test
pnpm build
```

Run from the repository root:

```powershell
python site/scripts/export_data.py --check
```

The original project's test and environment instructions remain in the repository's existing documentation.

### Actual browser verification

The development server responded with HTTP 200 at `http://127.0.0.1:5173/`. The production homepage was then served locally under `/hong-kong-minibus-ridership-analysis/`, using the built assets, to exercise the GitHub Pages project-path structure. Nominal production loading produced no captured JavaScript errors or warnings. Deliberate missing-data tests generated the expected HTTP 404 response and displayed the handled error state.

The documented `pnpm preview` server also started successfully at `http://127.0.0.1:4173/`; both its homepage and bundled research JSON returned HTTP 200, and the browser rendered the actual KPIs and chart without captured errors or warnings. Owned preview and QA servers were stopped after verification. Use the [local preview instructions](../README.md#local-development) to restart them for review.

| Behavior | Observed result |
| --- | --- |
| Desktop, 1440 × 1000 CSS pixels | Headline, four-column findings strip, chart controls, labels and narrative rendered correctly; no horizontal page overflow |
| Tablet, 768 × 1024 | Navigation and all four aligned KPI values remained readable; chart resized to its container; no horizontal page overflow |
| Mobile, 390 × 844 | Headline wrapped naturally, findings used two columns, navigation collapsed and chart controls fitted the width |
| Narrow mobile, 320 × 720 | Page and opened annual table fitted the viewport without horizontal page overflow |
| Mobile navigation | Menu expanded to real destinations and closed with Escape or link selection |
| Skip navigation | Keyboard focus revealed the skip link; Enter reached `#main`; the link remained clipped when unfocused, including in full-page screenshot capture |
| Chart views | Indexed and absolute buttons updated the axis units, series values, selected control state and year comparison; keyboard activation worked |
| Annual points | All eleven years appeared; mobile reduced visible tick labels while retaining both endpoints and every observation |
| Year exploration | Native year selection and ArrowDown updated the textual comparison and highlighted the selected annual tooltip |
| Pointer tooltip | Selecting the 2025 desktop plot displayed GMB **495.80 million** and estimated RMB **50.74 million** in the absolute view |
| Mobile tooltip | 2019 absolute comparison displayed GMB **539.63 million** and estimated RMB **103.17 million** inside the plot boundary |
| Data table | Native disclosure opened all eleven rows with units, column headers and RMB estimate qualifications |
| Headline findings | Actual rendered values were **−19.51%, −11.17%, −58.00%, 49.18%**, matching the approved analytical results |
| Loading | Controlled delayed data response showed em-dash KPIs, disabled chart controls and a reserved 306px mobile chart region, then resolved to the working chart |
| Empty data | Explicit no-observations message, disabled view controls and unavailable table text; missing values were not displayed as zero |
| Failed download and retry | Handled message and Retry button appeared; restoring the local response and activating Retry loaded the real chart/KPIs without reloading the page |

Actual full-page desktop and mobile screenshots were captured from the functioning production build for local visual review. A tablet capture and a desktop absolute-view tooltip capture also support the review. Screenshots are local review artifacts rather than resources required by the website.

### Visual and accessibility review

The page uses semantic landmarks, one `h1`, a skip link, native buttons with `aria-pressed`, a labeled native year selector, an announced comparison, a captioned data table and visible keyboard focus. Principal chart/menu/year controls have at least 44px height. SVG rendering and ECharts descriptions supplement the textual alternatives.

Text contrast was calculated from the actual palette. Against paper, ink is **13.36:1**, muted text **5.69:1**, jade **6.33:1** and coral **4.91:1**. The narrative background also passes for its text: ink **12.33:1**, muted **5.25:1**, jade **5.84:1**. Light rules remain decorative; essential input boundaries use the darker muted token. Green solid circles and Red dashed diamonds provide cues beyond color.

Reduced-motion behavior is covered by the chart-option tests and the CSS media query. The browser's operating-system motion preference was not changed during review. This validation is not a full accessibility certification or a cross-browser matrix: browser observations used the available Chromium-based in-app browser.

### Remaining review and next scope

No blocking homepage defect was identified in the completed checks. The next milestone is the owner's visual review and approval of this direction. A broader browser/accessibility review can accompany the remaining research sections. Additional market-share, disruption/recovery and methodology content should reuse the validated research outputs and this design system.

The local build is ready for review. This phase does not configure hosting or publish new repository changes.

## Phase 6B — Complete research publication

Validated locally on **12 October 2026**. Four chapters extend the approved homepage: recovery against 2019, selected comparison-group shares, fleet and demand, and methodology/sources. The original annual chart, hero, findings strip and research introduction remain in place. The publication has four SVG ECharts visualizations and six expandable methodology explanations.

### Automated verification and data preservation

| Check | Observed result |
| --- | --- |
| Frontend Node suite | **146 passed, 0 failed**: 18 source agreement, 37 original presentation, 21 new chart-option and 70 chapter-contract tests |
| Isolated standard-library exporter contracts | **16 passed, 0 failed**; isolated inputs exercise deterministic output, stale assets and invalid relationships |
| Deterministic export `--check` | Passed: 22 original annual observations, four KPIs, five recovery rows, 55 share/subtotal rows and 22 fleet/proxy rows |
| Original Python / SQL / Streamlit suite | **201 passed, 0 failed**, 89.02 seconds; temporary fixtures removed after verification |
| Original dependency environment | `pip check`: no broken requirements |
| Published research preservation | All **107 original tracked files**, excluding the existing permitted `.gitignore` change, remain byte-identical to commit `75df532bfc829bfc25b1e3e26f0121907bbcd21b` |
| Source provenance | All **17 input hashes** match current files; the original annual/KPI values and original ten input hashes are preserved |
| Source relationships | Recovery uses each mode's own 2019 annual total; shares use four exclusive components; fleet stocks reconcile against all 264 monthly licensing records |
| GitHub document/source links | All **12 links** to **11 unique files** were fetched through the connected GitHub API and their blob IDs matched local originals; the fleet interpretation heading exists |

The extended tests check exact source values, full-year coverage, measurement and estimate flags, recovery baselines, share denominators, subtotals without double-counting, calendar-weighted vehicle days, independent 2015 indices, tooltip units and estimate qualifications, mobile axis labels, reduced-motion options and malformed/missing chapter data. All 47 Phase 6A frontend tests remain covered.

The source and formula mapping is documented in [metric provenance](metric_provenance.md). The exporter reads analytical files without rewriting them. The browser reuses the existing annual journey array for fleet comparisons rather than shipping a duplicate passenger series.

### Production build and repository paths

`pnpm build` passed using **Vite 8.3.4**, transforming 596 modules in 209 ms with no chunk-size warning. The production directory contains **26 files, 919,138 bytes**. Its 36,628-byte research asset is deterministic. ECharts and zrender remain separate vendor chunks; no new application framework or dependency was added.

All **24 runtime asset references** resolve to local build files beneath `/hong-kong-minibus-ridership-analysis/`. The ten public assets are copied byte-for-byte, all ten font assets match their dependency originals, and seven dependency license/copyright texts retain their content. Scoped pattern checks and source review found no credentials or private absolute paths in the checked website/build text files; this is a bounded review rather than universal secret detection.

The actual production build was served locally beneath the repository-style prefix. The documented `pnpm preview` homepage and bundled JSON also returned **HTTP 200** at port 4173 and rendered all four charts. This verifies local path compatibility; public hosting verification belongs to the next phase.

### Actual browser and interaction verification

| Scenario | Observed result |
| --- | --- |
| Desktop, 1440 × 1000 CSS pixels | All four charts render; the publication retains the approved typography and palette; no horizontal page overflow |
| Tablet, 768 × 1024 | Chapters and controls fit, charts resize and the page has no horizontal overflow |
| Mobile, 390 × 844 | Chapter headings wrap naturally; controls, legends, numerical readouts and methodology remain legible |
| Narrow mobile, 320 × 720 | Two-line recovery mode labels and 0/40/80/120% ticks fit; the dashed 100% reference remains visible with its external key |
| Expanded share table at 320px | The table scrolls inside its bounded region: table client width 261px versus 359px content; document client and scroll widths both 305px |
| Recovery | Selecting MTR displays **101.99%** and highlights its bar; selecting PLB displays **85.03%** with estimate qualifications; an actual pointer tooltip exposes the same PLB value and overlapping-component caveat |
| Comparison-group shares | Minibus detail changes the plotted components and range to 0–20% while retaining the four-mode denominator; 2015 and 2025 selections expose all four shares and the separate PLB subtotal |
| Share keyboard interaction | Enter activates the all-mode view; 2025 displays GMB **12.99%**, estimated RMB **1.33%**, MTR **49.79%**, buses **35.88%**, and PLB subtotal **14.32%** |
| Fleet interactions | Mode and measure switches update real series; estimated RMB's 2025 proxy is **195.39 journeys per licensed vehicle-day**; GMB/stock view and ArrowDown from 2015 select 2016 with **3,254 vehicles** and **559.01 million journeys** |
| Mobile tooltips | Observed share and fleet tooltips stay inside the plot boundary; full estimate and denominator notes wrap without clipping |
| Supporting tables | Native disclosures expose complete recovery and eleven-year share/fleet tables with units and estimate qualifications |
| Methodology | Native disclosure opens the service-boundary definition, including MTR coverage and the July 2023 franchise treatment |
| Navigation | Research contents reach real chapter anchors; the narrow-screen menu expands and closes on Methodology selection; captured chapter headings are unobscured |
| Original annual chart | Indexed/absolute views still work; actual absolute 2025 readout is GMB **495.80 million** and estimated RMB **50.74 million** |
| Delayed download | Four visible loading states, disabled controls, reserved chart regions and em-dash KPIs; response completion renders all four charts and clears statuses |
| Empty overall annual data | Explicit no-observations message, four unavailable charts and disabled analytical controls; methodology remains available and no KPI is replaced with zero |
| Missing individual chapters | Missing recovery, empty share rows or missing fleet rows disable only the affected chapter; the other three charts remain functional |
| Failed download and retry | Controlled HTTP 404 displays handled error states; restoring the response and clicking a chapter Retry loads all four charts and real KPIs without reloading the page |
| JavaScript logs | No captured application errors or warnings during nominal production loading and interactions; deliberately failed downloads produce the expected HTTP error |

Actual desktop, tablet and mobile full-page screenshots were captured from the functioning production build. Representative desktop recovery and mobile share captures show real annotations and tooltip content. These are retained as local review evidence rather than runtime website assets. An independent screenshot review found no actionable continuity, clipping or editorial issues; it covered captured views rather than operating controls.

### Mobile, accessibility and review limits

The narrow-screen table fix bounds the new table disclosures with `min-width: 0` and internal horizontal scrolling. Recovery labels preserve estimation qualifications while wrapping long names; mobile tick spacing avoids the former end-axis crowding. Research tooltips wrap their text independently of the approved annual tooltip. Native selectors and supporting data tables provide alternatives to pointer exploration.

Semantic headings, real buttons, pressed states, labeled selectors, announced readouts, native disclosures and visible focus support keyboard reading. New MTR and bus colors have text contrast of **5.58:1** and **4.95:1** against paper. Fleet stock and passenger series have distinct dash/marker cues; comparison controls retain at least 44px height. Reduced-motion behavior is tested in chart options and CSS; the operating-system preference was not changed.

Browser observations used the available Chromium-based in-app browser. Safari, Firefox, physical touchscreen devices and a complete assistive-technology audit remain outside this local verification. No blocking defect was identified in the completed checks.

### Reproduction and next milestone

From `site/`, run `pnpm test` and `pnpm build`. From the repository root, run `python site/scripts/export_data.py --check` and `python site/tests/export_data_test.py`. The original analytical suite requires its documented pinned environment and reproduction prerequisites.

Owned local preview/QA servers are stopped after verification. Restart the local preview using [the website instructions](../README.md#local-development). Phase 6B is complete for visual review. Phase 6C should establish the final release file list, rerun checks on the approved release, publish the authorized website changes, configure GitHub Pages and verify the public URL, links, data and responsive behavior.

No website commit, push or public deployment was performed in Phase 6B.
