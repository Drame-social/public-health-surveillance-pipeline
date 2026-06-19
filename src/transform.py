"""
transform.py — Data Transformation Module
Public Health Surveillance Data Pipeline
Author: Aly Drame, MD, MPH, MBA

Merges clean tables and creates the analytical dataset used for
all downstream analysis and dashboard reporting.
"""

import pandas as pd
import os


def build_analytical_dataset(cases: pd.DataFrame,
                               lab_results: pd.DataFrame,
                               contacts: pd.DataFrame,
                               jurisdictions: pd.DataFrame
                               ) -> pd.DataFrame:
    """
    Join all four tables into a single analytical dataset.
    Adds derived indicators used in dashboard reporting.
    """
    # Join jurisdiction attributes
    analytical = cases.merge(
        jurisdictions[['jurisdiction_id','jurisdiction_name','region',
                        'population_2022','urban_rural_class',
                        'health_department_capacity']],
        on='jurisdiction_id',
        how='left'
    )

    # Lab result summary per case — is there any positive result?
    if not lab_results.empty:
        lab_summary = (
            lab_results
            .groupby('case_id')
            .agg(
                n_lab_tests       = ('lab_id',   'count'),
                any_positive      = ('result',    lambda x: int('Positive' in x.values)),
                days_to_first_result = ('days_to_result', 'min')
            )
            .reset_index()
        )
        analytical = analytical.merge(lab_summary, on='case_id', how='left')
        analytical['n_lab_tests']       = analytical['n_lab_tests'].fillna(0)
        analytical['any_positive']      = analytical['any_positive'].fillna(0)

    # Contact summary per case
    if not contacts.empty:
        contact_summary = (
            contacts
            .groupby('case_id')
            .agg(
                n_contacts_identified = ('contact_id', 'count'),
                n_contacts_became_case = ('became_case',
                                           lambda x: (x=='Y').sum()),
                n_lost_to_followup    = ('contact_status',
                                          lambda x: (x=='Lost to Follow-up').sum())
            )
            .reset_index()
        )
        analytical = analytical.merge(contact_summary,
                                       on='case_id', how='left')
        analytical['n_contacts_identified']  = \
            analytical['n_contacts_identified'].fillna(0)
        analytical['n_contacts_became_case'] = \
            analytical['n_contacts_became_case'].fillna(0)
        analytical['n_lost_to_followup']     = \
            analytical['n_lost_to_followup'].fillna(0)

    # Derived indicators
    analytical['hospitalized_binary'] = (
        (analytical['hospitalized'] == 'Y').astype(int))
    analytical['died_binary'] = (
        (analytical['died'] == 'Y').astype(int))
    analytical['confirmed_binary'] = (
        (analytical['case_status'] == 'Confirmed').astype(int))
    analytical['investigation_complete_binary'] = (
        analytical['investigation_status'].isin(
            ['Complete','Closed'])).astype(int)

    # Incidence rate per 100,000 — will be aggregated later
    # (kept at row level as a flag for jurisdiction-level calculations)
    analytical['report_year'] = pd.to_datetime(
        analytical['report_date'], errors='coerce').dt.year

    print(f"[TRANSFORM] Analytical dataset: {len(analytical):,} rows × "
          f"{analytical.shape[1]} columns")
    return analytical


def save_processed_tables(cases_clean: pd.DataFrame,
                           lab_clean: pd.DataFrame,
                           contacts_clean: pd.DataFrame,
                           analytical: pd.DataFrame,
                           output_dir: str = 'data/processed') -> None:
    """Save all cleaned and transformed tables to CSV."""
    os.makedirs(output_dir, exist_ok=True)
    cases_clean.to_csv(
        os.path.join(output_dir, 'cases_clean.csv'),    index=False)
    lab_clean.to_csv(
        os.path.join(output_dir, 'lab_results_clean.csv'), index=False)
    contacts_clean.to_csv(
        os.path.join(output_dir, 'contacts_clean.csv'), index=False)
    analytical.to_csv(
        os.path.join(output_dir, 'surveillance_analytical.csv'),
        index=False)
    print(f"[TRANSFORM] All cleaned tables saved to {output_dir}/")
