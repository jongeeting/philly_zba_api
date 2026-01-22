#!/usr/bin/env python3
"""
Match the exact periods from the city's 5-year report
"""

import requests
from datetime import datetime

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("MATCHING CITY'S ZONING CODE 5-YEAR REPORT PERIODS")
print("="*80)

# City's exact periods
periods = {
    "Old Code (8/22/08-8/21/12)": ("2008-08-22", "2012-08-22"),
    "New Code (8/22/12-8/21/16)": ("2012-08-22", "2016-08-22"),
}

results = {}

for period_name, (start_date, end_date) in periods.items():
    # Get ZBA appeals
    appeals_query = f"""
        SELECT COUNT(*) as count
        FROM appeals
        WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND createddate >= '{start_date}'
            AND createddate < '{end_date}'
    """
    
    response = requests.get(CARTO_API, params={'q': appeals_query})
    data = response.json()
    appeals = data['rows'][0]['count']
    
    # Get zoning permits
    permits_query = f"""
        SELECT COUNT(*) as count
        FROM permits
        WHERE (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
            AND permitissuedate >= '{start_date}'
            AND permitissuedate < '{end_date}'
    """
    
    response = requests.get(CARTO_API, params={'q': permits_query})
    data = response.json()
    permits = data['rows'][0]['count']
    
    total = appeals + permits
    var_rate = appeals / total * 100 if total > 0 else 0
    by_right_rate = permits / total * 100 if total > 0 else 0
    
    results[period_name] = {
        'appeals': appeals,
        'permits': permits,
        'total': total,
        'var_rate': var_rate,
        'by_right': by_right_rate
    }
    
    print(f"\n{period_name}:")
    print(f"  ZBA Appeals:       {appeals:>8,}")
    print(f"  Zoning Permits:    {permits:>8,}")
    print(f"  Total Projects:    {total:>8,}")
    print(f"  Variance rate:     {var_rate:>8.1f}%")
    print(f"  By-right rate:     {by_right_rate:>8.1f}%")

# Calculate improvement
print("\n" + "="*80)
print("COMPARISON")
print("="*80)

old_by_right = results["Old Code (8/22/08-8/21/12)"]['by_right']
new_by_right = results["New Code (8/22/12-8/21/16)"]['by_right']
improvement = new_by_right - old_by_right

print(f"\nOld Code by-right:     {old_by_right:.1f}%")
print(f"New Code by-right:     {new_by_right:.1f}%")
print(f"Improvement:           {improvement:+.1f} percentage points")

print(f"\nCity's reported improvement:  +6.0 percentage points")
print(f"Our calculated improvement:   {improvement:+.1f} percentage points")

if abs(improvement - 6.0) < 1:
    print("\n✓ MATCH! Our numbers align with city's report")
else:
    print(f"\n⚠️  DISCREPANCY: {abs(improvement - 6.0):.1f} point difference")

# Also check what the city's table shows
print("\n" + "="*80)
print("CITY'S TABLE 1 DATA")
print("="*80)
print("""
From the report (Table 1):

Old Code periods:
- 2008-2009: 5,864 apps, 1,843 appeals (31%)
- 2009-2010: 6,223 apps, 1,643 appeals (26%)
- 2010-2011: 6,020 apps, 1,505 appeals (25%)
- 2011-2012: 6,347 apps, 1,506 appeals (24%)

New Code periods:
- 2012-2013: 6,439 apps, 1,574 appeals (24%)
- 2013-2014: 6,177 apps, 1,435 appeals (23%)
- 2014-2015: 6,293 apps, 1,567 appeals (25%)
- 2015-2016: 6,504 apps, 1,609 appeals (25%)
- 2016-2017: 6,779 apps, 1,587 appeals (23%)

Note: City calculates % as appeals/completed_apps
We calculate: appeals/(appeals+permits) = variance rate
""")

