-- Recovery is 2025 annual journeys / 2019 annual journeys * 100.
-- It compares two full calendar years; 100% means the 2019 level is matched.
WITH annual AS (
    SELECT CAST(substr(month, 1, 4) AS INTEGER) AS year, mode,
           SUM(passenger_journeys_thousands) AS passenger_journeys_thousands,
           measurement_basis, includes_estimates
    FROM monthly_passenger_journeys
    WHERE month BETWEEN '2019-01-01' AND '2019-12-01'
       OR month BETWEEN '2025-01-01' AND '2025-12-01'
    GROUP BY year, mode, measurement_basis, includes_estimates
), comparison AS (
    SELECT baseline.mode,
           baseline.passenger_journeys_thousands AS baseline_2019_journeys_thousands,
           endpoint.passenger_journeys_thousands AS journeys_2025_thousands,
           baseline.measurement_basis, baseline.includes_estimates
    FROM annual AS baseline
    JOIN annual AS endpoint
      ON endpoint.mode = baseline.mode AND endpoint.year = 2025
    WHERE baseline.year = 2019
)
SELECT mode, baseline_2019_journeys_thousands, journeys_2025_thousands,
       journeys_2025_thousands - baseline_2019_journeys_thousands
           AS absolute_change_thousands,
       100.0 * journeys_2025_thousands
           / NULLIF(baseline_2019_journeys_thousands, 0) AS recovery_pct,
       100.0 * (journeys_2025_thousands - baseline_2019_journeys_thousands)
           / NULLIF(baseline_2019_journeys_thousands, 0) AS change_pct,
       measurement_basis, includes_estimates
FROM comparison
ORDER BY mode;
