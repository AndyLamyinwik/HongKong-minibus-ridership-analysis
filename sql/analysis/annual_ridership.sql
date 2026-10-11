-- Annual totals are sums of the twelve monthly flows, in thousand journeys.
-- Any provisional/revised monthly flag propagates to the annual observation.
WITH annual AS (
    SELECT CAST(substr(month, 1, 4) AS INTEGER) AS year,
           mode,
           SUM(passenger_journeys_thousands) AS passenger_journeys_thousands,
           measurement_basis,
           includes_estimates,
           MAX(is_provisional) AS is_provisional,
           MAX(is_revised) AS is_revised
    FROM monthly_passenger_journeys
    WHERE month BETWEEN '2015-01-01' AND '2025-12-01'
    GROUP BY year, mode, measurement_basis, includes_estimates
), previous AS (
    SELECT *,
           LAG(year) OVER (PARTITION BY mode ORDER BY year) AS previous_year,
           LAG(passenger_journeys_thousands)
               OVER (PARTITION BY mode ORDER BY year) AS previous_journeys_thousands
    FROM annual
)
SELECT year, mode, passenger_journeys_thousands,
       CASE WHEN previous_year = year - 1
            THEN passenger_journeys_thousands - previous_journeys_thousands
       END AS absolute_yoy_change_thousands,
       CASE WHEN previous_year = year - 1
            THEN 100.0 * (passenger_journeys_thousands - previous_journeys_thousands)
                 / NULLIF(previous_journeys_thousands, 0)
       END AS yoy_change_pct,
       measurement_basis, includes_estimates, is_provisional, is_revised
FROM previous
ORDER BY year, mode;
