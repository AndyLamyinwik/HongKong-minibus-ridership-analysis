-- Transport Department observations for the fixed January 2015–December 2025 study.
-- Monthly flows, daily rates, and month-end stocks remain separate tables.

CREATE TABLE source_files (
    source_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    publisher TEXT NOT NULL,
    retrieved_on TEXT NOT NULL,
    revision_date TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0 AND typeof(size_bytes) = 'integer'),
    file_format TEXT NOT NULL
);

CREATE TABLE transport_modes (
    mode TEXT PRIMARY KEY CHECK (mode IN ('GMB', 'RMB', 'PLB', 'MTR', 'FRANCHISED_BUS')),
    label TEXT NOT NULL,
    measurement_basis TEXT NOT NULL CHECK (measurement_basis IN ('reported', 'estimated', 'mixed')),
    includes_estimates INTEGER NOT NULL CHECK (includes_estimates IN (0, 1)),
    definition TEXT NOT NULL,
    UNIQUE (mode, measurement_basis, includes_estimates),
    CHECK ((measurement_basis = 'reported' AND includes_estimates = 0)
        OR (measurement_basis IN ('estimated', 'mixed') AND includes_estimates = 1))
);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE passenger_source_records (
    source_record_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source_files(source_id),
    source_row_number INTEGER NOT NULL CHECK (source_row_number >= 2 AND typeof(source_row_number) = 'integer'),
    month TEXT NOT NULL CHECK (
        length(month) = 10 AND month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-01'
        AND substr(month, 1, 4) BETWEEN '2015' AND '2025'
        AND substr(month, 6, 2) BETWEEN '01' AND '12'),
    source_mode TEXT NOT NULL,
    operator_code TEXT NOT NULL,
    franchise_type TEXT NOT NULL,
    rail_category TEXT NOT NULL,
    passenger_journeys_thousands REAL NOT NULL CHECK (passenger_journeys_thousands >= 0 AND typeof(passenger_journeys_thousands) IN ('real', 'integer')),
    source_numeric_text TEXT NOT NULL,
    source_indicator TEXT NOT NULL,
    measurement_basis TEXT NOT NULL CHECK (measurement_basis IN ('reported', 'estimated', 'mixed')),
    includes_estimates INTEGER NOT NULL CHECK (includes_estimates IN (0, 1)),
    UNIQUE (source_id, source_row_number),
    UNIQUE (month, source_mode, operator_code, franchise_type, rail_category),
    UNIQUE (source_record_id, month),
    CHECK ((measurement_basis = 'reported' AND includes_estimates = 0)
        OR (measurement_basis IN ('estimated', 'mixed') AND includes_estimates = 1))
);

CREATE TABLE daily_source_records (
    source_record_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source_files(source_id),
    source_row_number INTEGER NOT NULL CHECK (source_row_number >= 2 AND typeof(source_row_number) = 'integer'),
    month TEXT NOT NULL CHECK (
        length(month) = 10 AND month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-01'
        AND substr(month, 1, 4) BETWEEN '2015' AND '2025'
        AND substr(month, 6, 2) BETWEEN '01' AND '12'),
    source_mode TEXT NOT NULL,
    operator_code TEXT NOT NULL,
    rail_category TEXT NOT NULL,
    average_daily_journeys_thousands REAL NOT NULL CHECK (average_daily_journeys_thousands >= 0 AND typeof(average_daily_journeys_thousands) IN ('real', 'integer')),
    source_numeric_text TEXT NOT NULL,
    source_indicator TEXT NOT NULL,
    measurement_basis TEXT NOT NULL CHECK (measurement_basis IN ('reported', 'estimated', 'mixed')),
    includes_estimates INTEGER NOT NULL CHECK (includes_estimates IN (0, 1)),
    UNIQUE (source_id, source_row_number),
    UNIQUE (month, source_mode, operator_code, rail_category),
    UNIQUE (source_record_id, month),
    CHECK ((measurement_basis = 'reported' AND includes_estimates = 0)
        OR (measurement_basis IN ('estimated', 'mixed') AND includes_estimates = 1))
);

CREATE TABLE monthly_passenger_journeys (
    month TEXT NOT NULL CHECK (
        length(month) = 10 AND month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-01'
        AND substr(month, 1, 4) BETWEEN '2015' AND '2025'
        AND substr(month, 6, 2) BETWEEN '01' AND '12'),
    mode TEXT NOT NULL REFERENCES transport_modes(mode),
    passenger_journeys_thousands REAL NOT NULL CHECK (passenger_journeys_thousands >= 0 AND typeof(passenger_journeys_thousands) IN ('real', 'integer')),
    unit TEXT NOT NULL CHECK (unit = 'thousand_journeys'),
    measurement_basis TEXT NOT NULL CHECK (measurement_basis IN ('reported', 'estimated', 'mixed')),
    includes_estimates INTEGER NOT NULL CHECK (includes_estimates IN (0, 1)),
    is_derived INTEGER NOT NULL CHECK (is_derived IN (0, 1)),
    source_id TEXT NOT NULL REFERENCES source_files(source_id),
    source_indicator TEXT NOT NULL,
    is_provisional INTEGER NOT NULL CHECK (is_provisional IN (0, 1)),
    is_revised INTEGER NOT NULL CHECK (is_revised IN (0, 1)),
    component_count INTEGER NOT NULL CHECK (component_count >= 1 AND typeof(component_count) = 'integer'),
    PRIMARY KEY (month, mode),
    FOREIGN KEY (mode, measurement_basis, includes_estimates)
        REFERENCES transport_modes(mode, measurement_basis, includes_estimates)
);

