#!/usr/bin/env python3
"""
Create refined denominator for 2007-2018 focusing on new construction
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("REFINED PERMIT DENOMINATOR 2007-2018")
print("="*80)

# Try different combinations to approximate residential new construction
queries = {
    "All building permits (MAJOR/ENTIRE/NEWCON/FOUND)": """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
            AND (
                permittype IN ('BP_NEWCNST', 'BP_ADDITON')
                OR typeofwork IN ('MAJOR', 'ENTIRE', 'NEWCON', 'FOUND')
            )
            AND permittype NOT IN ('PP_PLUMBNG', 'EP_ELECTRL', 'BP_MECH')
        GROUP BY year ORDER BY year
    """,
    
    "New construction focused (ENTIRE/FOUND/BP_NEWCNST)": """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
            AND (
                typeofwork IN ('ENTIRE', 'FOUND')
                OR permittype = 'BP_NEWCNST'
            )
        GROUP BY year ORDER BY year
    """,
    
    "MAJOR construction only": """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
            AND typeofwork = 'MAJOR'
        GROUP BY year ORDER BY year
    """,
    
    "BP_NEWCNST + typeofwork ENTIRE": """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
            AND (permittype = 'BP_NEWCNST' OR typeofwork = 'ENTIRE')
        GROUP BY year ORDER BY year
    """,
}

# Get ZBA appeals
appeals_query = """
    SELECT EXTRACT(YEAR FROM createddate) as year, COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2007-01-01' AND createddate < '2019-01-01'
    GROUP BY year ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': appeals_query})
appeals_data = response.json()
appeals_by_year = {int(row['year']): row['count'] for row in appeals_data['rows']}

# Test each query
for name, query in queries.items():
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    permits_by_year = {int(row['year']): row['count'] for row in data['rows']}
    
    print(f"\n{name}")
    print("="*80)
    print(f"{'Year':<6} {'ZBA Appeals':>12} {'Permits':>12} {'Variance Rate':>14} {'By-Right':>10}")
    print("-"*80)
    
    total_appeals = 0
    total_permits = 0
    
    for year in range(2007, 2019):
        appeals = appeals_by_year.get(year, 0)
        permits = permits_by_year.get(year, 0)
        
        total_appeals += appeals
        total_permits += permits
        
        if permits > 0:
            var_rate = appeals / permits * 100
            by_right = 100 - var_rate
            print(f"{year:<6} {appeals:>12,} {permits:>12,} {var_rate:>13.1f}% {by_right:>9.1f}%")
        else:
            print(f"{year:<6} {appeals:>12,} {permits:>12} {'N/A':>13} {'N/A':>9}")
    
    # Period summaries
    avg_appeals = total_appeals / 12
    avg_permits = total_permits / 12
    overall_var = total_appeals / total_permits * 100 if total_permits > 0 else 0
    overall_byright = 100 - overall_var
    
    print("-"*80)
    print(f"{'Avg':<6} {avg_appeals:>12,.0f} {avg_permits:>12,.0f} {overall_var:>13.1f}% {overall_byright:>9.1f}%")
    
    # Split into periods
    pre_reform_appeals = sum(appeals_by_year.get(y, 0) for y in range(2007, 2013))
    pre_reform_permits = sum(permits_by_year.get(y, 0) for y in range(2007, 2013))
    
    post_reform_appeals = sum(appeals_by_year.get(y, 0) for y in range(2013, 2019))
    post_reform_permits = sum(permits_by_year.get(y, 0) for y in range(2013, 2019))
    
    pre_var = pre_reform_appeals / pre_reform_permits * 100 if pre_reform_permits > 0 else 0
    post_var = post_reform_appeals / post_reform_permits * 100 if post_reform_permits > 0 else 0
    
    print(f"\n  2007-2012 variance rate: {pre_var:.1f}% ({100-pre_var:.1f}% by-right)")
    print(f"  2013-2018 variance rate: {post_var:.1f}% ({100-post_var:.1f}% by-right)")
    print(f"  Improvement: {pre_var-post_var:+.1f} percentage points")

