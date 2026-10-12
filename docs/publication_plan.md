# Publication and Deployment Plan

The public [GitHub repository](https://github.com/AndyLamyinwik/HongKong-minibus-ridership-analysis) was published in Phase 5B-1. The [interactive research website](https://andylamyinwik.github.io/HongKong-minibus-ridership-analysis/) is deployed and verified on GitHub Pages in Phase 6C; its [deployment record](website_deployment.md) describes the workflow and public checks. The original Streamlit application remains available for local use. **Phase 5B-2 Streamlit Community Cloud deployment remains a separate, unverified milestone requiring approval.**

## GitHub presentation

- **Repository name:** `HongKong-minibus-ridership-analysis`
- **Description:** An 11-year analysis of Hong Kong's Green and Red Minibus ridership, pandemic recovery, and transport market share using Python, SQL, and Streamlit.
- **Visibility and default branch:** Public; `main`.
- **Suggested topics:** `data-analysis`, `python`, `sql`, `sqlite`, `pandas`, `streamlit`, `plotly`, `hong-kong`, `public-transport`.
- **Portfolio narrative:** One Industry, Two Different Futures — separate the Green and Red Minibus trajectories while retaining estimation and comparison-boundary qualifications.

## Release contents

Keep the complete source, SQL, tests and documentation; the verified raw CSV snapshot; prepared CSVs and SQLite database; analytical tables and figures; reports; and genuine portfolio screenshots. These compact artifacts let a reviewer explore the dashboard immediately. Full workflow reproduction additionally requires the official data-specification PDF downloaded with its pinned hash. The [data reuse review](data_reuse.md) and [third-party notices](../THIRD_PARTY_NOTICES.md) govern source-material attribution and distinguish it from the original code license.

`data/raw/mttd_dataspec_eng.pdf` is retained unchanged for local validation but excluded from publication while its redistribution permission remains unresolved. Follow the exact official download and checksum instructions in [the data reuse review](data_reuse.md) before running preparation, analysis or the complete software suite after cloning. A changed or unavailable PDF prevents reproduction of this exact snapshot; hash verification must remain enabled. This prerequisite does not affect dashboard startup.

The dashboard's required runtime inputs are twelve CSVs in `analysis/outputs/`: `monthly_ridership`, `annual_ridership`, `endpoint_comparison`, `recovery_2019`, `annual_recovery`, `monthly_market_share`, `annual_market_share`, `annual_minibus_composition`, `minibus_composition`, `annual_fleet`, `fleet_normalized`, and `trend_segments`, plus `analysis/outputs/analysis_summary.json` and `config/sources.json`. Keep `reports/` for the available report downloads. Raw sources, the database and other analysis exports are retained for reproduction rather than dashboard startup. [Application contract](dashboard.md).

Exclude the PDF above, virtual environments, Python/pytest caches, disposable verification directories, credentials, local logs and machine-specific files using `.gitignore`. Inspect the actual staged file list before publication; an ignore file alone does not establish what has been staged. In particular, confirm that the locally present PDF is not staged, even when staging the `data/raw` directory.

## Completed GitHub publication and website release

Phase 5B-1 published the approved 108-file analytical project to public `main`, with initial commit `75df532bfc829bfc25b1e3e26f0121907bbcd21b`. Phase 6C adds the approved website source, deployment workflow and release documentation while preserving historical data and analytical conclusions. The repository website field and opening README link point to the verified GitHub Pages publication.

The Pages workflow builds and publishes only `site/dist/`; the complete repository retains the Python, SQL, Streamlit, research and reproducibility assets. Generated build files, frontend dependencies and private verification artifacts remain untracked. Future release changes require inspection of the actual diff and file list; use ordinary commits and pushes without overwriting unrelated remote work. Authentication uses the account's normal GitHub flow, with no credentials in project files.

See the [website deployment record](website_deployment.md) and [website validation record](../site/docs/validation.md#phase-6c--public-release) for the current static publication. The remaining instructions below apply specifically to a future Streamlit Community Cloud release.

## Streamlit Community Cloud configuration

| Setting | Project value |
| --- | --- |
| Repository | `AndyLamyinwik/HongKong-minibus-ridership-analysis` |
| Branch | `main` |
| Main file path | `dashboard/app.py` |
| Python | Select **3.12** in Advanced settings; this is the verified local major/minor runtime |
| Python dependencies | Root `requirements.txt`; pinned preparation, analysis, dashboard and test environment |
| Application configuration | Root `.streamlit/config.toml`; light theme and project colours |
| Required local inputs | The twelve CSVs and two JSON files listed above; retain reports for downloads |
| Secrets | None required by this application |
| System packages | No `packages.txt` is currently required by the application |

Community Cloud starts the entry point from the repository root. The project's import and data paths resolve from `dashboard/app.py`, and deployment paths use forward slashes. Configuration remains in the root `.streamlit/` directory. [Official file-organization guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization).

The root `requirements.txt` is the dependency declaration. `pyproject.toml` contains pytest configuration, rather than a second package environment. Do not add a competing dependency file beside `dashboard/app.py`; Community Cloud searches the entry-point directory before the repository root. [Official dependency guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## Phase 5B-2: hosted deployment and verification

After publication and approval to deploy:

1. Open [Streamlit Community Cloud](https://share.streamlit.io), connect the approved GitHub account, and choose **Create app**.
2. Select the published repository, `main` and `dashboard/app.py`. In **Advanced settings**, explicitly select Python 3.12 and leave secrets empty. Choose an available, memorable subdomain if desired.
3. Start deployment and review dependency/build logs. Treat a successful local install as preparation; the cloud build must establish Linux compatibility.
4. Check all five sections, four headline KPIs, mode/year/frequency controls, recovery above 100%, comparison-group denominators, fleet labels, source notes and report/CSV downloads. Repeat desktop and narrow-screen checks on the hosted URL.
5. Once the hosted version passes those checks, add its real URL to the README as a separate Streamlit implementation link. Keep the research website as the primary presentation and repository website field. Do not add a placeholder live-demo link or an unverified deployment badge.

The repository, branch, entry point and Python selection are documented in [Streamlit's official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). Cloud settings and service availability should be checked again when Phase 5B-2 begins.

## Readiness and remaining limits

The dashboard performs no source download or pipeline rebuild at startup. A local loader inspection on 11 October 2026 read **1,949 records** across twelve frames; required CSV/JSON files total **271,469 bytes**, and the frames occupy **246,955 bytes** using pandas' deep-memory estimate. This measures table size, not total process or concurrent-session memory. Dependency installation and Plotly/Streamlit runtime overhead remain separate.

Windows/Python 3.12 is the verified local environment. The [fresh-environment reproduction record](reproducibility_check.md) and [portfolio validation record](portfolio_validation.md) describe the local evidence. Neither Linux execution nor a Community Cloud build has been performed during Phase 5A. Cloud readiness is therefore a reviewed configuration, not a claim of successful deployment or a guarantee about resource limits. Community Cloud uses Debian Linux and can override some local settings, including browser usage-statistics configuration. [Official platform limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status).

The Phase 5A Linux-targeted pip dry run successfully resolved all 49 pinned packages
to CPython 3.12 Linux-compatible binary/pure-Python wheels. This supports the
dependency preflight; the actual cloud build must still verify installation,
platform-specific runtime behaviour and system-library compatibility.

Source revisions and estimated RMB volumes remain analytical limitations after publication. Preserve the validated snapshot and existing definitions when releasing; a newer official file belongs to a separately documented provenance and validation decision.
