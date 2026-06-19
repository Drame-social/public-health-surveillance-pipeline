-- ============================================================
-- 06_outbreak_detection.sql
-- Purpose: Statistical threshold-based outbreak detection
-- Mirrors CDC syndrome surveillance alert methodology
-- ============================================================

-- 1. HISTORICAL BASELINE CALCULATION
-- Calculate mean and standard deviation of weekly case counts
-- over the past 3 years as a baseline for alert thresholds.
WITH weekly_historical AS (
    SELECT
        disease_name,
        epi_week_num,
        epi_year,
        COUNT(*) AS weekly_count
    FROM cases
    WHERE report_date IS NOT NULL
      AND epi_week_num IS NOT NULL
    GROUP BY disease_name, epi_week_num, epi_year
),
baseline AS (
    SELECT
        disease_name,
        epi_week_num,
        AVG(weekly_count)                                      AS historical_mean,
        -- Approximate standard deviation using MAX as a proxy
        -- (SQLite does not have native STDDEV)
        (MAX(weekly_count) - MIN(weekly_count)) / 4.0         AS approx_stddev
    FROM weekly_historical
    GROUP BY disease_name, epi_week_num
),
current_week AS (
    SELECT
        disease_name,
        epi_week_num,
        epi_year,
        COUNT(*) AS current_count
    FROM cases
    WHERE epi_year = (SELECT MAX(CAST(SUBSTR(report_date,1,4) AS INTEGER))
                      FROM cases WHERE report_date IS NOT NULL)
      AND epi_week_num IS NOT NULL
    GROUP BY disease_name, epi_week_num, epi_year
)
SELECT
    c.disease_name,
    c.epi_year,
    c.epi_week_num,
    c.current_count,
    ROUND(b.historical_mean,1)                                AS historical_mean,
    ROUND(b.historical_mean + 2*b.approx_stddev,1)           AS alert_threshold_2sd,
    ROUND(b.historical_mean + 3*b.approx_stddev,1)           AS alert_threshold_3sd,
    CASE
        WHEN c.current_count > b.historical_mean + 3*b.approx_stddev
        THEN 'HIGH ALERT'
        WHEN c.current_count > b.historical_mean + 2*b.approx_stddev
        THEN 'ALERT'
        ELSE 'Within Expected Range'
    END                                                       AS alert_status
FROM current_week c
JOIN baseline b
    ON c.disease_name  = b.disease_name
   AND c.epi_week_num = b.epi_week_num
ORDER BY c.current_count DESC;

-- 2. OUTBREAK-ASSOCIATED CASE CLUSTERING
SELECT
    disease_name,
    jurisdiction_id,
    outbreak_associated,
    COUNT(*)                                                   AS case_count,
    ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (
        PARTITION BY disease_name),1)                        AS pct_of_disease
FROM cases
WHERE outbreak_associated IS NOT NULL
GROUP BY disease_name, jurisdiction_id, outbreak_associated
ORDER BY disease_name, case_count DESC;
