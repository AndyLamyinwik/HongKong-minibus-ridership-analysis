# Data Reuse and Licensing Review

Reviewed on **11 October 2026**. This record separates the project's original software from government data and linked publications. It records the publication choices supported by the inspected notices; it does not transfer third-party ownership.

## Government data and publisher notices

The [DATA.GOV.HK Terms and Conditions](https://data.gov.hk/en/terms-and-conditions), version 1.2 dated 26 May 2025, permit downloading, reproduction and distribution for commercial and non-commercial purposes subject to their conditions. They require clear source identification, acknowledgement of Government/relevant-organisation intellectual property ownership, and attribution to those organisations and DATA.GOV.HK. The data are supplied without warranties; the terms also contain an indemnity and may change. The full terms govern reuse, rather than a Creative Commons or software licence.

The [portal FAQ, questions 1 and 4](https://data.gov.hk/en/faq) also requires compliance with related-site terms and excludes resale of the data. The [Transport Department's Important Notices](https://www.td.gov.hk/en/important_notices/index.html) restrict public reproduction of its website copyright material without prior written authorisation. An accessible government URL alone therefore does not establish permission to redistribute every document.

The [Monthly Traffic and Transport Digest catalogue](https://data.gov.hk/en-data/dataset/hk-td-tis_17-monthly-traffic-and-transport-digest-csv) identifies TD as publisher, lists the four CSVs below as data resources, and separately links the specification as its data dictionary.

## File-by-file publication decisions

| Material | Handling and applicable scope |
| --- | --- |
| `data/raw/table21_eng.csv` | Include unchanged as a catalogue open-data resource, subject to the DATA.GOV.HK terms and source/ownership acknowledgement. |
| `data/raw/table21s_eng.csv` | Include unchanged under the same catalogue data-resource conditions. |
| `data/raw/table22_eng.csv` | Include unchanged under the same catalogue data-resource conditions. |
| `data/raw/DATA_LAST_REVISION_DATE_eng.csv` | Include unchanged under the same conditions; it is separately listed as revision metadata. |
| `data/raw/mttd_dataspec_eng.pdf` | Preserve the validated local copy, but exclude this exact path from planned Git publication. Provide its official link and the download/checksum procedure below. |
| `data/processed/`, `analysis/outputs/` and the SQLite database | Include the prepared and calculated records for reproducibility. These transform the attributed government data; their factual content is not relicensed as project-owned software. Retain this notice and source metadata with redistributed copies. |
| `config/reference_values.csv` | Contains nine reference values with publication URLs and status notes for validation. Attribute TD; the original publication pages and complete tables are not bundled. |
| Original research reports, charts and dashboard screenshots | Original project presentation based on the attributed government records. Captions and accompanying documentation identify the data source and analytical transformation; these are not official TD publications. Government data remain outside the original-software licence. |
| Annual Transport Digest HTML and December 2025 digest PDF | Link to the official publications for reference. Do not redistribute their pages, graphics or complete PDFs as project assets. |

### Why the dictionary PDF is treated separately

The portal's broad definition of data includes text, which could support treating its linked dictionary as part of the open-data package. However, the catalogue labels this file as documentation rather than a CSV data resource; the related-site notice remains restrictive. Inspection of the dictionary text found no separate redistribution licence resolving that scope. Two independent project reviewers chose a conservative exclusion instead of presenting its reuse permission as certain. No request for written authorisation was sent.

This exclusion changes publication packaging only. The original local PDF and its entry in [the source manifest](../config/sources.json) remain intact. The dashboard uses the included analytical tables and does not require this PDF. Preparation, analysis and the complete software suite verify the dictionary's pinned bytes and therefore require the download below in a new checkout. Hash validation must not be removed or relaxed.

## Download the dictionary for full local reproduction

Use the [official dictionary URL](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf). The official download was rechecked during this review: **367,151 bytes**, SHA-256 **`213f990f1bc2902c190a7f00825a407ad42b00dcdd53fa00cdda1ab49ce028e6`**. Existing validated copies must not be overwritten.

Run from the repository root in PowerShell:

```powershell
$ErrorActionPreference = 'Stop'
$dictionaryPath = 'data/raw/mttd_dataspec_eng.pdf'
$expectedDictionaryHash = '213f990f1bc2902c190a7f00825a407ad42b00dcdd53fa00cdda1ab49ce028e6'
if (-not (Test-Path -LiteralPath $dictionaryPath)) {
    curl.exe --fail --location --output $dictionaryPath 'https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf'
    if ($LASTEXITCODE -ne 0) { throw 'Official dictionary download failed.' }
}
$actualDictionaryHash = (Get-FileHash -LiteralPath $dictionaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualDictionaryHash -ne $expectedDictionaryHash) {
    throw 'Dictionary bytes differ from the preserved snapshot. Stop; do not weaken the manifest validation.'
}
```

On Windows, if curl specifically reports an unreachable certificate-revocation service, retry with `--ssl-revoke-best-effort`; certificate validation stays enabled. That option succeeded in this environment. Python Requests encountered a TLS EOF here, so a Requests-only download was not verified.

For macOS/Linux, download using `curl --fail --location --output data/raw/mttd_dataspec_eng.pdf` followed by the official URL, then verify with `sha256sum data/raw/mttd_dataspec_eng.pdf` or `shasum -a 256 data/raw/mttd_dataspec_eng.pdf` before running preparation. These shell variants were not executed on this Windows host.

The URL is mutable. The current checksum matched at review time; a future revision could prevent exact reconstruction from that URL. If it differs or access fails, the included dashboard remains usable, but full snapshot reproduction requires a legitimately obtained copy matching the manifest. Do not substitute a later dictionary silently or claim that a permanent archive has been verified.

## Attribution to preserve with copies

> Source: Transport Department, HKSAR Government, via DATA.GOV.HK. The Government and relevant rights holders retain intellectual property rights in the source data. Project tables, calculations and visualisations are derived from the preserved snapshot retrieved on 11 October 2026, with dataset revision date 21 September 2026. Reuse of government data is subject to the DATA.GOV.HK Terms and Conditions. This independent project is not endorsed by the Government.

Keep this acknowledgement and [the terms link](https://data.gov.hk/en/terms-and-conditions) with the repository and any separately redistributed data, figures or exports. A standalone CSV should be accompanied by the source/terms notice; the original raw CSV bytes stay unchanged.

## Original software and dependencies

The **MIT licence** is suitable for the original Python/application code, SQL, tests and associated software documentation. Its permission notice applies to that original software, not to government files, factual derived records, external publications or dependency packages. See the project's [LICENSE](../LICENSE) and [third-party notice](../THIRD_PARTY_NOTICES.md) for the implemented scope.

The repository imports packages rather than vendoring their source or binary distributions. Inspection found no copied dependency distribution in the intended publication files; virtual environments must remain excluded. Installed package metadata identifies Streamlit as Apache-2.0, Plotly and pytest as MIT, and pandas as BSD-3-Clause. NumPy's wheel declares multiple component licences; Matplotlib carries its own licence and bundled-component/font notices. Dependencies retain their own notices and licences when installed; the project's MIT licence does not replace them. This is a scope review, not an exhaustive licence audit of every transitive dependency or future wheel.
