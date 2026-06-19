# Data Dictionary — Public Health Surveillance Data Pipeline

## cases_raw.csv
One record per reported synthetic surveillance case; raw file includes intentional duplicate case IDs for deduplication practice.

| Column | Type | Description |
|---|---|---|
| case_id | string | Unique synthetic case identifier in cleaned data |
| disease_code | string | COV, INF, MEA, HEP, SAL, MPX, TUB, PER, VAR, MEN |
| disease_name | string | Full disease name |
| report_date | date | Date reported to public health; intentional missingness |
| onset_date | date | Symptom onset date; intentional missingness |
| report_source | string | Electronic Lab Report, Provider Report, Hospital Report, Death Certificate, Contact Tracing, Unknown |
| jurisdiction_id | string | Reporting jurisdiction |
| age_years | numeric | Age in years; intentional missingness |
| age_group | string | 0-4, 5-17, 18-49, 50-64, 65+ |
| sex | string | M, F, U; intentional missingness |
| race_ethnicity | string | Race/ethnicity category; intentional missingness |
| hospitalized | string | Y, N, U; intentional missingness |
| icu_admission | string | Y, N, U; intentional missingness |
| died | string | Y, N, U; intentional missingness |
| case_status | string | Confirmed, Probable, Suspect |
| investigation_status | string | Open, In Progress, Complete, Closed, Unable to Complete |
| close_date | date | Closed/completed investigation date |
| days_to_close | numeric | Days from report to close |
| imported_flag | string | Y/N imported flag |
| outbreak_associated | string | Y/N outbreak association |
| data_source | string | DCIPHER, ELR, Manual Entry, ESSENCE |
| completeness_score | float | Percent key fields complete |

## lab_results_raw.csv
One or more lab results per case.

## contacts_raw.csv
Contact tracing records linked to cases.

## jurisdictions.csv
Reference table with jurisdiction name, region, population, urban/rural class, and health department capacity tier.
