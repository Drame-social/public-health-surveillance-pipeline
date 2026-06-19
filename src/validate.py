"""
validate.py — Data Validation and Quality Reporting Module
Public Health Surveillance Data Pipeline
Author: Aly Drame, MD, MPH, MBA

Mirrors the data quality checks performed in CDC DCIPHER:
- Completeness monitoring by jurisdiction and field
- Coded value validation
- Date logic validation
- Referential integrity checks
- Duplicate detection
"""

import pandas as pd
import numpy as np
from typing import Optional
import os


def missingness_report(df: pd.DataFrame,
                        table_name: str,
                        output_path: Optional[str] = None
                        ) -> pd.DataFrame:
    """
    Calculate percent missing for every column.
    Flags fields exceeding thresholds (>10% = warning, >20% = alert).
    Mirrors DCIPHER completeness monitoring methodology.
    """
    # Exclude pipeline metadata columns
    data_cols = [c for c in df.columns
                 if not c.startswith('_')]

    report = pd.DataFrame({
        'table':            table_name,
        'field':            data_cols,
        'total_records':    len(df),
        'missing_count':    df[data_cols].isnull().sum().values,
        'pct_missing':      (df[data_cols].isnull().sum().values
                             / len(df) * 100).round(1),
        'completeness_pct': ((1 - df[data_cols].isnull().sum().values
                              / len(df)) * 100).round(1),
    })

    report['status'] = report['pct_missing'].apply(
        lambda x: 'ALERT — >20% missing'   if x > 20
        else      'WARNING — >10% missing'  if x > 10
        else      'OK')

    report = report.sort_values('pct_missing', ascending=False)

    # Console output
    print(f"\n[COMPLETENESS] {table_name.upper()} "
          f"({len(df):,} records)")
    print(f"  {'Field':<35} {'Missing':>8} {'% Missing':>10} "
          f"{'Status'}")
    print("  " + "-" * 72)
    for _, row in report.iterrows():
        marker = " ⚠️" if row['status'] != 'OK' else ""
        print(f"  {row['field']:<35} "
              f"{int(row['missing_count']):>8,} "
              f"{row['pct_missing']:>9.1f}%"
              f"  {row['status']}{marker}")

    if output_path:
        report.to_csv(output_path, index=False)
        print(f"\n  Saved → {output_path}")

    return report


def check_duplicates(df: pd.DataFrame,
                      key_col: str,
                      table_name: str) -> pd.DataFrame:
    """
    Detect duplicate records on a key column.
    Returns the duplicate records for inspection.
    """
    dupes = df[df.duplicated(subset=[key_col], keep=False)].copy()
    if len(dupes) > 0:
        print(f"[DUPLICATES] {table_name}.{key_col}: "
              f"{len(dupes):,} duplicate rows detected")
    else:
        print(f"[DUPLICATES] {table_name}.{key_col}: ✅ No duplicates")
    return dupes


def check_referential_integrity(child_df: pd.DataFrame,
                                 parent_df: pd.DataFrame,
                                 child_key: str,
                                 parent_key: str,
                                 child_name: str,
                                 parent_name: str) -> pd.DataFrame:
    """
    Verify all foreign key values exist in the parent table.
    Mirrors DCIPHER referential integrity validation.
    """
    orphans = child_df[
        ~child_df[child_key].isin(parent_df[parent_key])
    ].copy()

    if len(orphans) > 0:
        print(f"[REF INTEGRITY] {child_name}.{child_key}: "
              f"⚠️  {len(orphans):,} records not in {parent_name}")
    else:
        print(f"[REF INTEGRITY] {child_name}.{child_key} → "
              f"{parent_name}: ✅ All keys matched")
    return orphans


def validate_coded_values(df: pd.DataFrame,
                           field_rules: dict,
                           table_name: str) -> dict:
    """
    Validate that coded fields contain only expected values.
    field_rules: {column_name: [list_of_valid_values]}
    Returns dict of {field: invalid_count}.
    """
    results = {}
    for col, valid_vals in field_rules.items():
        if col not in df.columns:
            continue
        invalid = df[df[col].notna() & ~df[col].isin(valid_vals)]
        count   = len(invalid)
        results[col] = count
        status = f"⚠️  {count:,} invalid" if count > 0 else "✅ All valid"
        print(f"[CODED VALUES] {table_name}.{col}: {status}")
    return results


def validate_date_logic(df: pd.DataFrame,
                         earlier_col: str,
                         later_col: str,
                         table_name: str) -> pd.DataFrame:
    """
    Flag records where earlier_col date is after later_col date.
    Example: onset_date should not be after report_date.
    """
    df = df.copy()
    early = pd.to_datetime(df[earlier_col], errors='coerce')
    late  = pd.to_datetime(df[later_col],   errors='coerce')

    errors = df[(early.notna()) & (late.notna()) & (early > late)].copy()

    if len(errors) > 0:
        print(f"[DATE LOGIC] {table_name}: ⚠️  {len(errors):,} records "
              f"where {earlier_col} > {later_col}")
    else:
        print(f"[DATE LOGIC] {table_name}: ✅ {earlier_col} ≤ "
              f"{later_col} for all non-null records")
    return errors


