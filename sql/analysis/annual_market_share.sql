-- The comparison group has four nonoverlapping prepared series.
-- PLB is omitted because its GMB and RMB components are already included.
WITH annual AS (
    SELECT CAST(substr(month, 1, 4) AS INTEGER) AS year, mode,
           SUM(passenger_journeys_thousands) AS passenger_journeys_thousands,
           measurement_basis, includes_estimates
    FROM monthly_passenger_journeys
    WHERE month BETWEEN '2015-01-01' AND '2025-12-01'
      AND mode IN ('GMB', 'RMB', 'MTR', 'FRANCHISED_BUS')
    GROUP BY year, mode, measurement_basis, includes_estimates
), comparison AS (
    SELECT *,
           SUM(passenger_journeys_thousands) OVER (PARTITION BY year)
               AS comparison_group_journeys_thousands
    FROM annual
)
SELECT year, mode, passenger_journeys_thousands,
       comparison_group_journeys_thousands,
       100.0 * passenger_journeys_thousands
           / NULLIF(comparison_group_journeys_thousands, 0) AS share_pct,
       measurement_basis, includes_estimates
FROM comparison
ORDER BY year, mode;
