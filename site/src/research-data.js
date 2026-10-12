const years = Array.from({ length: 11 }, (_, i) => 2015 + i);
export const shareComponents = ["GMB", "RMB", "MTR", "FRANCHISED_BUS"];
export const allResearchModes = [...shareComponents, "PLB"];
const basis = {
  GMB: "reported",
  RMB: "estimated",
  PLB: "mixed",
  MTR: "reported",
  FRANCHISED_BUS: "reported",
};

function positive(value) {
  return Number.isFinite(value) && value > 0;
}
function near(actual, expected) {
  return Number.isFinite(actual) && Math.abs(actual - expected) <= 1e-7;
}
function annualKeys(rows, modes, message) {
  if (!Array.isArray(rows) || rows.length !== years.length * modes.length)
    throw new Error(message);
  const seen = new Set();
  for (const row of rows) {
    const key = `${row.year}/${row.mode}`;
    if (!years.includes(row.year) || !modes.includes(row.mode) || seen.has(key))
      throw new Error(message);
    seen.add(key);
  }
}
function passengerBasis(row) {
  return (
    row.measurement_basis === basis[row.mode] &&
    row.includes_estimates === ["RMB", "PLB"].includes(row.mode)
  );
}

export function validateRecovery(data) {
  if (
    !Array.isArray(data?.recovery) ||
    data.recovery.length !== 5 ||
    data.recovery_definition?.baseline_year !== 2019 ||
    data.recovery_definition?.reference_year !== 2025
  )
    throw new Error("The 2019 recovery comparison is missing or incomplete.");
  const modes = new Set();
  for (const row of data.recovery) {
    if (
      !allResearchModes.includes(row.mode) ||
      modes.has(row.mode) ||
      !positive(row.recovery_pct) ||
      !passengerBasis(row)
    )
      throw new Error("The recovery comparison has invalid measurements.");
    modes.add(row.mode);
  }
  for (const mode of ["GMB", "RMB", "PLB"]) {
    const journeys = (year) =>
      data.annual
        .filter(
          (row) =>
            row.year === year &&
            (mode === "PLB"
              ? ["GMB", "RMB"].includes(row.mode)
              : row.mode === mode),
        )
        .reduce((total, row) => total + row.journeys_thousands, 0);
    if (
      !positive(journeys(2019)) ||
      !near(
        data.recovery.find((row) => row.mode === mode).recovery_pct,
        (journeys(2025) / journeys(2019)) * 100,
      )
    )
      throw new Error(
        "The recovery comparison does not use the stated 2019 baseline.",
      );
  }
  return data.recovery;
}

export function validateMarketShare(data) {
  const shares = data?.market_share;
  if (
    !shares ||
    !Array.isArray(shares.components) ||
    shares.components.length !== 4 ||
    new Set(shares.components).size !== 4 ||
    !shareComponents.every((mode) => shares.components.includes(mode)) ||
    shares.denominator_includes_estimates !== true
  )
    throw new Error("The four-mode comparison denominator is unavailable.");
  annualKeys(
    shares.annual,
    allResearchModes,
    "The annual comparison-group shares are incomplete.",
  );
  if (
    !Array.isArray(shares.denominators) ||
    shares.denominators.length !== 11 ||
    new Set(shares.denominators.map((row) => row.year)).size !== 11 ||
    shares.denominators.some(
      (row) => !years.includes(row.year) || !positive(row.journeys_thousands),
    )
  )
    throw new Error("The annual comparison denominators are invalid.");
  for (const year of years) {
    const rows = shares.annual.filter((row) => row.year === year);
    if (
      rows.some(
        (row) =>
          !Number.isFinite(row.share_pct) ||
          row.share_pct < 0 ||
          row.share_pct > 100 ||
          row.is_subtotal !== (row.mode === "PLB") ||
          !passengerBasis(row),
      )
    )
      throw new Error("The comparison-group shares have invalid measurements.");
    const parts = rows.filter((row) => !row.is_subtotal);
    if (
      !near(
        parts.reduce((sum, row) => sum + row.share_pct, 0),
        100,
      )
    )
      throw new Error(
        "The four comparison-group components do not sum to 100%.",
      );
    const minibusShare =
      rows.find((row) => row.mode === "GMB").share_pct +
      rows.find((row) => row.mode === "RMB").share_pct;
    if (!near(rows.find((row) => row.mode === "PLB").share_pct, minibusShare))
      throw new Error("PLB must remain the two-minibus subtotal.");
    const denominator = shares.denominators.find(
      (row) => row.year === year,
    ).journeys_thousands;
    for (const mode of ["GMB", "RMB"]) {
      const annual = data.annual.find(
        (row) => row.mode === mode && row.year === year,
      );
      if (
        !annual ||
        !near(
          rows.find((row) => row.mode === mode).share_pct,
          (annual.journeys_thousands / denominator) * 100,
        )
      )
        throw new Error("The shares do not retain the four-mode denominator.");
    }
  }
  const endpoint = (year) =>
    shares.annual.find((row) => row.year === year && row.mode === "PLB")
      .share_pct;
  if (
    !near(shares.endpoints?.plb_share_2015_pct, endpoint(2015)) ||
    !near(shares.endpoints?.plb_share_2025_pct, endpoint(2025)) ||
    !near(
      shares.endpoints?.plb_share_change_pp,
      endpoint(2025) - endpoint(2015),
    )
  )
    throw new Error("The share endpoints are inconsistent.");
  for (const year of [2015, 2025]) {
    const gmb = shares.annual.find(
      (row) => row.year === year && row.mode === "GMB",
    ).share_pct;
    if (
      !near(
        data.narrative?.[`gmb_share_${year}_pct`],
        (100 * gmb) / endpoint(year),
      )
    )
      throw new Error("The within-PLB composition is inconsistent.");
  }
  return shares;
}

