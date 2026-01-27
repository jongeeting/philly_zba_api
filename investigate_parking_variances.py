#!/usr/bin/env python3
"""
Investigate parking variances in districts WITHOUT parking minimums

RSA-5, RM-1, CMX-2, CMX-2.5 have NO parking minimums, yet they show
parking variance appeals. What are these variances actually about?
"""

import requests
import time

CARTO_API = "https://phl.carto.com/api/v2/sql"

def safe_query(query, timeout=90, retries=3):
    """Execute query with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(CARTO_API, params={'q': query}, timeout=timeout)
            data = response.json()
            if 'error' in data:
                print(f"  Error: {data['error']}")
                return None
            return data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  Failed: {str(e)[:60]}")
    return None

print("=" * 100)
print("PARKING VARIANCES IN NO-MINIMUM DISTRICTS")
print("=" * 100)
print()
print("Investigating: RSA-5, RM-1, CMX-2, CMX-2.5")
print("These districts have NO parking minimums, yet show parking variance appeals")
print()

districts_to_check = ['RSA-5', 'RM-1', 'CMX-2', 'CMX-2.5']

for district in districts_to_check:
    print("=" * 100)
    print(f"DISTRICT: {district}")
    print("=" * 100)
    print()

    # Get sample parking-related appeals from this district
    query = f"""
        SELECT
            a.appealgrounds,
            a.createddate,
            a.address
        FROM appeals a
        INNER JOIN zoning_basedistricts z
            ON ST_Within(a.the_geom, z.the_geom)
        WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND a.createddate >= '2022-01-01'
            AND a.createddate < '2026-01-01'
            AND z.long_code = '{district}'
            AND a.appealgrounds ILIKE '%parking%'
        LIMIT 10
    """

    print(f"Fetching recent parking appeals in {district}...")
    data = safe_query(query, timeout=120)

    if not data or 'rows' not in data or len(data['rows']) == 0:
        print(f"  No parking appeals found (or query failed)")
        print()
        continue

    appeals = data['rows']
    print(f"✓ Found {len(appeals)} sample parking appeals")
    print()

    # Analyze the appeal text to see what they're asking for
    for i, appeal in enumerate(appeals, 1):
        text = appeal.get('appealgrounds', '')
        address = appeal.get('address', 'N/A')
        date = appeal.get('createddate', '')[:10]

        print(f"{i}. {address} ({date})")
        print(f"   Appeal text: {text[:400]}")

        # Try to identify what type of parking variance
        text_upper = text.upper()

        if 'PROVIDE' in text_upper and 'PARKING' in text_upper:
            if 'LESS' in text_upper or 'FEWER' in text_upper or 'REDUCE' in text_upper:
                print(f"   → Appears to be: REDUCING parking (but there's no minimum?)")
            elif 'MORE' in text_upper or 'ADDITIONAL' in text_upper or 'EXCESS' in text_upper:
                print(f"   → Appears to be: ADDING more parking (exceeding maximum?)")
            else:
                print(f"   → Appears to be: PROVIDING parking (unclear if more or less)")

        if 'LOCATION' in text_upper or 'LOCATION OF' in text_upper:
            print(f"   → Appears to be: PARKING LOCATION requirement")

        if 'DIMENSIONS' in text_upper or 'SIZE' in text_upper:
            print(f"   → Appears to be: PARKING SPACE DIMENSIONS")

        if 'ACCESS' in text_upper or 'DRIVEWAY' in text_upper:
            print(f"   → Appears to be: PARKING ACCESS/DRIVEWAY requirement")

        if 'SURFACE' in text_upper or 'PAVED' in text_upper or 'PAVING' in text_upper:
            print(f"   → Appears to be: PARKING SURFACE MATERIAL requirement")

        print()

print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()
print("Parking variances in no-minimum districts likely involve:")
print()
print("1. **Parking MAXIMUMS** - Districts may have maximums, not just minimums")
print("   (e.g., RSA-5 might limit parking to prevent garage conversions)")
print()
print("2. **Parking LOCATION requirements** - Where parking must be located")
print("   (e.g., rear yard only, not in front setback)")
print()
print("3. **Parking DESIGN standards** - Dimensions, surfacing, access")
print("   (e.g., must be paved, must have certain dimensions, driveway width)")
print()
print("4. **Accessory structure rules** - Garages counting against lot coverage")
print("   (e.g., detached garage exceeds accessory structure allowance)")
print()
print("5. **Historic or contextual requirements** - In certain overlays")
print()
print("This explains why 'eliminating parking minimums' alone won't solve all parking variances.")
print("Need to also address parking maximums, location rules, and design standards.")
