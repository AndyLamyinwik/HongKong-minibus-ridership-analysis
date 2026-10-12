import { colors } from "./chart.js";
import { chartFontFamily, chartModeLabels, englishModeLabels, isChinese } from "./chart-translations.js";

export const modeColors = {
  GMB: colors.jade,
  RMB: colors.coral,
  PLB: colors.ink,
  MTR: "#376781",
  FRANCHISED_BUS: "#87632f",
};

export const modeLabels = englishModeLabels;
export function getModeLabels(language = "en") {
  return chartModeLabels(language);
}

export const recoveryModes = ["GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"];
const componentModes = ["GMB", "RMB", "MTR", "FRANCHISED_BUS"];
const years = Array.from({ length: 11 }, (_, offset) => String(2015 + offset));
const symbols = {
  GMB: "circle",
  RMB: "diamond",
  MTR: "triangle",
  FRANCHISED_BUS: "rect",
};
const lineTypes = {
  GMB: "solid",
  RMB: "dashed",
  MTR: "dotted",
  FRANCHISED_BUS: "solid",
};

function selectedModes(focus) {
  if (!["all", "minibuses"].includes(focus))
    throw new Error("Unknown market-share focus.");
  return focus === "minibuses" ? ["GMB", "RMB"] : componentModes;
}

function fleetRows(data, mode, measure) {
  if (!["GMB", "RMB"].includes(mode))
    throw new Error("Unknown minibus service.");
  if (!["compare", "proxy"].includes(measure))
    throw new Error("Unknown fleet measure.");
  return data.fleet.annual
    .filter((row) => row.mode === mode)
    .sort((a, b) => a.year - b.year);
}

function tooltipRow(label, value, color = colors.ink) {
  return `<div class="tooltip-row" style="gap:12px"><span class="tooltip-label" style="min-width:0;white-space:normal;overflow-wrap:anywhere">${label}</span><span class="tooltip-value" style="color:${color};flex-shrink:0">${value}</span></div>`;
}

function tooltipConfig(formatter, trigger = "axis") {
  return {
    trigger,
    confine: true,
    renderMode: "html",
    enterable: false,
    backgroundColor: colors.paper,
    borderColor: colors.rule,
    padding: [12, 14],
    extraCssText:
      "box-shadow:0 4px 18px rgba(23,43,50,.08);border-radius:3px;max-width:calc(100% - 24px);white-space:normal;",
    axisPointer: {
      type: "line",
      lineStyle: { color: colors.muted, type: "dashed" },
    },
    formatter,
  };
}

function baseOptions(description, mobile, reducedMotion, language = "en") {
  return {
    animation: !reducedMotion,
    animationDuration: 350,
    animationDurationUpdate: 250,
    textStyle: { fontFamily: chartFontFamily(language), color: colors.ink },
    aria: {
      enabled: true,
      description: isChinese(language)
        ? `${description}圖表後附有完整且可無障礙閱讀的資料表。`
        : `${description} A complete accessible data table follows the chart.`,
    },
    grid: {
      left: mobile ? 34 : 42,
      right: mobile ? 16 : 28,
      top: 34,
      bottom: 30,
    },
  };
}

function yearAxis(mobile) {
  return {
    type: "category",
    data: years,
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
  };
}

function valueAxis(max, interval, mobile, percentage = false) {
  return {
    type: "value",
    min: 0,
    max,
    interval,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: {
      color: colors.muted,
      fontSize: mobile ? 10 : 11,
      margin: 12,
      ...(percentage ? { formatter: (value) => `${value}%` } : {}),
    },
    splitLine: {
      lineStyle: { color: colors.rule, type: "dashed", opacity: 0.75 },
    },
  };
}

function baseline(axis, name) {
  return {
    silent: true,
    symbol: ["none", "none"],
    lineStyle: { color: colors.muted, type: "dashed", width: 1.25 },
    label: {
      show: true,
      formatter: name,
      color: colors.muted,
      fontSize: 10,
      position: "insideEndTop",
    },
    data: [{ [axis]: 100 }],
  };
}

