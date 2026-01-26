#!/usr/bin/env python3
"""
Fast zoning district analysis - gets counts first, then details

Two-phase approach:
1. Get appeal counts by district (fast aggregation)
2. Sample appeals to analyze variance types
"""

import requests
import time
import re
from collections import defaultdict

CARTO_API = "https://phl.carto.com/api/v2/sql"

def safe_query(query, timeout=120, retries=3):
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
            print(f"  Attempt {attempt + 1} failed: {str(e)[:60]}...")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None

print("=" * 100)
print("FAST ZONING DISTRICT ANALYSIS (2013-2025)")
print("=" * 100)
print()

# Phase 1: Get appeal counts by district
print("Phase 1: Getting appeal counts by district...")
print()

query = """
    SELECT
        z.long_code,
        z.zoninggroup,
        EXTRACT(YEAR FROM a.createddate) as year,
        COUNT(*) as appeal_count
    FROM appeals a
    INNER JOIN zoning_basedistricts z
        ON ST_Within(a.the_geom, z.the_geom)
    WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND a.createddate >= '2013-01-01'
        AND a.createddate < '2026-01-01'
    GROUP BY z.long_code, z.zoninggroup, year
    ORDER BY year, appeal_count DESC
"""

print("Executing spatial join query (this may take a few minutes)...")
data = safe_query(query, timeout=300)

if not data or 'rows' not in data:
    print("✗ Failed to get data")
    exit(1)

print(f"✓ Got {len(data['rows'])} year-district records")
print()

# Aggregate results
district_stats = defaultdict(lambda: {
    'total': 0,
    'group': None,
    'by_year': {}
})

for row in data['rows']:
    code = row['long_code']
    year = int(row['year'])
    count = row['appeal_count']

    district_stats[code]['total'] += count
    district_stats[code]['group'] = row['zoninggroup']
    district_stats[code]['by_year'][year] = count

# Sort by total
sorted_districts = sorted(district_stats.items(), key=lambda x: x[1]['total'], reverse=True)

# Print results
print("=" * 100)
print("ZONING DISTRICTS RANKED BY APPEAL VOLUME (2013-2025)")
print("=" * 100)
print()

print(f"{'Rank':>4} {'Code':15} {'Group':35} {'Total':>8} {'Per Year':>9}")
print("-" * 100)

total_all = sum(stats['total'] for _, stats in sorted_districts)

for rank, (code, stats) in enumerate(sorted_districts[:30], 1):
    per_year = stats['total'] / 13
    pct = (stats['total'] / total_all) * 100
    print(f"{rank:>4} {code:15} {stats['group']:35} {stats['total']:>8,} {per_year:>9.1f} ({pct:4.1f}%)")

print()
print(f"Total appeals matched: {total_all:,}")
print()

# Group summary
print("=" * 100)
print("BY ZONING GROUP")
print("=" * 100)
print()

group_totals = defaultdict(int)
for code, stats in district_stats.items():
    group_totals[stats['group']] += stats['total']

sorted_groups = sorted(group_totals.items(), key=lambda x: x[1], reverse=True)

print(f"{'Group':40} {'Appeals':>8} {'Per Year':>9} {'% of Total':>10}")
print("-" * 75)
for group, total in sorted_groups:
    per_year = total / 13
    pct = (total / total_all) * 100
    print(f"{group:40} {total:>8,} {per_year:>9.1f} {pct:>9.1f}%")

print()

# Top 5 deep dive - year by year
print("=" * 100)
print("TOP 5 DISTRICTS - YEAR BY YEAR TRENDS")
print("=" * 100)
print()

for rank, (code, stats) in enumerate(sorted_districts[:5], 1):
    print(f"{rank}. {code} ({stats['group']})")
    print(f"   Total: {stats['total']:,} appeals ({stats['total']/13:.1f}/year)")
    print()
    print(f"   {'Year':>6}  {'Appeals':>8}")
    print(f"   {'-'*18}")

    for year in range(2013, 2026):
        count = stats['by_year'].get(year, 0)
        print(f"   {year:>6}  {count:>8,}")

    # Calculate trend
    early = sum(stats['by_year'].get(y, 0) for y in range(2013, 2019)) / 6
    late = sum(stats['by_year'].get(y, 0) for y in range(2019, 2026)) / 7
    trend = ((late - early) / early * 100) if early > 0 else 0

    print()
    print(f"   Trend: {early:.1f}/year (2013-2018) → {late:.1f}/year (2019-2025)")
    print(f"   Change: {trend:+.1f}%")
    print()

# Phase 2: Sample variance types for top districts
print("=" * 100)
print("Phase 2: Analyzing variance types for top districts")
print("=" * 100)
print()

print("Sampling recent appeals to identify variance patterns...")
print()

for rank, (code, stats) in enumerate(sorted_districts[:5], 1):
    print(f"{rank}. Analyzing {code}...")

    query = f"""
        SELECT
            a.appealgrounds
        FROM appeals a
        INNER JOIN zoning_basedistricts z
            ON ST_Within(a.the_geom, z.the_geom)
        WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND a.createddate >= '2022-01-01'
            AND a.createddate < '2026-01-01'
            AND z.long_code = '{code}'
    """

    data = safe_query(query, timeout=120)
    if not data or 'rows' not in data:
        print(f"   ✗ Failed to get sample")
        continue

    appeals = data['rows']
    print(f"   Sample: {len(appeals)} appeals (2022-2025)")

    # Count variance types
    roof_deck = sum(1 for a in appeals if a.get('appealgrounds') and 'roof deck' in a['appealgrounds'].lower())
    parking = sum(1 for a in appeals if a.get('appealgrounds') and 'parking' in a['appealgrounds'].lower())
    height = sum(1 for a in appeals if a.get('appealgrounds') and 'height' in a['appealgrounds'].lower())
    commercial = sum(1 for a in appeals if a.get('appealgrounds') and any(kw in a['appealgrounds'].lower() for kw in ['commercial', 'retail', 'office', 'store']))
    dwelling = sum(1 for a in appeals if a.get('appealgrounds') and re.search(r'\d+\s*(?:dwelling|family|unit)', a['appealgrounds'], re.I))

    total_sample = len(appeals)
    print(f"   Variance types:")
    print(f"     Roof decks: {roof_deck} ({roof_deck/total_sample*100:.1f}%)")
    print(f"     Parking: {parking} ({parking/total_sample*100:.1f}%)")
    print(f"     Height: {height} ({height/total_sample*100:.1f}%)")
    print(f"     Commercial: {commercial} ({commercial/total_sample*100:.1f}%)")
    print(f"     Dwelling units: {dwelling} ({dwelling/total_sample*100:.1f}%)")
    print()

print("=" * 100)
print("KEY FINDINGS")
print("=" * 100)
print()

top5_total = sum(stats['total'] for _, stats in sorted_districts[:5])
print(f"1. Top 5 districts account for {top5_total:,} appeals ({top5_total/total_all*100:.1f}% of total)")
print()

top1_code, top1_stats = sorted_districts[0]
print(f"2. {top1_code} alone accounts for {top1_stats['total']:,} appeals ({top1_stats['total']/total_all*100:.1f}% of total)")
print()

residential_total = sum(total for group, total in group_totals.items() if 'Residential' in group)
print(f"3. Residential zones account for {residential_total:,} appeals ({residential_total/total_all*100:.1f}% of total)")
print()

print("ANALYSIS COMPLETE")
