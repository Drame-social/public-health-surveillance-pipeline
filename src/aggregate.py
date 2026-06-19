"""
aggregate.py — Aggregation and Summary Module
Public Health Surveillance Data Pipeline
Author: Aly Drame, MD, MPH, MBA
"""

import pandas as pd
import numpy as np
import os


def weekly_case_counts(df: pd.DataFrame,
                        output_path: str = None) -> pd.DataFrame:
    """
    Aggregate case counts by epidemiologic week and disease.
    Calculates week-over-week change and case fatality rate.
    Mirrors CDC weekly surveillance reporting format.
    """
    # Filter to records with valid epi_week_label
    df_valid = df[df['epi_week_label'].notna()].copy()

    weekly = (
        df_valid
        .groupby(['epi_year','epi_week_num','epi_week_label','disease_name'])
        .agg(
            case_count          = ('case_id', 'count'),
            confirmed_cases     = ('confirmed_binary', 'sum'),
            hospitalized_count  = ('hospitalized_binary', 'sum'),
            death_count         = ('died_binary', 'sum'),
        )
        .reset_index()
        .sort_values(['disease_name','epi_year','epi_week_num'])
    )

    weekly['case_fatality_rate'] = (
        weekly['death_count'] / weekly['case_count'].replace(0, np.nan) * 100
    ).round(1)

    weekly['hospitalization_rate'] = (
        weekly['hospitalized_count'] / weekly['case_count'].replace(0, np.nan) * 100
    ).round(1)

    # Week-over-week change
    weekly['prior_week_count'] = (
        weekly.groupby('disease_name')['case_count'].shift(1))
    weekly['wow_change'] = weekly['case_count'] - weekly['prior_week_count']
    weekly['wow_pct_change'] = (
        weekly['wow_change'] /
        weekly['prior_week_count'].replace(0, np.nan) * 100
    ).round(1)

    if output_path:
        weekly.to_csv(output_path, index=False)
        print(f"[AGGREGATE] Weekly case counts saved → {output_path}")

    return weekly


def jurisdiction_summary(df: pd.DataFrame,
                           jurisdictions: pd.DataFrame,
                           output_path: str = None) -> pd.DataFrame:
    """
    Summarize cases by jurisdiction with incidence rates.
    """
    jur_counts = (
        df.groupby(['jurisdiction_id','report_year','disease_name'])
        .agg(
            case_count         = ('case_id',             'count'),
            hospitalized_count = ('hospitalized_binary', 'sum'),
            death_count        = ('died_binary',         'sum'),
            confirmed_count    = ('confirmed_binary',     'sum'),
            completeness_mean  = ('completeness_score',  'mean'),
        )
        .reset_index()
    )

    jur_counts = jur_counts.merge(
        jurisdictions[['jurisdiction_id','jurisdiction_name',
                        'region','population_2022']],
        on='jurisdiction_id', how='left')

    jur_counts['incidence_per_100k'] = (
        jur_counts['case_count'] /
        jur_counts['population_2022'] * 100_000
    ).round(2)

    jur_counts['completeness_mean'] = jur_counts['completeness_mean'].round(1)

    if output_path:
        jur_counts.to_csv(output_path, index=False)
        print(f"[AGGREGATE] Jurisdiction summary saved → {output_path}")

    return jur_counts


def contact_tracing_metrics(contacts: pd.DataFrame,
                              cases: pd.DataFrame,
                              output_path: str = None) -> pd.DataFrame:
    """
    Calculate contact tracing performance metrics by jurisdiction.
    """
    # Merge contacts with case jurisdiction
    merged = contacts.merge(
        cases[['case_id','jurisdiction_id','disease_name']],
        on='case_id', how='left')

    metrics = (
        merged
        .groupby(['jurisdiction_id','disease_name'])
        .agg(
            total_cases_traced    = ('case_id',         'nunique'),
            total_contacts        = ('contact_id',       'count'),
            contacts_completed    = ('contact_status',
                                      lambda x: (x=='Completed').sum()),
            contacts_ltf          = ('contact_status',
                                      lambda x: (x=='Lost to Follow-up').sum()),
            contacts_became_cases = ('became_case',
                                      lambda x: (x=='Y').sum()),
        )
        .reset_index()
    )

    metrics['pct_contacts_completed'] = (
        metrics['contacts_completed'] /
        metrics['total_contacts'].replace(0, np.nan) * 100
    ).round(1)

    metrics['secondary_attack_rate'] = (
        metrics['contacts_became_cases'] /
        metrics['total_contacts'].replace(0, np.nan) * 100
    ).round(1)

    metrics['loss_to_followup_rate'] = (
        metrics['contacts_ltf'] /
        metrics['total_contacts'].replace(0, np.nan) * 100
    ).round(1)

    if output_path:
        metrics.to_csv(output_path, index=False)
        print(f"[AGGREGATE] Contact tracing metrics saved → {output_path}")

    return metrics
