import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";

const root = new URL("../../", import.meta.url);
const data = JSON.parse(
  readFileSync(
    new URL("../public/data/research.json", import.meta.url),
    "utf8",
  ),
);

// Analytical CSV fields have no embedded line breaks or quoted numeric values.
function csv(filename) {
  const [header, ...lines] = readFileSync(
    new URL(`analysis/outputs/${filename}`, root),
    "utf8",
  )
    .trim()
    .split(/\r?\n/);
  const columns = header.split(",");
  return lines.map((line) =>
    Object.fromEntries(
      line.split(",").map((value, index) => [columns[index], value]),
    ),
  );
}

const annual = csv("annual_ridership.csv");
const endpoints = csv("endpoint_comparison.csv");
const recovery = csv("recovery_2019.csv");
const composition = csv("annual_minibus_composition.csv");
const segments = csv("trend_segments.csv");
const marketShares = csv("annual_market_share.csv");
const annualFleet = csv("annual_fleet.csv");
const find = (rows, mode, year) =>
  rows.find(
    (row) =>
      row.mode === mode && (year === undefined || Number(row.year) === year),
  );
const close = (actual, expected, tolerance = 1e-9) =>
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `${actual} differs from ${expected}`,
  );

test("study contract covers all eleven complete years and 132 months", () => {
  assert.equal(data.schema_version, 1);
  assert.deepEqual(data.study, {
    start_year: 2015,
    end_year: 2025,
    months: 132,
  });
  assert.equal(data.annual.length, 22);
  const expected = Array.from({ length: 11 }, (_, offset) => 2015 + offset);
  for (const mode of ["GMB", "RMB"]) {
    assert.deepEqual(
      data.annual.filter((row) => row.mode === mode).map((row) => row.year),
      expected,
    );
  }
  assert.equal(
    new Set(data.annual.map((row) => `${row.year}/${row.mode}`)).size,
    22,
  );
});

test("all chart observations retain exact annual CSV totals and estimation flags", () => {
  for (const row of data.annual) {
    const source = find(annual, row.mode, row.year);
    assert.equal(
      row.journeys_thousands,
      Number(source.passenger_journeys_thousands),
    );
    assert.ok(
      Number.isFinite(row.journeys_thousands) && row.journeys_thousands > 0,
    );
    assert.equal(row.includes_estimates, source.includes_estimates === "1");
    assert.equal(row.measurement_basis, source.measurement_basis);
    assert.equal(row.is_provisional, source.is_provisional === "1");
    assert.equal(row.is_revised, source.is_revised === "1");
    assert.equal(row.includes_estimates, row.mode === "RMB");
    assert.equal(
      row.measurement_basis,
      row.mode === "RMB" ? "estimated" : "reported",
    );
  }
});

test("annual chart observations reconcile to validated PLB totals", () => {
  for (let year = 2015; year <= 2025; year += 1) {
    const total = data.annual
      .filter((row) => row.year === year)
      .reduce((sum, row) => sum + row.journeys_thousands, 0);
    close(
      total,
      Number(find(annual, "PLB", year).passenger_journeys_thousands),
      1e-7,
    );
  }
});

test("2015 chart index uses the existing Streamlit annual display definition", () => {
  for (const row of data.annual) {
    const baseline = data.annual.find(
      (candidate) => candidate.mode === row.mode && candidate.year === 2015,
    ).journeys_thousands;
    assert.equal(row.index_2015, (100 * row.journeys_thousands) / baseline);
    assert.ok(Number.isFinite(row.index_2015));
    if (row.year === 2015) assert.equal(row.index_2015, 100);
  }
});

test("four KPI values are copied unrounded from authoritative endpoint and recovery outputs", () => {
  assert.deepEqual(Object.keys(data.kpis), [
    "plb_change_pct",
    "gmb_change_pct",
    "rmb_change_pct",
    "rmb_recovery_2019_pct",
  ]);
  assert.equal(
    data.kpis.plb_change_pct,
    Number(find(endpoints, "PLB").change_2015_2025_pct),
  );
  assert.equal(
    data.kpis.gmb_change_pct,
    Number(find(endpoints, "GMB").change_2015_2025_pct),
  );
  assert.equal(
    data.kpis.rmb_change_pct,
    Number(find(endpoints, "RMB").change_2015_2025_pct),
  );
  assert.equal(
    data.kpis.rmb_recovery_2019_pct,
    Number(find(recovery, "RMB").recovery_pct),
  );
  assert.equal(
    data.kpis.rmb_recovery_2019_pct,
    Number(find(endpoints, "RMB").recovery_2025_vs_2019_pct),
  );
});

