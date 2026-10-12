# Portfolio Preparation and Final Quality Review

Phase 5A reviewed on **11–12 October 2026**. The project is prepared for a subsequent
publication decision. No GitHub repository, remote push or hosted deployment was
performed during Phase 5A. Subsequent source publication and the GitHub Pages
research website release are recorded in [website_deployment.md](website_deployment.md).
The historical analytical findings and data remain unchanged.

## Review scope and changes

- Rewrote the [README](../README.md) around the research question, five verified
  findings and **One Industry, Two Different Futures**, with a direct local quickstart.
- Kept the established Python/SQL/data structure, pinned dependencies and all tests.
  Included prepared and analytical outputs support dashboard startup after cloning.
- Added one actual application screenshot and three unchanged research figures in
  [assets](../assets/README.md), with captions, provenance and data attribution.
- Shortened redundant overview text and moved repeated KPI detail into a shared
  caption and help tooltips. The primary GMB/RMB chart follows the cards and measure
  selector. Labels, controls, baselines and calculations remain the same.
- Added scoped [MIT licensing](../LICENSE), [third-party/data notices](../THIRD_PARTY_NOTICES.md)
  and a [file-by-file reuse review](data_reuse.md). Excluded only the local dictionary
  PDF from future Git publication; its local bytes and manifest hash are unchanged.
- Expanded `.gitignore` for environments, caches, credentials, logs and isolated
  verification files. Updated stale planning language to the implemented scope.
- Added [future publication/deployment instructions](publication_plan.md), a
  [fresh-install record](reproducibility_check.md) and a portable, read-only
  [Python SQL example](../sql/analysis/README.md).

## Automated and reproduction results

| Check | Observed result |
| --- | --- |
| Fresh environment | Python 3.12.14 / Windows 11; all 49 pinned packages installed; `pip check` passed |
| Complete software suite | **201 passed**, 0 failures, in **85.84 seconds** |
| Preparation validation | 103 passes, 4 warnings, 0 failures |
| Analytical validation | 54 passes, 3 warnings, 0 failures |
| Independent SQL/Pandas checks | All six query outputs agreed |
| Fresh reconstructed CSVs | All 28 prepared, analytical and SQL exports matched values and bytes exactly |
| SQLite reconstruction | Schema, all 11 tables and 6 views, integrity and foreign keys matched |
| Reconstructed illustrations | All seven research PNGs were byte-identical |
| Reconstructed diagnostic/report files | Source inspection, preparation summary, analysis summary and findings report were byte-identical |
| Standalone documented SQL example | 55 annual rows matched the included SQL export; database bytes remained unchanged |
| Fresh dashboard server | Health endpoint and root page returned HTTP 200 |
| Linux-targeted wheel resolution | All 49 pins resolved to CPython 3.12 x86-64 Linux-compatible binary/pure-Python wheels; no installation or Linux execution performed |

The full suite was executed from the repository root with:

```powershell
.\.venv-portfolio-check\Scripts\python.exe -m pytest -q --basetemp analysis/.pytest-tmp-phase5a-final -p no:cacheprovider --tb=short
```

Local socket permission was necessary for Streamlit AppTest in this restricted
Windows environment. No test was removed or weakened. Tests cover source validation,
failed-run isolation, aggregation/calendar contracts, independent SQL parity,
dashboard data validation, metrics, chart specifications and all five application
sections with their filters and boundary cases. Pipeline warnings retain the
documented measurement and publication-vintage limitations.

The isolated reproduction first confirmed all 57 baseline artifacts unchanged.
The final review retains 56 byte-identical baseline artifacts; the sole intentional
change within that baseline is `sql/analysis/README.md`, which now includes the
portable inspection example. All government source files, numerical outputs,
database bytes, analytical SQL queries, research figures and findings reports are
unchanged. Source code comparison against the isolated copy also preserves the
preparation and analytical calculation modules.

## Numerical communication checks

The README claims were recalculated directly from the included complete-year totals
and cross-checked against the endpoint, composition and share tables:

| Metric | Displayed value |
| --- | ---: |
| PLB annual change, 2015–2025 | −19.51% |
| GMB annual change, 2015–2025 | −11.17% |
| Estimated RMB annual change, 2015–2025 | −58.00% |
| RMB 2025 annual journeys / 2019 | 49.18% |
| GMB share of PLB journeys, 2025 | 90.72% |
| PLB share of the comparison group, 2015 → 2025 | 16.99% → 14.32% |

Additional README totals, the GMB recovery benchmark, 2015 composition and the share
difference also match the unrounded calculations. Annual PLB equals GMB + RMB;
the share denominator counts PLB once alongside MTR railway services and franchised
buses. Estimated quantities and descriptive interpretation remain explicit.

## Visual, file and security review

The actual dashboard was inspected at observed CSS widths of **1,211 px**, **900 px**
and **390 px**. Wide screens show four KPI cards, medium screens two per row and
narrow screens one per row. Values and labels fit their cards, the mobile chart's
years, axes and estimated RMB legend remain readable, and the page has no horizontal
overflow at the checked widths. Temporary viewport overrides were reset.

The README was rendered locally with GFM-compatible tables and opened in a browser.
Both tables, the genuine overview image and the expandable three-figure section
rendered correctly; all four images loaded at their original dimensions. This
checks the local presentation; GitHub's actual rendering is a Phase 5B verification.
All eleven repository PNG/JPEG files decoded successfully. The three portfolio PNGs
are byte-identical copies of their analytical originals.

A final audit verified **123 local file/heading references**, required dashboard
resources and the source hashes against the intended **108-file publication set**.
Git's ignore engine was exercised using an isolated temporary bare repository,
without initializing this project's repository or creating a commit. It excludes
the dictionary PDF, both environments, caches, QA fixtures, credential files and
logs while retaining required historical data and runtime files. The project
publication set is approximately **5.2 MB**, excluding environments and the PDF.

Review of publishable text files found no credential-token/private-key pattern or
machine-specific absolute-path match. No secrets are needed by the dashboard.
The required twelve CSVs and two JSON files are present; report downloads have their
local source files. Temporary reproduction, rendering and software-fixture files are
excluded and removed after verification.

An independent hiring-manager review confirmed a clear research problem, credible
Python/SQL and validation evidence, readable genuine visuals, accessible setup and
qualified business interpretation. It caught the PDF prerequisite and a broken
heading fragment; these were corrected throughout the relevant guides.

## Remaining release conditions

1. The dictionary's public redistribution scope remains unresolved. The exact path
   stays excluded; new clones must use the [official download and checksum instructions](data_reuse.md#download-the-dictionary-for-full-local-reproduction)
   before preparation, analysis or the complete test suite. The current official
   file matches the hash, but its mutable URL is not a guaranteed permanent archive.
2. Windows/Python 3.12 execution is verified. Linux execution, actual cloud resource
   use and a successful Streamlit Community Cloud build remain future checks.
3. Estimated RMB patronage, changing service coverage, licensed-stock proxies and
   cross-vintage differences remain analytical limits, rather than software failures.
4. Phase 5B requires approval, the intended GitHub account and review of the actual
   staged files. Follow [the exact release plan](publication_plan.md); add a live
   dashboard link only after the hosted application passes its checks.
