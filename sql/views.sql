-- These views expose inputs for later analysis; no shares, growth, or recovery
-- metrics are calculated during data preparation.

CREATE VIEW v_monthly_comparison_group AS
SELECT p.*, m.label AS mode_label, m.definition AS mode_definition
FROM monthly_passenger_journeys AS p
JOIN transport_modes AS m USING (mode)
WHERE p.mode IN ('PLB', 'MTR', 'FRANCHISED_BUS');

CREATE VIEW v_monthly_minibus_journeys AS
SELECT p.*, m.label AS mode_label
FROM monthly_passenger_journeys AS p
JOIN transport_modes AS m USING (mode)
WHERE p.mode IN ('GMB', 'RMB', 'PLB');

CREATE VIEW v_monthly_minibus_fleet_context AS
SELECT p.month, p.mode, p.passenger_journeys_thousands,
       p.unit AS passenger_unit, p.measurement_basis AS passenger_measurement_basis,
       p.includes_estimates, p.is_provisional AS passenger_is_provisional,
       p.is_revised AS passenger_is_revised,
       f.licensed_vehicles, f.passenger_capacity, f.vehicle_km_thousands,
       f.cross_harbour_vehicle_km_thousands,
       f.fleet_unit, f.capacity_unit, f.km_unit,
       f.measurement_basis AS fleet_measurement_basis,
       f.is_provisional AS fleet_is_provisional, f.is_revised AS fleet_is_revised,
       p.source_id AS passenger_source_id, f.source_id AS fleet_source_id,
       f.source_record_id AS fleet_source_record_id
FROM monthly_passenger_journeys AS p
JOIN monthly_minibus_fleet AS f ON f.month = p.month AND f.mode = p.mode
WHERE p.mode IN ('GMB', 'RMB');

CREATE VIEW v_passenger_source_lineage AS
SELECT l.month, l.mode, m.label AS mode_label,
       p.passenger_journeys_thousands AS aggregate_passenger_journeys_thousands,
       p.measurement_basis AS aggregate_measurement_basis,
       p.component_count, r.source_record_id, r.source_row_number,
       r.source_mode, r.operator_code, r.franchise_type, r.rail_category,
       r.passenger_journeys_thousands AS component_passenger_journeys_thousands,
       r.source_numeric_text, r.source_indicator,
       r.measurement_basis AS component_measurement_basis,
       r.includes_estimates AS component_includes_estimates,
       s.source_id, s.filename, s.source_url, s.publisher,
       s.retrieved_on, s.revision_date, s.sha256
FROM passenger_lineage AS l
JOIN monthly_passenger_journeys AS p ON p.month = l.month AND p.mode = l.mode
JOIN transport_modes AS m ON m.mode = l.mode
JOIN passenger_source_records AS r ON r.source_record_id = l.source_record_id
JOIN source_files AS s ON s.source_id = r.source_id;

CREATE VIEW v_daily_reconciliation_inputs AS
SELECT p.month, p.mode, p.passenger_journeys_thousands,
       p.unit AS monthly_unit, d.average_daily_journeys_thousands,
       d.unit AS daily_unit,
       CAST(strftime('%d', date(p.month, '+1 month', '-1 day')) AS INTEGER) AS calendar_days,
       p.component_count AS monthly_component_count,
       d.component_count AS daily_component_count,
       p.source_id AS monthly_source_id, d.source_id AS daily_source_id,
       p.source_indicator AS monthly_source_indicator,
       d.source_indicator AS daily_source_indicator,
       p.measurement_basis, p.includes_estimates
FROM monthly_passenger_journeys AS p
JOIN monthly_average_daily_journeys AS d ON d.month = p.month AND d.mode = p.mode;

CREATE VIEW v_monthly_passenger_wide AS
SELECT month,
       MAX(CASE WHEN mode = 'GMB' THEN passenger_journeys_thousands END) AS gmb_journeys_thousands,
       MAX(CASE WHEN mode = 'RMB' THEN passenger_journeys_thousands END) AS rmb_journeys_thousands,
       MAX(CASE WHEN mode = 'PLB' THEN passenger_journeys_thousands END) AS plb_journeys_thousands,
       MAX(CASE WHEN mode = 'MTR' THEN passenger_journeys_thousands END) AS mtr_journeys_thousands,
       MAX(CASE WHEN mode = 'FRANCHISED_BUS' THEN passenger_journeys_thousands END) AS franchised_bus_journeys_thousands
FROM monthly_passenger_journeys
GROUP BY month;
