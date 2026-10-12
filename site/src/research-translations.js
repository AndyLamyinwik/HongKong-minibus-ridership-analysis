const english = {
  locale: "en-GB",
  statuses: {
    loading: "Loading the verified research comparison…",
    unavailable:
      "The verified research data could not be loaded. Please try again.",
    invalid:
      "This research comparison is missing or invalid. Retry, or read the linked source documentation.",
  },
  chartState: (name, loading) =>
    `${name === "share" ? "Comparison-group shares" : name === "fleet" ? "Licensed fleet comparison" : "Recovery comparison"} ${loading ? "is loading" : "is unavailable"}.`,
  chartReady: (name) =>
    `${name === "share" ? "Comparison-group shares" : name === "fleet" ? "Licensed fleet comparison" : "Recovery comparison"}. A complete accessible data table follows the chart.`,
  endpointLoading: "Endpoint comparison is loading.",
  endpointUnavailable: "Endpoint comparison is unavailable.",
  tableLoading: "Research data is loading.",
  tableUnavailable:
    "This comparison is unavailable. Use the linked source documentation or retry.",
  recoveryReadout: (label, value) =>
    `${label}: ${value} of its own 2019 annual journeys in 2025.`,
  plbSubtotal: "PLB subtotal · includes estimates",
  plbOption: "PLB total · includes estimates",
  shareUnit: (focus) =>
    focus === "minibuses"
      ? "Minibus detail · 0–20% · same four-mode denominator"
      : "Share of the four-mode comparison group · percent",
  fleetReadout: (measure, stock, journeys, proxy, estimated) =>
    measure === "compare"
      ? `${stock} reported licensed vehicles in December · ${journeys} million annual journeys${estimated ? " · estimated" : ""}`
      : `${proxy} journeys per licensed vehicle-day (proxy)${estimated ? " · estimated passenger input" : ""}`,
  fleetLegend: (measure, estimated) =>
    measure === "compare"
      ? [
          "December licensed stock · reported",
          `Annual journeys${estimated ? " · estimated" : ""}`,
        ]
      : [
          `Annual vehicle-day proxy${estimated ? " · estimated passenger input" : ""}`,
        ],
  fleetUnit: (mode, measure) =>
    `${mode} · ${measure === "compare" ? "own 2015 = 100 for each measure" : "own 2015 annual vehicle-day proxy = 100"}`,
  fleetEndpoint: (mode, start, end, stockChange, proxyChange, estimated) =>
    `${mode} · December licensed stock: ${start} → ${end} (${stockChange}). Annual vehicle-day proxy change, 2015 → 2025: ${proxyChange}${estimated ? " · estimated passenger input" : ""}.`,
  fleetTableCaption: (estimated) =>
    `${estimated ? "Red" : "Green"} Minibus annual context. December licensing stocks are reported; ${estimated ? "journeys and the proxy include RMB estimates" : "journeys use reported passenger totals"}. The vehicle-day denominator sums all twelve month-end stocks × calendar days.`,
  basis: {
    includesEstimates: "Includes estimates",
    estimated: "Estimated",
    reported: "Reported",
  },
  composition: (year, gmb, rmb) =>
    `${year} PLB composition: Green Minibuses ${gmb}%, estimated Red Minibuses ${rmb}%.`,
};

const traditionalChinese = {
  locale: "zh-Hant-HK",
  statuses: {
    loading: "正在載入已驗證的研究比較資料…",
    unavailable: "未能載入已驗證的研究資料。請重試。",
    invalid: "此研究比較的資料缺漏或格式無效。請重試，或查看連結的資料來源說明。",
  },
  chartState: (name, loading) =>
    `${name === "share" ? "比較組別佔比" : name === "fleet" ? "持牌車隊比較" : "復甦比較"}${loading ? "正在載入" : "暫時無法顯示"}。`,
  chartReady: (name) =>
    `${name === "share" ? "比較組別佔比" : name === "fleet" ? "持牌車隊比較" : "復甦比較"}。圖表下方提供完整的無障礙資料表。`,
  endpointLoading: "正在載入起點與終點比較。",
  endpointUnavailable: "暫時無法顯示起點與終點比較。",
  tableLoading: "正在載入研究資料。",
  tableUnavailable: "暫時無法顯示此比較。請查看連結的資料來源說明，或重試。",
  recoveryReadout: (label, value) =>
    `${label}：2025 年全年乘客旅次為其自身 2019 年水平的 ${value}。`,
  plbSubtotal: "公共小巴小計 · 含估算",
  plbOption: "公共小巴總計 · 含估算",
  shareUnit: (focus) =>
    focus === "minibuses"
      ? "小巴細節 · 0–20% · 同一四模式分母"
      : "佔四模式比較組別的比例 · 百分比",
  fleetReadout: (measure, stock, journeys, proxy, estimated) =>
    measure === "compare"
      ? `${stock} 輛 12 月持牌車輛（公布數字） · 全年 ${journeys} 百萬旅次${estimated ? " · 估算" : ""}`
      : `每持牌車輛日 ${proxy} 乘客旅次（proxy）${estimated ? " · 乘客旅次採用估算" : ""}`,
  fleetLegend: (measure, estimated) =>
    measure === "compare"
      ? ["12 月持牌車輛數 · 公布數字", `全年乘客旅次${estimated ? " · 估算" : ""}`]
      : [`全年每持牌車輛日旅次${estimated ? " · 乘客旅次採用估算" : ""}`],
  fleetUnit: (mode, measure) =>
    `${mode === "RMB" ? "紅色小巴（RMB）" : "專線小巴（GMB）"} · ${measure === "compare" ? "各指標以自身 2015 年 = 100" : "以自身 2015 年每持牌車輛日旅次 = 100"}`,
  fleetEndpoint: (mode, start, end, stockChange, proxyChange, estimated) =>
    `${mode === "RMB" ? "紅色小巴（RMB）" : "專線小巴（GMB）"} · 12 月持牌車輛數：${start} → ${end}（${stockChange}）。全年持牌車輛日旅次指標（proxy）變化，2015 → 2025：${proxyChange}${estimated ? " · 乘客旅次採用估算" : ""}。`,
  fleetTableCaption: (estimated) =>
    `${estimated ? "紅色" : "專線"}小巴全年資料。12 月持牌車輛數為公布數字；${estimated ? "乘客旅次及持牌車輛日旅次指標（proxy）包含紅色小巴估算" : "乘客旅次採用公布總數"}。車輛日分母為十二個月的月末持牌車輛數 × 各月日曆日數的總和。`,
  basis: {
    includesEstimates: "含估算",
    estimated: "估算",
    reported: "公布數字",
  },
  composition: (year, gmb, rmb) =>
    `${year} 年公共小巴組成：專線小巴 ${gmb}%，紅色小巴（估算）${rmb}%。`,
};

export function getResearchText(language = "en") {
  return ["zh-Hant", "zh", "zh-TW", "zh-HK"].includes(language)
    ? traditionalChinese
    : english;
}
