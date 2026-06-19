/*====================================================================
  01_descriptive_surveillance.sas
  Project: Public Health Surveillance Data Pipeline
  Author:  Aly Drame, MD, MPH, MBA
  Purpose: Descriptive analysis of surveillance case data
====================================================================*/

libname surv "/home/yourusername/surveillance";

/* Import cleaned cases */
proc import
    datafile="/home/yourusername/surveillance/data/processed/cases_clean.csv"
    out=surv.cases dbms=csv replace;
    guessingrows=1000;
run;

proc import
    datafile="/home/yourusername/surveillance/data/raw/jurisdictions.csv"
    out=surv.jurisdictions dbms=csv replace;
run;

/* Verify */
proc contents data=surv.cases; run;
proc print data=surv.cases(obs=5); run;

/* Overall case counts */
title "Case Count by Disease";
proc freq data=surv.cases;
    tables disease_name / nocum;
run;

/* Case counts by year */
title "Case Count by Disease and Year";
proc freq data=surv.cases;
    tables disease_name*epi_year / nocum norow;
run;

/* Demographic distribution */
title "Case Distribution by Age Group and Sex";
proc freq data=surv.cases;
    tables age_group*sex / chisq;
run;

/* Clinical severity */
title "Clinical Severity by Disease";
proc freq data=surv.cases;
    tables disease_name*hospitalized / nocum norow;
    tables disease_name*died / nocum norow;
run;

/* Completeness score distribution */
title "Completeness Score Distribution";
proc means data=surv.cases n mean median std min p25 p75 max;
    var completeness_score;
    class disease_name;
run;

/* Investigation timeliness */
title "Investigation Timeliness — Days to Close";
proc means data=surv.cases(where=(days_to_close ne .))
    n mean median std p25 p75 min max;
    var days_to_close;
    class disease_name;
run;
