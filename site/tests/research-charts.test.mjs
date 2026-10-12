import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  fleetOptions, fleetTooltipMarkup, modeColors, recoveryModes,
  recoveryOptions, recoveryTooltipMarkup, shareOptions, shareTooltipMarkup,
} from "../src/research-charts.js";

const research = JSON.parse(readFileSync(new URL("../public/data/research.json", import.meta.url), "utf8"));
const years = Array.from({ length: 11 }, (_, index) => String(2015 + index));
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) <= 1e-9, `${actual} differs from ${expected}`);

test("recovery bars preserve all five independent own-2019 percentages and expose a 100-percent baseline", () => {
  const chart = recoveryOptions(research);
  assert.deepEqual(chart.yAxis.data, ["GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"]);
  assert.equal(chart.yAxis.inverse, true);
  assert.equal(chart.series.length, 1);
  assert.equal(chart.series[0].type, "bar");
  assert.equal(chart.xAxis.min, 0);
  assert.equal(chart.series[0].markLine.data[0].xAxis, 100);
  for (const bar of chart.series[0].data) {
    assert.equal(bar.value, research.recovery.find(row => row.mode === bar.mode).recovery_pct);
    assert.ok(bar.value <= chart.xAxis.max, "Recovery axis must retain MTR recovery above 100%");
  }
  assert.equal(chart.series[0].data.find(row => row.mode === "RMB").value.toFixed(2), "49.18");
  assert.equal(chart.series[0].data.find(row => row.mode === "MTR").value.toFixed(2), "101.99");
  assert.match(chart.aria.description, /not market shares/);
});

test("recovery selection changes only the highlighted bar, retaining all values", () => {
  const defaultChart = recoveryOptions(research);
  for (const selectedMode of recoveryModes) {
    const selected = recoveryOptions(research, { selectedMode });
    assert.deepEqual(selected.series[0].data.map(row => row.value), defaultChart.series[0].data.map(row => row.value));
    assert.equal(selected.series[0].data.filter(row => row.itemStyle.borderWidth > 0).length, 1);
    assert.equal(selected.series[0].data.find(row => row.mode === selectedMode).itemStyle.borderWidth, 2);
  }
});

test("mobile recovery reduces tick crowding while preserving the complete 100-percent benchmark", () => {
  const desktop = recoveryOptions(research);
  const mobile = recoveryOptions(research, { mobile: true });
  assert.equal(desktop.xAxis.interval, 20);
  assert.equal(mobile.xAxis.interval, 40);
  assert.equal(mobile.xAxis.min, 0);
  assert.equal(mobile.xAxis.max, desktop.xAxis.max);
  assert.deepEqual(mobile.series[0].data, desktop.series[0].data);
  assert.equal(mobile.series[0].markLine.data[0].xAxis, 100);
  assert.equal(mobile.series[0].markLine.label.show, false);
  assert.equal(desktop.series[0].markLine.label.show, true);
  assert.match(mobile.aria.description, /own 2019 total, equal to 100 percent/);
});

test("recovery tooltips distinguish the two baseline years, Red estimates, and the PLB subtotal", () => {
  const rmb = recoveryTooltipMarkup(research, "RMB");
  assert.match(rmb, /2025/);
  assert.match(rmb, /2019 annual passenger journeys = 100%/);
  assert.match(rmb, /49\.18%/);
  assert.match(rmb, /estimated/);
  const plb = recoveryTooltipMarkup(research, "PLB");
  assert.match(plb, /85\.03%/);
  assert.match(plb, /GMB \+ RMB/);
  assert.match(plb, /subtotal/);
  assert.match(plb, /Includes estimated/);
  const gmb = recoveryTooltipMarkup(research, "GMB");
  assert.match(gmb, /91\.88%/);
  assert.match(gmb, /Reported passenger journeys/);
  assert.equal(recoveryTooltipMarkup(research, "unknown"), "");
});

