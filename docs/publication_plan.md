# Publication and Deployment Plan

Phase 5A prepared the local portfolio for review. **Phase 5B-1 covers GitHub publication; Phase 5B-2 covers Streamlit Community Cloud deployment. Each requires separate approval.** No public repository or hosted application has been created. The commands below are future instructions, not evidence of completed publication.

## Proposed GitHub presentation

- **Repository name:** `hong-kong-minibus-ridership-analysis`
- **Description:** An 11-year analysis of Hong Kong's Green and Red Minibus ridership, pandemic recovery, and transport market share using Python, SQL, and Streamlit.
- **Visibility and default branch:** Public; `main`.
- **Suggested topics:** `data-analysis`, `python`, `sql`, `sqlite`, `pandas`, `streamlit`, `plotly`, `hong-kong`, `public-transport`.
- **Portfolio narrative:** One Industry, Two Different Futures — separate the Green and Red Minibus trajectories while retaining estimation and comparison-boundary qualifications.

## Files to publish

Keep the complete source, SQL, tests and documentation; the verified raw CSV snapshot; prepared CSVs and SQLite database; analytical tables and figures; reports; and genuine portfolio screenshots. These compact artifacts let a reviewer explore the dashboard immediately. Full workflow reproduction additionally requires the official data-specification PDF downloaded with its pinned hash. The [data reuse review](data_reuse.md) and [third-party notices](../THIRD_PARTY_NOTICES.md) govern source-material attribution and distinguish it from the original code license.

`data/raw/mttd_dataspec_eng.pdf` is retained unchanged for local validation but excluded from publication while its redistribution permission remains unresolved. Follow the exact official download and checksum instructions in [the data reuse review](data_reuse.md) before running preparation, analysis or the complete software suite after cloning. A changed or unavailable PDF prevents reproduction of this exact snapshot; hash verification must remain enabled. This prerequisite does not affect dashboard startup.

The dashboard's required runtime inputs are twelve CSVs in `analysis/outputs/`: `monthly_ridership`, `annual_ridership`, `endpoint_comparison`, `recovery_2019`, `annual_recovery`, `monthly_market_share`, `annual_market_share`, `annual_minibus_composition`, `minibus_composition`, `annual_fleet`, `fleet_normalized`, and `trend_segments`, plus `analysis/outputs/analysis_summary.json` and `config/sources.json`. Keep `reports/` for the available report downloads. Raw sources, the database and other analysis exports are retained for reproduction rather than dashboard startup. [Application contract](dashboard.md).

Exclude the PDF above, virtual environments, Python/pytest caches, disposable verification directories, credentials, local logs and machine-specific files using `.gitignore`. Inspect the actual staged file list before publication; an ignore file alone does not establish what has been staged. In particular, confirm that the locally present PDF is not staged, even when staging the `data/raw` directory.

## Phase 5B-1: GitHub publication

Before creating a public repository or pushing files, complete a final local inspection and present the intended owner, repository name and visibility, exact file count and total size, licensing and attribution decisions, secret-scan results, complete software-suite results and unresolved risks. **Stop for explicit approval of this publication checklist.** Authentication must use a secure GitHub sign-in flow; do not place tokens or passwords in project files or chat.

After that approval, confirm the intended GitHub account and repository visibility, check whether the proposed repository already exists, then:

1. Rerun the documented verification checks, inspect source-material notices and review the staged files.
2. If it does not exist, create an empty public GitHub repository with the approved name and description. Do not generate another README, license or ignore file remotely; the project already contains them. If an existing repository is found, inspect it before proceeding; do not overwrite unrelated contents or force-push.
3. From the project root, initialize the local repository only if it is still untracked, then stage the explicit project allowlist below. If Git already exists, inspect its status, branch and remotes before proceeding.

```text
git init -b main
git add README.md LICENSE THIRD_PARTY_NOTICES.md .gitignore .streamlit/config.toml requirements.txt pyproject.toml dashboard src scripts sql tests config docs assets data/raw data/processed analysis/outputs analysis/figures reports
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
```

4. Review the staged diff, confirm that ignored local artifacts and credentials are absent, and create the first commit. Replace `YOUR-ACCOUNT` with the approved account; verify the resulting remote before pushing.

```text
git commit -m "Prepare validated Hong Kong minibus ridership portfolio"
git remote add origin https://github.com/YOUR-ACCOUNT/hong-kong-minibus-ridership-analysis.git
git remote -v
git push -u origin main
```

5. Inspect the published README, all four preview images, source/notice links, research reports and example SQL. Add the proposed topics and pin the repository if desired. Verify installation and dashboard startup from a fresh clone before presenting it as reproducible.

These instructions follow the [official GitHub guide for adding locally hosted code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github). Authentication must use the account's normal GitHub flow; credentials do not belong in project files.

## Streamlit Community Cloud configuration

| Setting | Project value |
| --- | --- |
| Repository | The approved GitHub account / `hong-kong-minibus-ridership-analysis` |
| Branch | `main`, after the publication commit |
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
5. Once the hosted version passes those checks, add its real URL to the README and repository website field. Do not add a placeholder live-demo link or an unverified deployment badge.

The repository, branch, entry point and Python selection are documented in [Streamlit's official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). Cloud settings and service availability should be checked again when Phase 5B-2 begins.

## Readiness and remaining limits

The dashboard performs no source download or pipeline rebuild at startup. A local loader inspection on 11 October 2026 read **1,949 records** across twelve frames; required CSV/JSON files total **271,469 bytes**, and the frames occupy **246,955 bytes** using pandas' deep-memory estimate. This measures table size, not total process or concurrent-session memory. Dependency installation and Plotly/Streamlit runtime overhead remain separate.

Windows/Python 3.12 is the verified local environment. The [fresh-environment reproduction record](reproducibility_check.md) and [portfolio validation record](portfolio_validation.md) describe the local evidence. Neither Linux execution nor a Community Cloud build has been performed during Phase 5A. Cloud readiness is therefore a reviewed configuration, not a claim of successful deployment or a guarantee about resource limits. Community Cloud uses Debian Linux and can override some local settings, including browser usage-statistics configuration. [Official platform limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status).

The Phase 5A Linux-targeted pip dry run successfully resolved all 49 pinned packages
to CPython 3.12 Linux-compatible binary/pure-Python wheels. This supports the
dependency preflight; the actual cloud build must still verify installation,
platform-specific runtime behaviour and system-library compatibility.

Source revisions and estimated RMB volumes remain analytical limitations after publication. Preserve the validated snapshot and existing definitions when releasing; a newer official file belongs to a separately documented provenance and validation decision.
