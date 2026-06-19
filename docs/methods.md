# Methods

## Data Quality
The pipeline checks missingness, duplicate case IDs, referential integrity, valid coded values, date logic, and conditional logic such as ICU admission only when hospitalization is present.

## Transformation
The case table is deduplicated using `case_id`. Cleaned case records are linked to laboratory, contact tracing, and jurisdiction reference data.

## Aggregation
Weekly case counts are produced by ISO epidemiologic week and disease. Jurisdiction completeness and contact tracing metrics are exported for dashboards and reports.

## Reporting
The project generates CSV outputs and charts that can be used in Power BI, Tableau, or a Word/PDF situation report.
