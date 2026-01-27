#!/usr/bin/env python3
"""
Parking Minimums as a Barrier to Multifamily Housing

Specific question: How many multifamily projects seek variances because
parking minimums require MORE parking than developers want to build?

Analysis approach:
1. Identify multifamily projects (with dwelling unit counts)
2. Among those, identify which mention parking
3. Calculate parking ratio (spaces/unit) to infer if seeking below-minimum
4. Compare to total multifamily permits
"""

import requests
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
                print(f"  Error: {data['error']}")
                return None
            return data
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry...")
            else:
                print(f"  Failed: {str(e)[:60]}")
    return None

print("=" * 100)
print("PARKING MINIMUMS AS A BARRIER TO MULTIFAMILY HOUSING")
print("=" * 100)
print()

# Step 1: Get multifamily appeals with both unit counts AND parking mentions
print("Step 1: Identifying multifamily appeals that mention parking...")
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
            appealgrounds ~* '\\d+\\s*(?:dwelling|family|unit)'
            OR appealgrounds ~* 'duplex|triplex|fourplex|sixplex'
            OR appealgrounds ILIKE '%multi%family%'
        )
        AND appealgrounds ILIKE '%parking%'
"""

data = safe_query(query, timeout=180)

if not data or 'rows' not in data:
    print("✗ Failed to get data")
    exit(1)

appeals = data['rows']
print(f"✓ Found {len(appeals):,} multifamily appeals mentioning parking")
print()

# Step 2: Extract unit counts and parking counts
print("Step 2: Extracting unit counts and parking ratios...")
print()

projects_with_data = []
by_year = defaultdict(int)

for appeal in appeals:
    text = appeal.get('appealgrounds', '')
    year = int(appeal['year'])

    if not text:
        continue

    text_upper = text.upper()
    by_year[year] += 1

    # Extract dwelling units
    unit_patterns = [
        r'(\d+)\s*(?:DWELLING\s*UNIT|FAMILY|D\.?U\.?)',
        r'(\d+)\s*UNIT',
    ]

    units = None
    for pattern in unit_patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 1 <= units <= 100:
                break
            else:
                units = None

    # Extract parking spaces
    parking_patterns = [
        r'(\d+)\s*(?:PARKING\s*SPACE|VEHICLE\s*SPACE|OFF[-\s]?STREET\s*(?:PARKING\s*)?SPACE)',
        r'(\d+)\s*ACCESSORY\s*(?:PARKING|OFF[-\s]?STREET)',
    ]

    parking_spaces = None
    for pattern in parking_patterns:
        match = re.search(pattern, text_upper)
        if match:
            parking_spaces = int(match.group(1))
            if 0 <= parking_spaces <= 200:
                break
            else:
                parking_spaces = None

    # If we have both units and parking, calculate ratio
    if units and parking_spaces is not None:
        ratio = parking_spaces / units
        projects_with_data.append({
            'year': year,
            'units': units,
            'parking': parking_spaces,
            'ratio': ratio,
            'text': text[:200]
        })

print(f"✓ Extracted data for {len(projects_with_data):,} projects with both unit and parking counts")
print()

# Step 3: Analyze parking ratios
print("=" * 100)
print("PARKING RATIO ANALYSIS")
print("=" * 100)
print()

ratios = [p['ratio'] for p in projects_with_data]

print(f"Total multifamily projects with parking data: {len(projects_with_data):,}")
print(f"Average parking ratio: {sum(ratios)/len(ratios):.2f} spaces/unit")
print()

# Categorize by ratio
ratio_ranges = {
    '0 spaces (no parking)': (0, 0),
    '0.01-0.49 (less than half)': (0.01, 0.49),
    '0.5 (half)': (0.5, 0.5),
    '0.51-0.99 (more than half, less than 1)': (0.51, 0.99),
    '1.0 (one per unit)': (1.0, 1.0),
    '1.01-1.49': (1.01, 1.49),
    '1.5 (1.5 per unit)': (1.5, 1.5),
    '1.51-1.99': (1.51, 1.99),
    '2.0+ (2 or more per unit)': (2.0, 100),
}

print(f"{'Parking Ratio Range':45} {'Projects':>10} {'% of Total':>12}")
print("-" * 75)

for range_name, (low, high) in ratio_ranges.items():
    count = sum(1 for p in projects_with_data if low <= p['ratio'] <= high)
    pct = (count / len(projects_with_data)) * 100
    print(f"{range_name:45} {count:>10,} {pct:>11.1f}%")

print()

# Identify likely "below minimum" appeals
# Most zoning codes require 1.0-2.0 spaces per unit for multifamily
# Projects with <1.0 likely seeking below-minimum variance

below_one = [p for p in projects_with_data if p['ratio'] < 1.0]
print(f"Projects with <1.0 parking ratio (likely below-minimum): {len(below_one):,}")
print(f"Per year: {len(below_one)/13:.1f}")
print(f"% of multifamily+parking appeals: {len(below_one)/len(projects_with_data)*100:.1f}%")
print()

# Show some examples
print("Examples of low-parking-ratio projects:")
print()
for i, project in enumerate(sorted(below_one, key=lambda x: x['ratio'])[:10], 1):
    print(f"{i}. {project['units']} units, {project['parking']} spaces (ratio: {project['ratio']:.2f})")
    print(f"   {project['text']}...")
    print()

# Step 4: Year-by-year trend
print("=" * 100)
print("MULTIFAMILY + PARKING APPEALS OVER TIME")
print("=" * 100)
print()

print(f"{'Year':>6}  {'Appeals':>8}")
print("-" * 18)
for year in range(2013, 2026):
    count = by_year.get(year, 0)
    print(f"{year:>6}  {count:>8,}")

total_appeals = sum(by_year.values())
avg_per_year = total_appeals / 13

print()
print(f"Total (2013-2025): {total_appeals:,}")
print(f"Average per year: {avg_per_year:.1f}")
print()

# Step 5: Compare to multifamily permits
print("=" * 100)
print("MULTIFAMILY VARIANCE RATE")
print("=" * 100)
print()

# We need to estimate multifamily permits
# From our data: 81,617 total zoning permits over 13 years
# Estimate ~20% are multifamily (conservative)

total_permits = 81617
estimated_mf_permits = int(total_permits * 0.20)  # Conservative estimate

print(f"Total zoning permits (2013-2025): {total_permits:,}")
print(f"Estimated multifamily permits (~20%): {estimated_mf_permits:,}")
print(f"Multifamily permits per year: {estimated_mf_permits/13:.0f}")
print()

print(f"Multifamily appeals with parking mention: {total_appeals:,}")
print(f"Multifamily appeals with parking mention per year: {avg_per_year:.1f}")
print()

# Calculate variance rate
variance_rate = (total_appeals / (total_appeals + estimated_mf_permits)) * 100

print(f"Multifamily + parking variance rate: {variance_rate:.1f}%")
print(f"Multifamily + parking by-right rate: {100 - variance_rate:.1f}%")
print()

# For low-parking projects specifically
low_parking_total = len(below_one)
low_parking_rate = (low_parking_total / (low_parking_total + estimated_mf_permits)) * 100

print(f"Low-parking (<1.0 ratio) appeals: {low_parking_total:,}")
print(f"Low-parking per year: {low_parking_total/13:.1f}")
print(f"Low-parking variance rate: {low_parking_rate:.1f}%")
print()

print("=" * 100)
print("KEY FINDINGS")
print("=" * 100)
print()

print(f"1. Multifamily projects mentioning parking: {total_appeals:,} appeals ({avg_per_year:.0f}/year)")
print()

print(f"2. Projects likely seeking below-minimum parking: {len(below_one):,} ({len(below_one)/13:.0f}/year)")
print(f"   These have <1.0 parking ratio, suggesting code requires more than developer wants")
print()

print(f"3. Parking ratios in variance appeals:")
print(f"   - No parking (0): {sum(1 for p in projects_with_data if p['ratio'] == 0):,} projects")
print(f"   - Less than 1 space/unit: {len(below_one):,} projects")
print(f"   - 1+ spaces/unit: {len(projects_with_data) - len(below_one):,} projects")
print()

print(f"4. Estimated multifamily variance rate (parking-related): {variance_rate:.1f}%")
print(f"   This means {variance_rate:.1f}% of multifamily projects need parking variances")
print()

print("IMPORTANT CAVEATS:")
print("- This counts ALL parking mentions, not just minimum-related")
print("- Some high-ratio projects may involve location/access issues, not minimums")
print("- Multifamily permit estimate is rough (~20% of all permits)")
print("- Need actual permit data to calculate true variance rate")
print()

print("=" * 100)
print("BOTTOM LINE")
print("=" * 100)
print()
print(f"Parking minimums likely force ~{len(below_one)/13:.0f} multifamily variance appeals per year")
print(f"(Projects with <1.0 parking ratio, indicating they want less than typical minimums)")
print()
print("This is a conservative estimate. True number may be higher because:")
print("- Some projects mention parking for other reasons (location, access)")
print("- Some projects don't explicitly state parking numbers")
print("- Some 1.0+ ratio projects may still be below district-specific minimums")