def validate_conditional_logic(df: pd.DataFrame,
                                 condition_col: str,
                                 condition_val: str,
                                 dependent_col: str,
                                 expected_val: str,
                                 table_name: str) -> pd.DataFrame:
    """
    Validate conditional field rules.
    Example: icu_admission should only be Y when hospitalized is Y.
    """
    errors = df[
        (df[condition_col] != condition_val) &
        (df[dependent_col] == expected_val)
    ].copy()

    if len(errors) > 0:
        print(f"[CONDITIONAL] {table_name}: ⚠️  {len(errors):,} records "
              f"where {dependent_col}={expected_val} "
              f"but {condition_col}≠{condition_val}")
    else:
        print(f"[CONDITIONAL] {table_name}: ✅ "
              f"{dependent_col}/{condition_col} logic valid")
    return errors


def run_all_validations(tables: dict,
                         output_dir: str = 'outputs') -> dict:
    """
    Run the complete validation suite on all four tables.
    Returns a validation summary dictionary.
    """
    os.makedirs(output_dir, exist_ok=True)
    cases         = tables.get('cases', pd.DataFrame())
    lab_results   = tables.get('lab_results', pd.DataFrame())
    contacts      = tables.get('contacts', pd.DataFrame())
    jurisdictions = tables.get('jurisdictions', pd.DataFrame())

    print("\n" + "="*70)
    print("VALIDATION REPORT — PUBLIC HEALTH SURVEILLANCE DATA PIPELINE")
    print("All data are synthetic — portfolio demonstration")
    print("="*70)

    # 1. Completeness
    miss_cases = missingness_report(
        cases, 'cases',
        os.path.join(output_dir, 'missingness_cases.csv'))
    miss_lab   = missingness_report(
        lab_results, 'lab_results',
        os.path.join(output_dir, 'missingness_lab.csv'))
    miss_con   = missingness_report(
        contacts, 'contacts',
        os.path.join(output_dir, 'missingness_contacts.csv'))

    # 2. Duplicates
    print("\n--- DUPLICATE DETECTION ---")
    dup_cases = check_duplicates(cases,       'case_id', 'cases')
    dup_lab   = check_duplicates(lab_results, 'lab_id',  'lab_results')
    dup_con   = check_duplicates(contacts,    'contact_id', 'contacts')

    # 3. Referential integrity
    print("\n--- REFERENTIAL INTEGRITY ---")
    if not cases.empty and not lab_results.empty:
        check_referential_integrity(
            lab_results, cases, 'case_id', 'case_id',
            'lab_results', 'cases')
    if not cases.empty and not contacts.empty:
        check_referential_integrity(
            contacts, cases, 'case_id', 'case_id',
            'contacts', 'cases')
    if not cases.empty and not jurisdictions.empty:
        check_referential_integrity(
            cases, jurisdictions, 'jurisdiction_id', 'jurisdiction_id',
            'cases', 'jurisdictions')

    # 4. Coded value validation — cases
    print("\n--- CODED VALUE VALIDATION ---")
    validate_coded_values(cases, {
        'sex':                  ['M','F','U'],
        'hospitalized':         ['Y','N','U'],
        'icu_admission':        ['Y','N','U'],
        'died':                 ['Y','N','U'],
        'case_status':          ['Confirmed','Probable','Suspect'],
        'investigation_status': ['Open','In Progress','Complete',
                                  'Closed','Unable to Complete'],
        'imported_flag':        ['Y','N'],
        'outbreak_associated':  ['Y','N'],
    }, 'cases')

    validate_coded_values(lab_results, {
        'result': ['Positive','Negative','Indeterminate','Pending'],
    }, 'lab_results')

    # 5. Date logic
    print("\n--- DATE LOGIC VALIDATION ---")
    if 'onset_date' in cases.columns and 'report_date' in cases.columns:
        validate_date_logic(cases, 'onset_date', 'report_date', 'cases')
    if ('collection_date' in lab_results.columns and
            'result_date' in lab_results.columns):
        validate_date_logic(lab_results, 'collection_date',
                             'result_date', 'lab_results')

    # 6. Conditional logic
    print("\n--- CONDITIONAL LOGIC ---")
    if 'hospitalized' in cases.columns and 'icu_admission' in cases.columns:
        validate_conditional_logic(
            cases, 'hospitalized', 'Y', 'icu_admission', 'Y', 'cases')

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70 + "\n")

    return {
        'missingness_cases':     miss_cases,
        'missingness_lab':       miss_lab,
        'missingness_contacts':  miss_con,
        'duplicate_cases':       dup_cases,
        'duplicate_lab':         dup_lab,
        'duplicate_contacts':    dup_con,
    }
