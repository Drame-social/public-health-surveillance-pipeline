-- ============================================================
-- 04_dcipher_style_queries.sql
-- Purpose: Queries mirroring analytical outputs from CDC DCIPHER
-- DCIPHER is CDC's data management platform for COVID-19, Mpox,
-- Ebola, and other emergency response surveillance programs.
-- ============================================================

-- 1. INVESTIGATION TIMELINESS MONITORING
-- CDC tracks time from report to investigation close as a key metric.
-- Programs target closure within 21 days for most diseases.
SELECT
    disease_name,
    jurisdiction_id,
    COUNT(*)                                                   AS total_cases,
    ROUND(AVG(days_to_close),1)                               AS avg_days_to_close,
    SUM(CASE WHEN days_to_close <= 7  THEN 1 ELSE 0 END)      AS closed_7d,
    SUM(CASE WHEN days_to_close <= 21 THEN 1 ELSE 0 END)      AS closed_21d,
    SUM(CASE WHEN days_to_close > 21  THEN 1 ELSE 0 END)      AS exceeded_21d,
    ROUND(SUM(CASE WHEN days_to_close <= 21
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_meeting_target
FROM cases
WHERE investigation_status IN ('Complete','Closed')
  AND days_to_close IS NOT NULL
GROUP BY disease_name, jurisdiction_id
ORDER BY pct_meeting_target ASC;

-- 2. SEVERITY DISTRIBUTION — DCIPHER SEVERITY TIERS
SELECT
    disease_name,
    CASE
        WHEN died = 'Y'          THEN '4 — Fatal'
        WHEN icu_admission = 'Y' THEN '3 — ICU'
        WHEN hospitalized = 'Y'  THEN '2 — Hospitalized'
        ELSE                          '1 — Not Hospitalized'
    END                                                        AS severity_tier,
    COUNT(*)                                                   AS case_count,
    ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (
        PARTITION BY disease_name),1)                         AS pct_of_disease,
    ROUND(AVG(CASE WHEN age_years IS NOT NULL
              THEN age_years END),1)                          AS mean_age
FROM cases
GROUP BY disease_name, severity_tier
ORDER BY disease_name, severity_tier DESC;

-- 3. COMPLETENESS TRENDING OVER TIME
-- Monitors whether data quality is improving or declining.
-- Mirrors DCIPHER weekly data quality dashboard.
WITH weekly_completeness AS (
    SELECT
        SUBSTR(report_date,1,4)                                AS report_year,
        epi_week_num,
        epi_week_label,
        COUNT(*)                                               AS total_records,
        ROUND(AVG(completeness_score),1)                      AS avg_completeness,
        SUM(CASE WHEN completeness_score >= 90
                 THEN 1 ELSE 0 END)                           AS n_highly_complete
    FROM cases
    WHERE epi_week_label IS NOT NULL
    GROUP BY SUBSTR(report_date,1,4), epi_week_num, epi_week_label
)
SELECT
    report_year,
    epi_week_label,
    total_records,
    avg_completeness,
    LAG(avg_completeness,1) OVER (ORDER BY report_year, epi_week_num)
                                                              AS prior_week_completeness,
    ROUND(avg_completeness -
          LAG(avg_completeness,1) OVER (ORDER BY report_year, epi_week_num),
          1)                                                   AS completeness_change,
    CASE
        WHEN avg_completeness - LAG(avg_completeness,1) OVER (
             ORDER BY report_year, epi_week_num) < -5
        THEN 'ALERT — Completeness Drop'
        ELSE 'Within Expected Range'
    END                                                        AS quality_alert
FROM weekly_completeness
ORDER BY report_year, epi_week_num;

-- 4. DATA SOURCE DISTRIBUTION
-- Which systems are contributing data?
SELECT
    data_source,
    COUNT(*)                                                   AS case_count,
    ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),1)            AS pct_of_total,
    ROUND(AVG(completeness_score),1)                          AS avg_completeness,
    SUM(CASE WHEN report_date IS NULL THEN 1 ELSE 0 END)      AS missing_report_date
FROM cases
GROUP BY data_source
ORDER BY case_count DESC;
