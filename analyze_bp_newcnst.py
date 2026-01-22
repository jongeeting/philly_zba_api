#!/usr/bin/env python3
"""
Analyze BP_NEWCNST (new construction building permits) as denominator
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("NEW CONSTRUCTION BUILDING PERMITS (BP_NEWCNST) 2007-2026")
print("="*80)

# Get BP_NEWCNST by year
query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as count
    FROM permits
    WHERE permittype = 'BP_NEWCNST'
        AND permitissuedate >= '2007-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

bp_newcnst_by_year = {int(row['year']): int(row['count']) for row in data['rows']}

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

# Get Res NewCon for 2019+
dev_query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as count
    FROM permits
    WHERE commercialorresidential = 'Residential'
        AND typeofwork = 'New Construction'
        AND permitissuedate >= '2019-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': dev_query})
dev_data = response.json()
dev_by_year = {int(row['year']): int(row['count']) for row in dev_data['rows']}

# Compare
print(f"\n{'Year':<6} {'ZBA Appeals':>12} {'BP_NEWCNST':>12} {'Ratio':>8} {'Res NewCon':>12} {'Ratio':>8}")
print("-"*80)

for year in range(2007, 2027):
    appeals = appeals_by_year.get(year, 0)
    bp = bp_newcnst_by_year.get(year, 0)
    dev = dev_by_year.get(year, 0)
    
    ratio_bp = f"{appeals/bp*100:.1f}%" if bp > 0 else "N/A"
    ratio_dev = f"{appeals/dev*100:.1f}%" if dev > 0 else "N/A"
    dev_str = f"{dev:,}" if dev > 0 else "-"
    bp_str = f"{bp:,}" if bp > 0 else "0"
    
    print(f"{year:<6} {appeals:>12,} {bp_str:>12} {ratio_bp:>8} {dev_str:>12} {ratio_dev:>8}")

# Period summaries
print("\n" + "="*80)
print("PERIOD SUMMARIES")
print("="*80)

periods = [
    ("2007-2012 (Pre-reform)", range(2007, 2013)),
    ("2013-2018 (Post-reform)", range(2013, 2019)),
]

for period_name, years in periods:
    total_appeals = sum(appeals_by_year.get(y, 0) for y in years)
    total_bp = sum(bp_newcnst_by_year.get(y, 0) for y in years)
    
    avg_appeals = total_appeals / len(years)
    avg_bp = total_bp / len(years) if total_bp > 0 else 0
    ratio = total_appeals / total_bp * 100 if total_bp > 0 else 0
    
    print(f"\n{period_name}:")
    print(f"  Total ZBA appeals:        {total_appeals:>8,}")
    print(f"  Total BP_NEWCNST:         {total_bp:>8,}")
    print(f"  Avg appeals/year:         {avg_appeals:>8,.0f}")
    print(f"  Avg BP_NEWCNST/year:      {avg_bp:>8,.0f}")
    print(f"  Variance rate:            {ratio:>8.1f}%")
    print(f"  By-right rate:            {100-ratio:>8.1f}%")

# Also check samples to see what BP_NEWCNST looks like
print("\n" + "="*80)
print("SAMPLE BP_NEWCNST PERMITS")
print("="*80)

for year in [2008, 2012, 2016]:
    query = f"""
        SELECT permitnumber, address, permitdescription, typeofwork
        FROM permits
        WHERE permittype = 'BP_NEWCNST'
            AND permitissuedate >= '{year}-01-01' 
            AND permitissuedate < '{year+1}-01-01'
        LIMIT 5
    """
    
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    print(f"\n{year} ({len(data['rows'])} samples):")
    for row in data['rows']:
        desc = row['permitdescription'][:60] if row['permitdescription'] else 'NULL'
        work = row['typeofwork'] if row['typeofwork'] else 'NULL'
        addr = row['address'][:40] if row['address'] else 'NULL'
        print(f"  {addr:<40} {work:<10} {desc}")