test("rounded headline figures agree with the approved research findings", () => {
  assert.deepEqual(
    Object.values(data.kpis).map((value) => value.toFixed(2)),
    ["-19.51", "-11.17", "-58.00", "49.18"],
  );
});

test("narrative values use saved composition and recent trend outputs", () => {
  assert.equal(
    data.narrative.gmb_share_2015_pct,
    Number(find(composition, "GMB", 2015).share_of_plb_pct),
  );
  assert.equal(
    data.narrative.gmb_share_2025_pct,
    Number(find(composition, "GMB", 2025).share_of_plb_pct),
  );
  for (const mode of ["GMB", "RMB"]) {
    const segment = segments.find(
      (row) => row.mode === mode && row.segment === "2023_to_2025",
    );
    assert.equal(
      data.narrative[`${mode.toLowerCase()}_change_2023_2025_pct`],
      Number(segment.change_pct),
    );
    assert.equal(segment.start_year, "2023");
    assert.equal(segment.end_year, "2025");
  }
});

test("provenance records current local input hashes rather than approximate source descriptions", () => {
  assert.equal(Object.keys(data.provenance.input_sha256).length, 17);
  for (const [filename, expected] of Object.entries(
    data.provenance.input_sha256,
  )) {
    assert.match(expected, /^[a-f0-9]{64}$/);
    assert.equal(
      createHash("sha256")
        .update(readFileSync(new URL(filename, root)))
        .digest("hex"),
      expected,
      filename,
    );
  }
});

test("official source vintage, publisher and terms match the existing source manifest", () => {
  const sources = JSON.parse(
    readFileSync(new URL("config/sources.json", root), "utf8"),
  );
  for (const key of [
    "publisher",
    "snapshot_retrieved_on",
    "expected_revision_date",
    "terms_url",
  ]) {
    assert.equal(data.provenance[key], sources[key]);
  }
  assert.equal(data.provenance.official_urls.length, 3);
  for (const url of data.provenance.official_urls) {
    assert.ok(["data.gov.hk", "www.td.gov.hk"].includes(new URL(url).hostname));
  }
  assert.ok(
    data.provenance.limitations.some((text) => text.includes("estimates")),
  );
  assert.ok(
    data.provenance.limitations.some((text) => text.includes("causation")),
  );
});

test("units retain annual flow meaning and distinguish the relative index", () => {
  assert.equal(data.units.journeys, "thousands of passenger journeys");
  assert.equal(data.units.index, "own 2015 annual journeys = 100");
  assert.equal(data.units.percentage, "percent");
  assert.equal(
    find(annual, "GMB", 2025).passenger_journeys_thousands,
    "495802.414",
  );
  assert.equal(
    find(annual, "RMB", 2025).passenger_journeys_thousands,
    "50742.718",
  );
});

test("five recovery bars retain the saved own-2019 benchmark and permit values above 100", () => {
  const expectedModes = ["GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"];
  assert.deepEqual(data.recovery.map((row) => row.mode), expectedModes);
  assert.equal(data.recovery_definition.baseline_year, 2019);
  assert.equal(data.recovery_definition.reference_year, 2025);
  assert.equal(data.recovery_definition.unit, "percent");
  for (const row of data.recovery) {
    const source = find(recovery, row.mode);
    assert.equal(row.recovery_pct, Number(source.recovery_pct));
    assert.equal(row.measurement_basis, source.measurement_basis);
    assert.equal(row.includes_estimates, source.includes_estimates === "1");
    close(row.recovery_pct, 100 * Number(source.journeys_2025_thousands) / Number(source.baseline_2019_journeys_thousands));
  }
  assert.deepEqual(data.recovery.map((row) => row.recovery_pct.toFixed(2)), ["91.88", "49.18", "85.03", "101.99", "91.63"]);
  assert.ok(data.recovery.find((row) => row.mode === "MTR").recovery_pct > 100);
});