test("share chart includes exactly four exclusive components and never adds PLB as a fifth", () => {
  const chart = shareOptions(research);
  assert.deepEqual(chart.series.map(series => series.id), ["GMB", "RMB", "MTR", "FRANCHISED_BUS"]);
  assert.ok(chart.series.every(series => series.id !== "PLB" && !series.stack));
  assert.deepEqual(chart.xAxis.data, years);
  for (let position = 0; position < 11; position += 1) {
    close(chart.series.reduce((sum, series) => sum + series.data[position], 0), 100);
    for (const series of chart.series) {
      assert.equal(series.data.length, 11);
      assert.equal(series.data[position], research.market_share.annual.find(row => row.mode === series.id && row.year === 2015 + position).share_pct);
      assert.ok(series.data[position] <= chart.yAxis.max);
    }
  }
  assert.match(chart.aria.description, /not a fifth component/);
  assert.match(chart.aria.description, /not the whole transport market/);
});

test("minibus share focus improves the axis scale without renormalizing the four-mode denominator", () => {
  const all = shareOptions(research);
  const focused = shareOptions(research, { focus: "minibuses" });
  assert.equal(all.yAxis.min, 0);
  assert.equal(all.yAxis.max, 50);
  assert.equal(focused.yAxis.min, 0);
  assert.equal(focused.yAxis.max, 20);
  assert.deepEqual(focused.series.map(series => series.id), ["GMB", "RMB"]);
  for (const series of focused.series) {
    assert.deepEqual(series.data, all.series.find(row => row.id === series.id).data);
  }
  assert.ok(focused.series.reduce((sum, series) => sum + series.data[0], 0) < 20);
  assert.match(focused.aria.description, /zero-to-20-percent axis/);
  assert.match(focused.aria.description, /four-mode denominator stays fixed/);
});

test("share tooltips retain annual selected-group denominators, estimates and the separately labelled PLB subtotal", () => {
  for (const focus of ["all", "minibuses"]) {
    for (const year of years) {
      const tooltip = shareTooltipMarkup(research, year, focus);
      assert.ok(tooltip.includes(`${year} · selected comparison group`));
      assert.match(tooltip, /Includes estimated RMB journeys/);
      assert.match(tooltip, /not the whole transport market/);
      assert.match(tooltip, /PLB subtotal \(GMB \+ RMB\)/);
      const denominator = research.market_share.denominators.find(row => row.year === Number(year));
      assert.ok(tooltip.includes(`${(denominator.journeys_thousands / 1000).toFixed(2)} million annual journeys`));
      assert.match(tooltip, /GMB, RMB, MTR and franchised buses/);
      if (focus === "minibuses") assert.match(tooltip, /denominator still includes all four modes/);
    }
  }
  assert.equal(shareTooltipMarkup(research, 2014), "");
});

