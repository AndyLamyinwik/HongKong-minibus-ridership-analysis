-- This descriptive proxy uses the monthly daily rate and month-end licensed stock.
-- Multiplying thousand journeys/day by 1,000 converts to journeys/day/vehicle.
WITH matched AS (
    SELECT d.month, d.mode, d.average_daily_journeys_thousands,
           f.licensed_vehicles, d.measurement_basis, d.includes_estimates
    FROM monthly_average_daily_journeys AS d
    JOIN monthly_minibus_fleet AS f ON f.month = d.month AND f.mode = d.mode
    WHERE d.month BETWEEN '2015-01-01' AND '2025-12-01'
      AND d.mode IN ('GMB', 'RMB')
)
SELECT month, mode, average_daily_journeys_thousands, licensed_vehicles,
       1000.0 * average_daily_journeys_thousands
           / NULLIF(licensed_vehicles, 0)
           AS average_daily_journeys_per_licensed_vehicle,
       measurement_basis, includes_estimates
FROM matched
ORDER BY month, mode;
