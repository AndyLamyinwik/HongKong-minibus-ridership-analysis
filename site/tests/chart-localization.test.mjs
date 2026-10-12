import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { chartOptions, tooltipMarkup } from "../src/chart.js";
import {
  fleetOptions, fleetTooltipMarkup, getModeLabels, modeLabels,
  recoveryModes, recoveryOptions, recoveryTooltipMarkup,
  shareOptions, shareTooltipMarkup,
} from "../src/research-charts.js";

const research = JSON.parse(readFileSync(new URL("../public/data/research.json", import.meta.url), "utf8"));
const visibleText = (markup) => markup.replace(/<[^>]*>/g, " ");
const numbers = (markup) => visibleText(markup).match(/-?\d[\d,]*(?:\.\d+)?/g) || [];
const englishFallback = /\b(?:journeys|million|estimated|reported|Recovery|Denominator|stock|productivity|subtotal|Green|Red|Minibuses|Franchised|comparison|index|market)\b/i;

function numericPresentation(chart) {
  return {
    grid: chart.grid,
    xAxis: { data: chart.xAxis.data, min: chart.xAxis.min, max: chart.xAxis.max, interval: chart.xAxis.interval },
    yAxis: { data: chart.yAxis.data, min: chart.yAxis.min, max: chart.yAxis.max, interval: chart.yAxis.interval },
    animation: chart.animation,
    series: chart.series.map((series) => ({
      id: series.id,
      type: series.type,
      data: series.data,
      symbol: series.symbol,
      symbolSize: series.symbolSize,
      lineStyle: series.lineStyle,
      itemStyle: series.itemStyle,
      markLine: series.markLine?.data,
      markArea: series.markArea?.data.map((span) => span.map(({ name, ...point }) => point)),
    })),
  };
}

const factories = [
  ...["index", "absolute"].map(view => ({ name: `annual ${view}`, make: options => chartOptions(research, view, options) })),
  ...[null, ...recoveryModes].map(selectedMode => ({ name: `recovery ${selectedMode || "all"}`, make: options => recoveryOptions(research, { ...options, selectedMode }) })),
  ...["all", "minibuses"].map(focus => ({ name: `share ${focus}`, make: options => shareOptions(research, { ...options, focus }) })),
  ...["GMB", "RMB"].flatMap(mode => ["compare", "proxy"].map(measure => ({ name: `${mode} fleet ${measure}`, make: options => fleetOptions(research, mode, measure, options) }))),
];

for (const { name, make } of factories) {
  test(`${name} changes language without changing any data, axis extent, baseline, symbol or color`, () => {
    for (const mobile of [false, true]) {
      for (const reducedMotion of [false, true]) {
        const english = make({ language: "en", mobile, reducedMotion });
        const chinese = make({ language: "zh-Hant", mobile, reducedMotion });
        assert.deepEqual(numericPresentation(chinese), numericPresentation(english));
        assert.match(chinese.aria.description, /[\u3400-\u9fff]/);
        assert.doesNotMatch(chinese.aria.description, englishFallback);
        assert.match(chinese.aria.description, /資料表/);
        assert.match(chinese.textStyle.fontFamily, /Microsoft JhengHei/);
        for (const series of chinese.series) {
          assert.match(series.name, /[\u3400-\u9fff]/);
          assert.doesNotMatch(series.name, englishFallback);
        }
      }
    }
  });
}

test("English defaults and existing mode-label exports retain their exact presentation", () => {
  assert.equal(modeLabels.GMB, "Green Minibuses");
  assert.equal(modeLabels.RMB, "Red Minibuses · estimated");
  assert.deepEqual(getModeLabels(), modeLabels);
  for (const { make } of factories) {
    assert.equal(JSON.stringify(make({})), JSON.stringify(make({ language: "en" })));
  }
  assert.equal(tooltipMarkup(research, 2025, "index"), tooltipMarkup(research, 2025, "index", "en"));
  assert.equal(recoveryTooltipMarkup(research, "RMB"), recoveryTooltipMarkup(research, "RMB", "en"));
  assert.equal(shareTooltipMarkup(research, 2025), shareTooltipMarkup(research, 2025, "all", "en"));
  assert.equal(fleetTooltipMarkup(research, 2025), fleetTooltipMarkup(research, 2025, "GMB", "compare", "en"));
});

test("Traditional Chinese mode labels retain the estimate and subtotal qualifications", () => {
  const labels = getModeLabels("zh-Hant");
  assert.deepEqual(labels, {
    GMB: "專線小巴", RMB: "紅色小巴（估算）", PLB: "公共小巴總計（含估算）",
    MTR: "港鐵鐵路服務", FRANCHISED_BUS: "專營巴士",
  });
  for (const alias of ["zh", "zh-TW", "zh-HK"]) assert.deepEqual(getModeLabels(alias), labels);
  assert.deepEqual(getModeLabels("unsupported"), modeLabels);
});

test("annual tooltips translate both views while preserving all two-decimal values and the own-2015 baseline", () => {
  for (const view of ["index", "absolute"]) {
    for (let year = 2015; year <= 2025; year += 1) {
      const english = tooltipMarkup(research, year, view);
      const chinese = tooltipMarkup(research, year, view, "zh-Hant");
      assert.deepEqual(numbers(chinese), numbers(english));
      assert.match(chinese, /專線小巴/);
      assert.match(chinese, /紅色小巴（估算）/);
      assert.match(chinese, /百萬旅次/);
      assert.doesNotMatch(visibleText(chinese), englishFallback);
      if (view === "index") assert.match(chinese, /各自的 2015 年 = 100/);
      assert.equal(chartOptions(research, view, { language: "zh-Hant" }).tooltip.formatter([{ axisValue: String(year) }]), chinese);
    }
  }
  const chinese = chartOptions(research, "index", { language: "zh-Hant" });
  assert.equal(chinese.series[0].markArea.data[0][0].name, "擾動時期");
  assert.equal(tooltipMarkup(research, 2014, "index", "zh-Hant"), "");
});