export function validateFleet(data) {
  const fleet = data?.fleet;
  if (!fleet || fleet.stock_measurement_basis !== "reported")
    throw new Error("The reported licensed-fleet context is unavailable.");
  annualKeys(
    fleet.annual,
    ["GMB", "RMB"],
    "The annual fleet context is incomplete.",
  );
  for (const row of fleet.annual) {
    if (
      !Number.isInteger(row.december_licensed_vehicles) ||
      row.december_licensed_vehicles <= 0 ||
      !positive(row.licensed_vehicle_days_proxy) ||
      !positive(row.journeys_per_licensed_vehicle_day_proxy) ||
      row.stock_measurement_basis !== "reported" ||
      row.proxy_measurement_basis !== basis[row.mode] ||
      !passengerBasis(row)
    )
      throw new Error(
        "The fleet stocks and passenger-based proxy have invalid measurements.",
      );
    const baseline = fleet.annual.find(
      (candidate) => candidate.mode === row.mode && candidate.year === 2015,
    );
    const annual = data.annual.find(
      (candidate) => candidate.mode === row.mode && candidate.year === row.year,
    );
    if (
      !annual ||
      !near(
        row.index_stock_2015,
        (row.december_licensed_vehicles / baseline.december_licensed_vehicles) *
          100,
      ) ||
      !near(
        row.index_proxy_2015,
        (row.journeys_per_licensed_vehicle_day_proxy /
          baseline.journeys_per_licensed_vehicle_day_proxy) *
          100,
      ) ||
      !near(
        row.journeys_per_licensed_vehicle_day_proxy,
        (annual.journeys_thousands * 1000) / row.licensed_vehicle_days_proxy,
      )
    )
      throw new Error(
        "The fleet context does not retain the saved annual vehicle-day proxy.",
      );
  }
  if (
    !Array.isArray(fleet.endpoints) ||
    fleet.endpoints.length !== 2 ||
    new Set(fleet.endpoints.map((row) => row.mode)).size !== 2
  )
    throw new Error("The fleet endpoints are incomplete.");
  for (const endpoint of fleet.endpoints) {
    const start = fleet.annual.find(
      (row) => row.mode === endpoint.mode && row.year === 2015,
    );
    const end = fleet.annual.find(
      (row) => row.mode === endpoint.mode && row.year === 2025,
    );
    if (
      !start ||
      !end ||
      endpoint.december_vehicles_2015 !== start.december_licensed_vehicles ||
      endpoint.december_vehicles_2025 !== end.december_licensed_vehicles ||
      !near(endpoint.stock_change_pct, end.index_stock_2015 - 100) ||
      !near(endpoint.proxy_change_pct, end.index_proxy_2015 - 100)
    )
      throw new Error("The fleet endpoint summaries are inconsistent.");
  }
  return fleet;
}

export function selectedShareRows(data, year) {
  return [...shareComponents, "PLB"].map((mode) =>
    data.market_share.annual.find(
      (row) => row.mode === mode && row.year === Number(year),
    ),
  );
}

export function selectedFleetRow(data, mode, year) {
  return data.fleet.annual.find(
    (row) => row.mode === mode && row.year === Number(year),
  );
}
