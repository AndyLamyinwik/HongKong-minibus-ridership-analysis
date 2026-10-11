# Clean Installation and Reproduction Check

Verified on **11 October 2026** using a newly created virtual environment and an isolated copy of the project inputs and source code. The original validated datasets, analytical outputs and reports were preserved throughout the check.

## Environment

| Component | Verified version or setting |
| --- | --- |
| Operating system | Windows 11, AMD64, build 26200 |
| Python | 3.12.14, 64-bit |
| SQLite | 3.53.1, supplied by Python |
| NumPy / Pandas | 2.5.4 / 3.0.1 |
| Matplotlib / Plotly | 3.11.2 / 7.1.0 |
| Streamlit / pytest | 1.65.0 / 9.0.2 |
| Virtual environment | `.venv-portfolio-check`, `include-system-site-packages = false` |
| Dependency installation | All 49 packages pinned in `requirements.txt` installed successfully |
| Dependency integrity | `python -m pip check`: no broken requirements found |

The fresh environment contained its own installed packages. Installation reused previously cached wheels; it did not inherit packages from the existing development environment. This verifies a clean installation against the pinned dependencies, rather than a second independent operating-system installation.

The isolated check included the locally preserved specification PDF. In a new checkout, obtain that file through the [official download/checksum prerequisite](data_reuse.md#download-the-dictionary-for-full-local-reproduction) before full reproduction or the complete software suite; its public redistribution scope remains unresolved.

## Verification method

The check copied `src/`, `scripts/`, `config/`, `sql/` and `data/raw/` into the temporary `.portfolio-qa/reproduction/` directory. Processed datasets and analytical outputs were **not copied** into that directory. Copied Python bytecode caches were removed before the final verification run. Both existing command-line entry points rebuilt the outputs from the preserved official snapshot.

Each copied entry point resolves its project root from its source location. Consequently, the preparation and analysis runs wrote to the isolated copy and did not overwrite the reviewed project outputs.

The commands actually executed from the repository root were:

```powershell
.\.venv\Scripts\python.exe -m venv .venv-portfolio-check
.\.venv-portfolio-check\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-portfolio-check\Scripts\python.exe -m pip check
.\.venv-portfolio-check\Scripts\python.exe .portfolio-qa/reproduction/scripts/prepare_data.py
.\.venv-portfolio-check\Scripts\python.exe .portfolio-qa/reproduction/scripts/analyze_data.py
```

The temporary verification workspace and virtual environment are excluded from publication. The normal reader workflow is documented in the [README](../README.md): create a Python 3.12 environment, install the requirements, and run the canonical scripts from the repository root.

## Results

| Check | Result |
| --- | --- |
| Preparation pipeline | 103 checks passed, 4 warnings, 0 failures |
| Analysis pipeline | 54 checks passed, 3 warnings, 0 failures |
| Prepared CSV exports | All 3 matched the existing files exactly |
| Analytical CSV exports | All 19 matched the existing files exactly |
| SQL result CSV exports | All 6 matched the existing files exactly |
| SQLite schema and records | All 11 tables and 6 views matched exactly |
| SQLite integrity | `PRAGMA integrity_check` returned `ok` |
| SQLite foreign keys | `PRAGMA foreign_key_check` returned no violations |
| Static figures | All 7 generated PNG files were byte-identical |
| Diagnostic and findings artifacts | Source inspection, preparation summary, analysis summary and findings report were byte-identical |
| Protected original artifacts | All 57 checked source, configuration, SQL, data, figure and report files retained their original SHA-256 hashes |

CSV comparison checked column order, row counts, parsed values, data types and missing-value representation, in addition to byte equality. SQLite comparison checked schema definitions and every returned record, including lineage and validation metadata; it did not rely on database file size or row counts alone.

The reproduced preparation retained 660 monthly passenger records, 660 monthly average-daily records and 264 monthly minibus fleet records for January 2015–December 2025.

### SQL and Pandas parity

The analysis runner executed the six existing queries in `sql/analysis/` against the newly built SQLite database. Its independent Pandas calculations agreed with SQL for:

- Annual ridership.
- Monthly year-over-year changes.
- Annual comparison-group shares.
- Monthly comparison-group shares.
- Recovery against each mode's own 2019 baseline.
- Journeys per licensed vehicle.

These comparisons preserve units, quality metadata and undefined values as well as numeric results. Running `python scripts/analyze_data.py` performs this SQL execution and verification; no separately installed SQLite command-line utility is required.

## Dashboard startup

The dashboard was also started with the fresh environment:

```powershell
.\.venv-portfolio-check\Scripts\python.exe -m streamlit run dashboard/app.py --server.headless true --server.address 127.0.0.1 --server.port 8502 --browser.gatherUsageStats false
```

The local `/_stcore/health` endpoint returned HTTP 200 with `ok`, and the root page returned HTTP 200. The temporary server was then stopped. This checks the clean installation's server startup; it complements the application tests and [dashboard visual validation](dashboard_validation.md).

The dashboard reads the included validated analytical tables and source metadata. A reader can launch it immediately after installing dependencies; rebuilding the preparation and analysis layers is optional for that first launch.

## Warnings and practical limits

The successful reproduction retained the existing warnings about estimated RMB patronage, changing transport service boundaries, licensed fleet interpretation and older publication revisions. Reproduction confirms that the recorded results follow consistently from the preserved inputs and code; it does not remove these measurement limitations.

The automated workspace initially denied `ensurepip` access to its sandbox temporary directory. Creating the environment and installing packages with the available authorized execution permission succeeded. Local server checks also used that permission because this workspace restricts loopback sockets. These restrictions arose from the validation environment and did not require changes to project code or weaker checks.

No Linux execution or Streamlit Community Cloud deployment was performed in this check. Platform compatibility and future deployment configuration are documented separately; a live deployment remains a subsequent release step.

## Linux-targeted dependency preflight

A later Phase 5A check on **12 October 2026** used pip's cross-platform dry-run
resolver for CPython 3.12, Linux x86-64 and compatible manylinux wheel tags.
All **49 pinned dependencies** resolved to binary or pure-Python wheels; no
Windows-only wheel was selected. The check downloaded package distributions for
resolution but installed nothing into a Linux environment:

```text
python -m pip install --dry-run --ignore-installed --only-binary=:all: --implementation cp --python-version 312 --abi cp312 --platform manylinux_2_34_x86_64 --platform manylinux_2_28_x86_64 --platform manylinux_2_27_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64 --platform linux_x86_64 --target .portfolio-qa/linux-resolution -r requirements.txt
```

This establishes wheel availability and successful declared dependency resolution
for the selected target tags from the Windows host. It does not execute Linux
imports, check runtime system-library compatibility or establish a successful
Community Cloud build. The actual cloud installation and application checks
remain Phase 5B-2 work.