test("comparison-group series contain four exclusive components and a separately marked PLB subtotal", () => {
  const components = ["GMB", "RMB", "MTR", "FRANCHISED_BUS"];
  assert.deepEqual(data.market_share.components, components);
  assert.equal(data.market_share.denominator_includes_estimates, true);
  assert.equal(data.market_share.annual.length, 55);
  assert.equal(data.market_share.denominators.length, 11);
  assert.equal(new Set(data.market_share.annual.map((row) => `${row.year}/${row.mode}`)).size, 55);
  assert.equal(new Set(data.market_share.denominators.map((row) => row.year)).size, 11);
  for (let year = 2015; year <= 2025; year += 1) {
    const rows = data.market_share.annual.filter((row) => row.year === year);
    assert.deepEqual(rows.map((row) => row.mode), [...components, "PLB"]);
    for (const row of rows) {
      assert.equal(row.is_subtotal, row.mode === "PLB");
      assert.equal(row.includes_estimates, ["RMB", "PLB"].includes(row.mode));
      if (row.mode !== "PLB") {
        const source = find(marketShares, row.mode, year);
        assert.equal(row.share_pct, Number(source.share_pct));
        assert.equal(row.measurement_basis, source.measurement_basis);
      }
    }
  }
});

test("all comparison-group denominators are positive and exclude repeated PLB journeys", () => {
  for (const denominator of data.market_share.denominators) {
    const components = data.market_share.components.map((mode) => Number(find(annual, mode, denominator.year).passenger_journeys_thousands));
    assert.ok(Number.isFinite(denominator.journeys_thousands) && denominator.journeys_thousands > 0);
    close(denominator.journeys_thousands, components.reduce((sum, value) => sum + value, 0), 1e-7);
    for (const mode of data.market_share.components) {
      assert.equal(denominator.journeys_thousands, Number(find(marketShares, mode, denominator.year).comparison_group_journeys_thousands));
    }
    const subtotal = Number(find(annual, "PLB", denominator.year).passenger_journeys_thousands);
    assert.ok(Math.abs(denominator.journeys_thousands - (components.reduce((sum, value) => sum + value, 0) + subtotal)) > 1);
  }
});

test("stackable shares sum to 100 and PLB is exactly the GMB/RMB subtotal in every year", () => {
  for (let year = 2015; year <= 2025; year += 1) {
    const rows = data.market_share.annual.filter((row) => row.year === year);
    const components = rows.filter((row) => data.market_share.components.includes(row.mode));
    close(components.reduce((sum, row) => sum + row.share_pct, 0), 100);
    const gmb = rows.find((row) => row.mode === "GMB");
    const rmb = rows.find((row) => row.mode === "RMB");
    const plb = rows.find((row) => row.mode === "PLB");
    assert.equal(plb.share_pct, gmb.share_pct + rmb.share_pct);
    const denominator = data.market_share.denominators.find((row) => row.year === year).journeys_thousands;
    close(plb.share_pct, 100 * Number(find(annual, "PLB", year).passenger_journeys_thousands) / denominator);
  }
});

test("share endpoints retain percentage-point change and approved within-PLB composition", () => {
  const endpoints = data.market_share.endpoints;
  assert.equal(endpoints.plb_share_2015_pct, data.market_share.annual.find((row) => row.mode === "PLB" && row.year === 2015).share_pct);
  assert.equal(endpoints.plb_share_2025_pct, data.market_share.annual.find((row) => row.mode === "PLB" && row.year === 2025).share_pct);
  assert.equal(endpoints.plb_share_change_pp, endpoints.plb_share_2025_pct - endpoints.plb_share_2015_pct);
  assert.deepEqual(Object.values(endpoints).map((value) => value.toFixed(2)), ["16.99", "14.32", "-2.67"]);
  assert.equal(data.units.share_change, "percentage points");
  assert.equal(data.narrative.gmb_share_2015_pct.toFixed(2), "82.21");
  assert.equal(data.narrative.gmb_share_2025_pct.toFixed(2), "90.72");
});

