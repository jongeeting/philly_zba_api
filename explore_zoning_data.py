#!/usr/bin/env python3
"""
Explore zoning base districts data and link to appeals
"""

import requests
import time
from collections import defaultdict, Counter

CARTO_API = "https://phl.carto.com/api/v2/sql"

def safe_query(query, timeout=60):
    """Execute query with retry."""
    for attempt in range(3):
        try:
            response = requests.get(CARTO_API, params={'q': query}, timeout=timeout)
            return response.json()
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    return None

print("=" * 100)
print("ZONING DISTRICTS EXPLORATION")
print("=" * 100)
print()

# Get sample of zoning data
print("1. Exploring zoning_basedistricts table...")
query = """
    SELECT *
    FROM zoning_basedistricts
    LIMIT 5
"""

data = safe_query(query)
if data and 'rows' in data and len(data['rows']) > 0:
    print("Sample fields:")
    for key in sorted(data['rows'][0].keys()):
        value = data['rows'][0][key]
        if isinstance(value, str) and len(value) > 100:
            value = value[:100] + "..."
        print(f"  {key:30} = {value}")
    print()

# Get list of unique zoning codes
print("2. Getting unique zoning codes...")
query = """
    SELECT long_code, short_code, COUNT(*) as parcel_count
    FROM zoning_basedistricts
    GROUP BY long_code, short_code
    ORDER BY parcel_count DESC
    LIMIT 30
"""

data = safe_query(query)
if data and 'rows' in data:
    print(f"Top zoning districts by parcel count:")
    print(f"{'Long Code':20} {'Short Code':15} {'Parcels':>10}")
    print("-" * 50)
    for row in data['rows']:
        print(f"{row.get('long_code', 'N/A'):20} {row.get('short_code', 'N/A'):15} {row.get('parcel_count', 0):>10,}")
    print()

# Now try to link appeals to zoning districts
print("=" * 100)
print("LINKING APPEALS TO ZONING DISTRICTS")
print("=" * 100)
print()

print("3. Checking if we can do spatial join (ST_Within)...")
print("   This may take a while...")

# Try simple spatial join for a small sample
query = """
    SELECT
        a.appealnumber,
        a.address,
        z.long_code,
        z.short_code
    FROM appeals a
    LEFT JOIN zoning_basedistricts z
        ON ST_Within(a.the_geom, z.the_geom)
    WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND a.createddate >= '2023-01-01'
        AND a.createddate < '2024-01-01'
    LIMIT 10
"""

data = safe_query(query, timeout=90)
if data and 'rows' in data:
    print(f"✓ Successfully linked {len(data['rows'])} sample appeals to zoning")
    print()
    print("Sample joined data:")
    for row in data['rows'][:5]:
        print(f"  {row.get('address', 'N/A'):40} → {row.get('long_code', 'N/A')}")
    print()
else:
    print("✗ Spatial join failed or timed out")
    print()

print("=" * 100)
print("APPROACH FOR ZONING ANALYSIS")
print("=" * 100)
print()
print("We can analyze variance rates by zoning district in several ways:")
print()
print("1. **Spatial Join Approach:**")
print("   - Join appeals to zoning_basedistricts using ST_Within")
print("   - Calculate: appeals per district / parcels per district = variance rate")
print("   - Challenge: May be slow for 16,954 appeals")
print()
print("2. **Parcel ID Approach:**")
print("   - Appeals have parcel_id_num field")
print("   - Zoning has parcel identifiers")
print("   - Join on parcel ID if field names match")
print()
print("3. **Sample Analysis:**")
print("   - Analyze recent years (2022-2025) first")
print("   - Then expand to full dataset if successful")
print()
print("Let me try approach #2 (parcel ID join) as it will be faster...")
print()

# Check if parcel_id works
print("4. Testing parcel_id join...")
query = """
    SELECT
        a.appealnumber,
        a.address,
        a.parcel_id_num,
        z.long_code,
        z.short_code
    FROM appeals a
    INNER JOIN zoning_basedistricts z
        ON a.parcel_id_num = z.parcel_id
    WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND a.createddate >= '2023-01-01'
        AND a.createddate < '2024-01-01'
    LIMIT 10
"""

data = safe_query(query, timeout=90)
if data and 'rows' in data and len(data['rows']) > 0:
    print(f"✓ Parcel ID join works! Found {len(data['rows'])} matches")
    print()
    print("Sample joined data:")
    for row in data['rows'][:5]:
        print(f"  Parcel: {row.get('parcel_id_num', 'N/A'):15} Address: {row.get('address', 'N/A'):35} → {row.get('long_code', 'N/A')}")
    print()
    print("✓✓✓ SUCCESS! We can use parcel_id to join appeals to zoning districts ✓✓✓")
else:
    print("✗ Parcel ID join didn't work, will need to use spatial join")
    print()
