#!/usr/bin/env python3
"""
Verify if zoning permits are the right denominator for 2007-2018
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("COMPARING ZBA APPEALS vs ZONING PERMITS (2007-2026)")
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
    WHERE permittype LIKE '%ZONING%'
        AND permitissuedate >= '2007-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': permits_query})
permits_data = response.json()
permits_by_year = {int(row['year']): int(row['permit_count']) for row in permits_data['rows']}

# Get residential new construction for 2019+ (Development Digest approach)
dev_digest_query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as permit_count
    FROM permits
    WHERE commercialorresidential = 'Residential'
        AND typeofwork = 'New Construction'
        AND permitissuedate >= '2019-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': dev_digest_query})
dev_data = response.json()
dev_by_year = {int(row['year']): int(row['permit_count']) for row in dev_data['rows']}

# Compare
print(f"\n{'Year':<6} {'ZBA Appeals':>12} {'Zoning Permits':>15} {'Ratio':>8} {'Res NewCon':>12} {'Ratio':>8}")
print("-"*80)

for year in range(2007, 2027):
    appeals = appeals_by_year.get(year, 0)
    zoning = permits_by_year.get(year, 0)
    dev = dev_by_year.get(year, 0)
    
    ratio_zoning = f"{appeals/zoning*100:.1f}%" if zoning > 0 else "N/A"
    ratio_dev = f"{appeals/dev*100:.1f}%" if dev > 0 else "N/A"
    dev_str = f"{dev:,}" if dev > 0 else "-"
    
    print(f"{year:<6} {appeals:>12,} {zoning:>15,} {ratio_zoning:>8} {dev_str:>12} {ratio_dev:>8}")

# Period summaries
print("\n" + "="*80)
print("PERIOD SUMMARIES")
print("="*80)

periods = [
    ("2007-2012 (Pre-reform)", range(2007, 2013)),
    ("2013-2018 (Post-reform)", range(2013, 2019)),
    ("2019-2026 (Res NewCon data)", range(2019, 2027)),
]

for period_name, years in periods:
    total_appeals = sum(appeals_by_year.get(y, 0) for y in years)
    total_zoning = sum(permits_by_year.get(y, 0) for y in years)
    total_dev = sum(dev_by_year.get(y, 0) for y in years)
    
    avg_appeals = total_appeals / len(years)
    avg_zoning = total_zoning / len(years) if total_zoning > 0 else 0
    avg_dev = total_dev / len(years) if total_dev > 0 else 0
    
    ratio_zoning = total_appeals / total_zoning * 100 if total_zoning > 0 else 0
    ratio_dev = total_appeals / total_dev * 100 if total_dev > 0 else 0
    
    print(f"\n{period_name}:")
    print(f"  Avg ZBA appeals/year:        {avg_appeals:>8,.0f}")
    print(f"  Avg zoning permits/year:     {avg_zoning:>8,.0f}  (ratio: {ratio_zoning:.1f}%)")
    if avg_dev > 0:
        print(f"  Avg res new construction/yr: {avg_dev:>8,.0f}  (ratio: {ratio_dev:.1f}%)")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)
print("""
FINDINGS:

1. ZONING PERMITS (2007-2018):
   - Consistent ~1,500-2,000 permits/year
   - Variance rate: ~85-95% (VERY HIGH!)
   - This can't be right - way too high
   - Likely represents only variances + special exceptions, not all development

2. RESIDENTIAL NEW CONSTRUCTION (2019-2026):
   - ~2,700-5,000 permits/year
   - Variance rate: ~22-37% (REASONABLE)
   - This makes sense - about 1 in 3 projects needs variances

3. THE PROBLEM:
   - "Zoning permits" in old system ≠ "all development requiring zoning approval"
   - "Zoning permits" likely = variances + special exceptions + certificates
   - So zoning permits ≈ ZBA appeals (both ~1,500/year)
   - This makes them unsuitable as denominator!

4. CONCLUSION:
   - We CANNOT calculate accurate variance-to-permit ratios for 2007-2018
   - The data fields we need (commercialorresidential, typeofwork) don't exist
   - We can only reliably calculate ratios for 2019-2026
""")
