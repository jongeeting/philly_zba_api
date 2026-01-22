#!/usr/bin/env python3
"""
Try to find residential new construction using old system codes
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("FINDING RESIDENTIAL NEW CONSTRUCTION 2007-2018")
print("="*80)

# First, explore what permit types and descriptions existed
print("\n1. Top permit types 2007-2018:")
print("-"*80)

query = """
    SELECT permittype, COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
    GROUP BY permittype
    ORDER BY count DESC
    LIMIT 15
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

for row in data['rows']:
    print(f"  {row['permittype']:<25} {row['count']:>10,}")

# Check descriptions for building permits
print("\n\n2. Top descriptions for building-related permits 2007-2018:")
print("-"*80)

query = """
    SELECT permitdescription, COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
        AND (permittype LIKE '%BUILD%' OR permittype LIKE '%CONSTR%')
    GROUP BY permitdescription
    ORDER BY count DESC
    LIMIT 20
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

for row in data['rows']:
    desc = row['permitdescription'] if row['permitdescription'] else 'NULL'
    print(f"  {desc[:60]:<60} {row['count']:>8,}")

# Look for residential indicators in old system
print("\n\n3. Permits with 'RESIDENTIAL' in description 2007-2018:")
print("-"*80)

query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
        AND (permitdescription ILIKE '%RESIDENTIAL%' 
             OR permitdescription ILIKE '%DWELLING%'
             OR permitdescription ILIKE '%FAMILY%')
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

for row in data['rows']:
    print(f"  {int(row['year'])}: {row['count']:,}")

# Check typeofwork = 'MAJOR' or 'NEWCON' which might indicate new construction
print("\n\n4. typeofwork = 'MAJOR' by year (might indicate new construction):")
print("-"*80)

query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
        AND typeofwork = 'MAJOR'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

for row in data['rows']:
    print(f"  {int(row['year'])}: {row['count']:,}")

# Look for L_BLDG_PERMIT (building permits) specifically
print("\n\n5. Building permits (L_BLDG_PERMIT, PP_BUILDING, etc.) by year:")
print("-"*80)

query = """
    SELECT 
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
        AND (permittype IN ('L_BLDG_PERMIT', 'PP_BUILDING', 'Building')
             OR permittype LIKE '%BUILD%')
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': query})
data = response.json()

total = 0
for row in data['rows']:
    count = row['count']
    total += count
    print(f"  {int(row['year'])}: {count:,}")
print(f"  Average/year: {total/12:,.0f}")

# Sample some building permits to see what they look like
print("\n\n6. Sample building permits from different years:")
print("-"*80)

for year in [2008, 2012, 2016]:
    query = f"""
        SELECT permitnumber, permittype, permitdescription, typeofwork, address
        FROM permits
        WHERE permitissuedate >= '{year}-01-01' AND permitissuedate < '{year+1}-01-01'
            AND (permittype = 'L_BLDG_PERMIT' OR permittype = 'PP_BUILDING')
        LIMIT 3
    """
    
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    print(f"\n{year} samples:")
    for row in data['rows']:
        desc = row['permitdescription'][:50] if row['permitdescription'] else 'NULL'
        work = row['typeofwork'] if row['typeofwork'] else 'NULL'
        print(f"  {row['permitnumber']}: {desc} ({work})")

