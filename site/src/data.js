export function validateResearchData(data) {
  if (!data || data.schema_version !== 1 || !Array.isArray(data.annual))
    throw new Error("Unsupported research data.");
  if (data.annual.length === 0)
    throw new Error("The bundled research data is empty.");
  if (
    data.study?.start_year !== 2015 ||
    data.study?.end_year !== 2025 ||
    data.study?.months !== 132 ||
    data.annual.length !== 22
  )
    throw new Error("Incomplete research period.");
  const seen = new Set();
  for (const row of data.annual) {
    if (
      !Number.isInteger(row.year) ||
      row.year < 2015 ||
      row.year > 2025 ||
      !["GMB", "RMB"].includes(row.mode)
    )
      throw new Error("Invalid annual observation.");
    const key = `${row.year}/${row.mode}`;
    if (seen.has(key)) throw new Error("Duplicate annual observation.");
    seen.add(key);
    if (
      !Number.isFinite(row.journeys_thousands) ||
      row.journeys_thousands <= 0 ||
      !Number.isFinite(row.index_2015) ||
      row.index_2015 <= 0
    )
      throw new Error("Invalid annual measurement.");
    if (
      row.includes_estimates !== (row.mode === "RMB") ||
      row.measurement_basis !== (row.mode === "RMB" ? "estimated" : "reported")
    )
      throw new Error("Invalid measurement basis.");
  }
  for (const mode of ["GMB", "RMB"]) {
    const baseline = data.annual.find(
      (row) => row.mode === mode && row.year === 2015,
    );
    for (const row of data.annual.filter((row) => row.mode === mode)) {
      if (
        Math.abs(
          row.index_2015 -
            (100 * row.journeys_thousands) / baseline.journeys_thousands,
        ) > 1e-8
      )
        throw new Error("Inconsistent indexed baseline.");
    }
  }
  for (const key of [
    "plb_change_pct",
    "gmb_change_pct",
    "rmb_change_pct",
    "rmb_recovery_2019_pct",
  ]) {
    if (!Number.isFinite(data.kpis?.[key]))
      throw new Error("Missing research finding.");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(data.provenance?.snapshot_retrieved_on ?? ""))
    throw new Error("Missing source vintage.");
  return data;
}

export function percentage(value, unsigned = false) {
  if (!Number.isFinite(value)) throw new Error("Invalid percentage.");
  return `${!unsigned && value < 0 ? "−" : ""}${Math.abs(value).toFixed(2)}%`;
}

export function annualSeries(data, mode, view) {
  if (!["index", "absolute"].includes(view))
    throw new Error("Unknown chart view.");
  return data.annual
    .filter((row) => row.mode === mode)
    .sort((a, b) => a.year - b.year)
    .map((row) =>
      view === "index" ? row.index_2015 : row.journeys_thousands / 1000,
    );
}

export function yearRows(data, year) {
  return ["GMB", "RMB"].map((mode) =>
    data.annual.find((row) => row.mode === mode && row.year === year),
  );
}
