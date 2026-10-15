# Hong Kong Minibus Ridership: A Decade in Transition

**Language / 語言 / 语言:** [English](#english) · [繁體中文](#traditional-chinese) · [简体中文](#simplified-chinese)

<a id="english"></a>

**One Industry, Two Different Futures.** A historical transport analytics study, 2015–2025.

**[Explore the Interactive Research Website](https://andylamyinwik.github.io/HongKong-minibus-ridership-analysis/)**

Read the complete research through interactive annual trends, recovery comparisons, transport shares and fleet context. The publication is hosted on GitHub Pages, with visible methodology, source links and estimation qualifications.

**Using the website:** open the link above in your browser, choose **English / 繁體中文** at the top, then explore the chapters using the year selectors, transport-mode controls and chart views. Tooltips and expandable data tables provide exact values. Read **Methodology & sources** for definitions and interpretation limits. No installation is needed to browse the published website.

Hong Kong's Green and Red Minibuses share an industry headline but follow different passenger-demand trajectories. This project examines eleven complete years of official transport statistics to distinguish long-term change, disruption-period patterns and subsequent recovery, with MTR railway services and franchised buses as comparators.

The study connects source verification, Python preparation, a constrained SQLite model, independent SQL/Pandas calculations and the interactive research website. A separate Streamlit implementation presents the same analytical tables. The research shows why transport planning and industry discussion benefit from examining the two minibus categories separately. Findings describe published aggregate journeys; Red Minibus (RMB) volumes are estimates.

## Research questions

- How did Green Minibus (GMB), RMB and combined Public Light Bus (PLB) journeys change over the decade?
- Did the categories differ before, during and after 2020–2022, and how far did demand recover against pre-pandemic benchmarks?
- How did minibus composition and passenger shares within a defined transport comparison group change?
- What do calendar-month patterns and licensed fleet stock add to the historical picture?

The [research plan](docs/project_plan.md) specifies seven questions and their interpretation limits.

## Five findings

| Finding | Verified evidence |
| --- | --- |
| **The industry total was lower in 2025.** | Annual PLB journeys changed **−19.51%**, from **679.001 million** in 2015 to **546.545 million** in 2025. |
| **Green and Red Minibuses followed different paths.** | GMB annual journeys changed **−11.17%**, while estimated RMB journeys changed **−58.00%** between 2015 and 2025. |
| **RMB remained well below its 2019 benchmark.** | Its 2025 annual journeys were **49.18%** of its 2019 level; GMB reached **91.88%** of its own benchmark. |
| **GMB accounted for more of minibus patronage.** | GMB represented **90.72%** of PLB journeys in 2025, compared with **82.21%** in 2015. |
| **PLB's comparison-group share was smaller.** | Its share changed from **16.99% to 14.32%**, a reduction of **2.67 percentage points**, within PLB + MTR railway services + franchised buses. |

These claims trace to the unrounded [endpoint table](analysis/outputs/endpoint_comparison.csv), [minibus composition](analysis/outputs/annual_minibus_composition.csv) and [comparison-group shares](analysis/outputs/annual_market_share.csv). Read the [findings report](reports/eda_findings.md) for subperiods, alternative benchmarks and fleet context. These comparisons do not establish causes or individual passenger switching.

## Streamlit implementation preview

![Executive overview of the functioning dashboard, with four verified KPIs and annual GMB/RMB indices](assets/dashboard_overview.jpg)

*Actual application capture. Each mode's annual index uses its own 2015 total; shading marks 2020–2022. RMB is estimated. Five sections explore the overview, trends, recovery, shares and fleet context.*

<details>
<summary>Explore three research figures</summary>

![Annual GMB, estimated RMB and combined PLB passenger journeys](assets/annual_minibus_ridership.png)

*Complete-year totals show both scale and direction. PLB is GMB + RMB, so these are overlapping series.*

![Annual recovery indices for minibuses, MTR railway services and franchised buses](assets/recovery_2019_baseline.png)

*Recovery uses each mode's full-year 2019 journey total. A value above 100 exceeds that benchmark.*

![Passenger shares within the specified transport comparison group](assets/comparison_group_share.png)

*The denominator is GMB + RMB + MTR railway services + franchised buses. The separate minibus panel uses a zero-based scale; PLB is not counted twice.*

</details>

All previews use the verified research outputs. **Data source: Transport Department, HKSAR Government, via DATA.GOV.HK.** Government and relevant rights holders retain intellectual property rights in source data. [Reuse terms](https://data.gov.hk/en/terms-and-conditions), [asset provenance](assets/README.md).

## Stack and analytical workflow

**Python 3.12 · pandas · SQLite/SQL · Matplotlib · Streamlit · Plotly · pytest**

**Research website: HTML/CSS/JavaScript · Apache ECharts · Vite · GitHub Pages**

1. **Verify sources:** preserve official CSV bytes and record coverage, revision dates, schemas and SHA-256 hashes.
2. **Prepare:** parse dates and status flags, map service components, retain RMB estimation metadata and build separate monthly-total, daily-rate and fleet tables with lineage.
3. **Validate:** check keys, coverage, units, calendar reconciliation, aggregation identities and annual publication discrepancies before replacing outputs.
4. **Analyze:** calculate complete-year trends, growth, composition, recovery and fleet proxies; cross-check six independent SQL queries against Pandas.
5. **Present:** generate seven research figures, a five-section Streamlit dashboard and a static editorial website that reuse the validated analytical outputs.

The [cleaning methodology](docs/cleaning_methodology.md), [data dictionary](docs/data_dictionary.md), [analytical methods](docs/analysis_methodology.md) and [SQL examples using CTEs and window functions](sql/analysis/README.md) explain the implementation. The [portfolio validation record](docs/portfolio_validation.md) and [fresh-environment reproduction check](docs/reproducibility_check.md) document quality assurance.

## Official data

Publisher: **Transport Department, Government of the Hong Kong Special Administrative Region**, through the [Monthly Traffic and Transport Digest catalogue on DATA.GOV.HK](https://data.gov.hk/en-data/dataset/hk-td-tis_17-monthly-traffic-and-transport-digest-csv).

| Resource | Measurement |
| --- | --- |
| [Table 2.1](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table21_eng.csv) | Monthly passenger journeys, thousands |
| [Table 2.1S](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table21s_eng.csv) | Average daily passenger journeys, thousands per day |
| [Table 2.2](https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table22_eng.csv) | Month-end licensed minibus vehicles/capacity and available mileage |

The preserved snapshot was retrieved **11 October 2026**, with official revision date **21 September 2026**. Source coverage is January 2013–July 2026; analysis consistently selects **January 2015–December 2025: 132 months and 11 complete years**. Annual digest publications are separate validation references, rather than replacement observations. [Inventory, reference URLs and checksums](docs/data_sources.md).

## Project structure

```text
├── site/                     # Published research website, static export and frontend tests
├── .github/workflows/        # Tested build and GitHub Pages deployment
├── dashboard/app.py          # Streamlit entry point
├── src/hk_minibus/           # Preparation, analysis, figures and dashboard modules
├── scripts/                  # Preparation and analytical runners
├── sql/                      # SQLite schema/views and six analytical queries
├── config/                   # Fixed snapshot manifest and annual reference values
├── data/raw/                 # Four official CSVs; specification PDF stays local
├── data/processed/           # Validated CSVs, SQLite database and quality records
├── analysis/outputs/         # Analytical tables, SQL exports and check summary
├── analysis/figures/         # Seven reproducible research PNGs
├── reports/                  # Findings and publication-vintage investigation
├── docs/                     # Definitions, provenance, validation and release guide
├── assets/                   # Genuine dashboard preview and selected figures
└── tests/                    # Preparation, SQL parity, metrics, charts and app tests
```

Root files include pinned `requirements.txt`, `pyproject.toml`, `LICENSE`, `THIRD_PARTY_NOTICES.md` and `.gitignore`; `.streamlit/config.toml` sets the dashboard theme. Included outputs let reviewers run the dashboard immediately. [Website source, metrics and local instructions](site/README.md); [deployment and verification record](docs/website_deployment.md).

## Run locally

For the website, use Node.js **24.19.0** and pnpm **11.25.0**. From the repository root:

```bash
cd site
pnpm install --frozen-lockfile
pnpm dev
```

Open [the local research website](http://127.0.0.1:5173/HongKong-minibus-ridership-analysis/). Website tests and build instructions are in [site/README.md](site/README.md).

For the separate Streamlit implementation, start from the repository root.

**Python 3.12 is the verified runtime.** Run from the repository root:

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on macOS/Linux or `.\.venv\Scripts\Activate.ps1` in Windows PowerShell. Then:

```bash
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

Open [localhost:8501](http://localhost:8501). If PowerShell activation is restricted, replace `python` with `.\.venv\Scripts\python.exe`. [Dashboard controls and metric definitions](docs/dashboard.md).

## Reproduce and test

**Before full reproduction or the complete test suite after cloning**, download the official specification PDF and verify its pinned SHA-256 using [these exact instructions](docs/data_reuse.md#download-the-dictionary-for-full-local-reproduction). It is retained locally but excluded from Git publication because redistribution permission is unresolved. The dashboard uses the included analytical outputs without this download; the pipelines and their tests verify all five original source files.

With that prerequisite satisfied:

```bash
python scripts/prepare_data.py
python scripts/analyze_data.py
```

The analytical runner executes all six SQL queries and checks their results against Pandas. For independent read-only query inspection, see [the SQL run instructions](sql/analysis/README.md). Run the complete software suite separately:

```bash
python -m pytest -q --basetemp analysis/.pytest-tmp-review -p no:cacheprovider
```

The named test directory is disposable; pytest replaces it. A fresh Windows/Python 3.12 environment reproduced the CSVs, SQLite contents and figures. Local socket permission is required for Streamlit's app tests. The website's GitHub Actions build verifies frontend and standard-library exporter checks on Ubuntu. Full Python/Streamlit Linux execution and Community Cloud deployment remain separate, unverified milestones in the [publication and deployment plan](docs/publication_plan.md).

## Interpretation and reuse

- **RMB is estimated:** surveys, licensed fleet counts and other parameters underpin its passenger series; quantified uncertainty is unavailable. PLB incorporates these estimates.
- **Shares have a limited denominator:** PLB + MTR railway services + franchised buses is a comparison group, rather than all Hong Kong public transport or unique travellers.
- **Service boundaries change:** MTR comprises MTR Lines, Airport Express and Light Rail, including cross-boundary services within MTR Lines. Tramways and MTR buses are excluded. Applicable bus franchises are counted once across the 2023 merger.
- **Publication vintages differ:** older provisional annual totals disagree with some current monthly sums. The [discrepancy investigation](reports/reference_discrepancies.md) retains the exceptions; revision sensitivity does not measure RMB estimation uncertainty.
- **Fleet ratios are proxies:** licensed month-end stock is not daily deployment. Journeys per licensed vehicle-day do not measure occupancy or productivity, and RMB estimation already uses fleet information.
- **Period comparisons are descriptive:** COVID-19 timing, recovery ratios and aggregate associations do not identify causal effects.

Original project code is [MIT licensed](LICENSE). Government source materials and derived factual values retain separate [reuse conditions and attribution](docs/data_reuse.md), documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No external dataset ownership or Government endorsement is claimed. The four raw CSVs accompany the project; the specification PDF and linked annual publications are not rehosted in the publication set.

---

<a id="traditional-chinese"></a>

## 繁體中文簡介

### 這個項目研究甚麼？

本項目利用香港運輸署的官方統計，研究 **2015–2025 年專線小巴（GMB）與紅色小巴（RMB）的乘客旅次變化**，並與港鐵鐵路服務及專營巴士比較。分析涵蓋 **11 個完整年份、132 個月**，結合 Python 資料處理、SQLite／SQL 驗證及互動視覺化，探索長期趨勢、受衝擊時期的變化、需求復甦與車隊背景。

### 網站入口與使用方式

**[開啟互動研究網站（繁體中文）](https://andylamyinwik.github.io/HongKong-minibus-ridership-analysis/?lang=zh-Hant)** · [開啟英文版](https://andylamyinwik.github.io/HongKong-minibus-ridership-analysis/?lang=en)

網站可直接在瀏覽器使用，毋須安裝軟件。

1. **選擇語言：** 在網站頂部切換 **English / 繁體中文**；瀏覽器允許儲存時，網站會記住你的選擇。
2. **瀏覽研究章節：** 從首頁重點開始，向下查看年度趨勢、復甦比較、交通比較組別佔比，以及車隊與乘客需求。
3. **互動查看數據：** 使用年份選單、交通模式及圖表視圖選項進行比較；透過圖表提示或展開資料表查看數值。切換語言會保留已選的圖表設定。
4. **了解定義與限制：** 閱讀「研究方法與資料來源」。年度趨勢指數以各服務自身的 **2015 年旅次 = 100**；復甦比較則以各服務自身的 **2019 年旅次 = 100%**，兩者基準不同。

**解讀提醒：** 紅色小巴旅次屬估算，公共小巴總數也包含這部分估算。交通佔比只涵蓋公共小巴、港鐵鐵路服務與專營巴士的指定比較組別，並非全港公共交通市場。研究描述歷史變化，不能據此確定因果或個別乘客轉用交通模式。

### 完整報告、程式碼與本機執行

- [完整研究結果（英文）](reports/eda_findings.md) · [官方資料來源與品質說明（英文）](docs/data_sources.md)
- [本機執行方式（英文）](#run-locally)：包含研究網站與另一個 Streamlit 本機版本的安裝及啟動指令。
- [研究網站開發說明（英文）](site/README.md) · [Streamlit 使用說明（英文）](docs/dashboard.md)；Streamlit 程式入口為 [`dashboard/app.py`](dashboard/app.py)。

[返回英文介紹](#english) · [查看简体中文简介](#simplified-chinese)

---

<a id="simplified-chinese"></a>

## 简体中文简介

### 这个项目研究什么？

本项目利用香港运输署的官方统计，研究 **2015–2025 年专线小巴（GMB）与红色小巴（RMB）的乘客旅次变化**，并与港铁铁路服务及专营巴士比较。分析覆盖 **11 个完整年份、132 个月**，结合 Python 数据处理、SQLite／SQL 验证及交互式可视化，探索长期趋势、受冲击时期的变化、需求恢复与车队背景。

### 网站入口与使用方法

**[打开交互研究网站（繁体中文界面）](https://andylamyinwik.github.io/HongKong-minibus-ridership-analysis/?lang=zh-Hant)** · [打开英文版](https://andylamyinwik.github.io/HongKong-minibus-ridership-analysis/?lang=en)

网站可直接在浏览器使用，无需安装软件。**网站目前提供英语和繁体中文界面；本节为简体中文使用说明。**

1. **选择语言：** 在网站顶部切换 **English / 繁體中文**；浏览器允许存储时，网站会记住你的选择。
2. **浏览研究章节：** 从首页重点开始，向下查看年度趋势、恢复比较、交通比较组别占比，以及车队与乘客需求。
3. **交互查看数据：** 使用年份菜单、交通方式及图表视图选项进行比较；通过图表提示或展开数据表查看数值。切换语言会保留已选的图表设置。
4. **了解定义与限制：** 阅读「研究方法与资料来源」。年度趋势指数以各服务自身的 **2015 年旅次 = 100**；恢复比较则以各服务自身的 **2019 年旅次 = 100%**，两者基准不同。

**解读提醒：** 红色小巴旅次为估算，公共小巴合计也包含这部分估算。交通占比仅覆盖公共小巴、港铁铁路服务与专营巴士的指定比较组别，并非全港公共交通市场。研究描述历史变化，不能据此确定因果或个别乘客改用其他交通方式。

### 完整报告、代码与本地运行

- [完整研究结果（英文）](reports/eda_findings.md) · [官方数据来源与质量说明（英文）](docs/data_sources.md)
- [本地运行方法（英文）](#run-locally)：包含研究网站与另一个 Streamlit 本地版本的安装及启动命令。
- [研究网站开发说明（英文）](site/README.md) · [Streamlit 使用说明（英文）](docs/dashboard.md)；Streamlit 程序入口为 [`dashboard/app.py`](dashboard/app.py)。

[返回英文介绍](#english) · [查看繁體中文簡介](#traditional-chinese)
