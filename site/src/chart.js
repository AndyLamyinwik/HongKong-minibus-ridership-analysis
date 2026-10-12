import { annualSeries, yearRows } from "./data.js";

export const colors = {
  ink: "#172b32",
  muted: "#53645f",
  jade: "#236451",
  coral: "#aa4e44",
  rule: "#d7dbd2",
  paper: "#f6f4ed",
};

export function tooltipMarkup(data, year, view) {
  const rows = yearRows(data, Number(year));
  if (rows.some((row) => !row)) return "";
  return `<div class="chart-tooltip"><div class="tooltip-year">${Number(year)}</div>${rows.map((row) => `<div class="tooltip-row"><span class="tooltip-label">${row.mode === "GMB" ? "Green Minibuses" : "Red Minibuses · est."}</span><span class="tooltip-value" style="color:${row.mode === "GMB" ? colors.jade : colors.coral}">${view === "index" ? row.index_2015.toFixed(2) : (row.journeys_thousands / 1000).toFixed(2)}${view === "index" ? "" : "m"}</span></div>${view === "index" ? `<div class="tooltip-absolute">${(row.journeys_thousands / 1000).toFixed(2)} million journeys${row.mode === "RMB" ? " · estimated" : ""}</div>` : ""}`).join("")}<div class="tooltip-absolute">${view === "index" ? "Index · own 2015 = 100" : "Annual passenger journeys · millions"}</div></div>`;
}

export function chartOptions(
  data,
  view,
  { mobile = false, reducedMotion = false } = {},
) {
  const indexed = view === "index";
  const max = indexed ? 120 : 600;
  return {
    animation: !reducedMotion,
    animationDuration: 350,
    animationDurationUpdate: 250,
    textStyle: { fontFamily: "DM Sans, sans-serif", color: colors.ink },
    aria: {
      enabled: true,
      description: `Annual Green and estimated Red Minibus passenger journeys, 2015 to 2025. ${indexed ? "Each series is indexed to its own 2015 total, equal to 100." : "Values are millions of passenger journeys."} A complete data table follows the chart.`,
    },
    grid: {
      left: mobile ? 33 : 40,
      right: mobile ? 16 : 30,
      top: 32,
      bottom: 28,
    },
    tooltip: {
      trigger: "axis",
      confine: true,
      renderMode: "html",
      enterable: false,
      backgroundColor: colors.paper,
      borderColor: colors.rule,
      padding: [12, 14],
      extraCssText:
        "box-shadow:0 4px 18px rgba(23,43,50,.08);border-radius:3px;max-width:calc(100% - 24px);",
      axisPointer: {
        type: "line",
        lineStyle: { color: "#9ca9a1", type: "dashed" },
      },
      formatter: (params) => tooltipMarkup(data, params[0]?.axisValue, view),
    },
    xAxis: {
      type: "category",
      data: Array.from({ length: 11 }, (_, i) => String(2015 + i)),
      boundaryGap: false,
      axisLine: { lineStyle: { color: colors.rule } },
      axisTick: { show: false },
      axisLabel: {
        color: colors.muted,
        fontSize: mobile ? 10 : 11,
        margin: 12,
        interval: mobile ? 1 : 0,
        showMinLabel: true,
        showMaxLabel: true,
      },
    },
    yAxis: {
      type: "value",
      min: 0,
      max,
      interval: indexed ? 20 : 100,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: colors.muted,
        fontSize: mobile ? 10 : 11,
        margin: 12,
      },
      splitLine: {
        lineStyle: { color: colors.rule, type: "dashed", opacity: 0.75 },
      },
    },
    series: ["GMB", "RMB"].map((mode) => ({
      id: mode,
      name: mode === "GMB" ? "Green Minibuses" : "Red Minibuses · estimated",
      type: "line",
      data: annualSeries(data, mode, view),
      smooth: false,
      showSymbol: true,
      symbol: mode === "GMB" ? "circle" : "diamond",
      symbolSize: mobile ? 5 : 6,
      lineStyle: {
        color: mode === "GMB" ? colors.jade : colors.coral,
        width: 2.5,
        type: mode === "GMB" ? "solid" : "dashed",
      },
      itemStyle: { color: mode === "GMB" ? colors.jade : colors.coral },
      emphasis: { scale: 1.5, focus: "none" },
      ...(mode === "GMB"
        ? {
            markArea: {
              silent: true,
              itemStyle: { color: "rgba(23,43,50,0.045)" },
              label: {
                show: true,
                color: colors.muted,
                fontSize: mobile ? 9 : 10,
                position: "insideTop",
                padding: [10, 0, 0, 0],
              },
              data: [
                [
                  { name: "Disruption period", xAxis: "2020" },
                  { xAxis: "2022" },
                ],
              ],
            },
          }
        : {}),
    })),
  };
}
