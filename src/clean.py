"""
clean.py — Data Cleaning Module
Public Health Surveillance Data Pipeline
Author: Aly Drame, MD, MPH, MBA

Implements standardized cleaning steps for surveillance data:
- Date standardization
- Duplicate removal
- Coded value standardization
- Derived variable creation
- Age group imputation
"""

import pandas as pd
import numpy as np
from datetime import datetime


def standardize_dates(df: pd.DataFrame,
                       date_cols: list,
                       table_name: str) -> pd.DataFrame:
    """
    Parse and standardize all date columns to YYYY-MM-DD.
    Records with unparseable dates have the date set to null
    and are flagged in a new _date_parse_error column.
    """
    df = df.copy()
    error_flags = pd.Series(False, index=df.index)

    for col in date_cols:
        if col not in df.columns:
            continue
        original_nulls = df[col].isnull().sum()
        df[col] = pd.to_datetime(df[col], errors='coerce')
        new_nulls = df[col].isnull().sum()
        newly_failed = new_nulls - original_nulls

        if newly_failed > 0:
            error_flags = error_flags | df[col].isnull()
            print(f"[CLEAN] {table_name}.{col}: "
                  f"{newly_failed:,} unparseable dates → set to null")

        # Format back to string YYYY-MM-DD for consistent output
        df[col] = df[col].dt.strftime('%Y-%m-%d')

    df['_date_parse_errors'] = error_flags.astype(int)
    return df


def remove_duplicates(df: pd.DataFrame,
                       key_col: str,
                       table_name: str) -> pd.DataFrame:
    """
    Remove duplicate records keeping the first occurrence.
    Logs count removed.
    """
    before = len(df)
    df = df.drop_duplicates(subset=[key_col], keep='first')
    after  = len(df)
    removed = before - after
    if removed > 0:
        print(f"[CLEAN] {table_name}: Removed {removed:,} duplicates "
              f"on {key_col} ({before:,} → {after:,})")
    else:
        print(f"[CLEAN] {table_name}: No duplicates removed")
    return df


def standardize_coded_values(df: pd.DataFrame,
                               col: str,
                               valid_values: list,
                               replacement: str = 'Unknown',
                               table_name: str = '') -> pd.DataFrame:
    """
    Replace out-of-range coded values with a standard unknown value.
    Logs count replaced.
    """
    df = df.copy()
    if col not in df.columns:
        return df
    mask = df[col].notna() & ~df[col].isin(valid_values)
    n_replaced = mask.sum()
    if n_replaced > 0:
        df.loc[mask, col] = replacement
        print(f"[CLEAN] {table_name}.{col}: "
              f"{n_replaced:,} invalid values → '{replacement}'")
    return df


