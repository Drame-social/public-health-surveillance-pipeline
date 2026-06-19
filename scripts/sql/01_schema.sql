-- ============================================================
-- 01_schema.sql
-- Project: Public Health Surveillance Data Pipeline
-- Author: Aly Drame, MD, MPH, MBA
-- Note: All data are synthetic
-- ============================================================

CREATE TABLE IF NOT EXISTS cases (
    case_id              TEXT    PRIMARY KEY,
    disease_code         TEXT    NOT NULL,
    disease_name         TEXT    NOT NULL,
    report_date          TEXT,
    onset_date           TEXT,
    report_source        TEXT    NOT NULL,
    jurisdiction_id      TEXT    NOT NULL,
    age_years            REAL,
    age_group            TEXT,
    sex                  TEXT,
    race_ethnicity       TEXT,
    hospitalized         TEXT,
    icu_admission        TEXT,
    died                 TEXT,
    case_status          TEXT    NOT NULL,
    investigation_status TEXT    NOT NULL,
    close_date           TEXT,
    days_to_close        REAL,
    imported_flag        TEXT,
    outbreak_associated  TEXT,
    data_source          TEXT    NOT NULL,
    completeness_score   REAL,
    epi_year             INTEGER,
    epi_week_num         INTEGER,
    epi_week_label       TEXT,
    CHECK (sex           IN ('M','F','U') OR sex IS NULL),
    CHECK (hospitalized  IN ('Y','N','U') OR hospitalized IS NULL),
    CHECK (icu_admission IN ('Y','N','U') OR icu_admission IS NULL),
    CHECK (died          IN ('Y','N','U') OR died IS NULL),
    CHECK (case_status   IN ('Confirmed','Probable','Suspect')),
    CHECK (completeness_score BETWEEN 0 AND 100
           OR completeness_score IS NULL)
);

CREATE TABLE IF NOT EXISTS lab_results (
    lab_id           TEXT    PRIMARY KEY,
    case_id          TEXT    NOT NULL,
    specimen_type    TEXT    NOT NULL,
    collection_date  TEXT,
    result_date      TEXT,
    test_type        TEXT    NOT NULL,
    result           TEXT    NOT NULL,
    pathogen_detected TEXT,
    lab_name         TEXT    NOT NULL,
    days_to_result   REAL,
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    CHECK (result IN ('Positive','Negative','Indeterminate','Pending'))
);

CREATE TABLE IF NOT EXISTS contacts (
    contact_id       TEXT    PRIMARY KEY,
    case_id          TEXT    NOT NULL,
    contact_date     TEXT,
    exposure_setting TEXT,
    contact_status   TEXT    NOT NULL,
    became_case      TEXT,
    days_monitored   REAL,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS jurisdictions (
    jurisdiction_id             TEXT    PRIMARY KEY,
    jurisdiction_name           TEXT    NOT NULL,
    region                      TEXT    NOT NULL,
    population_2022             INTEGER NOT NULL,
    urban_rural_class           TEXT    NOT NULL,
    health_department_capacity  TEXT    NOT NULL
);
