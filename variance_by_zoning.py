#!/usr/bin/env python3
"""
Analyze variance rates by zoning district

Approach: Since joins are timing out, we'll:
1. Get appeals year by year with addresses
2. Use a sample to establish methodology
3. Build up gradually
"""

import requests
import time
from collections import defaultdict, Counter

CARTO_API = "https://phl.carto.com/api/v2/sql"

def safe_query(query, timeout=60, retries=3):
    """Execute query with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(CARTO_API, params={'q': query}, timeout=timeout)
            data = response.json()
            if 'error' in data:
                print(f"  SQL Error: {data['error']}")
                return None
            return data
        except Exception as e:
            print(f"  Attempt {attempt + 1}/{retries} failed: {str(e)[:100]}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None

print("=" * 100)
print("VARIANCE RATE BY ZONING DISTRICT ANALYSIS")
print("=" * 100)
print()

# Step 1: Get the list of zoning districts
print("Step 1: Getting list of zoning districts...")
query = """
    SELECT
        long_code,
        zoninggroup,
        COUNT(*) as parcel_count
    FROM zoning_basedistricts
    WHERE long_code IS NOT NULL
    GROUP BY long_code, zoninggroup
    ORDER BY parcel_count DESC
"""

data = safe_query(query, timeout=90)
if not data or 'rows' not in data:
    print("✗ Failed to get zoning districts")
    exit(1)

zoning_districts = {}
for row in data['rows']:
    code = row['long_code']
    zoning_districts[code] = {
        'parcel_count': row['parcel_count'],
        'group': row['zoninggroup'],
        'appeals': 0
    }

print(f"✓ Found {len(zoning_districts)} unique zoning districts")
print(f"  Total parcels: {sum(d['parcel_count'] for d in zoning_districts.values()):,}")
print()

# Show top districts
print("Top 20 zoning districts by parcel count:")
print(f"{'Code':15} {'Group':25} {'Parcels':>10}")
print("-" * 55)
for row in data['rows'][:20]:
    print(f"{row['long_code']:15} {row.get('zoninggroup', 'N/A'):25} {row['parcel_count']:>10,}")
print()

# Step 2: Try to get appeals with zoning - start with just 2024
print("Step 2: Linking 2024 appeals to zoning (sample year)...")
print("  Trying direct parcel_id match...")

# First check what zoning table parcel fields are called
query = """
    SELECT *
    FROM zoning_basedistricts
    LIMIT 1
"""
data = safe_query(query)
if data and 'rows' in data:
    print("  Zoning table fields:", sorted([k for k in data['rows'][0].keys() if 'parcel' in k.lower() or 'id' in k.lower()]))
print()

# Try different join approaches for 2024 only
print("  Testing joins for 2024 appeals...")

# Approach A: Try with objectid
query_a = """
    SELECT
        COUNT(*) as count
    FROM appeals a
    INNER JOIN zoning_basedistricts z
        ON a.addressobjectid = z.objectid
    WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND a.createddate >= '2024-01-01'
        AND a.createddate < '2025-01-01'
