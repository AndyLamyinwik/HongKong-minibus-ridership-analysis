import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  selectedFleetRow, selectedShareRows, validateFleet,
  validateMarketShare, validateRecovery,
} from "../src/research-data.js";

const research = JSON.parse(readFileSync(new URL("../public/data/research.json", import.meta.url), "utf8"));
const copy = () => structuredClone(research);
const shareRow = (data, mode = "GMB", year = 2025) => data.market_share.annual.find(row => row.mode === mode && row.year === year);
const fleetRow = (data, mode = "RMB", year = 2025) => data.fleet.annual.find(row => row.mode === mode && row.year === year);
const recoveryRow = (data, mode = "RMB") => data.recovery.find(row => row.mode === mode);

test("all three research contracts accept the authentic export without altering its values", () => {
  const candidate = copy();
  assert.equal(validateRecovery(candidate), candidate.recovery);
  assert.equal(validateMarketShare(candidate), candidate.market_share);
  assert.equal(validateFleet(candidate), candidate.fleet);
  assert.deepEqual(candidate, research);
  assert.ok(recoveryRow(candidate, "MTR").recovery_pct > 100);
});

test("research validators accept chronological completeness independently of source row order", () => {
  const candidate = copy();
  candidate.annual.reverse();
  candidate.recovery.reverse();
  candidate.market_share.annual.reverse();
  candidate.market_share.denominators.reverse();
  candidate.fleet.annual.reverse();
  candidate.fleet.endpoints.reverse();
  assert.doesNotThrow(() => validateRecovery(candidate));
  assert.doesNotThrow(() => validateMarketShare(candidate));
  assert.doesNotThrow(() => validateFleet(candidate));
});

const recoveryCases = [
  ["missing recovery chapter", data => { delete data.recovery; }, /missing or incomplete/],
  ["empty recovery chapter", data => { data.recovery = []; }, /missing or incomplete/],
  ["missing recovery service", data => { data.recovery.pop(); }, /missing or incomplete/],
  ["wrong stated baseline year", data => { data.recovery_definition.baseline_year = 2015; }, /missing or incomplete/],
  ["wrong reference year", data => { data.recovery_definition.reference_year = 2024; }, /missing or incomplete/],
  ["duplicate recovery service", data => { data.recovery[1] = { ...data.recovery[0] }; }, /invalid measurements/],
  ["unknown recovery service", data => { data.recovery[0].mode = "TAXI"; }, /invalid measurements/],
  ["non-finite recovery", data => { recoveryRow(data).recovery_pct = NaN; }, /invalid measurements/],
  ["zero recovery", data => { recoveryRow(data).recovery_pct = 0; }, /invalid measurements/],
  ["Red recovery falsely marked reported", data => { recoveryRow(data).measurement_basis = "reported"; }, /invalid measurements/],
  ["Red recovery estimate flag removed", data => { recoveryRow(data).includes_estimates = false; }, /invalid measurements/],
  ["PLB aggregate estimates omitted", data => { recoveryRow(data, "PLB").includes_estimates = false; }, /invalid measurements/],
  ["Green recovery falsely marked estimated", data => { recoveryRow(data, "GMB").includes_estimates = true; }, /invalid measurements/],
  ["2015 journey baseline substituted for 2019", data => { recoveryRow(data, "GMB").recovery_pct = data.annual.find(row => row.mode === "GMB" && row.year === 2025).index_2015; }, /stated 2019 baseline/],
  ["PLB recovery replaced by an unweighted service average", data => { recoveryRow(data, "PLB").recovery_pct = (recoveryRow(data, "GMB").recovery_pct + recoveryRow(data, "RMB").recovery_pct) / 2; }, /stated 2019 baseline/],
  ["zero 2019 journey baseline", data => { data.annual.find(row => row.mode === "GMB" && row.year === 2019).journeys_thousands = 0; }, /stated 2019 baseline/],
];

for (const [description, mutate, error] of recoveryCases) {
  test(`recovery validation rejects ${description}`, () => {
    const candidate = copy();
    mutate(candidate);
    assert.throws(() => validateRecovery(candidate), error);
  });
}

