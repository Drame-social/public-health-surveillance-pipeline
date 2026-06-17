# Public Health Surveillance Data Pipeline

**Author:** Aly Drame, MD, MPH, MBA  
**Tools:** Python, SQL, SAS, PySpark  
**Data:** Synthetic surveillance records. No real patient, CDC, or state health department data are included.

## Public Health Question
How can raw electronic surveillance data be cleaned, validated, deduplicated, linked with lab/contact records, and transformed into weekly reporting outputs for outbreak monitoring and data quality review?

## Dataset
This repository includes four synthetic tables:

- `data/raw/cases_raw.csv` — 10,100 raw case rows, including intentional duplicate records
- `data/raw/lab_results_raw.csv` — 9,796 lab result rows
- `data/raw/contacts_raw.csv` — 25,603 contact tracing rows
- `data/raw/jurisdictions.csv` — 15 jurisdiction reference rows

Processed files are saved in `data/processed/`.

## Pipeline Steps
1. Extract raw CSVs
2. Validate schema, missingness, coded values, and date logic
3. Deduplicate raw case records
4. Link case, lab, contact, and jurisdiction tables
5. Aggregate weekly case counts
6. Export dashboard-ready tables and visual outputs

## Key Outputs
- `outputs/missingness_before.csv`
- `outputs/missingness_after.csv`
- `outputs/weekly_case_summary.csv`
- `outputs/jurisdiction_completeness.csv`
- `outputs/contact_tracing_metrics.csv`
- `outputs/epidemic_curve.png`
- `outputs/disease_distribution.png` (optional if generated)

## How to Reproduce
```bash
pip install -r requirements.txt
python src/run_pipeline.py
```

## Data Disclaimer
All data are synthetic and generated for portfolio demonstration purposes. No real patient records, CDC surveillance data, state health department records, or personally identifiable information are included.
