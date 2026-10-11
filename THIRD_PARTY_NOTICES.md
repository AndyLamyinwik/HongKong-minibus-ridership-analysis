# Code license, data terms and third-party notices

## Original code

The [MIT license](LICENSE) applies to original Python and SQL code, scripts,
tests, project configuration and associated software documentation. It does not license government source files,
the SQLite database, processed or analytical datasets, or government-derived
factual values displayed in reports, figures and screenshots. Original narrative
and visual presentation do not transfer ownership of the underlying data.

## Government data and derived outputs

**Source: Transport Department, Government of the Hong Kong Special Administrative
Region, via DATA.GOV.HK. The Government and relevant rights holders retain
intellectual property rights in the source data.**

The four included raw CSV resources and their derived factual values are used
subject to the [DATA.GOV.HK Terms and Conditions](https://data.gov.hk/en/terms-and-conditions),
including source acknowledgement, intellectual property ownership acknowledgement
and attribution to the publisher, Government and DATA.GOV.HK. The portal's
[FAQ](https://data.gov.hk/en/faq) additionally excludes resale of the data.
These conditions are separate from MIT; no Creative Commons license or external
dataset ownership is asserted. Data are supplied by their publisher without a
warranty; estimates, revisions and service-definition limits remain applicable.

This notice accompanies the copies in `data/`, `analysis/`, `reports/` and `assets/`.
When redistributing a dataset, CSV export, report or figure separately, carry this
source acknowledgement, the terms link and the relevant measurement caveats with it.
The research is an independent analysis and does not imply Government endorsement.

The official specification PDF is preserved locally for source verification but
excluded from future Git publication while its redistribution scope remains
unresolved. Annual Transport Digest pages and other government PDFs are linked,
rather than rehosted. The file-by-file decision and official download/checksum
instructions are in [the data reuse review](docs/data_reuse.md).

## Software and fonts

Dependencies are installed from their package distributions; neither a virtual
environment nor third-party source or font files are included in the publication
set. Each dependency retains its own license and packaged notices. Direct tools
include pandas and NumPy (BSD-family licensing with additional packaged component
notices), Streamlit (Apache-2.0), Plotly and pytest (MIT), and Matplotlib (its
project license and bundled component/font notices). Installing pinned packages
preserves those upstream notices; the project's MIT license does not replace them.

Research PNGs were rendered by the original Matplotlib code using its packaged
fonts, including DejaVu Sans. They contain rendered pixels rather than redistributed
font software. Dashboard screenshots capture the actual Streamlit/Plotly application;
no government logos, stock photography or separately downloaded icon assets were
introduced. See upstream [pandas licensing](https://github.com/pandas-dev/pandas/blob/main/LICENSE),
[NumPy licensing](https://github.com/numpy/numpy/blob/main/LICENSE.txt),
[Streamlit licensing](https://github.com/streamlit/streamlit/blob/develop/LICENSE),
[Plotly licensing](https://github.com/plotly/plotly.py/blob/master/LICENSE.txt),
[Matplotlib license and notices](https://matplotlib.org/stable/project/license.html)
and [pytest licensing](https://github.com/pytest-dev/pytest/blob/main/LICENSE).
