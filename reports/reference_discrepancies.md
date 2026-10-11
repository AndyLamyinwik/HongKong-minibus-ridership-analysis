# Annual Reference Discrepancy Investigation

Verified on 11 October 2026. This investigation addresses the six comparisons outside the Phase 2 rounding tolerance; it does not replace the preserved source snapshot or constitute an audit of every annual publication.

## Decision and evidence

Retain the internally consistent monthly snapshot, whose recorded dataset revision date is **21 September 2026**, for the 2015–2025 analysis. All six exceptions concern older **provisional** minibus figures. The three 2024 comparisons against the later December 2025 publication agree within rounding. Differences between vintages are therefore consistent with updates to provisional statistics, rather than an aggregation or unit error. The exact administrative or estimation changes behind each revision remain undocumented in the inspected material.

The [official data specification](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/mttd_dataspec_eng.pdf), page 1, explicitly states that newer CSV data may differ from earlier versions because revisions incorporate the latest available figures. Its symbol table defines `#` as provisional and `*` as revised. The specification documents the RMB estimation basis: surveys, licensed fleet counts and other parameters, without regular operator returns. It supplies no quantified uncertainty or detailed revision log.

The [Annual Transport Digest 2025, section 5.3](https://www.td.gov.hk/mini_site/atd/2025/en/section5-3.html) reports 2024 GMB, RMB and PLB figures with `#`. The [December 2025 monthly digest](https://www.td.gov.hk/filemanager/en/content_5378/2512_e.pdf), Table 2.1, printed page 5 / PDF page 14, gives changed 2024 figures without status marks and 2025 figures with `#`. Both use thousands of passenger journeys and the same GMB/RMB/PLB categories. Both warn that displayed components may not sum to displayed totals after rounding.

No inspected note documents a GMB/RMB definition change explaining these six exceptions. The bus franchise merger and MTR service notes concern other categories and do not reconcile the minibus totals. A changed RMB estimation parameter could contribute, but the sources do not identify such an update for these particular observations; it remains a hypothesis.

## Complete comparison table

Values are **thousands of journeys**. Difference = current monthly-snapshot annual sum minus published annual reference. Relative difference = difference / reference × 100. The established annual-reference tolerance is **±0.5 thousand journeys** (±500 journeys), reflecting rounding of an annual figure to a whole thousand; monthly values retain their published decimals.

`ATD 2025` means section 5.3; `Dec 2025` means the December 2025 Table 2.1 PDF. Reference values and indicators are retained in [`config/reference_values.csv`](../config/reference_values.csv); current values and tolerance outcomes also appear in the `cross_vintage_annual_references` diagnostic in [`validation_summary.json`](../data/processed/validation_summary.json).

| Publication | Year | Mode | Reference | Reference flag | Current sum | Difference | Difference (%) | Tolerance | Assessment |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| ATD 2025 | 2024 | GMB | 485,356 | `#` | 485,329.687 | −26.313 | −0.005421 | Outside | R24 |
| ATD 2025 | 2024 | RMB | 53,492 | `#` | 53,489.623 | −2.377 | −0.004444 | Outside | R24 |
| ATD 2025 | 2024 | PLB | 538,848 | `#` | 538,819.310 | −28.690 | −0.005324 | Outside | R24 |
| Dec 2025 | 2024 | GMB | 485,330 | blank | 485,329.687 | −0.313 | −0.000064 | Within | Rounding |
| Dec 2025 | 2024 | RMB | 53,490 | blank | 53,489.623 | −0.377 | −0.000705 | Within | Rounding |
| Dec 2025 | 2024 | PLB | 538,819 | blank | 538,819.310 | +0.310 | +0.000058 | Within | Rounding |
| Dec 2025 | 2025 | GMB | 496,112 | `#` | 495,802.414 | −309.586 | −0.062402 | Outside | R25 |
| Dec 2025 | 2025 | RMB | 50,773 | `#` | 50,742.718 | −30.282 | −0.059642 | Outside | R25 |
| Dec 2025 | 2025 | PLB | 546,886 | `#` | 546,545.132 | −340.868 | −0.062329 | Outside | R25 |

All contributing GMB/RMB source indicators in the selected current 2015–2025 snapshot are blank; derived PLB indicators are also blank. The current data carry neither `#` nor `*` for these observations. A blank mark means no explicit status flag, not that a value is final or was never revised. RMB remains estimated and PLB contains an estimated component regardless of the flag.

### R24: each 2024 ATD exception

For GMB, the annual published value changes from 485,356 provisional to 485,330 unflagged in the later digest; for RMB, from 53,492 provisional to 53,490 unflagged; for PLB, from 538,848 provisional to 538,819 unflagged. Each later value agrees with the current snapshot within the stated annual rounding tolerance. These are documented value/status changes across publications. The inference is that updates to provisional data explain the earlier discrepancy; a case-specific revision reason is not supplied.

The October 2024 row provides additional localization. ATD reports GMB **43,004**, RMB **4,666** and PLB **47,670**, all provisional. The December publication reports **42,978**, **4,663** and **47,642**, respectively, without flags; current values are **42,978.297**, **4,663.264** and **47,641.561**. This month is consistent with the size and direction of the annual update. Rounded monthly rows cannot establish its exact contribution to the annual difference, so it is not claimed as a complete accounting reconciliation. [ATD table](https://www.td.gov.hk/mini_site/atd/2025/en/section5-3.html), [December Table 2.1](https://www.td.gov.hk/filemanager/en/content_5378/2512_e.pdf).

### R25: each 2025 December-publication exception

GMB is 309.586 thousand lower in the current snapshot, RMB 30.282 thousand lower, and PLB 340.868 thousand lower than the provisional annual references. The differences exceed rounding but are each less than 0.063% of the reference. The same category labels, units and RMB estimation qualification are present in the official source. Publication revision is the best-supported interpretation given the general revision policy and changed provisional values; the specific cause, revision dates by row and source of each adjustment remain unresolved.

The changes are not confined to a single rounding adjustment. For example, December 2025 GMB changes from **42,891 provisional** to **42,416.688**, a difference of **−474.312 thousand** (−1.106%); RMB changes from **4,270 provisional** to **4,222.744**, **−47.256 thousand** (−1.107%). In contrast, current GMB is higher than the old rounded monthly values in April, October and November by **48.587**, **54.401** and **92.948 thousand**, respectively. These offsets explain why the annual discrepancy is smaller than December's discrepancy. This establishes changed monthly values, not an underlying mechanism. [December 2025 Table 2.1, printed page 5](https://www.td.gov.hk/filemanager/en/content_5378/2512_e.pdf).

## Materiality and sensitivity

Materiality here means whether replacing the endpoint with the older provisional annual reference would change the direction or practical magnitude of the main descriptive conclusion. It is not a statistical significance test or a claim about total measurement uncertainty. These are isolated endpoint sensitivity calculations; no alternative monthly series is constructed or substituted.

For each mode below, hold the **current-snapshot 2015 and 2019 baselines** fixed, then replace only the 2025 numerator with the December 2025 annual reference. The 2015–2025 change is `100 × (2025 / 2015 − 1)`. Recovery is `100 × 2025 / 2019`, with 100% indicating the 2019 annual journey total.

| Mode | Current 2015–2025 change (%) | Older 2025 endpoint change (%) | Difference (percentage points) | Current 2019 recovery (%) | Older 2025 endpoint recovery (%) | Difference (percentage points) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GMB | −11.174 | −11.119 | +0.055464 | 91.879 | 91.936 | +0.057370 |
| RMB | −58.004 | −57.979 | +0.025062 | 49.184 | 49.213 | +0.029352 |
| PLB | −19.508 | −19.457 | +0.050201 | 85.026 | 85.079 | +0.053029 |

These changes do not reverse any endpoint decline or the ranking of GMB versus RMB recovery. The largest shift in the decade-change metric is 0.055464 percentage points; the largest recovery shift is 0.057370 points. Holding current 2024 totals fixed, using the old 2025 endpoints would change GMB 2025 growth from **+2.158% to +2.222%**, RMB from **−5.135% to −5.079%**, and PLB from **+1.434% to +1.497%**. None changes sign.

For the comparison-group share, preserve current 2025 MTR (**1,899,839.725 thousand**) and franchised bus (**1,369,197.693 thousand**) totals, and substitute the old GMB/RMB endpoints as a pair. Use their sum **546,885 thousand** rather than the separately rounded PLB reference of 546,886, so the counterfactual composition remains internally additive. PLB share would change from **14.324029% to 14.331659%**, a **+0.007631 percentage-point** shift. This group consists only of GMB + RMB + MTR railway services + franchised buses; PLB is not added again. The share conclusion is insensitive to these particular endpoint discrepancies.

The annual exceptions are small for the major endpoint comparisons, but a roughly 1.1% December monthly difference is relevant to precise monthly growth or within-year pattern interpretation. Use the selected vintage consistently for seasonality, troughs and monthly comparisons. No uncertainty interval is inferred from these observed cross-vintage differences: RMB survey/model uncertainty may be substantially different and is not quantified in the sources.

## Reproducible calculations and trace

The Phase 2 diagnostic is generated by `check_annual_references` in [`src/hk_minibus/pipeline.py`](../src/hk_minibus/pipeline.py), using twelve monthly records for each year/mode and decimal arithmetic. The analytical values remain traceable through SQLite's `passenger_lineage` and `passenger_source_records` tables to physical rows and numeric tokens in the preserved Table 2.1 CSV. See the [data dictionary](../docs/data_dictionary.md) for those identifiers.

Run the following Python code from the repository root to reproduce the annual table and endpoint sensitivity. It reads existing files only. `Decimal` preserves the published decimal tokens in these calculations.

```python
import csv
from decimal import Decimal
from pathlib import Path

root = Path('.')
with (root / 'data/processed/monthly_passenger_journeys.csv').open(
    encoding='utf-8', newline=''
) as handle:
    monthly = list(csv.DictReader(handle))
with (root / 'config/reference_values.csv').open(
    encoding='utf-8', newline=''
) as handle:
    references = list(csv.DictReader(handle))

annual = {}
for row in monthly:
    key = (row['month'][:4], row['mode'])
    annual[key] = annual.get(key, Decimal(0)) + Decimal(
        row['passenger_journeys_thousands']
    )

for row in references:
    current = annual[(row['year'], row['mode'])]
    reference = Decimal(row['passenger_journeys_thousands'])
    difference = current - reference
    print(row['publication'], row['year'], row['mode'],
          reference, row['source_indicator'], current, difference,
          100 * difference / reference,
          abs(difference) <= Decimal('0.5'))

for mode in ('GMB', 'RMB', 'PLB'):
    current = annual[('2025', mode)]
    older = next(Decimal(row['passenger_journeys_thousands'])
                 for row in references
                 if row['year'] == '2025' and row['mode'] == mode)
    for year in ('2015', '2019', '2024'):
        baseline = annual[(year, mode)]
        offset = Decimal(0) if year == '2019' else Decimal(100)
        print(mode, year,
              100 * current / baseline - offset,
              100 * older / baseline - offset,
              100 * (older - current) / baseline)

other = annual[('2025', 'MTR')] + annual[('2025', 'FRANCHISED_BUS')]
current_plb = annual[('2025', 'GMB')] + annual[('2025', 'RMB')]
older_plb = sum(Decimal(row['passenger_journeys_thousands'])
                for row in references
                if row['year'] == '2025' and row['mode'] in ('GMB', 'RMB'))
current_share = 100 * current_plb / (current_plb + other)
older_share = 100 * older_plb / (older_plb + other)
print('PLB comparison-group share', current_share, older_share,
      older_share - current_share)

# Additional monthly evidence transcribed from the linked official tables.
# These constants are reference values only; they do not alter observations.
monthly_references = {
    ('2024-10-01', 'GMB'): 43004,
    ('2024-10-01', 'RMB'): 4666,
    ('2024-10-01', 'PLB'): 47670,
    ('2025-04-01', 'GMB'): 39501,
    ('2025-10-01', 'GMB'): 43681,
    ('2025-11-01', 'GMB'): 42462,
    ('2025-12-01', 'GMB'): 42891,
    ('2025-12-01', 'RMB'): 4270,
}
for row in monthly:
    key = (row['month'], row['mode'])
    if key in monthly_references:
        current = Decimal(row['passenger_journeys_thousands'])
        reference = Decimal(monthly_references[key])
        print(key, reference, current, current - reference,
              100 * (current - reference) / reference)
```

The inspected official pages do not provide a complete change log, historic RMB parameter sets or uncertainty estimates. Retain the warning and publication flags in the research record, qualify the revision explanation as an inference, and revisit precise month-level claims if a later documented revision history becomes available.
