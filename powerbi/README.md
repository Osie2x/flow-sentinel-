# Power BI Pack

This folder holds the Power BI artifacts used to turn the exported pipeline outputs into an executive dashboard.

Files:
- `flowsentinel_measures.dax`: reusable KPI measures for scorecards, trend lines, and compliance views.
- `flowsentinel_transform.m`: Power Query script for loading the curated CSV exports from `data/processed/`.

Suggested dashboard pages:
1. Executive Overview: health score, throughput, violations, anomaly rate.
2. Team Operations: exceptions by team, severity, and department.
3. Process Efficiency: average processing time by hour, region, and category.
4. Compliance Monitoring: rule-level failure counts and daily trend lines.

