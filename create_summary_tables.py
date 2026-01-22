#!/usr/bin/env python3
"""
Create summary tables for comparison document
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("TABLE 1: YEAR-BY-YEAR VARIANCE VS BY-RIGHT SHARE")
print("="*80)

# Get ZBA appeals by year
appeals_query = """
    SELECT
        EXTRACT(YEAR FROM createddate) as year,
        COUNT(*) as appeal_count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2007-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': appeals_query})
appeals_data = response.json()
appeals_by_year = {int(row['year']): int(row['appeal_count']) for row in appeals_data['rows']}

# Get zoning permits by year
permits_query = """
    SELECT
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as permit_count
    FROM permits
    WHERE permitissuedate >= '2007-01-01'
        AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': permits_query})
permits_data = response.json()
permits_by_year = {int(row['year']): int(row['permit_count']) for row in permits_data['rows']}

print("\n| Year | ZBA Appeals | Zoning Permits | Total Projects | Variance Share | By-Right Share |")
print("|------|-------------|----------------|----------------|----------------|----------------|")

for year in range(2007, 2026):  # Exclude 2026 partial year
    appeals = appeals_by_year.get(year, 0)
    permits = permits_by_year.get(year, 0)
    total = appeals + permits
    
    if total > 0:
        var_share = appeals / total * 100
        by_right_share = permits / total * 100
        print(f"| {year} | {appeals:,} | {permits:,} | {total:,} | {var_share:.1f}% | {by_right_share:.1f}% |")

# Period averages
print("\n" + "="*80)
print("PERIOD AVERAGES")
print("="*80)

periods = {
    "Pre-reform (2007-2012)": range(2007, 2013),
    "Post-reform (2013-2018)": range(2013, 2019),
    "Recent (2019-2025)": range(2019, 2026),
}

print("\n| Period | Avg Appeals/Year | Avg Permits/Year | Avg Total | Variance Share | By-Right Share |")
print("|--------|------------------|------------------|-----------|----------------|----------------|")

for period_name, years in periods.items():
    total_appeals = sum(appeals_by_year.get(y, 0) for y in years)
    total_permits = sum(permits_by_year.get(y, 0) for y in years)
    total = total_appeals + total_permits
    
    avg_appeals = total_appeals / len(years)
    avg_permits = total_permits / len(years)
    avg_total = total / len(years)
    
    var_share = total_appeals / total * 100 if total > 0 else 0
    by_right_share = total_permits / total * 100 if total > 0 else 0
    
    print(f"| {period_name} | {avg_appeals:,.0f} | {avg_permits:,.0f} | {avg_total:,.0f} | {var_share:.1f}% | {by_right_share:.1f}% |")

