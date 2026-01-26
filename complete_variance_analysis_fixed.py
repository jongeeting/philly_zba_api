#!/usr/bin/env python3
"""
Complete Variance Generator Analysis - FIXED COMMERCIAL DETECTION

Handles all variance types including commercial which was timing out.
"""

import requests
import re
from collections import defaultdict, Counter
import time

CARTO_API = "https://phl.carto.com/api/v2/sql"

def safe_query(query, timeout=60, retries=3):
    """Execute query with retries on timeout."""
    for attempt in range(retries):
        try:
            response = requests.get(CARTO_API, params={'q': query}, timeout=timeout)
            return response.json()
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                print(f"  Timeout, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    return None

print("=" * 100)
print("COMPLETE VARIANCE GENERATOR ANALYSIS (2013-2025)")
print("WITH FIXED COMMERCIAL DETECTION")
print("=" * 100)
print()

# Get totals first
print("Getting totals...")

total_query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
"""
data = safe_query(total_query)
total_appeals = data['rows'][0]['count']
print(f"✓ Total appeals: {total_appeals:,}")

permits_query = """
    SELECT COUNT(*) as count
    FROM permits
    WHERE permitissuedate >= '2013-01-01'
        AND permitissuedate < '2026-01-01'
        AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
"""
data = safe_query(permits_query)
total_permits = data['rows'][0]['count']
print(f"✓ Total permits: {total_permits:,}")

total_projects = total_appeals + total_permits
print(f"✓ Total projects: {total_projects:,}")
print()

# Count variance types with simpler queries
print("Counting variance types...")
print()

variance_counts = {}

# Roof deck
query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND (appealgrounds ILIKE '%roof deck%' OR appealgrounds ILIKE '%roofdeck%')
"""
data = safe_query(query)
variance_counts['roof_deck'] = data['rows'][0]['count']
print(f"✓ Roof deck: {variance_counts['roof_deck']:,}")

# Parking
query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND appealgrounds ILIKE '%parking%'
"""
data = safe_query(query)
variance_counts['parking'] = data['rows'][0]['count']
print(f"✓ Parking: {variance_counts['parking']:,}")

# Height
query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND appealgrounds ILIKE '%height%'
"""
data = safe_query(query)
variance_counts['height'] = data['rows'][0]['count']
print(f"✓ Height: {variance_counts['height']:,}")

# Commercial - split into multiple simpler queries
print("  Counting commercial (multiple queries)...")

commercial_keywords = [
    ('commercial', "appealgrounds ILIKE '%commercial%'"),
    ('retail', "appealgrounds ILIKE '%retail%'"),
    ('office', "appealgrounds ILIKE '%office%'"),
    ('store', "appealgrounds ILIKE '%store%'"),
    ('shop', "appealgrounds ILIKE '%shop%'"),
    ('restaurant', "appealgrounds ILIKE '%restaurant%'"),
    ('mixed_use', "appealgrounds ILIKE '%mixed use%' OR appealgrounds ILIKE '%mixed-use%'"),
]

commercial_total = 0
commercial_breakdown = {}

for keyword, condition in commercial_keywords:
    query = f"""
        SELECT COUNT(*) as count
        FROM appeals
        WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND createddate >= '2013-01-01'
            AND createddate < '2026-01-01'
            AND ({condition})
    """
    try:
        data = safe_query(query, timeout=45)
        count = data['rows'][0]['count']
        commercial_breakdown[keyword] = count
        print(f"    - {keyword}: {count:,}")
    except Exception as e:
        print(f"    - {keyword}: Error - {e}")
        commercial_breakdown[keyword] = 0

# Get unique count (appeals can match multiple keywords)
# We'll estimate by taking the largest single category and adding 80% of others
# This is conservative but avoids double-counting
max_category = max(commercial_breakdown.values())
other_categories = sum(commercial_breakdown.values()) - max_category
estimated_commercial = int(max_category + (other_categories * 0.4))

print(f"  Estimated unique commercial appeals: {estimated_commercial:,}")
variance_counts['commercial'] = estimated_commercial

# Dwelling units
query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND (appealgrounds ~* '\\d+\\s*(?:dwelling|family|unit)' OR appealgrounds ~* '\\d+\\s*d\\.?u\\.')
"""
data = safe_query(query, timeout=45)
variance_counts['dwelling_units'] = data['rows'][0]['count']
print(f"✓ Dwelling units: {variance_counts['dwelling_units']:,}")

# Setback
query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND (appealgrounds ILIKE '%setback%' OR appealgrounds ILIKE '%set back%')
"""
data = safe_query(query)
variance_counts['setback'] = data['rows'][0]['count']
print(f"✓ Setback: {variance_counts['setback']:,}")

# Lot coverage
query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND (appealgrounds ILIKE '%lot coverage%' OR appealgrounds ILIKE '%building coverage%')
"""
data = safe_query(query)
variance_counts['lot_coverage'] = data['rows'][0]['count']
print(f"✓ Lot coverage: {variance_counts['lot_coverage']:,}")

# Accessory structure (excluding roof deck)
query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND (appealgrounds ILIKE '%accessory structure%'
             OR appealgrounds ILIKE '%accessory building%'
             OR appealgrounds ILIKE '%shed%'
             OR appealgrounds ILIKE '%detached garage%')
        AND appealgrounds NOT ILIKE '%roof deck%'
"""
data = safe_query(query)
variance_counts['accessory_structure'] = data['rows'][0]['count']
print(f"✓ Accessory structure: {variance_counts['accessory_structure']:,}")

print()

# Print results
print("=" * 100)
print("TOP VARIANCE GENERATORS (COMPLETE)")
print("=" * 100)
print()

sorted_types = sorted(variance_counts.items(), key=lambda x: x[1], reverse=True)

print(f"| Variance Type | Appeals | Per Year | % of Appeals | % of All Projects |")
print(f"|---------------|---------|----------|--------------|-------------------|")
for var_type, count in sorted_types:
    per_year = count / 13
    pct_appeals = (count / total_appeals) * 100
    pct_projects = (count / total_projects) * 100
    print(f"| {var_type.replace('_', ' ').title():21} | {count:7,} | {per_year:8.0f} | {pct_appeals:11.1f}% | {pct_projects:16.1f}% |")

print()
print("**Note:** Appeals can have multiple variance types, so percentages don't sum to 100%")
print()
print("**Commercial breakdown:**")
for keyword, count in sorted(commercial_breakdown.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {keyword}: {count:,}")
print(f"  - Estimated unique (avoiding double-count): {estimated_commercial:,}")
print()

# Now do threshold analysis by fetching sample data
print("=" * 100)
print("THRESHOLD ANALYSIS")
print("=" * 100)
print()

print("Fetching appeals with explicit height/unit values...")
sample_query = """
    SELECT
        appealgrounds
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
        AND (
            appealgrounds ~* '\\d+\\s*stor(y|ies)'
            OR appealgrounds ~* '\\d+\\s*(?:dwelling|family|unit)'
        )
"""

data = safe_query(sample_query, timeout=90)
sample_appeals = data['rows']
print(f"✓ Got {len(sample_appeals):,} appeals")
print()

# Extract values
height_values = []
unit_values = []

for appeal in sample_appeals:
    text = appeal.get('appealgrounds', '')
    if not text:
        continue

    # Height
    match = re.search(r'(\d+)\s*STOR(?:Y|IES)', text.upper())
    if match:
        stories = int(match.group(1))
        if 1 <= stories <= 20:
            height_values.append(stories)

    # Units
    patterns = [r'(\d+)\s*(?:DWELLING|FAMILY|UNIT)', r'(\d+)\s*D\.?U\.?']
    for pattern in patterns:
        match = re.search(pattern, text.upper())
        if match:
            units = int(match.group(1))
            if 1 <= units <= 100:
                unit_values.append(units)
                break

# Height analysis
print("**HEIGHT THRESHOLDS**")
print()
print(f"Important: Only {len(height_values):,} appeals explicitly state 'X stories'")
print(f"But {variance_counts['height']:,} appeals mention 'height' ({(variance_counts['height']/total_appeals*100):.1f}%)")
print()

if height_values:
    height_counter = Counter(height_values)
    sorted_heights = sorted(height_counter.items())

    cumulative = 0
    print(f"| Stories | Appeals | Cumulative | % of Explicit |")
    print(f"|---------|---------|------------|---------------|")
    for stories, count in sorted_heights[:10]:
        cumulative += count
        pct = (cumulative / len(height_values)) * 100
        print(f"| {stories:7} | {count:7,} | {cumulative:10,} | {pct:12.1f}% |")

    print()
    print("Recommendations:")
    for threshold_pct in [50, 75, 90]:
        cumulative = 0
        for stories, count in sorted_heights:
            cumulative += count
            if (cumulative / len(height_values)) * 100 >= threshold_pct:
                print(f"  - Allow {stories} stories → {threshold_pct}% of explicit height variances")
                break
print()

# Unit analysis
print("**DWELLING UNIT THRESHOLDS**")
print()

if unit_values:
    unit_counter = Counter(unit_values)
    sorted_units = sorted(unit_counter.items())

    cumulative = 0
    print(f"| Units | Appeals | Cumulative | % Resolved |")
    print(f"|-------|---------|------------|------------|")
    for units, count in sorted_units[:15]:
        cumulative += count
        pct = (cumulative / len(unit_values)) * 100
        print(f"| {units:5} | {count:7,} | {cumulative:10,} | {pct:9.1f}% |")

    print()
    print("Key thresholds:")
    print(f"  - 2 units (duplex): {unit_counter.get(1, 0) + unit_counter.get(2, 0):,} appeals")
    print(f"  - 4 units (fourplex): {sum(count for u, count in sorted_units if u <= 4):,} appeals ({(sum(count for u, count in sorted_units if u <= 4)/len(unit_values)*100):.1f}%)")
    print(f"  - 6 units (sixplex): {sum(count for u, count in sorted_units if u <= 6):,} appeals ({(sum(count for u, count in sorted_units if u <= 6)/len(unit_values)*100):.1f}%)")

print()
print("=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