function lineSeries(id, name, values, color, symbol, lineType, mobile) {
  return {
    id,
    name,
    type: "line",
    data: values,
    smooth: false,
    showSymbol: true,
    symbol,
    symbolSize: mobile ? 5 : 6,
    lineStyle: { color, type: lineType, width: 2.5 },
    itemStyle: { color },
    emphasis: { scale: 1.5, focus: "none" },
  };
}

export function recoveryTooltipMarkup(data, mode, language = "en") {
  const row = data.recovery.find((candidate) => candidate.mode === mode);
  if (!row) return "";
  if (isChinese(language)) {
    return `<div class="chart-tooltip research-tooltip"><div class="tooltip-year">2025 · ${getModeLabels(language)[mode]}</div>${tooltipRow("相對其本身 2019 年總量的復甦比例", `${row.recovery_pct.toFixed(2)}%`, modeColors[mode])}<div class="tooltip-absolute">2019 年度乘客旅次 = 100%。${row.includes_estimates ? "包含紅色小巴估算旅次。" : "乘客旅次採用公布數字。"}${mode === "PLB" ? "公共小巴為專線小巴與紅色小巴之和，以小計呈現。" : ""}</div></div>`;
  }
  return `<div class="chart-tooltip research-tooltip"><div class="tooltip-year">2025 · ${modeLabels[mode]}</div>${tooltipRow("Recovery against own 2019 total", `${row.recovery_pct.toFixed(2)}%`, modeColors[mode])}<div class="tooltip-absolute">2019 annual passenger journeys = 100%.${row.includes_estimates ? " Includes estimated Red Minibus journeys." : " Reported passenger journeys."}${mode === "PLB" ? " PLB is GMB + RMB, shown as a subtotal." : ""}</div></div>`;
}

export function recoveryOptions(
  data,
  { mobile = false, reducedMotion = false, selectedMode = null, language = "en" } = {},
) {
  const chinese = isChinese(language);
  if (selectedMode !== null && !recoveryModes.includes(selectedMode))
    throw new Error("Unknown recovery service.");
  const rows = recoveryModes.map((mode) =>
    data.recovery.find((row) => row.mode === mode),
  );
  if (rows.some((row) => !row))
    throw new Error("Incomplete recovery observations.");
  const shortLabels = chinese ? {
    GMB: "專線小巴",
    RMB: "紅色小巴\n（估算）",
    PLB: "公共小巴總計\n（含估算）",
    MTR: "港鐵\n鐵路服務",
    FRANCHISED_BUS: "專營巴士",
  } : {
    GMB: "Green\nMinibuses",
    RMB: "Red Minibuses\nestimated",
    PLB: "PLB total\nincludes est.",
    MTR: "MTR railway",
    FRANCHISED_BUS: "Franchised\nbuses",
  };
  const fullLabels = chinese ? getModeLabels(language) : {
    GMB: "Green Minibuses",
    RMB: "Red Minibuses · est.",
    PLB: "PLB total · incl. est.",
    MTR: "MTR",
    FRANCHISED_BUS: "Franchised buses",
  };
  const recoveryBaseline = baseline("xAxis", chinese ? "2019 年 = 100%" : "2019 = 100%");
  if (mobile) recoveryBaseline.label.show = false;
  return {
    ...baseOptions(
      chinese
        ? "2025 年度旅次相對各服務本身 2019 年總量的復甦比例，2019 年設為 100%。服務包括專線小巴、紅色小巴（估算）、兩者合計的公共小巴小計、港鐵鐵路服務及專營巴士。每個長條採用各自的分母；此比例並非市場佔比。"
        : "2025 annual journey recovery against each service's own 2019 total, equal to 100 percent. Green Minibuses, estimated Red Minibuses, their combined Public Light Bus subtotal, MTR and franchised buses. Each bar has its own denominator; these bars are not market shares.",
      mobile,
      reducedMotion,
      language,
    ),
    grid: {
      left: mobile ? 80 : 162,
      right: mobile ? 27 : 36,
      top: 36,
      bottom: 30,
    },
    tooltip: tooltipConfig(
      (params) => recoveryTooltipMarkup(data, params?.data?.mode, language),
      "item",
    ),
    xAxis: {
      ...valueAxis(120, mobile ? 40 : 20, mobile, true),
      splitLine: { lineStyle: { color: colors.rule, type: "dashed" } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: recoveryModes,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: colors.ink,
        fontSize: mobile ? 10 : 11,
        formatter: (mode) => (mobile ? shortLabels : fullLabels)[mode],
      },
    },
    series: [
      {
        id: "recovery",
        name: chinese ? "2025 年復甦比例 · 各自的 2019 年 = 100%" : "2025 recovery · own 2019 = 100%",
        type: "bar",
        barMaxWidth: 28,
        data: rows.map((row) => ({
          value: row.recovery_pct,
          mode: row.mode,
          itemStyle: {
            color: modeColors[row.mode],
            borderColor: colors.ink,
            borderWidth: selectedMode === row.mode ? 2 : 0,
          },
        })),
        label: {
          show: true,
          position: "right",
          fontSize: mobile ? 10 : 11,
          color: colors.ink,
          formatter: (params) => `${params.value.toFixed(2)}%`,
        },
        emphasis: { focus: "none" },
        markLine: recoveryBaseline,
      },
    ],
  };
}

