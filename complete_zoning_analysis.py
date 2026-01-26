#!/usr/bin/env python3
"""
Complete zoning district analysis for 2013-2025

Links all appeals to zoning districts and breaks down by variance type.
"""

import requests
import time
import re
from collections import defaultdict, Counter

CARTO_API = "https://phl.carto.com/api/v2/sql"

def safe_query(query, timeout=120, retries=3):
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
            print(f"  Attempt {attempt + 1}/{retries} failed: {str(e)[:80]}...")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None

print("=" * 100)
print("COMPLETE ZONING DISTRICT ANALYSIS (2013-2025)")
print("=" * 100)
print()

# Get appeals by zoning district for each year
print("Fetching appeals by zoning district for 2013-2025...")
print("(This will take several minutes as we process 13 years of data)")
print()

all_results = []

for year in range(2013, 2026):
    print(f"Processing {year}...", end=" ", flush=True)

    query = f"""
        SELECT
            z.long_code,
            z.zoninggroup,
            a.appealgrounds,
            COUNT(*) as appeal_count
        FROM appeals a
        INNER JOIN zoning_basedistricts z
            ON ST_Within(a.the_geom, z.the_geom)
        WHERE a.applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND a.createddate >= '{year}-01-01'
            AND a.createddate < '{year + 1}-01-01'
        GROUP BY z.long_code, z.zoninggroup, a.appealgrounds
    """

    data = safe_query(query, timeout=180)
    if data and 'rows' in data:
        for row in data['rows']:
            row['year'] = year
            all_results.append(row)
        print(f"✓ {len([r for r in all_results if r['year'] == year])} records")
    else:
        print(f"✗ Failed")

print()
print(f"Total records collected: {len(all_results):,}")
print()

# Aggregate by district across all years
district_stats = defaultdict(lambda: {
    'total_appeals': 0,
    'group': None,
    'roof_deck': 0,
    'parking': 0,
    'height': 0,
    'commercial': 0,
    'dwelling_units': 0,
    'by_year': defaultdict(int)
})

print("Analyzing variance types by district...")
for row in all_results:
    code = row['long_code']
    year = row['year']
    text = row.get('appealgrounds', '')
    count = row['appeal_count']

    district_stats[code]['total_appeals'] += count
    district_stats[code]['group'] = row.get('zoninggroup', 'N/A')
    district_stats[code]['by_year'][year] += count

    if not text:
        continue

    text_upper = text.upper()

    # Detect variance types
    if 'ROOF DECK' in text_upper or 'ROOFDECK' in text_upper:
        district_stats[code]['roof_deck'] += count

    if 'PARKING' in text_upper:
        district_stats[code]['parking'] += count

    if 'HEIGHT' in text_upper:
        district_stats[code]['height'] += count

    if any(kw in text_upper for kw in ['COMMERCIAL', 'RETAIL', 'OFFICE', 'STORE', 'SHOP', 'RESTAURANT', 'MIXED USE']):
        district_stats[code]['commercial'] += count

    if re.search(r'\d+\s*(?:DWELLING|FAMILY|UNIT)', text_upper):
        district_stats[code]['dwelling_units'] += count

print(f"✓ Analyzed {len(district_stats)} districts")
print()

# Sort by total appeals
sorted_districts = sorted(district_stats.items(), key=lambda x: x[1]['total_appeals'], reverse=True)

# Print overall results
print("=" * 100)
print("APPEALS BY ZONING DISTRICT (2013-2025)")
print("=" * 100)
print()

print(f"{'Rank':>4} {'Code':15} {'Group':30} {'Total':>8} {'Per Year':>9}")
print("-" * 90)
for rank, (code, stats) in enumerate(sorted_districts[:30], 1):
    per_year = stats['total_appeals'] / 13
    print(f"{rank:>4} {code:15} {stats['group']:30} {stats['total_appeals']:>8,} {per_year:>9.1f}")

print()

# Top 10 with variance type breakdown
print("=" * 100)
print("TOP 10 DISTRICTS - VARIANCE TYPE BREAKDOWN")
print("=" * 100)
print()