test("fleet observations preserve reported December stock and independently qualified annual proxy inputs", () => {
  assert.equal(data.fleet.annual.length, 22);
  assert.equal(new Set(data.fleet.annual.map((row) => `${row.year}/${row.mode}`)).size, 22);
  assert.equal(data.fleet.stock_measurement_basis, "reported");
  for (const row of data.fleet.annual) {
    const source = find(annualFleet, row.mode, row.year);
    const baseline = find(annualFleet, row.mode, 2015);
    assert.equal(row.december_licensed_vehicles, Number(source.december_licensed_vehicles));
    assert.equal(row.licensed_vehicle_days_proxy, Number(source.licensed_vehicle_days_proxy));
    assert.equal(row.journeys_per_licensed_vehicle_day_proxy, Number(source.average_daily_journeys_per_licensed_vehicle));
    assert.ok(Number.isInteger(row.december_licensed_vehicles) && row.december_licensed_vehicles > 0);
    assert.ok(Number.isInteger(row.licensed_vehicle_days_proxy) && row.licensed_vehicle_days_proxy > 0);
    assert.equal(row.stock_measurement_basis, "reported");
    assert.equal(row.proxy_measurement_basis, row.mode === "RMB" ? "estimated" : "reported");
    assert.equal(row.measurement_basis, row.proxy_measurement_basis);
    assert.equal(row.includes_estimates, row.mode === "RMB");
    assert.equal(row.index_stock_2015, 100 * row.december_licensed_vehicles / Number(baseline.december_licensed_vehicles));
    assert.equal(row.index_proxy_2015, 100 * row.journeys_per_licensed_vehicle_day_proxy / Number(baseline.average_daily_journeys_per_licensed_vehicle));
    close(row.journeys_per_licensed_vehicle_day_proxy, Number(source.annual_passenger_journeys_thousands) * 1000 / Number(source.licensed_vehicle_days_proxy));
    if (row.year === 2015) {
      assert.equal(row.index_stock_2015, 100);
      assert.equal(row.index_proxy_2015, 100);
    }
    assert.equal(Object.hasOwn(row, "journeys_thousands"), false, "annual passenger journeys are already available in data.annual");
  }
});

test("fleet proxy denominators reproduce calendar-weighted month-end stocks rather than December-only ratios", () => {
  const [header, ...lines] = readFileSync(new URL("data/processed/monthly_minibus_fleet.csv", root), "utf8").trim().split(/\r?\n/);
  const columns = header.split(",");
  const monthly = lines.map((line) => Object.fromEntries(line.split(",").map((value, index) => [columns[index], value])));
  for (const row of data.fleet.annual) {
    const records = monthly.filter((record) => record.mode === row.mode && Number(record.month.slice(0, 4)) === row.year);
    assert.equal(records.length, 12);
    const vehicleDays = records.reduce((sum, record) => {
      assert.equal(record.measurement_basis, "reported");
      const month = Number(record.month.slice(5, 7));
      return sum + Number(record.licensed_vehicles) * new Date(Date.UTC(row.year, month, 0)).getUTCDate();
    }, 0);
    assert.equal(row.licensed_vehicle_days_proxy, vehicleDays);
    assert.equal(row.december_licensed_vehicles, Number(records.find((record) => record.month.endsWith("-12-01")).licensed_vehicles));
    const days = Number(find(annualFleet, row.mode, row.year).calendar_days);
    const decemberOnlyProxy = Number(find(annual, row.mode, row.year).passenger_journeys_thousands) * 1000 / (days * row.december_licensed_vehicles);
    assert.ok(Math.abs(row.journeys_per_licensed_vehicle_day_proxy - decemberOnlyProxy) > 0.001);
  }
});

test("fleet endpoint counts and proxy changes match the verified structural findings", () => {
  const green = data.fleet.endpoints.find((row) => row.mode === "GMB");
  const red = data.fleet.endpoints.find((row) => row.mode === "RMB");
  assert.deepEqual([green.december_vehicles_2015, green.december_vehicles_2025], [3203, 3360]);
  assert.deepEqual([red.december_vehicles_2015, red.december_vehicles_2025], [1141, 693]);
  assert.equal(green.stock_change_pct.toFixed(2), "4.90");
  assert.equal(red.stock_change_pct.toFixed(2), "-39.26");
  assert.equal(green.proxy_change_pct.toFixed(2), "-16.00");
  assert.equal(red.proxy_change_pct.toFixed(2), "-30.77");
  for (const row of data.fleet.endpoints) {
    const start = data.fleet.annual.find((candidate) => candidate.mode === row.mode && candidate.year === 2015);
    const end = data.fleet.annual.find((candidate) => candidate.mode === row.mode && candidate.year === 2025);
    assert.equal(row.stock_change_pct, 100 * (end.december_licensed_vehicles / start.december_licensed_vehicles - 1));
    assert.equal(row.proxy_change_pct, 100 * (end.journeys_per_licensed_vehicle_day_proxy / start.journeys_per_licensed_vehicle_day_proxy - 1));
  }
  assert.match(data.fleet.definitions.proxy, /sum\(month-end licensed vehicles × calendar days\)/);
  assert.match(data.fleet.definitions.proxy, /journeys in thousands × 1,000/);
  assert.ok(data.provenance.limitations.some((text) => text.includes("partly mechanical")));
  assert.ok(data.provenance.limitations.some((text) => text.includes("specific revision causes remain unresolved")));
});