test("recovery tooltips translate all five services, own denominators, reported journeys and the estimated PLB subtotal", () => {
  for (const mode of recoveryModes) {
    const chinese = recoveryTooltipMarkup(research, mode, "zh-Hant");
    assert.deepEqual(numbers(chinese), numbers(recoveryTooltipMarkup(research, mode)));
    assert.match(chinese, /2019 年度乘客旅次 = 100%/);
    assert.doesNotMatch(visibleText(chinese), englishFallback);
    assert.equal(recoveryOptions(research, { language: "zh-Hant" }).tooltip.formatter({ data: { mode } }), chinese);
    if (["RMB", "PLB"].includes(mode)) assert.match(chinese, /包含紅色小巴估算旅次/);
    else assert.match(chinese, /乘客旅次採用公布數字/);
    if (mode === "PLB") assert.match(chinese, /專線小巴與紅色小巴之和，以小計呈現/);
  }
  assert.equal(recoveryTooltipMarkup(research, "unknown", "zh-Hant"), "");
});

test("mobile recovery uses compact Chinese labels with visible estimation qualifications", () => {
  const chart = recoveryOptions(research, { language: "zh-Hant", mobile: true });
  assert.equal(chart.yAxis.axisLabel.formatter("RMB"), "紅色小巴\n（估算）");
  assert.equal(chart.yAxis.axisLabel.formatter("PLB"), "公共小巴總計\n（含估算）");
  assert.equal(chart.yAxis.axisLabel.formatter("MTR"), "港鐵\n鐵路服務");
  for (const mode of recoveryModes) {
    for (const line of chart.yAxis.axisLabel.formatter(mode).split("\n")) assert.ok(line.length <= 6);
  }
  assert.equal(chart.series[0].markLine.data[0].xAxis, 100);
  assert.equal(chart.series[0].markLine.label.show, false);
});

test("Chinese share tooltips preserve four-mode denominators, the PLB subtotal and the market-scope limitation in both focuses", () => {
  for (const focus of ["all", "minibuses"]) {
    for (let year = 2015; year <= 2025; year += 1) {
      const chinese = shareTooltipMarkup(research, year, focus, "zh-Hant");
      assert.deepEqual(numbers(chinese), numbers(shareTooltipMarkup(research, year, focus)));
      assert.match(chinese, /公共小巴小計（專線小巴 \+ 紅色小巴）/);
      assert.match(chinese, /分母：專線小巴、紅色小巴、港鐵鐵路服務及專營巴士合計/);
      assert.match(chinese, /包含紅色小巴估算旅次/);
      assert.match(chinese, /並非整體交通運輸市場/);
      assert.doesNotMatch(visibleText(chinese), englishFallback);
      if (focus === "minibuses") assert.match(chinese, /分母仍包含全部四種模式/);
      assert.equal(shareOptions(research, { language: "zh-Hant", focus }).tooltip.formatter([{ axisValue: String(year) }]), chinese);
    }
  }
  assert.equal(shareTooltipMarkup(research, 2014, "all", "zh-Hant"), "");
});

for (const mode of ["GMB", "RMB"]) {
  for (const measure of ["compare", "proxy"]) {
    test(`Chinese ${mode} ${measure} tooltip preserves reported stock, raw units, month-end proxy definitions and independence caveats`, () => {
      for (let year = 2015; year <= 2025; year += 1) {
        const chinese = fleetTooltipMarkup(research, year, mode, measure, "zh-Hant");
        // "December" becomes "12 月" in Chinese; this month label is not a changed data value.
        assert.deepEqual(numbers(chinese.replaceAll("12 月", "十二月")), numbers(fleetTooltipMarkup(research, year, mode, measure)));
        assert.match(chinese, /其本身的 2015 年數值設為 100/);
        assert.match(chinese, /並不代表實際出車數或生產力/);
        assert.doesNotMatch(visibleText(chinese), englishFallback);
        if (measure === "compare") {
          assert.match(chinese, /12 月持牌車隊 · 公布數字/);
          assert.match(chinese, /12 月月底共有/);
          assert.match(chinese, /百萬年度旅次/);
        } else {
          assert.match(chinese, /持牌車輛日旅次指標（proxy）/);
          assert.match(chinese, /每持牌車輛日/);
          assert.match(chinese, /月底持牌車數 × 該月曆日數加總/);
          assert.match(chinese, /並非只採用 12 月車隊數/);
        }
        if (mode === "RMB") {
          assert.match(chinese, /估算/);
          assert.match(chinese, /乘客估算採用車隊資料；兩項指標並非獨立/);
        }
        assert.equal(fleetOptions(research, mode, measure, { language: "zh-Hant" }).tooltip.formatter([{ axisValue: String(year) }]), chinese);
      }
      assert.equal(fleetTooltipMarkup(research, 2014, mode, measure, "zh-Hant"), "");
    });
  }
}

test("constructing every bilingual presentation leaves the research data unchanged", () => {
  const before = JSON.stringify(research);
  for (const { make } of factories) {
    make({ language: "en" });
    make({ language: "zh-Hant" });
  }
  assert.equal(JSON.stringify(research), before);
});
