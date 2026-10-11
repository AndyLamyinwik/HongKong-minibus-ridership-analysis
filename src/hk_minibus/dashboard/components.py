"""Shared presentation components for the historical transport dashboard."""

from pathlib import Path

import pandas as pd
import streamlit as st

from .data import DashboardData
from .metrics import MODE_LABELS


CATALOGUE = "https://data.gov.hk/en-data/dataset/hk-td-tis_17-monthly-traffic-and-transport-digest-csv"
TD_BASE = "https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/"


def apply_style() -> None:
    """Keep the native accessible controls while refining the page hierarchy."""
    st.markdown(
        """<style>
        .block-container {max-width: 1320px; padding-top: 3.8rem; padding-bottom: 3rem;}
        h1 {letter-spacing: -0.035em; line-height: 1.12;}
        h2, h3 {letter-spacing: -0.02em;}
        [data-testid="stMetricValue"] {font-variant-numeric: tabular-nums;}
        [data-testid="stMetric"] {background: #F8FAFB;}
        [data-testid="stMetricLabel"] {height: auto; min-height: 2.5rem;}
        [data-testid="stMetricLabel"] div, [data-testid="stMetricLabel"] p {
            white-space: normal; overflow: visible; text-overflow: clip;
        }
        [data-testid="stSidebar"] {border-right: 1px solid #E1E8EC;}
        @media (min-width: 641px) and (max-width: 1100px) {
            [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
                flex-wrap: wrap;
            }
            [data-testid="stColumn"]:has([data-testid="stMetric"]) {
                flex: 1 1 calc(50% - 1rem) !important;
                width: calc(50% - 1rem) !important;
                min-width: calc(50% - 1rem) !important;
            }
        }
        @media (max-width: 640px) {
            .block-container {padding-left: 1rem; padding-right: 1rem;}
            h1 {font-size: 2rem;}
        }
        </style>""",
        unsafe_allow_html=True,
    )


def page_header(number: str, title: str, question: str) -> None:
    st.caption(f"HONG KONG TRANSPORT STUDY  /  {number} OF 05  /  2015–2025")
    st.title(title)
    st.markdown(f"**{question}**")


def plot(figure, key: str) -> None:
    st.plotly_chart(
        figure,
        width="stretch",
        theme=None,
        key=key,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": False,
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )


def finding(title: str, evidence: str, interpretation: str) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.markdown(evidence)
        st.caption(interpretation)


def source_note(table: str, caveat: str = "") -> None:
    st.caption(
        f"Source: Transport Department, HKSAR Government · analytical table: {table}. "
        + caveat
    )


def mode_picker(key: str, options: tuple[str, ...], defaults: tuple[str, ...]) -> list[str]:
    return st.multiselect(
        "Transport modes",
        options=options,
        default=list(defaults),
        format_func=lambda mode: MODE_LABELS[mode],
        key=key,
    )


