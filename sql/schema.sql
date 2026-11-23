-- Petroleum import research database. Run once on an empty database.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS metadata;

CREATE TABLE metadata.country (
    iso3 CHAR(3) PRIMARY KEY,
    name TEXT NOT NULL,
    comtrade_code INTEGER NOT NULL UNIQUE,
    country_group TEXT NOT NULL,
    lldc BOOLEAN NOT NULL,
    importer_type_provisional TEXT NOT NULL,
    tier TEXT
);

CREATE TABLE metadata.product (
    hs_code VARCHAR(6) PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_group TEXT NOT NULL,
    classification_versions TEXT NOT NULL,
    research_relevance TEXT,
    in_target BOOLEAN NOT NULL
);

CREATE TABLE metadata.dataset_inventory (
    dataset_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    frequency TEXT NOT NULL,
    period_start INTEGER,
    period_end INTEGER,
    row_count BIGINT,
    retrieved_on DATE NOT NULL,
    access TEXT,
    notes TEXT
);

-- Every field the API returned, verbatim, one JSON document per record
CREATE TABLE raw.un_comtrade_imports (
    source_task TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    reporter_code INTEGER NOT NULL,
    flow TEXT NOT NULL,
    hs_code TEXT NOT NULL,
    partner_code INTEGER NOT NULL,
    period INTEGER NOT NULL,
    record JSONB NOT NULL,
    PRIMARY KEY (source_task, reporter_code, flow, hs_code, partner_code, period)
);

CREATE TABLE staging.petroleum_imports (
    iso3 CHAR(3) NOT NULL REFERENCES metadata.country (iso3),
    flow TEXT NOT NULL,
    period INTEGER NOT NULL CHECK (period BETWEEN 200001 AND 209912),
    hs_code VARCHAR(6) NOT NULL REFERENCES metadata.product (hs_code),
    product_group TEXT NOT NULL,
    classification TEXT NOT NULL,
    partner_code INTEGER NOT NULL,
    partner_iso TEXT,
    partner_name TEXT,
    mass_t DOUBLE PRECISION CHECK (mass_t IS NULL OR mass_t >= 0),
    mass_source TEXT NOT NULL,
    mass_estimated BOOLEAN NOT NULL,
    value_usd DOUBLE PRECISION,
    net_weight_kg_original DOUBLE PRECISION,
    qty_original DOUBLE PRECISION,
    qty_unit TEXT,
    is_reported BOOLEAN,
    is_aggregate BOOLEAN,
    retrieved_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (iso3, flow, period, hs_code, partner_code)
);
CREATE INDEX ON staging.petroleum_imports (iso3, product_group, period);

CREATE VIEW analytics.bilateral_petroleum_imports AS
SELECT iso3, flow, period, product_group, partner_code, partner_iso, partner_name,
       SUM(mass_t) AS mass_t, SUM(value_usd) AS value_usd, BOOL_OR(mass_estimated) AS any_estimated
FROM staging.petroleum_imports
GROUP BY iso3, flow, period, product_group, partner_code, partner_iso, partner_name;

CREATE TABLE analytics.monthly_petroleum_imports (
    iso3 CHAR(3) NOT NULL REFERENCES metadata.country (iso3),
    product_group TEXT NOT NULL,
    flow TEXT NOT NULL,
    period INTEGER NOT NULL,
    month DATE NOT NULL,
    mass_t DOUBLE PRECISION,
    mass_t_reported DOUBLE PRECISION,
    mass_t_partner_sum DOUBLE PRECISION,
    mass_t_world DOUBLE PRECISION,
    value_usd DOUBLE PRECISION,
    unit_value_usd_t DOUBLE PRECISION,
    total_source TEXT,
    n_partners INTEGER,
    value_share_with_mass DOUBLE PRECISION,
    share_estimated DOUBLE PRECISION,
    share_mass_recovered_from_qty DOUBLE PRECISION,
    flag_uv_low BOOLEAN,
    flag_uv_high BOOLEAN,
    flag_mass_outlier BOOLEAN,
    mass_t_incl_volume_estimate DOUBLE PRECISION,
    month_status TEXT NOT NULL,
    first_released TIMESTAMP,
    publication_lag_days INTEGER,
    PRIMARY KEY (iso3, product_group, flow, period)
);
CREATE INDEX ON analytics.monthly_petroleum_imports (product_group, period);

CREATE TABLE analytics.supplier_concentration (
    iso3 CHAR(3) NOT NULL REFERENCES metadata.country (iso3),
    product_group TEXT NOT NULL,
    period INTEGER NOT NULL,
    total_mass_t DOUBLE PRECISION NOT NULL,
    active_suppliers INTEGER NOT NULL,
    top1_share DOUBLE PRECISION NOT NULL,
    top3_share DOUBLE PRECISION NOT NULL,
    hhi DOUBLE PRECISION NOT NULL CHECK (hhi BETWEEN 0 AND 1.000001),
    top_supplier_iso TEXT,
    russia_share DOUBLE PRECISION,
    new_suppliers DOUBLE PRECISION,
    value_share_covered DOUBLE PRECISION,
    PRIMARY KEY (iso3, product_group, period)
);

-- Long form so global, country and annual series keep their own frequency and source
CREATE TABLE analytics.monthly_external_indicators (
    scope TEXT NOT NULL CHECK (scope IN ('global', 'country')),
    iso3 CHAR(3) NOT NULL DEFAULT 'WLD',
    period INTEGER NOT NULL,
    series TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (scope, iso3, period, series)
);

CREATE TABLE analytics.annual_external_indicators (
    iso3 CHAR(3) NOT NULL REFERENCES metadata.country (iso3),
    year INTEGER NOT NULL,
    series TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (iso3, year, series)
);
