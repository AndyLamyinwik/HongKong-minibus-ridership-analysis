import "./style.css";
import * as echarts from "echarts/core";
import { LineChart, BarChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  MarkAreaComponent,
  AriaComponent,
  MarkLineComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { validateResearchData, percentage, yearRows } from "./data.js";
import { chartOptions } from "./chart.js";
import { createResearch } from "./research.js";
import { getLanguage, initializeLanguage } from "./i18n.js";
import { annualText } from "./annual-translations.js";

echarts.use([
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  MarkAreaComponent,
  AriaComponent,
  MarkLineComponent,
  SVGRenderer,
]);
document.documentElement.classList.add("js");
const menuToggle = document.querySelector("#menu-toggle");
const navigation = document.querySelector("#navigation");
menuToggle.hidden = false;
function closeMenu() {
  menuToggle.setAttribute("aria-expanded", "false");
  navigation.classList.remove("is-open");
}
menuToggle.addEventListener("click", () => {
  const open = menuToggle.getAttribute("aria-expanded") !== "true";
  menuToggle.setAttribute("aria-expanded", String(open));
  navigation.classList.toggle("is-open", open);
});
navigation.addEventListener("click", (event) => {
  if (event.target.closest("a")) closeMenu();
});
document.addEventListener("keydown", (event) => {
  if (
    event.key === "Escape" &&
    menuToggle.getAttribute("aria-expanded") === "true"
  ) {
    closeMenu();
    menuToggle.focus();
  }
});

const status = document.querySelector("#data-status");
const statusMessage = document.querySelector("#status-message");
const retry = document.querySelector("#retry-data");
const shell = document.querySelector("#chart-shell");
const chartElement = document.querySelector("#ridership-chart");
const viewButtons = [...document.querySelectorAll("[data-view]")];
const unit = document.querySelector("#chart-unit");
const yearSelect = document.querySelector("#inspect-year");
const yearValues = document.querySelector("#year-values");
const table = document.querySelector("#annual-table");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const smallViewport = matchMedia("(max-width: 680px)");
let data;
let chart;
let view = "index";
let loading = false;
let loadState = "loading";
let errorKey = "unavailable";
const text = (key, values) => annualText(key, getLanguage(), values);
const research = createResearch(echarts, () => loadData(), getLanguage);

function updateYear(showTooltip = false) {
  const year = Number(yearSelect.value);
  const rows = yearRows(data, year);
  yearValues.replaceChildren(
    ...rows.map((row) => {
      const span = document.createElement("span");
      span.className = row.mode === "GMB" ? "year-gmb" : "year-rmb";
      const marker = document.createElement("i");
      marker.className = row.mode === "GMB" ? "mode-dot" : "mode-diamond";
      marker.setAttribute("aria-hidden", "true");
      const label = document.createTextNode(
        text(row.mode === "GMB" ? "gmb" : "rmb"),
      );
      const value = document.createElement("strong");
      value.textContent =
        view === "index"
          ? text("indexValue", { value: row.index_2015.toFixed(2) })
          : text("volumeValue", { value: (row.journeys_thousands / 1000).toFixed(2) });
      span.append(marker, label, value);
      return span;
    }),
  );
  if (showTooltip)
    chart.dispatchAction({
      type: "showTip",
      seriesIndex: 0,
      dataIndex: year - 2015,
    });
}

function drawChart() {
  chart.setOption(
    chartOptions(data, view, {
      mobile: smallViewport.matches,
      reducedMotion: reducedMotion.matches,
      language: getLanguage(),
    }),
    { notMerge: true },
  );
  unit.textContent =
    view === "index"
      ? text("indexUnit")
      : text("volumeUnit");
  document.querySelector(".chart-intro").textContent =
    view === "index"
      ? text("indexIntro")
      : text("volumeIntro");
  chartElement.setAttribute(
    "aria-label",
    text(view === "index" ? "indexDescription" : "volumeDescription"),
  );
  viewButtons.forEach((button) =>
    button.setAttribute("aria-pressed", String(button.dataset.view === view)),
  );
  updateYear();
}

function renderData() {
  document.querySelectorAll("[data-kpi]").forEach((element) => {
    element.textContent = percentage(data.kpis[element.dataset.kpi]);
  });
  document.querySelectorAll("[data-value]").forEach((element) => {
    element.textContent = percentage(
      data.kpis[element.dataset.value],
      element.hasAttribute("data-unsigned"),
    );
  });
  document.querySelector("#kpis").setAttribute("aria-busy", "false");
  yearSelect.replaceChildren(
    ...Array.from({ length: 11 }, (_, i) => {
      const option = document.createElement("option");
      option.value = String(2015 + i);
      option.textContent = option.value;
      return option;
    }),
  );
  yearSelect.value = "2025";
  table.replaceChildren(
    ...Array.from({ length: 11 }, (_, i) => {
      const year = 2015 + i;
      const [gmb, rmb] = yearRows(data, year);
      const tr = document.createElement("tr");
      for (const [index, value] of [
        String(year),
        (gmb.journeys_thousands / 1000).toFixed(3),
        (rmb.journeys_thousands / 1000).toFixed(3),
        gmb.index_2015.toFixed(2),
        rmb.index_2015.toFixed(2),
      ].entries()) {
        const cell = document.createElement(index === 0 ? "th" : "td");
        if (index === 0) cell.scope = "row";
        cell.textContent = value;
        tr.append(cell);
      }
      return tr;
    }),
  );
  updateSnapshotDate();
  chart ??= echarts.init(chartElement, null, { renderer: "svg" });
  drawChart();
  status.hidden = true;
  shell.setAttribute("aria-busy", "false");
  document.querySelector("#year-inspector").hidden = false;
  viewButtons.forEach((button) => {
    button.disabled = false;
  });
}

function updateSnapshotDate() {
  if (!data) return;
  document.querySelector("#snapshot-date").textContent =
    new Intl.DateTimeFormat(getLanguage() === "en" ? "en-GB" : "zh-Hant-HK", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    }).format(new Date(`${data.provenance.snapshot_retrieved_on}T00:00:00Z`));
}

