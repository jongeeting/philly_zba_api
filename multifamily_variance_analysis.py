#!/usr/bin/env python3
"""
Multifamily Housing Variance Analysis

Identifies what's blocking multifamily (2+ unit) housing development and
which reforms would have the biggest impact.
"""

import requests
import re
from collections import defaultdict, Counter

CARTO_API = "https://phl.carto.com/api/v2/sql"

def safe_query(query, timeout=120):
    """Execute query with retries."""
    for attempt in range(3):
        try:
            response = requests.get(CARTO_API, params={'q': query}, timeout=timeout)
            data = response.json()
            if 'error' in data:
                print(f"  Error: {data['error']}")
                return None
            return data
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt + 1}...")
            else:
                print(f"  Failed: {str(e)[:60]}")
    return None

print("=" * 100)
print("MULTIFAMILY HOUSING VARIANCE ANALYSIS")
print("=" * 100)
print()

# Approach 1: Find appeals explicitly mentioning dwelling units
print("Phase 1: Identifying multifamily projects...")
print()

query = """
    SELECT
        appealgrounds,
        EXTRACT(YEAR FROM createddate) as year
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND (
            appealgrounds ~* '\\d+\\s*dwelling'
            OR appealgrounds ~* '\\d+\\s*family'
            OR appealgrounds ~* '\\d+\\s*unit'
            OR appealgrounds ~* 'duplex|triplex|fourplex|sixplex'
            OR appealgrounds ILIKE '%multi%family%'
            OR appealgrounds ILIKE '%apartment%'
        )
"""

print("Fetching appeals with multifamily keywords...")
data = safe_query(query, timeout=180)

if not data or 'rows' not in data:
    print("✗ Failed to get data")
    exit(1)

appeals = data['rows']
print(f"✓ Found {len(appeals):,} appeals with multifamily indicators")
print()

# Extract unit counts and analyze variance types
unit_counts = []
variance_types = defaultdict(int)
by_year = defaultdict(int)
unit_distribution = Counter()