const shareCases = [
  ["missing market-share chapter", data => { delete data.market_share; }, /denominator is unavailable/],
  ["PLB added as a fifth component", data => { data.market_share.components.push("PLB"); }, /denominator is unavailable/],
  ["PLB replacing an exclusive component", data => { data.market_share.components[3] = "PLB"; }, /denominator is unavailable/],
  ["repeated component", data => { data.market_share.components[1] = "GMB"; }, /denominator is unavailable/],
  ["estimated denominator falsely treated as wholly reported", data => { data.market_share.denominator_includes_estimates = false; }, /denominator is unavailable/],
  ["missing annual share observation", data => { data.market_share.annual.pop(); }, /shares are incomplete/],
  ["duplicate annual share observation", data => { data.market_share.annual[1] = { ...data.market_share.annual[0] }; }, /shares are incomplete/],
  ["share year outside the study", data => { data.market_share.annual[0].year = 2014; }, /shares are incomplete/],
  ["missing annual denominator", data => { data.market_share.denominators.pop(); }, /denominators are invalid/],
  ["duplicate denominator year", data => { data.market_share.denominators[1].year = 2015; }, /denominators are invalid/],
  ["non-finite denominator", data => { data.market_share.denominators[0].journeys_thousands = NaN; }, /denominators are invalid/],
  ["zero denominator", data => { data.market_share.denominators[0].journeys_thousands = 0; }, /denominators are invalid/],
  ["non-finite share", data => { shareRow(data).share_pct = Infinity; }, /invalid measurements/],
  ["negative share", data => { shareRow(data).share_pct = -1; }, /invalid measurements/],
  ["share above 100 percent", data => { shareRow(data).share_pct = 101; }, /invalid measurements/],
  ["PLB falsely marked an exclusive component", data => { shareRow(data, "PLB").is_subtotal = false; }, /invalid measurements/],
  ["Green component falsely marked a subtotal", data => { shareRow(data).is_subtotal = true; }, /invalid measurements/],
  ["Red estimate flag omitted", data => { shareRow(data, "RMB").includes_estimates = false; }, /invalid measurements/],
  ["PLB mixed measurement basis replaced by reported", data => { shareRow(data, "PLB").measurement_basis = "reported"; }, /invalid measurements/],
  ["four components failing to sum to 100", data => { shareRow(data, "MTR").share_pct += 1; }, /do not sum to 100%/],
  ["PLB subtotal differing from Green plus Red", data => { shareRow(data, "PLB").share_pct += 1; }, /two-minibus subtotal/],
  ["denominator incompatible with saved annual flows", data => { data.market_share.denominators.find(row => row.year === 2025).journeys_thousands *= 2; }, /four-mode denominator/],
  ["altered Green share hidden by balancing another component and subtotal", data => { shareRow(data).share_pct += 1; shareRow(data, "FRANCHISED_BUS").share_pct -= 1; shareRow(data, "PLB").share_pct += 1; }, /four-mode denominator/],
  ["inconsistent endpoint percentage", data => { data.market_share.endpoints.plb_share_2025_pct += 1; }, /endpoints are inconsistent/],
  ["percentage-point change confused with percentage change", data => { const endpoints = data.market_share.endpoints; endpoints.plb_share_change_pp = 100 * (endpoints.plb_share_2025_pct / endpoints.plb_share_2015_pct - 1); }, /endpoints are inconsistent/],
  ["inconsistent within-PLB composition", data => { data.narrative.gmb_share_2025_pct += 1; }, /within-PLB composition/],
];

for (const [description, mutate, error] of shareCases) {
  test(`market-share validation rejects ${description}`, () => {
    const candidate = copy();
    mutate(candidate);
    assert.throws(() => validateMarketShare(candidate), error);
  });
}

