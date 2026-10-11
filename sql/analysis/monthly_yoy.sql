-- Compare each monthly flow with the same calendar month one year earlier.
-- The explicit prior-month check prevents treating a gap as a prior-year value.
WITH previous AS (
    SELECT month, mode, passenger_journeys_thousands,
           LAG(month, 12) OVER (PARTITION BY mode ORDER BY month) AS previous_month,
           LAG(passenger_journeys_thousands, 12)
               OVER (PARTITION BY mode ORDER BY month) AS previous_journeys_thousands
    FROM monthly_passenger_journeys
    WHERE month BETWEEN '2015-01-01' AND '2025-12-01'
), matched AS (
    SELECT month, mode, passenger_journeys_thousands,
           CASE WHEN previous_month = date(month, '-1 year')
                THEN previous_journeys_thousands
           END AS prior_year_journeys_thousands
    FROM previous
)
SELECT month, mode, passenger_journeys_thousands, prior_year_journeys_thousands,
       passenger_journeys_thousands - prior_year_journeys_thousands
           AS absolute_yoy_change_thousands,
       100.0 * (passenger_journeys_thousands - prior_year_journeys_thousands)
           / NULLIF(prior_year_journeys_thousands, 0) AS yoy_change_pct
FROM matched
ORDER BY month, mode;