CREATE TABLE monthly_average_daily_journeys (
    month TEXT NOT NULL CHECK (
        length(month) = 10 AND month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-01'
        AND substr(month, 1, 4) BETWEEN '2015' AND '2025'
        AND substr(month, 6, 2) BETWEEN '01' AND '12'),
    mode TEXT NOT NULL REFERENCES transport_modes(mode),
    average_daily_journeys_thousands REAL NOT NULL CHECK (average_daily_journeys_thousands >= 0 AND typeof(average_daily_journeys_thousands) IN ('real', 'integer')),
    unit TEXT NOT NULL CHECK (unit = 'thousand_journeys_per_day'),
    measurement_basis TEXT NOT NULL CHECK (measurement_basis IN ('reported', 'estimated', 'mixed')),
    includes_estimates INTEGER NOT NULL CHECK (includes_estimates IN (0, 1)),
    is_derived INTEGER NOT NULL CHECK (is_derived IN (0, 1)),
    source_id TEXT NOT NULL REFERENCES source_files(source_id),
    source_indicator TEXT NOT NULL,
    is_provisional INTEGER NOT NULL CHECK (is_provisional IN (0, 1)),
    is_revised INTEGER NOT NULL CHECK (is_revised IN (0, 1)),
    component_count INTEGER NOT NULL CHECK (component_count >= 1 AND typeof(component_count) = 'integer'),
    PRIMARY KEY (month, mode),
    FOREIGN KEY (mode, measurement_basis, includes_estimates)
        REFERENCES transport_modes(mode, measurement_basis, includes_estimates)
);

CREATE TABLE monthly_minibus_fleet (
    month TEXT NOT NULL CHECK (
        length(month) = 10 AND month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-01'
        AND substr(month, 1, 4) BETWEEN '2015' AND '2025'
        AND substr(month, 6, 2) BETWEEN '01' AND '12'),
    mode TEXT NOT NULL REFERENCES transport_modes(mode) CHECK (mode IN ('GMB', 'RMB')),
    licensed_vehicles INTEGER NOT NULL CHECK (licensed_vehicles >= 0 AND typeof(licensed_vehicles) = 'integer'),
    passenger_capacity INTEGER NOT NULL CHECK (passenger_capacity >= 0 AND typeof(passenger_capacity) = 'integer'),
    vehicle_km_thousands REAL CHECK (vehicle_km_thousands IS NULL OR (vehicle_km_thousands >= 0 AND typeof(vehicle_km_thousands) IN ('real', 'integer'))),
    cross_harbour_vehicle_km_thousands REAL CHECK (cross_harbour_vehicle_km_thousands IS NULL OR (cross_harbour_vehicle_km_thousands >= 0 AND typeof(cross_harbour_vehicle_km_thousands) IN ('real', 'integer'))),
    fleet_unit TEXT NOT NULL CHECK (fleet_unit = 'vehicles'),
    capacity_unit TEXT NOT NULL CHECK (capacity_unit = 'passenger_places'),
    km_unit TEXT NOT NULL CHECK (km_unit = 'thousand_vehicle_km'),
    measurement_basis TEXT NOT NULL CHECK (measurement_basis = 'reported'),
    source_id TEXT NOT NULL REFERENCES source_files(source_id),
    source_record_id TEXT NOT NULL UNIQUE,
    source_row_number INTEGER NOT NULL CHECK (source_row_number >= 2 AND typeof(source_row_number) = 'integer'),
    source_fleet_text TEXT NOT NULL,
    source_capacity_text TEXT NOT NULL,
    source_km_text TEXT NOT NULL,
    source_cross_harbour_km_text TEXT NOT NULL,
    fleet_indicator TEXT NOT NULL,
    capacity_indicator TEXT NOT NULL,
    km_indicator TEXT NOT NULL,
    cross_harbour_km_indicator TEXT NOT NULL,
    is_provisional INTEGER NOT NULL CHECK (is_provisional IN (0, 1)),
    is_revised INTEGER NOT NULL CHECK (is_revised IN (0, 1)),
    PRIMARY KEY (month, mode),
    UNIQUE (source_id, source_row_number)
);

CREATE TABLE passenger_lineage (
    month TEXT NOT NULL,
    mode TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    PRIMARY KEY (month, mode, source_record_id),
    FOREIGN KEY (month, mode) REFERENCES monthly_passenger_journeys(month, mode),
    FOREIGN KEY (source_record_id, month) REFERENCES passenger_source_records(source_record_id, month)
);

CREATE TABLE daily_lineage (
    month TEXT NOT NULL,
    mode TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    PRIMARY KEY (month, mode, source_record_id),
    FOREIGN KEY (month, mode) REFERENCES monthly_average_daily_journeys(month, mode),
    FOREIGN KEY (source_record_id, month) REFERENCES daily_source_records(source_record_id, month)
);

CREATE INDEX ix_passenger_lineage_source ON passenger_lineage(source_record_id);
CREATE INDEX ix_daily_lineage_source ON daily_lineage(source_record_id);

CREATE TABLE validation_checks (
    check_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('pass', 'fail', 'warning')),
    severity TEXT NOT NULL CHECK (severity IN ('error', 'warning', 'info')),
    message TEXT NOT NULL,
    details_json TEXT NOT NULL CHECK (json_valid(details_json))
);