for rank, (code, stats) in enumerate(sorted_districts[:10], 1):
    print(f"{rank}. {code} ({stats['group']})")
    print(f"   Total appeals: {stats['total_appeals']:,} ({stats['total_appeals']/13:.1f}/year)")
    print(f"   Variance types:")
    print(f"     - Roof decks: {stats['roof_deck']:,} ({stats['roof_deck']/stats['total_appeals']*100:.1f}%)")
    print(f"     - Parking: {stats['parking']:,} ({stats['parking']/stats['total_appeals']*100:.1f}%)")
    print(f"     - Height: {stats['height']:,} ({stats['height']/stats['total_appeals']*100:.1f}%)")
    print(f"     - Commercial: {stats['commercial']:,} ({stats['commercial']/stats['total_appeals']*100:.1f}%)")
    print(f"     - Dwelling units: {stats['dwelling_units']:,} ({stats['dwelling_units']/stats['total_appeals']*100:.1f}%)")
    print()

# Group by zoning type
print("=" * 100)
print("APPEALS BY ZONING GROUP (2013-2025)")
print("=" * 100)
print()

group_stats = defaultdict(lambda: {
    'total_appeals': 0,
    'roof_deck': 0,
    'parking': 0,
    'height': 0,
    'commercial': 0,
    'dwelling_units': 0
})

for code, stats in district_stats.items():
    group = stats['group']
    group_stats[group]['total_appeals'] += stats['total_appeals']
    group_stats[group]['roof_deck'] += stats['roof_deck']
    group_stats[group]['parking'] += stats['parking']
    group_stats[group]['height'] += stats['height']
    group_stats[group]['commercial'] += stats['commercial']
    group_stats[group]['dwelling_units'] += stats['dwelling_units']

sorted_groups = sorted(group_stats.items(), key=lambda x: x[1]['total_appeals'], reverse=True)

for group, stats in sorted_groups:
    total = stats['total_appeals']
    print(f"{group}")
    print(f"  Total: {total:,} ({total/13:.1f}/year)")
    print(f"  Roof decks: {stats['roof_deck']:,} ({stats['roof_deck']/total*100:.1f}%)")
    print(f"  Parking: {stats['parking']:,} ({stats['parking']/total*100:.1f}%)")
    print(f"  Height: {stats['height']:,} ({stats['height']/total*100:.1f}%)")
    print(f"  Commercial: {stats['commercial']:,} ({stats['commercial']/total*100:.1f}%)")
    print(f"  Dwelling units: {stats['dwelling_units']:,} ({stats['dwelling_units']/total*100:.1f}%)")
    print()

# RSA-5 deep dive
print("=" * 100)
print("RSA-5 DEEP DIVE (THE BIGGEST PROBLEM)")
print("=" * 100)
print()

rsa5 = district_stats.get('RSA-5', {})
if rsa5:
    print(f"RSA-5 (Residential Single-Family Attached - Rowhouses)")
    print()
    print(f"Total appeals (2013-2025): {rsa5['total_appeals']:,}")
    print(f"Average per year: {rsa5['total_appeals']/13:.1f}")
    print()
    print("Variance type breakdown:")
    print(f"  Roof decks: {rsa5['roof_deck']:,} ({rsa5['roof_deck']/rsa5['total_appeals']*100:.1f}%)")
    print(f"  Parking: {rsa5['parking']:,} ({rsa5['parking']/rsa5['total_appeals']*100:.1f}%)")
    print(f"  Height: {rsa5['height']:,} ({rsa5['height']/rsa5['total_appeals']*100:.1f}%)")
    print(f"  Commercial: {rsa5['commercial']:,} ({rsa5['commercial']/rsa5['total_appeals']*100:.1f}%)")
    print(f"  Dwelling units: {rsa5['dwelling_units']:,} ({rsa5['dwelling_units']/rsa5['total_appeals']*100:.1f}%)")
    print()

    print("Year-by-year trend:")
    for year in range(2013, 2026):
        count = rsa5['by_year'][year]
        print(f"  {year}: {count:,}")
    print()

    # Calculate reform impact for RSA-5
    total_rsa5 = rsa5['total_appeals']
    potentially_eliminated = rsa5['roof_deck'] + rsa5['parking'] + rsa5['height']

    print("Estimated reform impact on RSA-5:")
    print(f"  Current appeals: {total_rsa5:,} ({total_rsa5/13:.1f}/year)")
    print(f"  Potentially eliminated by Tier 2 reforms: {potentially_eliminated:,} ({potentially_eliminated/total_rsa5*100:.1f}%)")
    print(f"  Remaining appeals: {total_rsa5 - potentially_eliminated:,} ({(total_rsa5-potentially_eliminated)/13:.1f}/year)")
    print(f"  Reduction: {potentially_eliminated/13:.1f} appeals/year")

print()
print("=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
print()
print(f"Successfully analyzed {len(all_results):,} appeal records across {len(district_stats)} zoning districts")
