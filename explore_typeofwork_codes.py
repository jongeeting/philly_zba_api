#!/usr/bin/env python3
"""
Explore old typeofwork codes to approximate new construction
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("EXPLORING OLD TYPEOFWORK CODES")
print("="*80)

# What do the old typeofwork codes mean?
print("\n1. Old typeofwork codes and sample descriptions:")
print("-"*80)

for code in ['MAJOR', 'MINOR', 'ENTIRE', 'FOUND', 'NEWCON', 'EZPLUM', 'EZELEC']:
    query = f"""
        SELECT permittype, permitdescription, COUNT(*) as count
        FROM permits
        WHERE typeofwork = '{code}'
            AND permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
        GROUP BY permittype, permitdescription
        ORDER BY count DESC
        LIMIT 3
    """
    
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    print(f"\n{code}:")
    for row in data['rows']:
        desc = row['permitdescription'][:50] if row['permitdescription'] else 'NULL'
        print(f"  {row['permittype']:<20} {desc:<50} ({row['count']:,})")

# Try combining permit types that likely represent building construction
print("\n\n2. Building-related permit types by year:")
print("-"*80)

# Try permits that are likely new buildings
query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
        AND (
            permittype IN ('BP_NEWCNST', 'BP_ADDITON')
            OR (typeofwork IN ('MAJOR', 'ENTIRE', 'NEWCON', 'FOUND'))
        )
        AND permittype NOT IN ('PP_PLUMBNG', 'EP_ELECTRL', 'BP_MECH')  -- Exclude trade permits
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

print(f"\n{'Year':<6} {'Count':>10}")
print("-"*30)
for row in data['rows']:
    print(f"{int(row['year']):<6} {row['count']:>10,}")

total = sum(row['count'] for row in data['rows'])
print(f"{'Avg':<6} {total/12:>10,.0f}")

# Get corresponding ZBA data
appeals_query = """
    SELECT 
        EXTRACT(YEAR FROM createddate) as year,
        COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2007-01-01' AND createddate < '2019-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': appeals_query})
appeals_data = response.json()

print("\n\n3. Ratio analysis:")
print("-"*80)

# Store results for ratio calculation
year_data = {}
for row in data['rows']:
    year_data[int(row['year'])] = row['count']

print(f"\n{'Year':<6} {'ZBA Appeals':>12} {'Building Permits':>16} {'Ratio':>10}")
print("-"*50)

for row in appeals_data['rows']:
    year = int(row['year'])
    appeals = row['count']
    permits = year_data.get(year, 0)
    ratio = appeals / permits * 100 if permits > 0 else 0
    
    print(f"{year:<6} {appeals:>12,} {permits:>16,} {ratio:>9.1f}%")