function showTableMessage(key) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 5;
  cell.textContent = text(key);
  row.append(cell);
  table.replaceChildren(row);
}

function refreshLanguage() {
  if (loadState === "ready" && chart) {
    chart.dispatchAction({ type: "hideTip" });
    drawChart();
    chart.resize();
  } else {
    statusMessage.textContent = text(loadState === "loading" ? "loading" : errorKey);
    chartElement.setAttribute("aria-label", text(loadState === "loading" ? "chartLoading" : "chartUnavailable"));
    showTableMessage(loadState === "loading" ? "tableLoading" : "tableUnavailable");
  }
  updateSnapshotDate();
  research.refreshLanguage();
}

async function loadData() {
  if (loading) return;
  loading = true;
  loadState = "loading";
  research.loading();
  status.hidden = false;
  retry.hidden = true;
  shell.setAttribute("aria-busy", "true");
  document.querySelector("#kpis").setAttribute("aria-busy", "true");
  statusMessage.textContent = text("loading");
  showTableMessage("tableLoading");
  chartElement.setAttribute(
    "aria-label",
    text("chartLoading"),
  );
  try {
    const response = await fetch(
      `${import.meta.env.BASE_URL}data/research.json`,
      { signal: AbortSignal.timeout(10000) },
    );
    if (!response.ok) throw new Error("Research data could not be downloaded.");
    data = validateResearchData(await response.json());
    loadState = "ready";
    renderData();
    research.render(data);
  } catch (error) {
    loadState = "error";
    research.unavailable();
    chart?.dispose();
    chart = undefined;
    errorKey = error.message === "The bundled research data is empty." ? "empty" : "unavailable";
    statusMessage.textContent = text(errorKey);
    retry.hidden = false;
    chartElement.setAttribute(
      "aria-label",
      text("chartUnavailable"),
    );
    status.setAttribute("role", "alert");
    shell.setAttribute("aria-busy", "false");
    document.querySelector("#kpis").setAttribute("aria-busy", "false");
    showTableMessage("tableUnavailable");
  } finally {
    loading = false;
  }
}

retry.addEventListener("click", () => {
  status.setAttribute("role", "status");
  loadData();
});
viewButtons.forEach((button) =>
  button.addEventListener("click", () => {
    if (view !== button.dataset.view) {
      view = button.dataset.view;
      drawChart();
    }
  }),
);
yearSelect.addEventListener("change", () => updateYear(true));
yearSelect.addEventListener("blur", () =>
  chart?.dispatchAction({ type: "hideTip" }),
);
const observer = new ResizeObserver(() => chart?.resize());
observer.observe(chartElement);
smallViewport.addEventListener("change", () => {
  if (chart) drawChart();
});
reducedMotion.addEventListener("change", () => {
  if (chart) drawChart();
});
window.addEventListener("pagehide", (event) => {
  if (!event.persisted) {
    observer.disconnect();
    chart?.dispose();
  }
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted) chart?.resize();
});
initializeLanguage(refreshLanguage);
loadData();
