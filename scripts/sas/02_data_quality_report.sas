/*====================================================================
  02_data_quality_report.sas
  Purpose: SAS-based data quality report using ODS PDF
====================================================================*/

libname surv "/home/yourusername/surveillance";

ods pdf
    file="/home/yourusername/surveillance/outputs/data_quality_report.pdf"
    style=journal;

ods pdf text="^S={font_size=16pt font_weight=bold just=c}
Data Quality Report — Public Health Surveillance Pipeline";
ods pdf text="^S={font_size=10pt just=c}
Synthetic Data — Portfolio Demonstration | &sysdate9";

/* Section 1: Completeness */
ods pdf startpage=now;
title "Section 1 — Data Completeness Summary";
proc means data=surv.cases n nmiss;
    var completeness_score;
run;

/* Completeness by jurisdiction */
title "Completeness Score by Jurisdiction";
proc means data=surv.cases mean median min max;
    var completeness_score;
    class jurisdiction_id;
run;

/* Section 2: Missing data */
ods pdf startpage=now;
title "Section 2 — Missing Data by Key Field";
proc freq data=surv.cases;
    tables report_date onset_date age_group sex
           race_ethnicity hospitalized died / missing;
run;

/* Section 3: Timeliness */
ods pdf startpage=now;
title "Section 3 — Investigation Timeliness";
proc freq data=surv.cases;
    where days_to_close ne .;
    tables investigation_status;
run;

proc means data=surv.cases(where=(days_to_close ne .))
    n mean median p75 max;
    var days_to_close;
    class disease_name;
run;

ods pdf close;

%put NOTE: Data quality report saved to outputs/data_quality_report.pdf;
