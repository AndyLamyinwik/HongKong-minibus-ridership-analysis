# Portfolio illustrations

These previews contain real outputs from the preserved 2015–2025 study.

| Asset | Origin and caption |
| --- | --- |
| `dashboard_overview.jpg` | Unedited browser capture of the running Executive Overview on 11 October 2026. The four KPIs and annual GMB/RMB index chart use the included analytical tables; the main content is slightly scrolled to show the chart legend. |
| `annual_minibus_ridership.png` | Byte-identical copy of `analysis/figures/02_annual_minibus_ridership.png`. Annual passenger journeys show the scale and differing paths of GMB and estimated RMB; PLB is their overlapping subtotal. |
| `recovery_2019_baseline.png` | Byte-identical copy of `analysis/figures/04_recovery_2019_baseline.png`. Each mode is compared with its own full-year 2019 journey total; 100 is a benchmark, not a maximum. |
| `comparison_group_share.png` | Byte-identical copy of `analysis/figures/05_comparison_group_market_share.png`. The denominator is GMB + RMB + MTR railway services + franchised buses; PLB is not counted twice. |

**Data source: Transport Department, HKSAR Government, via DATA.GOV.HK.**
The Government and relevant rights holders retain intellectual property rights in
the source data. [DATA.GOV.HK reuse terms](https://data.gov.hk/en/terms-and-conditions)
and [the repository's third-party/data notice](../THIRD_PARTY_NOTICES.md) accompany
these illustrations. RMB passenger volumes remain estimates; the figures describe
aggregate published journeys and do not identify causes or individual mode switching.

The analytical PNGs can be reproduced with `python scripts/analyze_data.py` after
the [official specification download/checksum prerequisite](../docs/data_reuse.md).
The screenshot can be refreshed by starting `dashboard/app.py`, selecting Executive
Overview and its default index view, and capturing the actual rendered application.
