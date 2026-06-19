"""
large_dataset_pipeline.py
PySpark version of the surveillance data pipeline.
Demonstrates ability to handle large-scale surveillance datasets.
Author: Aly Drame, MD, MPH, MBA

Run with: python pyspark/large_dataset_pipeline.py
Requires: PySpark installed via Anaconda (pyspark package)
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField, StringType,
                                IntegerType, FloatType, DateType)
import os

# Initialize Spark session
spark = (SparkSession.builder
         .appName("PublicHealthSurveillancePipeline")
         .config("spark.sql.shuffle.partitions", "4")  # appropriate for local
         .getOrCreate())

spark.sparkContext.setLogLevel("WARN")

print("[PYSPARK] Spark session initialized")
print(f"[PYSPARK] Spark version: {spark.version}")

# ── Define schema for cases table ──────────────────────────────────
cases_schema = StructType([
    StructField("case_id",              StringType(),  True),
    StructField("disease_code",         StringType(),  True),
    StructField("disease_name",         StringType(),  True),
    StructField("report_date",          StringType(),  True),
    StructField("onset_date",           StringType(),  True),
    StructField("report_source",        StringType(),  True),
    StructField("jurisdiction_id",      StringType(),  True),
    StructField("age_years",            FloatType(),   True),
    StructField("age_group",            StringType(),  True),
    StructField("sex",                  StringType(),  True),
    StructField("race_ethnicity",       StringType(),  True),
    StructField("hospitalized",         StringType(),  True),
    StructField("icu_admission",        StringType(),  True),
    StructField("died",                 StringType(),  True),
    StructField("case_status",          StringType(),  True),
    StructField("investigation_status", StringType(),  True),
    StructField("close_date",           StringType(),  True),
    StructField("days_to_close",        FloatType(),   True),
    StructField("imported_flag",        StringType(),  True),
    StructField("outbreak_associated",  StringType(),  True),
    StructField("data_source",          StringType(),  True),
    StructField("completeness_score",   FloatType(),   True),
])

# ── Load data ──────────────────────────────────────────────────────
raw_path = "data/raw/cases_raw.csv"
if not os.path.exists(raw_path):
    print(f"[PYSPARK] Raw data not found at {raw_path}.")
    print("[PYSPARK] Run python data/synthetic/generate_synthetic_data.py first.")
    spark.stop()
    raise SystemExit(1)

cases_df = (spark.read
            .option("header", "true")
            .option("nullValue", "")
            .schema(cases_schema)
            .csv(raw_path))

print(f"[PYSPARK] Loaded {cases_df.count():,} raw records")

# ── Step 1: Schema validation ──────────────────────────────────────
print("\n[PYSPARK] === SCHEMA VALIDATION ===")
cases_df.printSchema()

# ── Step 2: Completeness report ────────────────────────────────────
print("\n[PYSPARK] === COMPLETENESS REPORT ===")
total = cases_df.count()
key_fields = ['disease_code','report_date','onset_date','age_years',
              'sex','hospitalized','investigation_status']

for col in key_fields:
    missing = cases_df.filter(F.col(col).isNull()).count()
    pct     = round(missing / total * 100, 1)
    status  = "⚠️" if pct > 10 else "✅"
    print(f"  {status} {col:<35} missing: {missing:>6,} ({pct:>5.1f}%)")

# ── Step 3: Deduplication ──────────────────────────────────────────
print("\n[PYSPARK] === DEDUPLICATION ===")
before = total
cases_df = cases_df.dropDuplicates(["case_id"])
after   = cases_df.count()
print(f"[PYSPARK] Removed {before - after:,} duplicate records "
      f"({before:,} → {after:,})")

# ── Step 4: Date parsing ───────────────────────────────────────────
cases_df = cases_df.withColumn(
    "report_date_parsed",
    F.to_date("report_date", "yyyy-MM-dd")
).withColumn(
    "onset_date_parsed",
    F.to_date("onset_date", "yyyy-MM-dd")
)

# Flag date logic errors
cases_df = cases_df.withColumn(
    "_date_logic_error",
    F.when(
        (F.col("onset_date_parsed").isNotNull()) &
        (F.col("report_date_parsed").isNotNull()) &
        (F.col("onset_date_parsed") > F.col("report_date_parsed")),
        1
    ).otherwise(0)
)
n_date_errors = cases_df.filter(F.col("_date_logic_error") == 1).count()
print(f"[PYSPARK] Date logic errors (onset > report): {n_date_errors:,}")

# ── Step 5: Add epidemiologic week ─────────────────────────────────
cases_df = cases_df.withColumn(
    "epi_year",
    F.year(F.col("report_date_parsed"))
).withColumn(
    "epi_week",
    F.weekofyear(F.col("report_date_parsed"))
)

# ── Step 6: Weekly aggregation ─────────────────────────────────────
print("\n[PYSPARK] === WEEKLY AGGREGATION ===")
weekly = (
    cases_df
    .filter(F.col("report_date_parsed").isNotNull())
    .groupBy("epi_year", "epi_week", "disease_name")
    .agg(
        F.count("case_id").alias("case_count"),
        F.sum(F.when(F.col("hospitalized") == "Y", 1).otherwise(0))
            .alias("hospitalized_count"),
        F.sum(F.when(F.col("died") == "Y", 1).otherwise(0))
            .alias("death_count"),
        F.avg("completeness_score").alias("avg_completeness"),
    )
    .orderBy("disease_name", "epi_year", "epi_week")
)

print(f"[PYSPARK] Weekly summary: {weekly.count():,} rows")
weekly.show(10, truncate=False)

# ── Step 7: Jurisdiction completeness ─────────────────────────────
print("\n[PYSPARK] === JURISDICTION COMPLETENESS ===")
jur_complete = (
    cases_df
    .groupBy("jurisdiction_id")
    .agg(
        F.count("case_id").alias("total_records"),
        F.avg("completeness_score").alias("avg_completeness_score"),
        F.sum(F.when(F.col("report_date").isNull(), 1)
               .otherwise(0)).alias("missing_report_date"),
        F.sum(F.when(F.col("onset_date").isNull(), 1)
               .otherwise(0)).alias("missing_onset_date"),
    )
    .withColumn("avg_completeness_score",
                F.round("avg_completeness_score", 1))
    .orderBy("avg_completeness_score")
)

jur_complete.show(truncate=False)

# ── Step 8: Export outputs ─────────────────────────────────────────
os.makedirs("outputs", exist_ok=True)

(weekly.toPandas()
       .to_csv("outputs/pyspark_weekly_summary.csv", index=False))
(jur_complete.toPandas()
             .to_csv("outputs/pyspark_jurisdiction_completeness.csv",
                     index=False))

print("\n[PYSPARK] Outputs saved:")
print("  outputs/pyspark_weekly_summary.csv")
print("  outputs/pyspark_jurisdiction_completeness.csv")

spark.stop()
print("\n[PYSPARK] Pipeline complete. Spark session stopped.")
