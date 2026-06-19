# Public Health Surveillance Data Pipeline

**Author:** Aly Drame, MD, MPH, MBA  
**Languages:** Python · SQL · SAS · PySpark  
**Domain:** Epidemiological surveillance, CDC DCIPHER-style workflows  
**Data:** Fully synthetic — generated for portfolio demonstration

---

## Project Overview

This project implements an end-to-end public health surveillance data pipeline that mirrors the kind of work performed in CDC DCIPHER and similar federal epidemiological information systems. It ingests raw, messy surveillance case data from four source tables, applies staged validation and cleaning, merges and transforms the data into an analytical dataset, aggregates weekly outbreak metrics, and exports automated visualizations and a Word-format surveillance report.

The pipeline is structured as a modular Python package (`src/`) orchestrated through a Jupyter notebook, with companion SQL schema and query scripts, SAS descriptive analyses, and a PySpark script for large-dataset scenarios.

---

## Repository Structure

```
├── README.md
├── notebooks/
│   └── 01_surveillance_pipeline_walkthrough.ipynb   # Master pipeline notebook
├── src/
│   ├── extract.py          # Load raw CSV tables with validation
│   ├── validate.py         # Missingness, duplicate, and range checks
│   ├── clean.py            # Standardize dates, remove dupes, fix codes
│   ├── transform.py        # Merge tables, derive epi variables
│   ├── aggregate.py        # Weekly counts, jurisdiction summaries, CFR
│   └── export_report.py    # Epidemic curve, heatmap, Word report
├── data/
│   └── synthetic/
│       └── generate_synthetic_data.py   # Generates all raw input tables
├── scripts/
│   ├── sql/
│   │   ├── 01_schema.sql                  # DDL for surveillance schema
│   │   ├── 02_data_quality_checks.sql     # Pre-analysis QA queries
│   │   ├── 03_surveillance_analysis.sql   # Core epidemiological queries
│   │   ├── 04_dcipher_style_queries.sql   # CDC DCIPHER-pattern queries
│   │   ├── 05_contact_tracing_analysis.sql
│   │   └── 06_outbreak_detection.sql      # Rolling averages, threshold alerts
│   ├── sas/
│   │   ├── 01_descriptive_surveillance.sas
│   │   └── 02_data_quality_report.sas
│   └── pyspark/
│       └── large_dataset_pipeline.py      # Distributed processing variant
```

---

## Pipeline Stages

| Stage | Module | What It Does |
|-------|--------|-------------|
| Extract | `src/extract.py` | Loads 4 raw tables (cases, lab results, contacts, jurisdictions) with file validation and audit timestamps |
| Validate | `src/validate.py` | Missingness reports, duplicate detection, date-range checks — run before and after cleaning |
| Clean | `src/clean.py` | Standardizes date formats, removes exact duplicates, harmonizes coded fields |
| Transform | `src/transform.py` | Joins all tables, derives epi week, confirmation status, hospitalization and death binary flags |
| Aggregate | `src/aggregate.py` | Weekly case counts by disease with CFR and hospitalization rates; jurisdiction and contact-tracing summaries |
| Export | `src/export_report.py` | Epidemic curve, completeness heatmap, disease distribution plots; automated Word surveillance report |

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas numpy matplotlib python-docx openpyxl

# 2. Generate synthetic input data
python data/synthetic/generate_synthetic_data.py

# 3. Open and run the master notebook
jupyter notebook notebooks/01_surveillance_pipeline_walkthrough.ipynb
```

All outputs (CSVs, PNGs, Word report) are written to `outputs/`.

---

## SQL Scripts

The `scripts/sql/` directory contains a complete RDBMS implementation of the surveillance schema and analytical queries, including DCIPHER-style aggregation patterns and automated outbreak detection using rolling 4-week averages with configurable alert thresholds.

## SAS Scripts

`scripts/sas/` provides SAS equivalents of the descriptive analysis and data quality reporting — designed for environments where SAS is the production tool.

## PySpark Variant

`scripts/pyspark/large_dataset_pipeline.py` implements the core extract-validate-clean-aggregate steps using PySpark DataFrames for scenarios involving datasets too large for in-memory pandas processing.

---

*All data in this project are synthetic and were generated solely for portfolio demonstration. No real patient or public health records are used.*
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
