-- ============================================================
-- 03_surveillance_analysis.sql
-- Purpose: Epidemiologic analysis of surveillance data
-- ============================================================

-- 1. OVERALL CASE COUNTS BY DISEASE AND YEAR
SELECT
    disease_name,
    SUBSTR(report_date,1,4)                                    AS report_year,
    COUNT(*)                                                   AS case_count,
    SUM(CASE WHEN hospitalized='Y' THEN 1 ELSE 0 END)         AS hospitalized,
    SUM(CASE WHEN died='Y' THEN 1 ELSE 0 END)                 AS deaths,
    ROUND(SUM(CASE WHEN died='Y' THEN 1.0 ELSE 0 END)/
          COUNT(*)*100,1)                                      AS case_fatality_rate,
    ROUND(SUM(CASE WHEN case_status='Confirmed'
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS pct_confirmed
FROM cases
WHERE report_date IS NOT NULL
GROUP BY disease_name, SUBSTR(report_date,1,4)
ORDER BY disease_name, report_year;

-- 2. WEEKLY CASE COUNTS WITH PRIOR-WEEK COMPARISON
-- Uses window functions to calculate week-over-week change
-- Mirrors DCIPHER weekly reporting output
WITH weekly AS (
    SELECT
        disease_name,
        epi_year,
        epi_week_num,
        epi_week_label,
        COUNT(*)                                               AS case_count,
        SUM(CASE WHEN hospitalized='Y' THEN 1 ELSE 0 END)     AS hosp_count,
        SUM(CASE WHEN died='Y' THEN 1 ELSE 0 END)             AS death_count
    FROM cases
    WHERE epi_week_label IS NOT NULL
    GROUP BY disease_name, epi_year, epi_week_num, epi_week_label
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY disease_name
            ORDER BY epi_year, epi_week_num
        ) AS rn
    FROM weekly
)
SELECT
    a.disease_name,
    a.epi_week_label,
    a.case_count,
    a.hosp_count,
    a.death_count,
    ROUND(a.death_count*100.0/NULLIF(a.case_count,0),1)       AS cfr,
    b.case_count                                               AS prior_week_count,
    a.case_count - COALESCE(b.case_count,0)                   AS wow_change
FROM ranked a
LEFT JOIN ranked b
    ON a.disease_name = b.disease_name
   AND a.rn = b.rn + 1
ORDER BY a.disease_name, a.epi_year, a.epi_week_num;

-- 3. DEMOGRAPHICS — CASE DISTRIBUTION BY AGE AND SEX
SELECT
    disease_name,
    age_group,
    sex,
    COUNT(*)                                                   AS case_count,
    ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (
        PARTITION BY disease_name), 1)                        AS pct_of_disease
FROM cases
WHERE age_group IS NOT NULL AND sex IS NOT NULL
GROUP BY disease_name, age_group, sex
ORDER BY disease_name, age_group, sex;

-- 4. INCIDENCE BY JURISDICTION
SELECT
    c.jurisdiction_id,
    j.jurisdiction_name,
    j.region,
    j.population_2022,
    SUBSTR(c.report_date,1,4)                                  AS report_year,
    COUNT(*)                                                   AS case_count,
    ROUND(COUNT(*)*100000.0/j.population_2022,1)              AS incidence_per_100k,
    RANK() OVER (
        PARTITION BY SUBSTR(c.report_date,1,4)
        ORDER BY COUNT(*)*100000.0/j.population_2022 DESC
    )                                                          AS incidence_rank
FROM cases c
JOIN jurisdictions j ON c.jurisdiction_id = j.jurisdiction_id
WHERE c.report_date IS NOT NULL
GROUP BY c.jurisdiction_id, j.jurisdiction_name, j.region,
         j.population_2022, SUBSTR(c.report_date,1,4)
ORDER BY report_year, incidence_rank;
