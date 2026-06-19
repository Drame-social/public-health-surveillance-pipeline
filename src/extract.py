"""
extract.py — Data Extraction Module
Public Health Surveillance Data Pipeline
Author: Aly Drame, MD, MPH, MBA
"""

import pandas as pd
import os
from datetime import datetime


def load_csv(filepath: str, table_name: str) -> pd.DataFrame:
    """
    Load a CSV file with validation.
    Checks file existence, non-empty content, and logs summary.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"[EXTRACT] File not found: {filepath}")

    df = pd.read_csv(filepath, low_memory=False)

    if df.empty:
        raise ValueError(
            f"[EXTRACT] File is empty: {filepath}")

    df['_load_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df['_source_file']    = os.path.basename(filepath)

    print(f"[EXTRACT] {table_name}: {len(df):,} rows × "
          f"{df.shape[1]} columns loaded from {filepath}")
    return df


def load_all_raw_tables(data_dir: str = 'data/raw') -> dict:
    """
    Load all four raw surveillance tables.
    Returns a dictionary of DataFrames keyed by table name.
    """
    tables = {
        'cases':         os.path.join(data_dir, 'cases_raw.csv'),
        'lab_results':   os.path.join(data_dir, 'lab_results_raw.csv'),
        'contacts':      os.path.join(data_dir, 'contacts_raw.csv'),
        'jurisdictions': os.path.join(data_dir, 'jurisdictions.csv'),
    }

    loaded = {}
    print("[EXTRACT] Loading all raw surveillance tables...")
    for name, path in tables.items():
        try:
            loaded[name] = load_csv(path, name)
        except FileNotFoundError as e:
            print(f"  WARNING: {e} — skipping {name}")

    print(f"[EXTRACT] Loaded {len(loaded)} tables successfully\n")
    return loaded
