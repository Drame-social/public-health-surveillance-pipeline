-- ============================================================
-- 02_data_quality_checks.sql
-- Purpose: Comprehensive data quality validation
-- Mirrors DCIPHER data quality monitoring workflows
-- ============================================================

-- 1. ROW COUNTS
SELECT 'cases'        AS tbl, COUNT(*) AS rows FROM cases
UNION ALL
SELECT 'lab_results',          COUNT(*)         FROM lab_results
UNION ALL
SELECT 'contacts',             COUNT(*)         FROM contacts
UNION ALL
SELECT 'jurisdictions',        COUNT(*)         FROM jurisdictions;

-- 2. COMPLETENESS — CASES TABLE
SELECT
    COUNT(*)                                                   AS total_records,
    ROUND(SUM(CASE WHEN report_date IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_report_date,
    ROUND(SUM(CASE WHEN onset_date IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_onset_date,
    ROUND(SUM(CASE WHEN age_years IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_age,
    ROUND(SUM(CASE WHEN sex IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_sex,
    ROUND(SUM(CASE WHEN race_ethnicity IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_race,
    ROUND(SUM(CASE WHEN hospitalized IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_hosp,
    ROUND(SUM(CASE WHEN died IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_died
FROM cases;

-- 3. COMPLETENESS BY JURISDICTION
-- Mirrors DCIPHER jurisdiction-level completeness monitoring
SELECT
    jurisdiction_id,
    COUNT(*)                                                   AS total_records,
    ROUND(AVG(completeness_score),1)                          AS avg_completeness_score,
    ROUND(SUM(CASE WHEN onset_date IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_onset,
    ROUND(SUM(CASE WHEN race_ethnicity IS NULL
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_missing_race,
    CASE
        WHEN AVG(completeness_score) >= 95 THEN 'GREEN'
        WHEN AVG(completeness_score) >= 85 THEN 'YELLOW'
        ELSE 'RED'
    END                                                        AS completeness_status
FROM cases
GROUP BY jurisdiction_id
ORDER BY avg_completeness_score ASC;

-- 4. DUPLICATE DETECTION
SELECT case_id, COUNT(*) AS dupe_count
FROM cases
GROUP BY case_id
HAVING COUNT(*) > 1;

-- 5. REFERENTIAL INTEGRITY
SELECT l.case_id, COUNT(*) AS orphaned_lab_records
FROM lab_results l
LEFT JOIN cases c ON l.case_id = c.case_id
WHERE c.case_id IS NULL
GROUP BY l.case_id;

-- 6. DATE LOGIC ERRORS — onset after report
SELECT case_id, onset_date, report_date
FROM cases
WHERE onset_date IS NOT NULL
  AND report_date IS NOT NULL
  AND onset_date > report_date;

-- 7. INVALID CODED VALUES
SELECT case_id, sex, hospitalized, icu_admission, died, case_status
FROM cases
WHERE (sex NOT IN ('M','F','U') AND sex IS NOT NULL)
   OR (hospitalized NOT IN ('Y','N','U') AND hospitalized IS NOT NULL)
   OR (icu_admission NOT IN ('Y','N','U') AND icu_admission IS NOT NULL)
   OR (died NOT IN ('Y','N','U') AND died IS NOT NULL)
   OR case_status NOT IN ('Confirmed','Probable','Suspect');

-- 8. CONDITIONAL LOGIC — ICU without hospitalization
SELECT case_id, hospitalized, icu_admission
FROM cases
WHERE icu_admission = 'Y'
  AND (hospitalized = 'N' OR hospitalized IS NULL);
