export const annualMessages = {
  en: {
    gmb: "GMB ", rmb: "RMB · estimated ", indexValue: "{value} index", volumeValue: "{value} million",
    indexUnit: "Index · own 2015 annual journeys = 100", volumeUnit: "Annual passenger journeys · millions",
    indexIntro: "Two services. One starting point. Explore how their paths changed.",
    volumeIntro: "Compare the annual volume of passenger journeys for each service.",
    indexDescription: "Annual Green and estimated Red Minibus passenger journeys, 2015–2025. Index: each service’s own 2015 journeys = 100. Use the year selector or data table below for accessible values.",
    volumeDescription: "Annual Green and estimated Red Minibus passenger journeys, 2015–2025. Units: millions of journeys. Use the year selector or data table below for accessible values.",
    loading: "Loading the verified research data…", chartLoading: "Annual passenger-journey chart is loading.",
    empty: "No annual observations are available in this research file.",
    unavailable: "The verified research data could not be loaded. Please try again.",
    chartUnavailable: "Annual passenger-journey chart is unavailable.",
    tableLoading: "Research data is loading.",
    tableUnavailable: "Annual data is unavailable. Use the linked research documentation or retry.",
  },
  "zh-Hant": {
    gmb: "專線小巴 ", rmb: "紅色小巴・估算 ", indexValue: "{value} 指數", volumeValue: "{value} 百萬旅次",
    indexUnit: "指數・各服務的 2015 年度旅次 = 100", volumeUnit: "年度乘客旅次・百萬旅次",
    indexIntro: "兩種服務，同一起點。探索各自的歷年變化。",
    volumeIntro: "比較兩種小巴服務每年的乘客旅次規模。",
    indexDescription: "2015–2025 年專線小巴與紅色小巴（估算）的年度乘客旅次。指數以各服務的 2015 年旅次 = 100。可使用年份選單或下方資料表查看數值。",
    volumeDescription: "2015–2025 年專線小巴與紅色小巴（估算）的年度乘客旅次，單位為百萬旅次。可使用年份選單或下方資料表查看數值。",
    loading: "正在載入已驗證的研究資料…", chartLoading: "正在載入年度乘客旅次圖。",
    empty: "這份研究檔案沒有可用的年度觀測資料。",
    unavailable: "未能載入已驗證的研究資料，請重試。",
    chartUnavailable: "年度乘客旅次圖暫時無法使用。",
    tableLoading: "正在載入研究資料。",
    tableUnavailable: "年度資料暫時無法使用，請查看連結中的研究文件或重試。",
  },
};

export function annualText(key, language = "en", values = {}) {
  const text = (annualMessages[language] ?? annualMessages.en)[key];
  return text.replace(/\{(\w+)\}/g, (_, name) => String(values[name]));
}