for appeal in appeals:
    text = appeal.get('appealgrounds', '')
    year = int(appeal['year'])

    if not text:
        continue

    text_upper = text.upper()
    by_year[year] += 1

    # Extract unit count
    patterns = [
        r'(\d+)\s*(?:DWELLING|FAMILY)',
        r'(\d+)\s*UNIT',
        r'(\d+)\s*D\.?U\.?',
        r'(\d+)\s*F\.?A\.?M\.',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 1 <= units <= 100:
                unit_counts.append(units)
                unit_distribution[units] += 1
                break

    # Detect variance types
    if 'ROOF DECK' in text_upper or 'ROOFDECK' in text_upper:
        variance_types['roof_deck'] += 1

    if 'PARKING' in text_upper:
        variance_types['parking'] += 1

    if 'HEIGHT' in text_upper:
        variance_types['height'] += 1

    if 'SETBACK' in text_upper or 'SET BACK' in text_upper:
        variance_types['setback'] += 1

    if 'LOT COVERAGE' in text_upper or 'BUILDING COVERAGE' in text_upper:
        variance_types['lot_coverage'] += 1

    if any(kw in text_upper for kw in ['COMMERCIAL', 'RETAIL', 'OFFICE', 'STORE']):
        variance_types['commercial'] += 1

print("=" * 100)
print("MULTIFAMILY VARIANCE DRIVERS")
print("=" * 100)
print()

total = len(appeals)

print(f"Total multifamily-related appeals (2013-2025): {total:,}")
print(f"Average per year: {total/13:.1f}")
print()

# Sort variance types
sorted_types = sorted(variance_types.items(), key=lambda x: x[1], reverse=True)

print("Top variance types for multifamily projects:")
print(f"{'Variance Type':25} {'Count':>8} {'% of Multifamily':>18} {'Per Year':>10}")
print("-" * 75)
for var_type, count in sorted_types:
    pct = (count / total) * 100
    per_year = count / 13
    print(f"{var_type.replace('_', ' ').title():25} {count:>8,} {pct:>17.1f}% {per_year:>10.1f}")

print()

# Unit count distribution
print("=" * 100)
print("DWELLING UNIT DISTRIBUTION")
print("=" * 100)
print()

print(f"Total appeals with explicit unit counts: {len(unit_counts):,}")
print()

# Group by unit ranges
ranges = {
    '2 units (duplex)': [2],
    '3 units (triplex)': [3],
    '4 units (fourplex)': [4],
    '5 units': [5],
    '6 units (sixplex)': [6],
    '7-9 units': list(range(7, 10)),
    '10-19 units': list(range(10, 20)),
    '20+ units': list(range(20, 101)),
}

print(f"{'Unit Range':20} {'Appeals':>8} {'% of Total':>12} {'Cumulative %':>14}")
print("-" * 60)

cumulative = 0
for range_name, unit_list in ranges.items():
    count = sum(unit_distribution[u] for u in unit_list)
    cumulative += count
    pct = (count / len(unit_counts)) * 100
    cum_pct = (cumulative / len(unit_counts)) * 100
    print(f"{range_name:20} {count:>8,} {pct:>11.1f}% {cum_pct:>13.1f}%")

print()
print(f"**Key insight:** {sum(unit_distribution[u] for u in range(2, 5)):,} appeals are for 2-4 unit buildings")
print(f"That's {sum(unit_distribution[u] for u in range(2, 5))/len(unit_counts)*100:.1f}% of all multifamily variance requests")
print()

# Multifamily appeals by zoning district
print("=" * 100)
print("MULTIFAMILY APPEALS BY ZONING DISTRICT")
print("=" * 100)
print()

query = """
    SELECT
        z.long_code,
        z.zoninggroup,
        COUNT(*) as appeal_count
    FROM appeals a
    INNER JOIN zoning_basedistricts z
        ON ST_Within(a.the_geom, z.the_geom)
    WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND a.createddate >= '2013-01-01'
        AND a.createddate < '2026-01-01'
        AND (
            a.appealgrounds ~* '\\d+\\s*dwelling'
            OR a.appealgrounds ~* '\\d+\\s*family'
            OR a.appealgrounds ~* '\\d+\\s*unit'
            OR a.appealgrounds ~* 'duplex|triplex|fourplex|sixplex'
            OR a.appealgrounds ILIKE '%multi%family%'
            OR a.appealgrounds ILIKE '%apartment%'
        )
    GROUP BY z.long_code, z.zoninggroup
    ORDER BY appeal_count DESC
"""

print("Linking multifamily appeals to zoning districts...")
data = safe_query(query, timeout=180)

if data and 'rows' in data:
    districts = data['rows']
    print(f"✓ Found {len(districts)} zoning districts with multifamily appeals")
    print()

    print(f"{'Rank':>4} {'District':15} {'Group':35} {'Appeals':>8} {'Per Year':>9}")
    print("-" * 80)

    for rank, row in enumerate(districts[:20], 1):
        code = row['long_code']
        group = row['zoninggroup']
        count = row['appeal_count']
        per_year = count / 13
        print(f"{rank:>4} {code:15} {group:35} {count:>8,} {per_year:>9.1f}")

    print()

# Year-by-year trend
print("=" * 100)
print("MULTIFAMILY APPEALS OVER TIME")
print("=" * 100)
print()

print(f"{'Year':>6}  {'Appeals':>8}")
print("-" * 18)
for year in range(2013, 2026):
    count = by_year.get(year, 0)
    print(f"{year:>6}  {count:>8,}")

early = sum(by_year.get(y, 0) for y in range(2013, 2019)) / 6
late = sum(by_year.get(y, 0) for y in range(2019, 2026)) / 7
trend = ((late - early) / early * 100) if early > 0 else 0

print()
print(f"Trend: {early:.1f}/year (2013-2018) → {late:.1f}/year (2019-2025)")
print(f"Change: {trend:+.1f}%")
print()

# Reform impact
print("=" * 100)
print("REFORM IMPACT ON MULTIFAMILY HOUSING")
print("=" * 100)
print()

print("Current barriers to multifamily housing:")
print()

# Calculate what percentage each reform would help
total_mf = len(appeals)
roof_deck_impact = variance_types.get('roof_deck', 0)
parking_impact = variance_types.get('parking', 0)
height_impact = variance_types.get('height', 0)
setback_impact = variance_types.get('setback', 0)

print(f"1. Roof deck restrictions: {roof_deck_impact:,} appeals ({roof_deck_impact/total_mf*100:.1f}%)")
print(f"2. Parking minimums: {parking_impact:,} appeals ({parking_impact/total_mf*100:.1f}%)")
print(f"3. Height limits: {height_impact:,} appeals ({height_impact/total_mf*100:.1f}%)")
print(f"4. Setback requirements: {setback_impact:,} appeals ({setback_impact/total_mf*100:.1f}%)")
print()

print("Reform scenarios:")
print()

# Scenario 1: Allow duplexes (2 units)
duplex_appeals = unit_distribution[2]
print(f"Scenario 1: Allow duplexes by-right")
print(f"  Appeals eliminated: {duplex_appeals:,} ({duplex_appeals/total_mf*100:.1f}% of multifamily)")
print(f"  Per year: {duplex_appeals/13:.1f}")
print()

# Scenario 2: Allow fourplexes (2-4 units)
fourplex_appeals = sum(unit_distribution[u] for u in range(2, 5))
print(f"Scenario 2: Allow fourplexes by-right (2-4 units)")
print(f"  Appeals eliminated: {fourplex_appeals:,} ({fourplex_appeals/total_mf*100:.1f}% of multifamily)")
print(f"  Per year: {fourplex_appeals/13:.1f}")
print()

# Scenario 3: Allow sixplexes (2-6 units)
sixplex_appeals = sum(unit_distribution[u] for u in range(2, 7))
print(f"Scenario 3: Allow sixplexes by-right (2-6 units)")
print(f"  Appeals eliminated: {sixplex_appeals:,} ({sixplex_appeals/total_mf*100:.1f}% of multifamily)")
print(f"  Per year: {sixplex_appeals/13:.1f}")
print()

# Combined reforms
combined_impact = min(total_mf, fourplex_appeals + parking_impact + height_impact + roof_deck_impact)
print(f"Scenario 4: Fourplex + No parking + Height + Roof decks")
print(f"  Estimated appeals eliminated: ~{combined_impact/13:.0f}/year")
print(f"  (Conservative estimate accounting for overlap)")
print()

print("=" * 100)
print("KEY FINDINGS FOR MULTIFAMILY HOUSING")
print("=" * 100)
print()
print(f"1. {total:,} variance appeals involve multifamily housing ({total/13:.0f}/year)")
print(f"2. Small multifamily (2-4 units) represents {fourplex_appeals/len(unit_counts)*100:.1f}% of unit-specific appeals")
print(f"3. Allowing fourplexes by-right would eliminate ~{fourplex_appeals/13:.0f} multifamily variance appeals per year")
print(f"4. Top multifamily barriers: {sorted_types[0][0].replace('_', ' ')} ({sorted_types[0][1]} appeals), {sorted_types[1][0].replace('_', ' ')} ({sorted_types[1][1]} appeals)")
print(f"5. RSA-5 (rowhouse district) has the most multifamily appeals (if it ranks #1 above)")
print()
print("ANALYSIS COMPLETE")