"""

print("  Approach A: Join on addressobjectid = objectid...")
data = safe_query(query_a, timeout=45)
if data and 'rows' in data:
    count = data['rows'][0]['count']
    print(f"    ✓ Matched {count} appeals")
    if count > 0:
        JOIN_METHOD = "addressobjectid = objectid"
        print(f"    SUCCESS! Using: {JOIN_METHOD}")
    else:
        print("    ✗ No matches")
else:
    print("    ✗ Query failed")

# If that didn't work, try spatial within
if not data or data['rows'][0]['count'] == 0:
    print("  Approach B: Spatial join with ST_Within (slower)...")
    query_b = """
        SELECT
            COUNT(*) as count
        FROM appeals a
        INNER JOIN zoning_basedistricts z
            ON ST_Within(a.the_geom, z.the_geom)
        WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND a.createddate >= '2024-01-01'
            AND a.createddate < '2025-01-01'
    """

    data = safe_query(query_b, timeout=120)
    if data and 'rows' in data:
        count = data['rows'][0]['count']
        print(f"    ✓ Matched {count} appeals")
        if count > 0:
            JOIN_METHOD = "ST_Within(a.the_geom, z.the_geom)"
            print(f"    SUCCESS! Using: {JOIN_METHOD}")
        else:
            print("    ✗ No matches")
    else:
        print("    ✗ Query failed or timed out")
        JOIN_METHOD = None

print()

if not JOIN_METHOD:
    print("✗ Could not establish a working join method")
    print()
    print("ALTERNATIVE APPROACH:")
    print("We can analyze variance patterns by:")
    print("1. Manual geocoding of sample appeals")
    print("2. Using external GIS tools to spatially join")
    print("3. Focusing on variance types rather than zoning districts")
    print("4. Analyzing by council district (already in appeals table)")
    exit(1)

# Step 3: Get appeals by zoning district for 2024
print(f"Step 3: Getting 2024 appeals by zoning district using: {JOIN_METHOD}...")

if JOIN_METHOD == "addressobjectid = objectid":
    join_clause = "a.addressobjectid = z.objectid"
else:
    join_clause = "ST_Within(a.the_geom, z.the_geom)"

query = f"""
    SELECT
        z.long_code,
        z.zoninggroup,
        COUNT(*) as appeal_count
    FROM appeals a
    INNER JOIN zoning_basedistricts z
        ON {join_clause}
    WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND a.createddate >= '2024-01-01'
        AND a.createddate < '2025-01-01'
    GROUP BY z.long_code, z.zoninggroup
    ORDER BY appeal_count DESC
"""

data = safe_query(query, timeout=120)
if not data or 'rows' not in data:
    print("✗ Failed to get appeals by zoning")
    exit(1)

print(f"✓ Got appeals for {len(data['rows'])} zoning districts")
print()

# Calculate variance rates
print("=" * 100)
print("2024 VARIANCE RATE BY ZONING DISTRICT")
print("=" * 100)
print()

results = []
for row in data['rows']:
    code = row['long_code']
    appeal_count = row['appeal_count']

    if code in zoning_districts:
        parcel_count = zoning_districts[code]['parcel_count']
        variance_rate = (appeal_count / parcel_count) * 100 if parcel_count > 0 else 0

        results.append({
            'code': code,
            'group': row.get('zoninggroup', 'N/A'),
            'appeals': appeal_count,
            'parcels': parcel_count,
            'rate': variance_rate
        })

# Sort by variance rate
results.sort(key=lambda x: x['rate'], reverse=True)

print("Top 30 zoning districts by variance rate:")
print(f"{'Code':15} {'Group':25} {'Appeals':>8} {'Parcels':>8} {'Rate %':>8}")
print("-" * 75)
for r in results[:30]:
    print(f"{r['code']:15} {r['group']:25} {r['appeals']:>8,} {r['parcels']:>8,} {r['rate']:>7.2f}%")

print()
print()

# Group by zoning type
print("=" * 100)
print("VARIANCE RATE BY ZONING GROUP")
print("=" * 100)
print()

group_stats = defaultdict(lambda: {'appeals': 0, 'parcels': 0})
for r in results:
    group = r['group']
    group_stats[group]['appeals'] += r['appeals']
    group_stats[group]['parcels'] += r['parcels']

group_results = []
for group, stats in group_stats.items():
    rate = (stats['appeals'] / stats['parcels']) * 100 if stats['parcels'] > 0 else 0
    group_results.append({
        'group': group,
        'appeals': stats['appeals'],
        'parcels': stats['parcels'],
        'rate': rate
    })

group_results.sort(key=lambda x: x['rate'], reverse=True)

print(f"{'Zoning Group':30} {'Appeals':>8} {'Parcels':>10} {'Rate %':>8}")
print("-" * 65)
for g in group_results:
    print(f"{g['group']:30} {g['appeals']:>8,} {g['parcels']:>10,} {g['rate']:>7.2f}%")

print()
print()
print("=" * 100)
print("KEY INSIGHTS")
print("=" * 100)
print()
print("This shows which zoning districts generate variances at the highest rates.")
print("Next steps:")
print("  1. Expand analysis to full 2013-2025 period")
print("  2. Break down variance types by zoning district")
print("  3. Identify which districts would benefit most from specific reforms")