for (const mode of ["GMB", "RMB"]) {
  test(`${mode} fleet comparison preserves December stock and annual journeys as different own-2015 indexes`, () => {
    const chart = fleetOptions(research, mode, "compare");
    assert.deepEqual(chart.series.map(series => series.id), ["licensed-stock", "annual-journeys"]);
    assert.deepEqual(chart.xAxis.data, years);
    assert.equal(chart.series[0].markLine.data[0].yAxis, 100);
    for (const series of chart.series) assert.equal(series.data[0], 100);
    const baseline = research.fleet.annual.find(row => row.mode === mode && row.year === 2015).december_licensed_vehicles;
    for (let position = 0; position < 11; position += 1) {
      const year = 2015 + position;
      const fleet = research.fleet.annual.find(row => row.mode === mode && row.year === year);
      const annual = research.annual.find(row => row.mode === mode && row.year === year);
      close(chart.series[0].data[position], 100 * fleet.december_licensed_vehicles / baseline);
      assert.equal(chart.series[1].data[position], annual.index_2015);
    }
    assert.match(chart.series[0].name, /reported/);
    if (mode === "RMB") assert.match(chart.series[1].name, /estimated/);
    assert.notEqual(chart.series[0].symbol, chart.series[1].symbol);
    assert.notEqual(chart.series[0].lineStyle.type, chart.series[1].lineStyle.type);
  });

  test(`${mode} fleet proxy uses the saved annual vehicle-day calculation rather than December fleet alone`, () => {
    const chart = fleetOptions(research, mode, "proxy");
    assert.equal(chart.series.length, 1);
    assert.equal(chart.series[0].id, "fleet-proxy");
    assert.equal(chart.series[0].data[0], 100);
    assert.equal(chart.series[0].markLine.data[0].yAxis, 100);
    const baseline = research.fleet.annual.find(row => row.mode === mode && row.year === 2015);
    for (let position = 0; position < 11; position += 1) {
      const fleet = research.fleet.annual.find(row => row.mode === mode && row.year === 2015 + position);
      const annual = research.annual.find(row => row.mode === mode && row.year === 2015 + position);
      close(fleet.journeys_per_licensed_vehicle_day_proxy, annual.journeys_thousands * 1000 / fleet.licensed_vehicle_days_proxy);
      close(chart.series[0].data[position], 100 * fleet.journeys_per_licensed_vehicle_day_proxy / baseline.journeys_per_licensed_vehicle_day_proxy);
      assert.equal(chart.series[0].data[position], fleet.index_proxy_2015);
    }
    const final = research.fleet.annual.find(row => row.mode === mode && row.year === 2025);
    const annual = research.annual.find(row => row.mode === mode && row.year === 2025);
    assert.notEqual(final.journeys_per_licensed_vehicle_day_proxy, annual.journeys_thousands * 1000 / (final.december_licensed_vehicles * 365));
    assert.match(chart.aria.description, /not December stock alone/);
    assert.match(chart.aria.description, /not a productivity measure/);
  });

  for (const measure of ["compare", "proxy"]) {
    test(`${mode} ${measure} fleet tooltip retains raw units, index baseline, and measurement independence limitations`, () => {
      const tooltip = fleetTooltipMarkup(research, 2025, mode, measure);
      assert.match(tooltip, /2025/);
      assert.match(tooltip, /own 2015 value = 100/);
      assert.match(tooltip, /does not measure deployed vehicles or productivity/);
      if (measure === "compare") {
        assert.match(tooltip, /December licensed stock · reported/);
        assert.match(tooltip, /licensed vehicles at December month-end/);
        assert.match(tooltip, /million annual journeys/);
      } else {
        assert.match(tooltip, /journeys per licensed vehicle-day \(proxy\)/);
        assert.match(tooltip, /month-end stock × calendar days/);
        assert.match(tooltip, /not December stock alone/);
      }
      if (mode === "RMB") {
        assert.match(tooltip, /estimated/);
        assert.match(tooltip, /passenger estimates use fleet inputs/);
        assert.match(tooltip, /not independent/);
      }
      assert.equal(fleetTooltipMarkup(research, 2014, mode, measure), "");
    });
  }
}

test("all chronological charts retain the full eleven-year data and endpoint labels on mobile", () => {
  const pairs = [
    [shareOptions(research), shareOptions(research, { mobile: true })],
    [shareOptions(research, { focus: "minibuses" }), shareOptions(research, { mobile: true, focus: "minibuses" })],
    ...["GMB", "RMB"].flatMap(mode => ["compare", "proxy"].map(measure => [fleetOptions(research, mode, measure), fleetOptions(research, mode, measure, { mobile: true })])),
  ];
  for (const [desktop, mobile] of pairs) {
    assert.deepEqual(mobile.xAxis.data, years);
    assert.equal(mobile.xAxis.axisLabel.showMinLabel, true);
    assert.equal(mobile.xAxis.axisLabel.showMaxLabel, true);
    assert.ok(mobile.xAxis.axisLabel.interval > desktop.xAxis.axisLabel.interval);
    assert.deepEqual(mobile.series.map(series => series.data), desktop.series.map(series => series.data));
  }
  const mobileRecovery = recoveryOptions(research, { mobile: true });
  assert.equal(mobileRecovery.series[0].data.length, 5);
  assert.match(mobileRecovery.yAxis.axisLabel.formatter("RMB"), /Red Minibuses.*estimated/s);
  assert.match(mobileRecovery.yAxis.axisLabel.formatter("PLB"), /PLB total.*includes est\./s);
});

