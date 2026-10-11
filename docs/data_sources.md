# Verified Data Sources and Quality Findings

## Verification record and recommended period

Sources were accessed on **11 October 2026**. Verification included downloading and reading the CSV headers and records, checking date continuity, numeric availability and composite-key uniqueness, and inspecting official HTML/PDF tables and notes. These were read-only discovery checks; no cleaned tables, annual aggregates, or exploratory findings were created.

The common analytical period is **January 2015–December 2025**, covering **132 months and 11 complete calendar years**. All requested passenger series and GMB/RMB fleet and capacity series have complete monthly coverage in the preserved snapshot. The three statistical CSVs each span **January 2013–July 2026**, with **163 consecutive monthly dates**. Later months remain in the original files but are outside the implemented study window.

The official [revision-date CSV](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/DATA_LAST_REVISION_DATE_eng.csv) contains `DATA_REVISION_DATE = 2026-09-21`. This is the dataset's reported revision date, distinct from the retrieval date and observation dates. TD's [data specification](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf) states that published files can be revised.

## Official source inventory

All sources below are published by the **Transport Department (TD), HKSAR Government**. The monthly CSV resources and dictionary are listed in the [DATA.GOV.HK Monthly Traffic and Transport Digest catalogue](https://data.gov.hk/en-data/dataset/hk-td-tis_17-monthly-traffic-and-transport-digest-csv), whose update frequency is monthly. The specification identifies TD's Road Safety and Standards Division as the source for Tables 2.1, 2.1S and 2.2.

| ID | Official resource | Actual verified coverage and frequency | Role and local preservation |
| --- | --- | --- | --- |
| S1 | [Table 2.1 — Public Transport Passenger Journeys by Public Transport Operator](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table21_eng.csv) | Monthly, 2013-01–2026-07; 2,897 data rows | Primary patronage source; `data/raw/table21_eng.csv` |
| S2 | [Table 2.1S — Average Daily Public Transport Passenger Journeys by Public Transport Operator](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table21s_eng.csv) | Monthly daily averages, 2013-01–2026-07; 2,734 data rows | Supporting rate source; `data/raw/table21s_eng.csv` |
| S3 | [Table 2.2 — Public Transport Operating Statistics by Public Transport Operator](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table22_eng.csv) | Monthly, 2013-01–2026-07; 5,105 data rows | Optional licensed fleet/capacity context; `data/raw/table22_eng.csv` |
| S4 | [Last revision date](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/DATA_LAST_REVISION_DATE_eng.csv) | One metadata row: 2026-09-21 | `data/raw/DATA_LAST_REVISION_DATE_eng.csv` |
| S5 | [Monthly digest data specification](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf) | Current 92-page dictionary; statistical fields on PDF pages 4–8, symbol definitions on pages 56–57 | `data/raw/mttd_dataspec_eng.pdf`; local preservation only, excluded from future Git publication |
| S6 | [Annual Transport Digest 2025, section 5.3](https://www.td.gov.hk/mini_site/atd/2025/en/section5-3.html) | Annual totals for 2015–2024 plus all twelve monthly rows of 2024 | Actual HTML table inspected; reference only, not copied locally |
| S7 | [December 2025 monthly digest PDF, Table 2.1](https://www.td.gov.hk/filemanager/en/content_5378/2512_e.pdf) | Annual totals for 2021–2025; monthly totals for 2024-07–2025-12 | Actual table inspected on PDF pages 13–14, printed pages 4–5; reference only |
| S8 | [Annual Transport Digest 2025, section 3.10](https://www.td.gov.hk/mini_site/atd/2025/en/section3-10.html) | Annual end-year licensed total PLBs, 2015–2024 | Optional fleet reference; actual HTML table inspected |
| S9 | [Annual Transport Digest 2025, section 3.2](https://www.td.gov.hk/mini_site/atd/2025/en/section3-2.html) | Annual end-year registered total PLBs, 2015–2024 | Definition contrast only; actual HTML table inspected |

S6's edition year does **not** mean it contains 2025 observations. S7 independently confirms full-year 2025 availability, but its 2025 minibus totals were provisional at that publication vintage. The main series should use S1's common snapshot rather than joining annual publications together.

S8 and S9 contain total PLBs without a historical GMB/RMB split. Registered and licensed vehicles are different stocks; neither directly counts vehicles actually deployed. S3 provides the monthly split needed for the optional fleet question.

## Passenger series and aggregation boundaries

| Requested series | Exact S1 selector | Coverage and measurement status |
| --- | --- | --- |
| Green Minibus | `MODE=PLB`, `TTD_PTO_CODE=GMB` | 132 target months; published operator statistics, subject to revision |
| Red Minibus | `MODE=PLB`, `TTD_PTO_CODE=RMB` | 132 target months; survey/model-based estimates, not regular operator returns |
| Total Public Light Bus | GMB + RMB for the same month | Components complete; no standalone total row in S1; derivation planned for Phase 2; includes an estimated component |
| MTR railway services | `TTD_PTO_CODE=MTRC`, `RAIL_LINE` in `Local`, `Airport`, `LRT` | Each component has 132 target months; aggregate planned for Phase 2 |
| Franchised buses | All `MODE=Fran_Bus` records for the same month | 132 target months; include applicable KMB, CTB franchises, NWFB, LWB and NLB rows once |

S1 stores **thousands of passenger journeys per month**; its decimal precision should be preserved. S2 stores **thousands of journeys per day averaged within each month**, not another monthly total. Journeys are the publisher's patronage measure, not unique people; these files contain no individual-level travel histories or explicit general transfer-counting methodology.

The MTR `Local` category is named “MTR Lines” in the dictionary and includes High Speed Rail and former Intercity Passenger Services. It must not be described as exclusively domestic. Airport Express and Light Rail have separate records. The annual **Railways subtotal includes Hong Kong Tramways**, so it is not an MTR total. MTR buses (`MODE=LRB`) are separate and excluded from the proposed railway comparator. The relevant definitions and service notes appear in [S5](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf) and [S6](https://www.td.gov.hk/mini_site/atd/2025/en/section5-3.html).

For S1, franchised buses have six component records per month through June 2023 and five from July 2023. CTB franchise `1` and NWFB end in June 2023; CTB franchise `3` begins in July. Franchise `2`, KMB, LWB and NLB continue. TD documents the Citybus/NWFB franchise merger effective **1 July 2023** in [S6, note 1](https://www.td.gov.hk/mini_site/atd/2025/en/section5-3.html). S2 already combines CTB's franchises and therefore has five bus records per month before the merger and four afterward. Record counts are not evidence of a loss of total bus coverage.

## Source schemas, definitions and units

### S1: Table 2.1

Exact header order:

```text
YR_MTH,MODE,TTD_PTO_CODE,FRANCHISE_TYPE,RAIL_LINE,PAX,PAX_INDI
```

| Column | Meaning and unit |
| --- | --- |
| `YR_MTH` | Reference month, source format `YYYYMM` |
| `MODE` | Transport mode code; relevant values: `PLB`, `Fran_Bus`, `Railways` |
| `TTD_PTO_CODE` | Operator/service code, including `GMB`, `RMB`, `MTRC` and bus operators |
| `FRANCHISE_TYPE` | Citybus franchise category: `1` = Hong Kong Island/cross-harbour, `2` = Airport/North Lantau, `3` = Urban/New Territories; structurally blank for other series |
| `RAIL_LINE` | MTR category: `Local`, `Airport`, `LRT`; structurally blank for other series |
| `PAX` | Passenger journeys within the month, thousands |
| `PAX_INDI` | Official status/remark indicator for `PAX`; retain separately |

The source key is the combination of the first five columns. No duplicate keys were found.

### S2: Table 2.1S

Exact header order:

```text
YR_MTH,MODE,TTD_PTO_CODE,RAIL_LINE,AVG_DAILY_PAX,AVG_DAILY_PAX_INDI
```

Date, mode, operator and rail fields have the meanings above. `AVG_DAILY_PAX` is average daily passenger journeys in thousands, and `AVG_DAILY_PAX_INDI` holds its official remark. There is no franchise field: Citybus records are already combined. The first four columns form a unique source key in the inspected file.

### S3: Table 2.2

Exact header order:

```text
YR_MTH,MODE,TTD_PTO_CODE,FRANCHISE_TYPE,RAIL_LINE,BUS_TYPE_CODE,KM,KM_INDI,KM_CROSS_HARBOUR,KM_CROSS_HARBOUR_INDI,NO_FLEET,NO_FLEET_INDI,PAX_CAP,PAX_CAP_INDI
```

The first five columns retain the meanings above. The remaining fields are:

| Column(s) | Meaning and unit |
| --- | --- |
| `BUS_TYPE_CODE` | Bus deck subtype (`DD`/`SD`); blank for totals or series without a subtype |
| `KM`, `KM_CROSS_HARBOUR` | Operated vehicle-kilometres and cross-harbour vehicle-kilometres during the month, thousands; rail definitions differ, as specified in S5 |
| `NO_FLEET` | Licensed fleet at month-end; for PLBs, number of vehicles, based on TD licensing records |
| `PAX_CAP` | Passenger carrying capacity at month-end; for PLBs, passenger places, not journeys |
| Corresponding `*_INDI` fields | Official remarks for each measure |

The first six columns form a unique source key. Total and deck-subtype rows coexist for buses; they must not be added together. The planned fleet extension selects only GMB/RMB rows.

### Reference publication headers

S6 and S7 are wide tables with `Year / Month`, franchised bus operator/franchise columns and a bus `Sub-total`, `MTR Lines`, `Airport Express Line`, `Light Rail`, `Green Minibus`, `Red Minibus`, and PLB `Sub-total`. Their passenger totals are in thousands. Annual and monthly rows are identified separately; published daily averages are separate columns/measures. S8 and S9 have annual reference years and a `Public Light Bus` vehicle-count column, measuring licensed and registered stocks respectively at year-end.

## Quality findings and interpretation limits

### Numeric coverage and status flags

Every GMB/RMB and MTR component has exactly twelve observations per target year in S1 and S2. Franchised bus components cover every target month under the contemporaneous franchise structure. No blank, nonnumeric, nonfinite, zero, or negative passenger values were found anywhere in either passenger CSV.

Across the full S1 file, `PAX_INDI` has 2,872 blanks, 24 `#` entries and one `*`. S2 has 2,709 blank indicators, 24 `#` and one `*`. All target-period GMB, RMB, MTR and franchised bus passenger indicators are blank. GMB/RMB values for January–July 2026 are provisional, outside the proposed study window. A blank indicator means no explicit status mark, not proof of perfect accuracy or immunity from later revision.

The [S5 symbol table](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf) defines `#` as provisional, `*` as revised and `N.A.` as unavailable. S6 additionally defines `-` as not applicable. Blank dimension fields do not mean missing patronage. No numeric missing-value imputation is indicated for the target passenger series.

### Estimated versus reported figures

TD states that **RMB operators do not submit regular returns**. Estimates use Comprehensive Surveys on Red Minibus Services, licensed RMB counts and other parameters; TD warns against treating the estimates as accurate actual patronage. This qualification applies even where `PAX_INDI` is blank. The inspected sources provide no standard errors, confidence intervals, or complete history of survey vintages and estimation formulas. [S5](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf), [S6, note 4](https://www.td.gov.hk/mini_site/atd/2025/en/section5-3.html).

TD's [2016–17 Finance Committee reply THB(T)366](https://www.td.gov.hk/filemanager/en/content_1863/fcq%202016-17%20eng.pdf), PDF page 198, states that 2015 GMB figures were subject to revision upon further verification of operators' annual returns. This supports a reported/operator-return basis, but does not establish that a revision occurred or audit the collection protocol for every study year. MTR and bus figures are published operator statistics without the RMB estimation warning in these tables; their underlying measurement systems were not independently audited. None should be described as an independently verified census of travellers.

### Publication revisions and precision

S6 marks 2024 minibus figures provisional, while the later S7 publication gives different, unflagged 2024 totals. For example, its GMB annual value is **485,330 thousand**, compared with **485,356 thousand** in S6. This is a source-vintage issue requiring reconciliation in Phase 2, not a discovered trend. S7's 2025 minibus figures are provisional; S1's current 2025 indicators are blank. Preserve each publication's status and use the common S1 vintage for the main analysis. Both reference publications warn that rounded components may not sum exactly to displayed totals. Do not force CSV decimal values to equal rounded PDF values without an explicit tolerance.

### Fleet and operating-statistics limitations

GMB/RMB `NO_FLEET` and `PAX_CAP` are complete, positive and unflagged for every month in S3, including 2015–2025. Licensed fleet is an administrative month-end stock, not the number operating each day. A monthly journeys-per-licensed-vehicle ratio is a descriptive proxy, not occupancy or operational productivity; changing carrying capacity also affects interpretation. RMB estimates already use fleet counts, so patronage/fleet associations are not independent evidence of demand effects.

The full S3 file contains 2,627 blank `KM` values, 4,490 blank `KM_CROSS_HARBOUR` values, and 2,209 blank `PAX_CAP` values. `NO_FLEET` has no blanks. For minibuses, GMB `KM` is available, RMB `KM` is blank throughout, and both have blank cross-harbour kilometres. The blank RMB fields establish that a comparable mileage-based GMB/RMB study is unsupported by this source. Missingness is field- and mode-specific.

The wider S3 file also includes zero fleet/subtype values and structurally blank subtype capacities. Most blank capacities belong to bus subtype rows; the remaining case is the NWFB total in June 2023. Historical ferry kilometre values include zeros followed by blanks. These observations do not affect PLB fleet coverage, but prevent a generic rule treating all blanks as missing measurements or all zeros as actual absence of service.

### Comparability and analytical boundaries

The verified window is defensible for a study of **published aggregate journeys under explicit service definitions**, not a perfectly unchanged transport network. MTR routes and cross-boundary services changed; TD notes Intercity Passenger Services were suspended in January 2020 and formally ceased in July 2024. The bus franchise reorganization changes operator-level labels. Broader public transport totals also include estimated taxi figures and changing Tramways counting conventions, so the planned primary share denominator is restricted to PLB + MTR railway services + franchised buses.

Associations, before/after differences and persistent departures from benchmarks cannot establish causes or individual mode switching from these aggregate data alone. Sources do not supply route-level minibus passenger demand, traveller demographics, or quantified RMB estimation uncertainty.

## Access history, reproducibility and reuse

The catalogue and actual annual HTML/PDF tables were accessible. The browsing extractor could not render direct CSVs because of their content type. Initial PowerShell/curl attempts encountered environment networking and Windows certificate-revocation connectivity errors; `curl.exe --ssl-revoke-best-effort` successfully downloaded the files while retaining certificate validation. Thus CSV downloading is verified, not inferred from catalogue descriptions.

An attempted 2026 Annual Transport Digest section 5.3 address was inaccessible through browsing and no verified edition was located. The documented 2025 digest and December 2025 PDF suffice as references; this access result is not a claim that a 2026 publication does not exist.

Downloaded files are byte-preserved in `data/raw/`; they have not been resaved through a CSV parser. The [DATA.GOV.HK Terms and Conditions](https://data.gov.hk/en/terms-and-conditions), version 1.2 dated 26 May 2025 as inspected, permit downloading, reproduction and redistribution subject to their conditions, including clear source acknowledgement and attribution. **Source: Transport Department, HKSAR Government, via DATA.GOV.HK. Government/relevant rights holders retain intellectual property ownership.** The four catalogue CSV resources are retained under these terms. The linked specification PDF is preserved locally but excluded from planned Git publication because its redistribution scope remains unresolved against TD's related-site notice. See [the file-by-file reuse review](data_reuse.md) for the decision and official download/checksum prerequisite. Government materials are outside the original-code license.

### Reproducible download instructions

From the repository root, run the following in PowerShell to download a **new snapshot**. Adjust the directory name to the retrieval date and preserve the Phase 1 files. The URLs are mutable; a future download may have a different revision date, coverage and hash.

```powershell
$ErrorActionPreference = 'Stop'
$snapshotDir = 'data/raw/new_snapshot'
New-Item -ItemType Directory -Path $snapshotDir -Force | Out-Null
$sourceBase = 'https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/'
$sourceFiles = @(
    'table21_eng.csv',
    'table21s_eng.csv',
    'table22_eng.csv',
    'DATA_LAST_REVISION_DATE_eng.csv',
    'mttd_dataspec_eng.pdf'
)
foreach ($sourceFile in $sourceFiles) {
    curl.exe --fail --location --output (Join-Path $snapshotDir $sourceFile) ($sourceBase + $sourceFile)
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $sourceFile" }
}
Get-Content -LiteralPath (Join-Path $snapshotDir 'DATA_LAST_REVISION_DATE_eng.csv')
Get-ChildItem -LiteralPath $snapshotDir -File | Get-FileHash -Algorithm SHA256
```

If Windows curl reports that a certificate-revocation service is unreachable, add `--ssl-revoke-best-effort` to the download command, as used for the successful Phase 1 retrieval. An HTTP/browser error or empty response must be recorded rather than treated as a verified file. Open S6–S9 using their direct links above to inspect the historical reference tables.

### Preserved snapshot checksums

These identify the exact Phase 1 bytes. Row counts exclude headers.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `table21_eng.csv` | 130,116 | `a219225a6000ac73be3d77f40f6266be243bbb751467aaaf9f867ab88c6d09a5` |
| `table21s_eng.csv` | 132,032 | `5d12a79d1953b40705fcf8987756021f98d4cf0388a5f7300bc8bac4e25e873d` |
| `table22_eng.csv` | 319,427 | `9362477f7883fd3bc6d27d8fe9ccd972592b28108c5cfb8608bad555ec1221c7` |
| `DATA_LAST_REVISION_DATE_eng.csv` | 37 | `f90baba66cf2144b5369cb8e1ee2bdcd449260b95d64d8dc82cba21d0c296191` |
| `mttd_dataspec_eng.pdf` | 367,151 | `213f990f1bc2902c190a7f00825a407ad42b00dcdd53fa00cdda1ab49ce028e6` |

## Discovery follow-through and remaining measurement limits

- Aggregates, calendar reconciliation and annual reference comparisons are implemented and validated; the [publication discrepancy investigation](../reports/reference_discrepancies.md) retains the six cross-vintage exceptions.
- Detailed passenger counting/transfer conventions are not fully specified in the inspected dictionary and remain an interpretation limit.
- RMB estimation uncertainty and historical parameter changes remain unquantified; no uncertainty intervals are invented.
- Field-specific missing-value handling and independent source-status flags are implemented in [the cleaning methodology](cleaning_methodology.md).
- Licensed fleet ratios are included as qualified descriptive proxies; estimate/fleet dependency remains visible in reports and the dashboard.