export function shareTooltipMarkup(data, year, focus = "all", language = "en") {
  const modes = selectedModes(focus);
  const annual = data.market_share.annual.filter(
    (row) => row.year === Number(year),
  );
  const rows = modes.map((mode) =>
    annual.find((row) => row.mode === mode && !row.is_subtotal),
  );
  const denominator = data.market_share.denominators.find(
    (row) => row.year === Number(year),
  );
  if (rows.some((row) => !row) || !denominator) return "";
  const subtotal = annual.find((row) => row.mode === "PLB" && row.is_subtotal);
  if (isChinese(language)) {
    return `<div class="chart-tooltip research-tooltip"><div class="tooltip-year">${Number(year)} · 指定比較組別</div>${rows.map((row) => tooltipRow(getModeLabels(language)[row.mode], `${row.share_pct.toFixed(2)}%`, modeColors[row.mode])).join("")}${subtotal ? `<div class="tooltip-absolute">公共小巴小計（專線小巴 + 紅色小巴）：${subtotal.share_pct.toFixed(2)}%。已包含在上述兩個小巴組成部分內。</div>` : ""}<div class="tooltip-absolute">分母：專線小巴、紅色小巴、港鐵鐵路服務及專營巴士合計 ${(denominator.journeys_thousands / 1000).toFixed(2)} 百萬年度旅次。包含紅色小巴估算旅次。${focus === "minibuses" ? "分母仍包含全部四種模式。" : ""}此組別並非整體交通運輸市場。</div></div>`;
  }
  return `<div class="chart-tooltip research-tooltip"><div class="tooltip-year">${Number(year)} · selected comparison group</div>${rows.map((row) => tooltipRow(modeLabels[row.mode], `${row.share_pct.toFixed(2)}%`, modeColors[row.mode])).join("")}${subtotal ? `<div class="tooltip-absolute">PLB subtotal (GMB + RMB): ${subtotal.share_pct.toFixed(2)}%. Included in the two minibus components above.</div>` : ""}<div class="tooltip-absolute">Denominator: ${(denominator.journeys_thousands / 1000).toFixed(2)} million annual journeys across GMB, RMB, MTR and franchised buses. Includes estimated RMB journeys.${focus === "minibuses" ? " The denominator still includes all four modes." : ""} This is not the whole transport market.</div></div>`;
}