test("all chart types respect reduced-motion preferences and expose analytical descriptions", () => {
  const constructors = [
    options => recoveryOptions(research, options),
    options => shareOptions(research, options),
    ...["GMB", "RMB"].flatMap(mode => ["compare", "proxy"].map(measure => options => fleetOptions(research, mode, measure, options))),
  ];
  for (const create of constructors) {
    const reduced = create({ reducedMotion: true });
    assert.equal(reduced.animation, false);
    assert.equal(create({ reducedMotion: false }).animation, true);
    assert.equal(reduced.aria.enabled, true);
    assert.match(reduced.aria.description, /accessible data table/);
  }
});

test("four market-share series remain distinguishable by symbol as well as color", () => {
  const chart = shareOptions(research);
  assert.equal(new Set(chart.series.map(series => series.symbol)).size, 4);
  assert.equal(new Set(chart.series.map(series => series.lineStyle.color)).size, 4);
  assert.equal(chart.series.find(series => series.id === "RMB").lineStyle.type, "dashed");
  assert.match(chart.series.find(series => series.id === "RMB").name, /estimated/);
  assert.ok(chart.series.every(series => !series.smooth));
  assert.equal(modeColors.MTR, "#376781");
  assert.equal(modeColors.FRANCHISED_BUS, "#87632f");
});

test("chart helpers fail clearly for unsupported service, measure or focus controls", () => {
  assert.throws(() => recoveryOptions(research, { selectedMode: "unknown" }), /Unknown recovery service/);
  assert.throws(() => shareOptions(research, { focus: "unknown" }), /Unknown market-share focus/);
  assert.throws(() => shareTooltipMarkup(research, 2025, "unknown"), /Unknown market-share focus/);
  assert.throws(() => fleetOptions(research, "PLB"), /Unknown minibus service/);
  assert.throws(() => fleetOptions(research, "GMB", "unknown"), /Unknown fleet measure/);
  const incomplete = structuredClone(research);
  incomplete.recovery.pop();
  assert.throws(() => recoveryOptions(incomplete), /Incomplete recovery observations/);
});

test("chart tooltip adapters use the selected category or mode without dropping estimation labels", () => {
  assert.equal(recoveryOptions(research).tooltip.formatter({ data: { mode: "RMB" } }), recoveryTooltipMarkup(research, "RMB"));
  assert.equal(shareOptions(research).tooltip.formatter([{ axisValue: "2025" }]), shareTooltipMarkup(research, 2025));
  assert.equal(fleetOptions(research, "RMB", "proxy").tooltip.formatter([{ axisValue: "2025" }]), fleetTooltipMarkup(research, 2025, "RMB", "proxy"));
  assert.equal(shareOptions(research).tooltip.formatter([]), "");
  assert.equal(fleetOptions(research).tooltip.formatter([]), "");
});

test("chart series stay chronological if the additive source rows arrive in reverse order", () => {
  const reversed = structuredClone(research);
  reversed.market_share.annual.reverse();
  reversed.fleet.annual.reverse();
  reversed.annual.reverse();
  reversed.recovery.reverse();
  assert.deepEqual(recoveryOptions(reversed).series[0].data, recoveryOptions(research).series[0].data);
  assert.deepEqual(shareOptions(reversed).series.map(series => series.data), shareOptions(research).series.map(series => series.data));
  for (const mode of ["GMB", "RMB"]) {
    for (const measure of ["compare", "proxy"]) {
      assert.deepEqual(fleetOptions(reversed, mode, measure).series.map(series => series.data), fleetOptions(research, mode, measure).series.map(series => series.data));
    }
  }
});
