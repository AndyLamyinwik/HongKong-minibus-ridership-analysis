import { percentage } from "./data.js";
import {
  validateRecovery,
  validateMarketShare,
  validateFleet,
  selectedShareRows,
  selectedFleetRow,
} from "./research-data.js";
import {
  recoveryOptions,
  shareOptions,
  fleetOptions,
  recoveryModes,
  modeColors,
  getModeLabels,
} from "./research-charts.js";
import { getResearchText } from "./research-translations.js";

const integer = (value) =>
  new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value);
const elements = (id) => document.querySelector(`#${id}`);

export function createResearch(echarts, retryData, getLanguage = () => "en") {
  const motion = matchMedia("(prefers-reduced-motion: reduce)");
  const mobile = matchMedia("(max-width: 680px)");
  const states = {
    recovery: {
      chart: null,
      ready: false,
      validate: validateRecovery,
      tableColumns: 3,
    },
    share: {
      chart: null,
      ready: false,
      validate: validateMarketShare,
      tableColumns: 7,
    },
    fleet: {
      chart: null,
      ready: false,
      validate: validateFleet,
      tableColumns: 5,
    },
  };
  let data;
  let shareFocus = "all";
  let fleetMode = "RMB";
  let fleetMeasure = "compare";
  const text = () => getResearchText(getLanguage());
  const labels = () => getModeLabels(getLanguage());
  const options = () => ({
    mobile: mobile.matches,
    reducedMotion: motion.matches,
    language: getLanguage(),
  });

  function buttonState(selector, key, value) {
    document
      .querySelectorAll(selector)
      .forEach((button) =>
        button.setAttribute(
          "aria-pressed",
          String(button.dataset[key] === value),
        ),
      );
  }
  function tableRows(id, rows) {
    const body = elements(id);
    body.replaceChildren(
      ...rows.map((values) => {
        const tr = document.createElement("tr");
        values.forEach((value, index) => {
          const cell = document.createElement(index === 0 ? "th" : "td");
          if (index === 0) cell.scope = "row";
          cell.textContent = String(value);
          tr.append(cell);
        });
        return tr;
      }),
    );
  }
  function fillYears(id) {
    const select = elements(id);
    const prior = select.value;
    select.replaceChildren(
      ...Array.from({ length: 11 }, (_, index) => {
        const option = document.createElement("option");
        option.value = String(2015 + index);
        option.textContent = option.value;
        return option;
      }),
    );
    select.value = prior || "2025";
  }
  function setMetric(selector, getter, format = percentage) {
    document.querySelectorAll(selector).forEach((element) => {
      element.textContent = format(getter(element));
    });
  }
  function setStatus(name, statusKey, loading = false) {
    const state = states[name];
    state.ready = false;
    state.statusKey = statusKey;
    state.loading = loading;
    if (!loading) {
      state.chart?.dispose();
      state.chart = null;
    }
    const status = elements(`${name}-status`);
    status.hidden = false;
    status.setAttribute("role", loading ? "status" : "alert");
    status.querySelector("p").textContent = text().statuses[statusKey];
    status.querySelector("button").hidden = loading;
    elements(`${name}-shell`).setAttribute("aria-busy", String(loading));
    elements(`${name}-chart`).setAttribute(
      "aria-label",
      text().chartState(name, loading),
    );
    elements(`${name}-inspector`).hidden = true;
    const sectionId = name === "share" ? "landscape" : name;
    document
      .querySelectorAll(
        `#${sectionId} button:not([data-retry-chapters]), #${sectionId} select`,
      )
      .forEach((control) => {
        control.disabled = true;
      });
    const metrics =
      name === "recovery"
        ? "[data-recovery]"
        : name === "share"
          ? "[data-share-endpoint], [data-composition]"
          : "[data-fleet-endpoint]";
    document.querySelectorAll(metrics).forEach((element) => {
      element.textContent = "—";
    });
    if (name === "fleet")
      elements("fleet-endpoint-note").textContent = loading
        ? text().endpointLoading
        : text().endpointUnavailable;
    const tr = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = state.tableColumns;
    cell.textContent = loading
      ? text().tableLoading
      : text().tableUnavailable;
    tr.append(cell);
    elements(`${name}-table`).replaceChildren(tr);
    if (name === "share") {
      elements("composition-strips").hidden = true;
      elements("composition-story").setAttribute("aria-busy", String(loading));
    }
  }
  function markReady(name) {
    states[name].ready = true;
    states[name].statusKey = null;
    states[name].loading = false;
    elements(`${name}-status`).hidden = true;
    elements(`${name}-shell`).setAttribute("aria-busy", "false");
    elements(`${name}-inspector`).hidden = false;
    elements(`${name}-chart`).setAttribute("aria-label", text().chartReady(name));
    const sectionId = name === "share" ? "landscape" : name;
    document
      .querySelectorAll(`#${sectionId} button, #${sectionId} select`)
      .forEach((control) => {
        control.disabled = false;
      });
  }
  function initChart(name) {
    states[name].chart ??= echarts.init(elements(`${name}-chart`), null, {
      renderer: "svg",
    });
    return states[name].chart;
  }
  function drawRecovery() {
    const mode = elements("recovery-mode").value;
    const row = data.recovery.find((row) => row.mode === mode);
    states.recovery.chart.setOption(
      recoveryOptions(data, { ...options(), selectedMode: mode }),
      { notMerge: true },
    );
    elements("recovery-readout").textContent =
      text().recoveryReadout(labels()[mode], percentage(row.recovery_pct));
    elements("recovery-readout").style.color = modeColors[mode];
  }
  function shareYear(showTooltip = false) {
    const year = Number(elements("share-year").value);
    elements("share-readout").replaceChildren(
      ...selectedShareRows(data, year).map((row) => {
        const span = document.createElement("span");
        span.className = row.is_subtotal
          ? "share-readout-item is-subtotal"
          : "share-readout-item";
        const label = document.createElement("span");
        label.textContent =
          row.mode === "PLB"
            ? text().plbSubtotal
            : labels()[row.mode];
        const value = document.createElement("strong");
        value.textContent = percentage(row.share_pct);
        span.style.color = modeColors[row.mode];
        span.append(label, value);
        return span;
      }),
    );
    if (showTooltip)
      states.share.chart.dispatchAction({
        type: "showTip",
        seriesIndex: 0,
        dataIndex: year - 2015,
      });
  }
  function drawShare() {
    states.share.chart.setOption(
      shareOptions(data, { ...options(), focus: shareFocus }),
      { notMerge: true },
    );
    elements("share-unit").textContent = text().shareUnit(shareFocus);
    elements("share-legend")
      .querySelectorAll(".legend-mtr, .legend-bus")
      .forEach((item) => {
        item.hidden = shareFocus === "minibuses";
      });
    buttonState("[data-share-focus]", "shareFocus", shareFocus);
    shareYear();
  }
  function fleetYear(showTooltip = false) {
    const year = Number(elements("fleet-year").value);
    const row = selectedFleetRow(data, fleetMode, year);
    const annual = data.annual.find(
      (row) => row.mode === fleetMode && row.year === year,
    );
    elements("fleet-readout").textContent = text().fleetReadout(
      fleetMeasure,
      integer(row.december_licensed_vehicles),
      (annual.journeys_thousands / 1000).toFixed(2),
      row.journeys_per_licensed_vehicle_day_proxy.toFixed(2),
      fleetMode === "RMB",
    );
    if (showTooltip)
      states.fleet.chart.dispatchAction({
        type: "showTip",
        seriesIndex: 0,
        dataIndex: year - 2015,
      });
  }
  function fleetLegend() {
    const legend = elements("fleet-legend");
    const names = text().fleetLegend(fleetMeasure, fleetMode === "RMB");
    legend.replaceChildren(
      ...names.map((name, index) => {
        const item = document.createElement("li");
        item.className =
          fleetMeasure === "compare" && index === 0
            ? "legend-stock"
            : fleetMode === "RMB"
              ? "legend-red"
              : "legend-green";
        const line = document.createElement("span");
        line.className = "legend-line";
        line.setAttribute("aria-hidden", "true");
        item.append(line, document.createTextNode(name));
        return item;
      }),
    );
  }
  function drawFleet() {
    states.fleet.chart.setOption(
      fleetOptions(data, fleetMode, fleetMeasure, options()),
      { notMerge: true },
    );
    elements("fleet-unit").textContent = text().fleetUnit(fleetMode, fleetMeasure);
    const endpoint = data.fleet.endpoints.find((row) => row.mode === fleetMode);
    elements("fleet-endpoint-note").textContent = text().fleetEndpoint(
      fleetMode,
      integer(endpoint.december_vehicles_2015),
      integer(endpoint.december_vehicles_2025),
      `${endpoint.stock_change_pct >= 0 ? "+" : ""}${percentage(endpoint.stock_change_pct)}`,
      percentage(endpoint.proxy_change_pct),
      fleetMode === "RMB",
    );
    buttonState("[data-fleet-mode]", "fleetMode", fleetMode);
    buttonState("[data-fleet-measure]", "fleetMeasure", fleetMeasure);
    fleetLegend();
    fleetYear();
    elements("fleet-table-caption").textContent = text().fleetTableCaption(
      fleetMode === "RMB",
    );
    tableRows(
      "fleet-table",
      data.fleet.annual
        .filter((row) => row.mode === fleetMode)
        .sort((a, b) => a.year - b.year)
        .map((row) => [
          row.year,
          integer(row.december_licensed_vehicles),
          (
            data.annual.find(
              (annual) => annual.mode === fleetMode && annual.year === row.year,
            ).journeys_thousands / 1000
          ).toFixed(3),
          integer(row.licensed_vehicle_days_proxy),
          row.journeys_per_licensed_vehicle_day_proxy.toFixed(2),
        ]),
    );
  }
  function renderRecovery() {
    const select = elements("recovery-mode");
    const prior = select.value;
    select.replaceChildren(
      ...recoveryModes.map((mode) => {
        const option = document.createElement("option");
        option.value = mode;
        option.textContent =
          mode === "PLB" ? text().plbOption : labels()[mode];
        return option;
      }),
    );
    select.value = prior || "RMB";
    setMetric(
      "[data-recovery]",
      (element) =>
        data.recovery.find((row) => row.mode === element.dataset.recovery)
          .recovery_pct,
    );
    tableRows(
      "recovery-table",
      recoveryModes.map((mode) => {
        const row = data.recovery.find((row) => row.mode === mode);
        return [
          labels()[mode],
          percentage(row.recovery_pct),
          row.mode === "PLB"
            ? text().basis.includesEstimates
            : row.mode === "RMB"
              ? text().basis.estimated
              : text().basis.reported,
        ];
      }),
    );
    initChart("recovery");
    drawRecovery();
  }
  function renderShare() {
    fillYears("share-year");
    document.querySelectorAll("[data-share-endpoint]").forEach((element) => {
      const value = data.market_share.endpoints[element.dataset.shareEndpoint];
      element.textContent = element.dataset.shareEndpoint.endsWith("_pp")
        ? Math.abs(value).toFixed(2)
        : percentage(value);
    });
    setMetric(
      "[data-composition]",
      (element) => data.narrative[element.dataset.composition],
    );
    for (const year of [2015, 2025]) {
      const gmb = data.narrative[`gmb_share_${year}_pct`];
      const track = elements(`composition-${year}`);
      track.style.setProperty("--gmb-share", `${gmb}%`);
      track.setAttribute(
        "aria-label",
        text().composition(year, gmb.toFixed(2), (100 - gmb).toFixed(2)),
      );
    }
    elements("composition-strips").hidden = false;
    elements("composition-story").setAttribute("aria-busy", "false");
    tableRows(
      "share-table",
      Array.from({ length: 11 }, (_, index) => {
        const year = 2015 + index;
        return [
          year,
          ...selectedShareRows(data, year).map((row) =>
            row.share_pct.toFixed(2),
          ),
          (
            data.market_share.denominators.find((row) => row.year === year)
              .journeys_thousands / 1000
          ).toFixed(3),
        ];
      }),
    );
    initChart("share");
    drawShare();
  }
  function renderFleet() {
    fillYears("fleet-year");
    document.querySelectorAll("[data-fleet-endpoint]").forEach((element) => {
      const [mode, key] = element.dataset.fleetEndpoint.split(".");
      const value = data.fleet.endpoints.find((row) => row.mode === mode)[key];
      element.textContent = key.endsWith("_pct")
        ? percentage(value)
        : integer(value);
    });
    initChart("fleet");
    drawFleet();
  }

  document
    .querySelectorAll("[data-retry-chapters]")
    .forEach((button) => button.addEventListener("click", retryData));
  elements("recovery-mode").addEventListener("change", drawRecovery);
  elements("share-year").addEventListener("change", () => shareYear(true));
  elements("fleet-year").addEventListener("change", () => fleetYear(true));
  for (const name of ["share", "fleet"])
    elements(`${name}-year`).addEventListener("blur", () =>
      states[name].chart?.dispatchAction({ type: "hideTip" }),
    );
  document.querySelectorAll("[data-share-focus]").forEach((button) =>
    button.addEventListener("click", () => {
      if (shareFocus !== button.dataset.shareFocus) {
        shareFocus = button.dataset.shareFocus;
        drawShare();
      }
    }),
  );
  document.querySelectorAll("[data-fleet-mode]").forEach((button) =>
    button.addEventListener("click", () => {
      if (fleetMode !== button.dataset.fleetMode) {
        fleetMode = button.dataset.fleetMode;
        drawFleet();
      }
    }),
  );
  document.querySelectorAll("[data-fleet-measure]").forEach((button) =>
    button.addEventListener("click", () => {
      if (fleetMeasure !== button.dataset.fleetMeasure) {
        fleetMeasure = button.dataset.fleetMeasure;
        drawFleet();
      }
    }),
  );
  const observer = new ResizeObserver((entries) =>
    entries.forEach((entry) => {
      const name = entry.target.id.split("-")[0];
      states[name].chart?.resize();
    }),
  );
  Object.keys(states).forEach((name) =>
    observer.observe(elements(`${name}-chart`)),
  );
  function redraw() {
    if (states.recovery.ready) drawRecovery();
    if (states.share.ready) drawShare();
    if (states.fleet.ready) drawFleet();
  }
  mobile.addEventListener("change", redraw);
  motion.addEventListener("change", redraw);
  window.addEventListener("pagehide", (event) => {
    if (!event.persisted) {
      observer.disconnect();
      Object.values(states).forEach((state) => state.chart?.dispose());
    }
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted)
      Object.values(states).forEach((state) => state.chart?.resize());
  });

  return {
    loading() {
      Object.keys(states).forEach((name) =>
        setStatus(name, "loading", true),
      );
    },
    unavailable() {
      Object.keys(states).forEach((name) =>
        setStatus(name, "unavailable"),
      );
    },
    render(researchData) {
      data = researchData;
      for (const [name, render] of [
        ["recovery", renderRecovery],
        ["share", renderShare],
        ["fleet", renderFleet],
      ]) {
        try {
          states[name].validate(data);
          render();
          markReady(name);
        } catch {
          setStatus(name, "invalid");
        }
      }
      const date = data.provenance?.expected_revision_date;
      if (/^\d{4}-\d{2}-\d{2}$/.test(date ?? ""))
        elements("revision-date").textContent = new Intl.DateTimeFormat(
          text().locale,
          { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" },
        ).format(new Date(`${date}T00:00:00Z`));
    },
    refreshLanguage() {
      for (const [name, render] of [
        ["recovery", renderRecovery],
        ["share", renderShare],
        ["fleet", renderFleet],
      ]) {
        if (states[name].ready) {
          render();
          markReady(name);
        } else if (states[name].statusKey) {
          setStatus(name, states[name].statusKey, states[name].loading);
        }
      }
      const date = data?.provenance?.expected_revision_date;
      if (/^\d{4}-\d{2}-\d{2}$/.test(date ?? ""))
        elements("revision-date").textContent = new Intl.DateTimeFormat(
          text().locale,
          { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" },
        ).format(new Date(`${date}T00:00:00Z`));
    },
  };
}