export function shareOptions(
  data,
  { mobile = false, reducedMotion = false, focus = "all", language = "en" } = {},
) {
  const modes = selectedModes(focus);
  const chinese = isChinese(language);
  return {
    ...baseOptions(
      chinese
        ? `指定比較組別內的年度旅次佔比：專線小巴、紅色小巴（估算）、港鐵鐵路服務及專營巴士。分母包含紅色小巴估算旅次。${focus === "minibuses" ? "圖中只顯示兩個小巴組成部分，座標軸為 0 至 20%；四模式分母保持不變。" : "圖中顯示四個互不重複的組成部分，座標軸為 0 至 50%。"}公共小巴為兩種小巴的小計，並非第五個組成部分。此組別並非整體交通運輸市場。`
        : `Annual journey shares within the selected comparison group: Green Minibuses, estimated Red Minibuses, MTR and franchised buses. The denominator includes estimated RMB journeys. ${focus === "minibuses" ? "Only the two minibus components are plotted on a zero-to-20-percent axis; the four-mode denominator stays fixed." : "Four exclusive components are plotted on a zero-to-50-percent axis."} PLB is their two-minibus subtotal and is not a fifth component. This is not the whole transport market.`,
      mobile,
      reducedMotion,
      language,
    ),
    tooltip: tooltipConfig((params) =>
      shareTooltipMarkup(data, params[0]?.axisValue, focus, language),
    ),
    xAxis: yearAxis(mobile),
    yAxis: valueAxis(
      focus === "minibuses" ? 20 : 50,
      focus === "minibuses" ? 5 : 10,
      mobile,
      true,
    ),
    series: modes.map((mode) => {
      const rows = data.market_share.annual
        .filter((row) => row.mode === mode && !row.is_subtotal)
        .sort((a, b) => a.year - b.year);
      return lineSeries(
        mode,
        getModeLabels(language)[mode],
        rows.map((row) => row.share_pct),
        modeColors[mode],
        symbols[mode],
        lineTypes[mode],
        mobile,
      );
    }),
  };
}

export function fleetTooltipMarkup(
  data,
  year,
  mode = "GMB",
  measure = "compare",
  language = "en",
) {
  const rows = fleetRows(data, mode, measure);
  const row = rows.find((candidate) => candidate.year === Number(year));
  const annual = data.annual.find(
    (candidate) => candidate.mode === mode && candidate.year === Number(year),
  );
  if (!row || !annual) return "";
  if (isChinese(language)) {
    const service = mode === "GMB" ? "專線小巴" : "紅色小巴";
    const estimated = row.includes_estimates ? " · 估算" : " · 公布數字";
    const values = measure === "compare"
      ? `${tooltipRow("12 月持牌車隊 · 公布數字", row.index_stock_2015.toFixed(2), colors.ink)}${tooltipRow(`年度乘客旅次${estimated}`, annual.index_2015.toFixed(2), modeColors[mode])}<div class="tooltip-absolute">車隊：12 月月底共有 ${row.december_licensed_vehicles.toLocaleString("en-GB")} 輛持牌車輛。旅次：${(annual.journeys_thousands / 1000).toFixed(2)} 百萬年度旅次${estimated}。</div>`
      : `${tooltipRow(`持牌車輛日旅次指標（proxy）${estimated}`, row.index_proxy_2015.toFixed(2), modeColors[mode])}<div class="tooltip-absolute">每持牌車輛日 ${row.journeys_per_licensed_vehicle_day_proxy.toFixed(2)} 旅次（proxy）。分母：${row.licensed_vehicle_days_proxy.toLocaleString("en-GB")} 持牌車輛日，按每月月底持牌車數 × 該月曆日數加總；並非只採用 12 月車隊數。</div>`;
    return `<div class="chart-tooltip research-tooltip"><div class="tooltip-year">${Number(year)} · ${service}</div>${values}<div class="tooltip-absolute">每個顯示數列均以其本身的 2015 年數值設為 100。持牌車隊數並不代表實際出車數或生產力。${mode === "RMB" ? "紅色小巴乘客估算採用車隊資料；兩項指標並非獨立。" : ""}</div></div>`;
  }
  const service = mode === "GMB" ? "Green Minibuses" : "Red Minibuses";
  const estimated = row.includes_estimates ? " · estimated" : " · reported";
  const values =
    measure === "compare"
      ? `${tooltipRow("December licensed stock · reported", row.index_stock_2015.toFixed(2), colors.ink)}${tooltipRow(`Annual passenger journeys${estimated}`, annual.index_2015.toFixed(2), modeColors[mode])}<div class="tooltip-absolute">Stock: ${row.december_licensed_vehicles.toLocaleString("en-GB")} licensed vehicles at December month-end. Journeys: ${(annual.journeys_thousands / 1000).toFixed(2)} million annual journeys${estimated}.</div>`
      : `${tooltipRow(`Fleet-normalized journey proxy${estimated}`, row.index_proxy_2015.toFixed(2), modeColors[mode])}<div class="tooltip-absolute">${row.journeys_per_licensed_vehicle_day_proxy.toFixed(2)} journeys per licensed vehicle-day (proxy). Denominator: ${row.licensed_vehicle_days_proxy.toLocaleString("en-GB")} licensed vehicle-days, summed from month-end stock × calendar days; not December stock alone.</div>`;
  return `<div class="chart-tooltip research-tooltip"><div class="tooltip-year">${Number(year)} · ${service}</div>${values}<div class="tooltip-absolute">Each displayed series uses its own 2015 value = 100. Licensed stock does not measure deployed vehicles or productivity.${mode === "RMB" ? " RMB passenger estimates use fleet inputs; these measures are not independent." : ""}</div></div>`;
}

