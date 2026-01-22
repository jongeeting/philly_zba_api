#!/usr/bin/env python3
"""
Try to match the city's exact methodology from Table 1
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("MATCHING CITY'S TABLE 1 METHODOLOGY")
print("="*80)

# City's exact period from report
start_date = "2008-08-22"
end_date_old = "2012-08-22"
end_date_new = "2016-08-22"

print(f"\nCity's Report Numbers (Table 1):")
print("-"*80)
print("\nOld Code (8/22/08 - 8/21/12):")
print("  Completed Applications: ~24,454 (avg 6,114/year)")
print("  Appeals: ~6,497 (avg 1,624/year)")
print("  % Appealed: ~27% (implies 73% by-right)")
print("  But text says: 68% by-right")

print("\nNew Code (8/22/12 - 8/21/16):")
print("  Completed Applications: ~25,413 (avg 6,353/year)")  
print("  Appeals: ~7,152 (avg 1,788/year)")
print("  Text says: 72% by-right")

# Try different interpretations
print("\n" + "="*80)
print("TESTING DIFFERENT PERMIT CATEGORIES")
print("="*80)

queries = {
    "All zoning permits (our current method)": f"""
        SELECT COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '{start_date}' AND permitissuedate < '{end_date_old}'
            AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
    """,
    
    "Exclude special exceptions (ZP_ADMIN, ZP_SPEC)": f"""
        SELECT COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '{start_date}' AND permitissuedate < '{end_date_old}'
            AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
            AND permittype NOT ILIKE '%ADMIN%'
            AND permittype NOT ILIKE '%SPEC%'
    """,
    
    "Only ZP_ZON/USE and ZP_ZONING": f"""
        SELECT COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '{start_date}' AND permitissuedate < '{end_date_old}'
            AND permittype IN ('ZP_ZON/USE', 'ZP_ZONING')
    """,
    
    "Check permittype breakdown": "LIST"
}

# Get ZBA appeals for comparison
appeals_query = f"""
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '{start_date}'
        AND createddate < '{end_date_old}'
"""

response = requests.get(CARTO_API, params={'q': appeals_query})
appeals = response.json()['rows'][0]['count']

print(f"\nOur ZBA appeals (8/22/08 - 8/21/12): {appeals:,}")
print(f"City's ZBA appeals: ~6,497")
print(f"Difference: {appeals - 6497:+,}")

# Test each query
for name, query in queries.items():
    if query == "LIST":
        # Show breakdown of permit types
        query = f"""
            SELECT permittype, COUNT(*) as count
            FROM permits
            WHERE permitissuedate >= '{start_date}' AND permitissuedate < '{end_date_old}'
                AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
            GROUP BY permittype
            ORDER BY count DESC
        """
        
        response = requests.get(CARTO_API, params={'q': query})
        data = response.json()
        
        print(f"\n{name}:")
        print(f"  {'Permit Type':<25} {'Count':>10} {'With Appeals':>15} {'By-Right %':>12}")
        print("  " + "-"*70)
        
        total = 0
        for row in data['rows']:
            count = row['count']
            total += count
            combined = count + appeals
            by_right = count / combined * 100
            print(f"  {row['permittype']:<25} {count:>10,} {combined:>15,} {by_right:>11.1f}%")
        
        print("  " + "-"*70)
        combined_total = total + appeals
        by_right_total = total / combined_total * 100
        print(f"  {'TOTAL':<25} {total:>10,} {combined_total:>15,} {by_right_total:>11.1f}%")
        print(f"\n  City's expected total: ~24,454")
        print(f"  Difference: {total - 24454:+,}")
        
    else:
        response = requests.get(CARTO_API, params={'q': query})
        permits = response.json()['rows'][0]['count']
        
        total = permits + appeals
        by_right = permits / total * 100
        
        print(f"\n{name}:")
        print(f"  Permits: {permits:,}")
        print(f"  Appeals: {appeals:,}")
        print(f"  Total: {total:,}")
        print(f"  By-right: {by_right:.1f}%")
        print(f"  City says: 68% by-right")
        print(f"  Difference: {by_right - 68:+.1f} points")