def derive_age_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive age_group from age_years where age_group is missing.
    Preserves existing age_group values.
    """
    df = df.copy()
    if 'age_years' not in df.columns or 'age_group' not in df.columns:
        return df

    def _group(age):
        if pd.isna(age):
            return None
        age = int(age)
        if age <= 4:   return '0-4'
        if age <= 17:  return '5-17'
        if age <= 49:  return '18-49'
        if age <= 64:  return '50-64'
        return '65+'

    mask = df['age_group'].isnull() & df['age_years'].notna()
    n_derived = mask.sum()
    df.loc[mask, 'age_group'] = df.loc[mask, 'age_years'].apply(_group)

    if n_derived > 0:
        print(f"[CLEAN] age_group: Derived {n_derived:,} values "
              f"from age_years")
    return df


def add_epi_week(df: pd.DataFrame,
                  date_col: str = 'report_date') -> pd.DataFrame:
    """
    Add epidemiologic week columns:
      - epi_week_num: ISO week number
      - epi_year:     ISO year
      - epi_week_label: YYYY-Www (e.g. 2022-W04)
    """
    df = df.copy()
    if date_col not in df.columns:
        return df

    dt = pd.to_datetime(df[date_col], errors='coerce')
    df['epi_year']       = dt.dt.isocalendar().year.astype('Int64')
    df['epi_week_num']   = dt.dt.isocalendar().week.astype('Int64')
    df['epi_week_label'] = (dt.dt.isocalendar().year.astype(str) + '-W' +
                             dt.dt.isocalendar().week.astype(str)
                                                     .str.zfill(2))
    df.loc[dt.isna(), ['epi_year','epi_week_num','epi_week_label']] = None
    print(f"[CLEAN] Epidemiologic week columns added from {date_col}")
    return df


def flag_data_quality_issues(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a _dq_flags column listing any data quality issues per record.
    This mirrors the data quality flagging approach in DCIPHER.
    """
    df = df.copy()
    flags = pd.Series([[] for _ in range(len(df))], index=df.index)

    # ICU without hospitalization
    if 'hospitalized' in df.columns and 'icu_admission' in df.columns:
        mask = ((df['icu_admission'] == 'Y') &
                (df['hospitalized'] != 'Y') &
                df['icu_admission'].notna())
        flags[mask] = flags[mask].apply(lambda x: x + ['ICU_WITHOUT_HOSP'])

    # Died without hospitalization (unusual — flag for review)
    if 'died' in df.columns and 'hospitalized' in df.columns:
        mask = ((df['died'] == 'Y') &
                (df['hospitalized'] == 'N') &
                df['died'].notna())
        flags[mask] = flags[mask].apply(lambda x: x + ['DIED_NOT_HOSP'])

    # Days to close is negative (impossible)
    if 'days_to_close' in df.columns:
        mask = df['days_to_close'].notna() & (df['days_to_close'] < 0)
        flags[mask] = flags[mask].apply(lambda x: x + ['NEGATIVE_DAYS_TO_CLOSE'])

    # Age > 120 (implausible)
    if 'age_years' in df.columns:
        mask = df['age_years'].notna() & (df['age_years'] > 120)
        flags[mask] = flags[mask].apply(lambda x: x + ['IMPLAUSIBLE_AGE'])

    df['_dq_flags'] = flags.apply(
        lambda x: '|'.join(x) if x else '')
    n_flagged = (df['_dq_flags'] != '').sum()
    print(f"[CLEAN] Data quality flags: {n_flagged:,} records flagged")
    return df


def clean_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline for the cases table."""
    print("\n[CLEAN] === CLEANING CASES TABLE ===")
    df = remove_duplicates(df, 'case_id', 'cases')
    df = standardize_dates(df, ['report_date','onset_date','close_date'],
                            'cases')
    df = standardize_coded_values(df, 'sex', ['M','F','U'], 'U', 'cases')
    df = standardize_coded_values(df, 'hospitalized', ['Y','N','U'],
                                   'U', 'cases')
    df = standardize_coded_values(df, 'icu_admission', ['Y','N','U'],
                                   'U', 'cases')
    df = standardize_coded_values(df, 'died', ['Y','N','U'], 'U', 'cases')
    df = derive_age_group(df)
    df = add_epi_week(df, 'report_date')
    df = flag_data_quality_issues(df)
    print(f"[CLEAN] Cases: {len(df):,} records after cleaning\n")
    return df


def clean_lab_results(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline for the lab_results table."""
    print("[CLEAN] === CLEANING LAB RESULTS TABLE ===")
    df = remove_duplicates(df, 'lab_id', 'lab_results')
    df = standardize_dates(df, ['collection_date','result_date'],
                            'lab_results')
    df = standardize_coded_values(
        df, 'result',
        ['Positive','Negative','Indeterminate','Pending'],
        'Indeterminate', 'lab_results')
    print(f"[CLEAN] Lab results: {len(df):,} records after cleaning\n")
    return df


def clean_contacts(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline for the contacts table."""
    print("[CLEAN] === CLEANING CONTACTS TABLE ===")
    df = remove_duplicates(df, 'contact_id', 'contacts')
    df = standardize_dates(df, ['contact_date'], 'contacts')
    df = standardize_coded_values(
        df, 'became_case', ['Y','N','Unknown'], 'Unknown', 'contacts')
    print(f"[CLEAN] Contacts: {len(df):,} records after cleaning\n")
    return df