export function fleetOptions(
  data,
  mode = "GMB",
  measure = "compare",
  { mobile = false, reducedMotion = false, language = "en" } = {},
) {
  const chinese = isChinese(language);
  const rows = fleetRows(data, mode, measure);
  const annual = data.annual
    .filter((row) => row.mode === mode)
    .sort((a, b) => a.year - b.year);
  const service = chinese
    ? mode === "GMB" ? "專線小巴" : "紅色小巴"
    : mode === "GMB" ? "Green Minibuses" : "Red Minibuses";
  const estimated = mode === "RMB" ? chinese ? " · 估算" : " · estimated" : "";
  const series =
    measure === "compare"
      ? [
          lineSeries(
            "licensed-stock",
            chinese ? "12 月持牌車隊 · 公布數字" : "December licensed stock · reported",
            rows.map((row) => row.index_stock_2015),
            colors.ink,
            "rect",
            "dotted",
            mobile,
          ),
          lineSeries(
            "annual-journeys",
            `${chinese ? "年度乘客旅次" : "Annual passenger journeys"}${estimated}`,
            annual.map((row) => row.index_2015),
            modeColors[mode],
            symbols[mode],
            lineTypes[mode],
            mobile,
          ),
        ]
      : [
          lineSeries(
            "fleet-proxy",
            `${chinese ? "持牌車輛日旅次指標（proxy）" : "Fleet-normalized journey proxy"}${estimated}`,
            rows.map((row) => row.index_proxy_2015),
            modeColors[mode],
            symbols[mode],
            lineTypes[mode],
            mobile,
          ),
        ];
  series[0].markLine = baseline("yAxis", chinese ? "2015 年 = 100" : "2015 = 100");
  return {
    ...baseOptions(
      chinese
        ? `${service}。${measure === "compare" ? "12 月月底持牌車隊及年度乘客旅次，各自以其本身 2015 年數值設為 100。車隊數採用公布數字；紅色小巴乘客旅次屬估算。" : "持牌車輛日旅次指標（proxy），以其本身 2015 年數值設為 100。分母按每月月底持牌車數乘以該月曆日數加總；並非只採用 12 月車隊數。"}持牌車輛並不代表實際出車車輛。此指標不是生產力指標。${mode === "RMB" ? "紅色小巴乘客估算採用車隊資料，因此兩項指標並非獨立。" : ""}`
        : `${service}. ${measure === "compare" ? "December month-end licensed stock and annual passenger journeys, each indexed to its own 2015 value, equal to 100. Stock is reported; RMB passenger journeys are estimated." : "Annual passenger journeys per licensed vehicle-day proxy, indexed to its own 2015 value, equal to 100. The denominator sums month-end licensed stock times calendar days; it is not December stock alone."} Licensed vehicles are not deployed vehicles. This is not a productivity measure.${mode === "RMB" ? " RMB passenger estimates use fleet inputs, so the measures are not independent." : ""}`,
      mobile,
      reducedMotion,
      language,
    ),
    tooltip: tooltipConfig((params) =>
      fleetTooltipMarkup(data, params[0]?.axisValue, mode, measure, language),
    ),
    xAxis: yearAxis(mobile),
    yAxis: valueAxis(120, 20, mobile),
    series,
  };
}