def export_table(frame: pd.DataFrame, label: str, filename: str, key: str) -> None:
    """Export the selected source rows with their original field names and units."""
    st.download_button(
        label,
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def methodology(data: DashboardData, root: Path) -> None:
    st.divider()
    metadata = data.metadata
    st.caption(
        "Historical scope: January 2015–December 2025 · 132 months per mode · "
        f"Snapshot retrieved {metadata.get('snapshot_retrieved_on', 'see source manifest')} · "
        f"Dataset revision {metadata.get('expected_revision_date', 'see source manifest')}"
    )
    with st.expander("Sources & methodology"):
        st.markdown(
            f"""### Official sources

Published by the **Transport Department, HKSAR Government**, through the
[Monthly Traffic and Transport Digest catalogue on DATA.GOV.HK]({CATALOGUE}).
The Government and relevant rights holders retain intellectual property rights in the source data.
The dashboard reads the
preserved, validated local historical tables used in the research report.

- [Table 2.1 — monthly passenger journeys]({TD_BASE}table21_eng.csv)
- [Table 2.1S — monthly average daily passenger journeys]({TD_BASE}table21s_eng.csv)
- [Table 2.2 — public light bus licensed stock and capacity]({TD_BASE}table22_eng.csv)
- [Official data specification]({TD_BASE}mttd_dataspec_eng.pdf)
- [Reuse terms and government attribution]({"https://data.gov.hk/en/terms-and-conditions"})

Official download links may now contain a later revision. The local snapshot dates above identify
the vintage used throughout this study.

### Service boundaries

**GMB** means Green Minibuses; **RMB** means Red Minibuses; **PLB** is their combined
public light bus journey total. Journeys count passenger trips, rather than unique people.
RMB passenger volumes are **estimates**, based on surveys and licensed fleet information;
confidence intervals and a complete estimation-parameter history are unavailable. PLB and
all comparison-group denominators include this estimated component. Blank source status
flags do not establish that a figure is observed or that it has never been revised.

**MTR railway services** combine MTR Lines, Airport Express and Light Rail. MTR Lines
include cross-boundary services. Hong Kong Tramways and MTR buses are excluded. Service
coverage changed over the period, so this is a published-series comparison rather than a
constant-network comparison. **Franchised buses** include each applicable franchise once;
the preparation accounts for the July 2023 Citybus/NWFB merger.

### Metrics and display units

- **Journey totals:** existing monthly totals or complete-year sums; source thousands are
  divided by 1,000 for display in millions. Monthly totals and annual totals are separate views.
- **Endpoint percentage change:** 100 × (end annual journeys / start annual journeys − 1).
- **Annual trend index:** 100 × annual journeys / the same mode's 2015 annual journeys.
- **Monthly trend index:** 100 × the average daily journeys in a month / the same mode's
  average daily journeys in the same calendar month of 2015. Each 2015 month equals 100.
  Baselines remain fixed when the displayed year range changes.
- **Recovery:** 100 × annual journeys / the same mode's 2019 annual journeys. The headline
  compares complete years 2025 and 2019. A value above 100% exceeds the benchmark.
- **Share within selected public transport modes:** 100 × journeys /
  (GMB + RMB + MTR railway services + franchised buses). The four components sum to 100%;
  PLB is their GMB/RMB subtotal. Annual shares divide annual totals rather than averaging
  monthly percentages. This denominator does not cover all Hong Kong public transport.
- **Minibus composition:** GMB or RMB journeys / PLB journeys × 100.
- **Monthly fleet indicator:** average daily journeys × 1,000 / month-end licensed vehicles.
  **Annual fleet indicator:** annual journeys × 1,000 /
  Σ(month-end licensed vehicles × days in month), expressed as journeys per licensed
  vehicle-day proxy. Annual stock charts show **December** licensed vehicles. They do not
  show the arithmetic mean or daily deployment.
- **Percentage points (pp):** the difference between two percentages; distinct from
  percentage change. Values are rounded only for display.

### Interpretation and revisions

The timing labels 2015–2019, 2020–2022 and 2023–2025 are descriptive. Recovery ratios and
aggregate shares do not identify causes or individual mode switching. Licensed stock does
not measure daily deployed vehicles, occupancy, utilization or operational productivity;
RMB estimation already uses fleet information, so the passenger/fleet relationship is partly
mechanical.

Older provisional annual publications differ from current monthly sums. The research retains
one consistent snapshot; publication updates are the best-supported explanation, while
specific revision reasons remain unresolved. The documented annual endpoint sensitivity
does not quantify RMB estimation uncertainty. See the included research and discrepancy
reports for the evidence and the alternative 2015–2018 recovery benchmark.
"""
        )
        for filename, label, key in (
            ("eda_findings.md", "Download the research findings", "download_findings"),
            ("reference_discrepancies.md", "Download the revision investigation", "download_revisions"),
        ):
            path = root / "reports" / filename
            if path.is_file():
                st.download_button(label, path.read_bytes(), filename, "text/markdown", key=key)
