#!/usr/bin/env python3
"""
Analyze ZONING permits consistently across all years (2007-2026)
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("ZONING PERMITS ANALYSIS (2007-2026)")
print("="*80)

# First, what zoning permit types exist?
print("\n1. Zoning permit types across all years:")
print("-"*80)

query = """
    SELECT permittype, COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01'
        AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
    GROUP BY permittype
    ORDER BY count DESC
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

print(f"\n{'Permit Type':<30} {'Count':>10}")
print("-"*45)
for row in data['rows']:
    print(f"{row['permittype']:<30} {row['count']:>10,}")

# Get zoning permits by year
print("\n\n2. Zoning permits by year (all types):")
print("-"*80)

query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01'
        AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

zoning_by_year = {int(row['year']): int(row['count']) for row in data['rows']}

# Get ZBA appeals
appeals_query = """
    SELECT 
        EXTRACT(YEAR FROM createddate) as year,
        COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2007-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': appeals_query})
appeals_data = response.json()
appeals_by_year = {int(row['year']): int(row['count']) for row in appeals_data['rows']}

# Compare
print(f"\n{'Year':<6} {'ZBA Appeals':>12} {'Zoning Permits':>15} {'Total Projects':>15} {'Variance Rate':>14} {'By-Right Rate':>14}")
print("-"*90)

for year in range(2007, 2027):
    appeals = appeals_by_year.get(year, 0)
    zoning = zoning_by_year.get(year, 0)
    total = appeals + zoning
    
    if total > 0:
        var_rate = appeals / total * 100
        by_right_rate = zoning / total * 100
        print(f"{year:<6} {appeals:>12,} {zoning:>15,} {total:>15,} {var_rate:>13.1f}% {by_right_rate:>13.1f}%")
    else:
        print(f"{year:<6} {appeals:>12,} {zoning:>15,} {total:>15,} {'N/A':>13} {'N/A':>13}")

# Period summaries
print("\n" + "="*80)
print("PERIOD SUMMARIES")
print("="*80)

periods = [
    ("2007-2012 (Pre-reform)", range(2007, 2013)),
    ("2013-2018 (Post-reform)", range(2013, 2019)),
    ("2019-2026 (Recent)", range(2019, 2027)),
]

for period_name, years in periods:
    total_appeals = sum(appeals_by_year.get(y, 0) for y in years)
    total_zoning = sum(zoning_by_year.get(y, 0) for y in years)
    total_projects = total_appeals + total_zoning
    
    if total_projects > 0:
        var_rate = total_appeals / total_projects * 100
        by_right_rate = total_zoning / total_projects * 100
        
        print(f"\n{period_name}:")
        print(f"  Total ZBA appeals:     {total_appeals:>8,}")
        print(f"  Total zoning permits:  {total_zoning:>8,}")
        print(f"  Total projects:        {total_projects:>8,}")
        print(f"  Variance rate:         {var_rate:>8.1f}%")
        print(f"  By-right rate:         {by_right_rate:>8.1f}%")

# Sample some zoning permits to see what they are
print("\n\n3. Sample zoning permits from 2020s:")
print("-"*80)

query = """
    SELECT permitnumber, permittype, permitdescription, address, permitissuedate
    FROM permits
    WHERE permitissuedate >= '2020-01-01'
        AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
    LIMIT 10
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

for row in data['rows']:
    desc = row['permitdescription'][:40] if row['permitdescription'] else 'NULL'
    addr = row['address'][:30] if row['address'] else 'NULL'
    date = row['permitissuedate'][:10] if row['permitissuedate'] else 'NULL'
    print(f"{date} | {row['permittype']:<20} | {desc}")

