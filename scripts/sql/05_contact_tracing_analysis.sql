-- ============================================================
-- 05_contact_tracing_analysis.sql
-- Purpose: Contact tracing performance analysis
-- ============================================================

-- 1. CONTACT TRACING COVERAGE BY DISEASE
SELECT
    c.disease_name,
    COUNT(DISTINCT c.case_id)                                  AS total_cases,
    COUNT(DISTINCT con.case_id)                                AS cases_with_contacts,
    ROUND(COUNT(DISTINCT con.case_id)*100.0/
          COUNT(DISTINCT c.case_id),1)                        AS pct_cases_traced,
    COUNT(con.contact_id)                                      AS total_contacts,
    ROUND(COUNT(con.contact_id)*1.0/
          NULLIF(COUNT(DISTINCT con.case_id),0),1)            AS avg_contacts_per_case
FROM cases c
LEFT JOIN contacts con ON c.case_id = con.case_id
GROUP BY c.disease_name
ORDER BY pct_cases_traced DESC;

-- 2. SECONDARY ATTACK RATE
SELECT
    c.disease_name,
    COUNT(con.contact_id)                                      AS total_contacts,
    SUM(CASE WHEN con.became_case='Y' THEN 1 ELSE 0 END)      AS became_cases,
    ROUND(SUM(CASE WHEN con.became_case='Y'
              THEN 1.0 ELSE 0 END)/
          NULLIF(COUNT(con.contact_id),0)*100,1)              AS secondary_attack_rate,
    SUM(CASE WHEN con.contact_status='Lost to Follow-up'
             THEN 1 ELSE 0 END)                               AS lost_to_followup,
    ROUND(SUM(CASE WHEN con.contact_status='Lost to Follow-up'
              THEN 1.0 ELSE 0 END)/
          NULLIF(COUNT(con.contact_id),0)*100,1)              AS loss_to_followup_rate
FROM cases c
JOIN contacts con ON c.case_id = con.case_id
GROUP BY c.disease_name
ORDER BY secondary_attack_rate DESC;

-- 3. EXPOSURE SETTING DISTRIBUTION
SELECT
    exposure_setting,
    COUNT(*)                                                   AS contact_count,
    ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),1)            AS pct_of_total,
    SUM(CASE WHEN became_case='Y' THEN 1 ELSE 0 END)          AS became_cases,
    ROUND(SUM(CASE WHEN became_case='Y'
              THEN 1.0 ELSE 0 END)/COUNT(*)*100,1)            AS attack_rate
FROM contacts
WHERE exposure_setting IS NOT NULL
GROUP BY exposure_setting
ORDER BY attack_rate DESC;
