#!/usr/bin/env python3
"""
Explore permit data structure for 2007-2018 period
"""

import requests
import pandas as pd

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("EXPLORING PERMIT DATA 2007-2018")
print("="*80)

# First, let's see what fields are available in the permits table
print("\n1. Sample of permits from different years to see field structure:")
print("-"*80)

for year in [2008, 2012, 2015, 2018, 2020, 2023]:
    query = f"""
        SELECT *
        FROM permits
        WHERE permitissuedate >= '{year}-01-01' 
            AND permitissuedate < '{year+1}-01-01'
        LIMIT 1
    """
    
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    if data['rows']:
        row = data['rows'][0]
        print(f"\n{year} sample permit:")
        print(f"  commercialorresidential: {row.get('commercialorresidential', 'MISSING')}")
        print(f"  typeofwork: {row.get('typeofwork', 'MISSING')}")
        print(f"  permittype: {row.get('permittype', 'MISSING')}")
        print(f"  permitdescription: {row.get('permitdescription', 'MISSING')[:100] if row.get('permitdescription') else 'MISSING'}")
    else:
        print(f"\n{year}: NO PERMITS FOUND")

# Check what values exist for key fields in different periods
print("\n\n2. Field value distributions by period:")
print("-"*80)

periods = [
    ("2007-2010", "2007-01-01", "2011-01-01"),
    ("2011-2014", "2011-01-01", "2015-01-01"),
    ("2015-2018", "2015-01-01", "2019-01-01"),
    ("2019-2023", "2019-01-01", "2024-01-01"),
]

for period_name, start, end in periods:
    print(f"\n{period_name}:")
    
    # Check commercialorresidential values
    query = f"""
        SELECT commercialorresidential, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '{start}' AND permitissuedate < '{end}'
        GROUP BY commercialorresidential
        ORDER BY count DESC
        LIMIT 5
    """
    
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    print(f"  commercialorresidential values:")
    if data['rows']:
        for row in data['rows']:
            val = row['commercialorresidential'] if row['commercialorresidential'] else 'NULL'
            print(f"    {val}: {row['count']:,}")
    else:
        print("    NO DATA")
    
    # Check typeofwork values
    query = f"""
        SELECT typeofwork, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '{start}' AND permitissuedate < '{end}'
        GROUP BY typeofwork
        ORDER BY count DESC
        LIMIT 5
    """
    
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    print(f"  typeofwork values:")
    if data['rows']:
        for row in data['rows']:
            val = row['typeofwork'] if row['typeofwork'] else 'NULL'
            print(f"    {val}: {row['count']:,}")
    else:
        print("    NO DATA")

# Try different query approaches for 2007-2018
print("\n\n3. Testing different queries for 2007-2018:")
print("-"*80)

queries = [
    ("Development Digest query", """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
            AND commercialorresidential = 'Residential'
            AND typeofwork = 'New Construction'
        GROUP BY year
        ORDER BY year
    """),
    ("All residential (any typeofwork)", """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
            AND commercialorresidential = 'Residential'
        GROUP BY year
        ORDER BY year
    """),
    ("Permit type ZONING", """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
            AND permittype LIKE '%ZONING%'
        GROUP BY year
        ORDER BY year
    """),
    ("All permits (no filter)", """
        SELECT EXTRACT(YEAR FROM permitissuedate) as year, COUNT(*) as count
        FROM permits
        WHERE permitissuedate >= '2007-01-01' AND permitissuedate < '2019-01-01'
        GROUP BY year
        ORDER BY year
    """),
]

for query_name, query in queries:
    response = requests.get(CARTO_API, params={'q': query})
    data = response.json()
    
    print(f"\n{query_name}:")
    if data['rows']:
        total = sum(row['count'] for row in data['rows'])
        print(f"  Total: {total:,} permits")
        for row in data['rows']:
            print(f"  {int(row['year'])}: {row['count']:,}")
    else:
        print("  NO RESULTS")

