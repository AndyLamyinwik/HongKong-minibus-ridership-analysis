// Language changes affect chart presentation only; all data and series IDs stay fixed.
export function isChinese(language = "en") {
  return ["zh-Hant", "zh", "zh-TW", "zh-HK"].includes(language);
}

export function chartFontFamily(language = "en") {
  return isChinese(language)
    ? 'DM Sans, "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif'
    : "DM Sans, sans-serif";
}

export const englishModeLabels = {
  GMB: "Green Minibuses",
  RMB: "Red Minibuses · estimated",
  PLB: "Public Light Bus total · includes estimates",
  MTR: "MTR",
  FRANCHISED_BUS: "Franchised buses",
};

export const chineseModeLabels = {
  GMB: "專線小巴",
  RMB: "紅色小巴（估算）",
  PLB: "公共小巴總計（含估算）",
  MTR: "港鐵鐵路服務",
  FRANCHISED_BUS: "專營巴士",
};

export function chartModeLabels(language = "en") {
  return isChinese(language) ? chineseModeLabels : englishModeLabels;
}
