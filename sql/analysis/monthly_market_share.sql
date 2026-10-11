-- Shares are within GMB + RMB + MTR + franchised buses, not all HK transport.
WITH comparison AS (
    SELECT month, mode, passenger_journeys_thousands,
           SUM(passenger_journeys_thousands) OVER (PARTITION BY month)
               AS comparison_group_journeys_thousands,
           measurement_basis, includes_estimates
    FROM monthly_passenger_journeys
    WHERE month BETWEEN '2015-01-01' AND '2025-12-01'
      AND mode IN ('GMB', 'RMB', 'MTR', 'FRANCHISED_BUS')
)
SELECT month, mode, passenger_journeys_thousands,
       comparison_group_journeys_thousands,
       100.0 * passenger_journeys_thousands
           / NULLIF(comparison_group_journeys_thousands, 0) AS share_pct,
       measurement_basis, includes_estimates
FROM comparison
ORDER BY month, mode;