const fleetCases = [
  ["missing fleet chapter", data => { delete data.fleet; }, /context is unavailable/],
  ["licensed stocks globally marked estimated", data => { data.fleet.stock_measurement_basis = "estimated"; }, /context is unavailable/],
  ["missing fleet year", data => { data.fleet.annual.pop(); }, /context is incomplete/],
  ["duplicate fleet year", data => { data.fleet.annual[1] = { ...data.fleet.annual[0] }; }, /context is incomplete/],
  ["fractional licensed vehicle stock", data => { fleetRow(data).december_licensed_vehicles += 0.5; }, /invalid measurements/],
  ["zero licensed vehicle stock", data => { fleetRow(data).december_licensed_vehicles = 0; }, /invalid measurements/],
  ["non-finite vehicle-day denominator", data => { fleetRow(data).licensed_vehicle_days_proxy = NaN; }, /invalid measurements/],
  ["negative vehicle-day denominator", data => { fleetRow(data).licensed_vehicle_days_proxy = -1; }, /invalid measurements/],
  ["non-finite journey proxy", data => { fleetRow(data).journeys_per_licensed_vehicle_day_proxy = NaN; }, /invalid measurements/],
  ["Red licensed stocks confused with estimated journeys", data => { fleetRow(data).stock_measurement_basis = "estimated"; }, /invalid measurements/],
  ["Red proxy wrongly marked reported", data => { fleetRow(data).proxy_measurement_basis = "reported"; }, /invalid measurements/],
  ["Red proxy estimate flag omitted", data => { fleetRow(data).includes_estimates = false; }, /invalid measurements/],
  ["Green proxy wrongly marked estimated", data => { fleetRow(data, "GMB").measurement_basis = "estimated"; }, /invalid measurements/],
  ["stock index using an inconsistent baseline", data => { fleetRow(data).index_stock_2015 += 1; }, /saved annual vehicle-day proxy/],
  ["non-finite proxy index", data => { fleetRow(data).index_proxy_2015 = NaN; }, /saved annual vehicle-day proxy/],
  ["2015 stock baseline index other than 100", data => { fleetRow(data, "GMB", 2015).index_stock_2015 = 99; }, /saved annual vehicle-day proxy/],
  ["December-only proxy despite a superficially consistent proxy index", data => { const row = fleetRow(data); const annual = data.annual.find(candidate => candidate.mode === "RMB" && candidate.year === 2025); row.journeys_per_licensed_vehicle_day_proxy = annual.journeys_thousands * 1000 / (row.december_licensed_vehicles * 365); row.index_proxy_2015 = 100 * row.journeys_per_licensed_vehicle_day_proxy / fleetRow(data, "RMB", 2015).journeys_per_licensed_vehicle_day_proxy; }, /saved annual vehicle-day proxy/],
  ["missing endpoint summary", data => { data.fleet.endpoints.pop(); }, /endpoints are incomplete/],
  ["duplicate endpoint service", data => { data.fleet.endpoints[1] = { ...data.fleet.endpoints[0] }; }, /endpoints are incomplete/],
  ["endpoint referring to an unrelated service", data => { data.fleet.endpoints[1].mode = "PLB"; }, /summaries are inconsistent/],
  ["wrong endpoint vehicle count", data => { data.fleet.endpoints[0].december_vehicles_2025 += 1; }, /summaries are inconsistent/],
  ["wrong endpoint stock change", data => { data.fleet.endpoints[0].stock_change_pct += 1; }, /summaries are inconsistent/],
  ["wrong endpoint proxy change", data => { data.fleet.endpoints[0].proxy_change_pct += 1; }, /summaries are inconsistent/],
];

for (const [description, mutate, error] of fleetCases) {
  test(`fleet validation rejects ${description}`, () => {
    const candidate = copy();
    mutate(candidate);
    assert.throws(() => validateFleet(candidate), error);
  });
}

test("a malformed chapter does not invalidate the two independent research chapters", () => {
  const missingRecovery = copy();
  delete missingRecovery.recovery;
  assert.doesNotThrow(() => validateMarketShare(missingRecovery));
  assert.doesNotThrow(() => validateFleet(missingRecovery));
  const missingShares = copy();
  delete missingShares.market_share;
  assert.doesNotThrow(() => validateRecovery(missingShares));
  assert.doesNotThrow(() => validateFleet(missingShares));
  const missingFleet = copy();
  delete missingFleet.fleet;
  assert.doesNotThrow(() => validateRecovery(missingFleet));
  assert.doesNotThrow(() => validateMarketShare(missingFleet));
});

test("share readout returns the four components in order and identifies the fifth row as a subtotal", () => {
  for (let year = 2015; year <= 2025; year += 1) {
    const rows = selectedShareRows(research, String(year));
    assert.deepEqual(rows.map(row => row.mode), ["GMB", "RMB", "MTR", "FRANCHISED_BUS", "PLB"]);
    assert.ok(rows.every(row => row.year === year));
    assert.deepEqual(rows.map(row => row.is_subtotal), [false, false, false, false, true]);
  }
  assert.ok(selectedShareRows(research, 2014).every(row => row === undefined));
});

test("fleet readout preserves the selected service and annual observation", () => {
  for (const mode of ["GMB", "RMB"]) {
    for (let year = 2015; year <= 2025; year += 1) {
      assert.equal(selectedFleetRow(research, mode, String(year)), fleetRow(research, mode, year));
    }
  }
  assert.equal(selectedFleetRow(research, "PLB", 2025), undefined);
  assert.equal(selectedFleetRow(research, "RMB", 2014), undefined);
});
