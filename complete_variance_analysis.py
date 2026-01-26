#!/usr/bin/env python3
"""
Complete Variance Generator Analysis with Corrected Height Detection

Fixes the height undercounting issue by searching for all height-related terms,
not just explicit "X stories" mentions.
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
                print(f"  Timeout, retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)
            else:
                raise
    return None

print("=" * 100)
print("COMPLETE VARIANCE GENERATOR ANALYSIS (2013-2025)")
print("WITH CORRECTED HEIGHT DETECTION")
print("=" * 100)
print()

# First, get counts using efficient SQL queries
print("Phase 1: Counting variance types using SQL aggregation...")
print()

# Get total appeals
print("Getting total appeals...")
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
print()

# Get total permits
print("Getting total permits...")
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
print()

total_projects = total_appeals + total_permits
print(f"✓ Total projects: {total_projects:,}")
print()

# Count each variance type
variance_counts = {}

print("Counting variance types...")

searches = {
    'roof_deck': "appealgrounds ILIKE '%roof deck%' OR appealgrounds ILIKE '%roofdeck%'",
    'parking': "appealgrounds ILIKE '%parking%'",
    'height': "appealgrounds ILIKE '%height%'",  # CORRECTED: All height mentions
    'commercial': "appealgrounds ILIKE '%commercial%' OR appealgrounds ILIKE '%retail%' OR appealgrounds ILIKE '%office%' OR appealgrounds ILIKE '%store%' OR appealgrounds ILIKE '%shop%' OR appealgrounds ILIKE '%restaurant%' OR appealgrounds ILIKE '%mixed use%' OR appealgrounds ILIKE '%mixed-use%'",
    'dwelling_units': "appealgrounds ~* '\\d+\\s*(?:dwelling|family|unit)' OR appealgrounds ~* '\\d+\\s*d\\.?u\\.'",
    'setback': "appealgrounds ILIKE '%setback%' OR appealgrounds ILIKE '%set back%' OR appealgrounds ILIKE '%set-back%'",
    'lot_coverage': "appealgrounds ILIKE '%lot coverage%' OR appealgrounds ILIKE '%building coverage%'",
    'accessory_structure': "(appealgrounds ILIKE '%accessory structure%' OR appealgrounds ILIKE '%accessory building%' OR appealgrounds ILIKE '%shed%' OR appealgrounds ILIKE '%detached garage%') AND appealgrounds NOT ILIKE '%roof deck%'",
}

for var_type, condition in searches.items():
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
        variance_counts[var_type] = count
        print(f"✓ {var_type}: {count:,}")
    except Exception as e:
        print(f"✗ {var_type}: Error - {e}")
        variance_counts[var_type] = 0

print()

# Print results table
print("=" * 100)
print("TOP VARIANCE GENERATORS (CORRECTED)")
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

# Now fetch a sample of data for detailed threshold analysis
print("=" * 100)
print("Phase 2: Detailed threshold analysis (sampling data)")
print("=" * 100)
print()

print("Fetching sample of appeals for threshold analysis...")
# Fetch appeals with height or dwelling unit mentions
sample_query = """
    SELECT
        appealgrounds,
        EXTRACT(YEAR FROM createddate) as year
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
print(f"✓ Got {len(sample_appeals):,} appeals with explicit height/unit values")
print()

# Extract height values
height_values = []
for appeal in sample_appeals:
    text = appeal.get('appealgrounds', '')
    if not text:
        continue

    match = re.search(r'(\d+)\s*STOR(?:Y|IES)', text.upper())
    if match:
        stories = int(match.group(1))
        if 1 <= stories <= 20:
            height_values.append(stories)

# Extract dwelling unit values
unit_values = []
for appeal in sample_appeals:
    text = appeal.get('appealgrounds', '')
    if not text:
        continue

    patterns = [r'(\d+)\s*(?:DWELLING|FAMILY|UNIT)', r'(\d+)\s*D\.?U\.?']
    for pattern in patterns:
        match = re.search(pattern, text.upper())
        if match:
            units = int(match.group(1))
            if 1 <= units <= 100:
                unit_values.append(units)
                break

# Height threshold analysis
print("=" * 100)
print("HEIGHT THRESHOLD ANALYSIS")
print("=" * 100)
print()
print(f"**IMPORTANT:** Only {len(height_values):,} appeals explicitly state 'X stories'")
print(f"But {variance_counts['height']:,} appeals mention 'height' in some form (7.4%)")
print(f"This means most height issues are expressed as 'maximum height' violations, not story counts")
print()

if height_values:
    height_counter = Counter(height_values)
    sorted_heights = sorted(height_counter.items())

    cumulative = 0
    print(f"| Max Stories | Appeals | Cumulative | % of Explicit Height |")
    print(f"|-------------|---------|------------|----------------------|")
    for stories, count in sorted_heights[:10]:
        cumulative += count
        pct_resolved = (cumulative / len(height_values)) * 100
        print(f"| {stories:11} | {count:7,} | {cumulative:10,} | {pct_resolved:19.1f}% |")

    print()
    print("**Recommendations for height thresholds:**")
    for threshold_pct in [50, 75, 90]:
        cumulative = 0
        for stories, count in sorted_heights:
            cumulative += count
            if (cumulative / len(height_values)) * 100 >= threshold_pct:
                print(f"  - Allow {stories} stories → resolves {threshold_pct}% of explicit 'X stories' variances")
                break
    print()

# Dwelling unit threshold analysis
print("=" * 100)
print("DWELLING UNIT THRESHOLD ANALYSIS")
print("=" * 100)
print()

if unit_values:
    unit_counter = Counter(unit_values)
    sorted_units = sorted(unit_counter.items())

    cumulative = 0
    print(f"| Max Units | Appeals | Cumulative | % Resolved |")
    print(f"|-----------|---------|------------|------------|")
    for units, count in sorted_units[:15]:
        cumulative += count
        pct_resolved = (cumulative / len(unit_values)) * 100
        print(f"| {units:9} | {count:7,} | {cumulative:10,} | {pct_resolved:9.1f}% |")

    print()
    print("**Recommendations:**")
    for threshold_pct in [50, 75]:
        cumulative = 0
        for units, count in sorted_units:
            cumulative += count
            if (cumulative / len(unit_values)) * 100 >= threshold_pct:
                print(f"  - Allow {units} units → resolves {threshold_pct}% of dwelling unit variances")
                break
    print()

# Reform scenario analysis
print("=" * 100)
print("REFORM SCENARIO: COMPREHENSIVE PACKAGE")
print("=" * 100)
print()
print("Scenario: 4 Stories + No Parking + Roof Decks + Commercial + Fourplex")
print()

# For this we need to fetch all appeals and analyze combinations
# But we'll estimate based on the counts we have
print("Fetching all appeals for detailed reform impact analysis...")

# Fetch in chunks by year to avoid timeout
all_appeals = []
for year in range(2013, 2026):
    print(f"  Fetching {year}...")
    query = f"""
        SELECT
            appealgrounds
        FROM appeals
        WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND createddate >= '{year}-01-01'
            AND createddate < '{year + 1}-01-01'
    """
    data = safe_query(query, timeout=30)
    all_appeals.extend(data['rows'])

print(f"✓ Fetched {len(all_appeals):,} appeals")
print()

# Analyze each appeal for reform impact
completely_eliminated = 0
partially_helped = 0

for appeal in all_appeals:
    text = appeal.get('appealgrounds', '')
    if not text:
        continue

    text_upper = text.upper()

    issues = []
    resolved = []

    # Check for each issue type
    if 'ROOF DECK' in text_upper or 'ROOFDECK' in text_upper:
        issues.append('roof_deck')
        resolved.append('roof_deck')  # Always resolved by allowing roof decks

    if 'PARKING' in text_upper:
        issues.append('parking')
        resolved.append('parking')  # Always resolved by eliminating parking minimums

    if any(kw in text_upper for kw in ['COMMERCIAL', 'RETAIL', 'OFFICE', 'STORE', 'SHOP', 'RESTAURANT', 'MIXED USE', 'MIXED-USE']):
        issues.append('commercial')
        resolved.append('commercial')  # Always resolved by allowing commercial

    # Height - allow up to 4 stories
    height_match = re.search(r'(\d+)\s*STOR(?:Y|IES)', text_upper)
    if height_match:
        stories = int(height_match.group(1))
        issues.append('height')
        if stories <= 4:
            resolved.append('height')
    elif 'HEIGHT' in text_upper:
        # Generic height mention - conservatively assume some would be resolved
        issues.append('height')
        # We'll be conservative and not count this as resolved unless explicit stories ≤4

    # Dwelling units - allow up to 4 units (fourplex)
    unit_patterns = [r'(\d+)\s*(?:DWELLING|FAMILY|UNIT)', r'(\d+)\s*D\.?U\.?']
    for pattern in unit_patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 1 <= units <= 100:
                issues.append('dwelling_units')
                if units <= 4:
                    resolved.append('dwelling_units')
                break

    # Setback, lot coverage, accessory - not resolved by our reforms
    if 'SETBACK' in text_upper or 'SET BACK' in text_upper or 'SET-BACK' in text_upper:
        issues.append('setback')

    if 'LOT COVERAGE' in text_upper or 'BUILDING COVERAGE' in text_upper:
        issues.append('lot_coverage')

    # Categorize impact
    if issues and resolved:
        if len(resolved) == len(issues):
            completely_eliminated += 1
        else:
            partially_helped += 1

total_impacted = completely_eliminated + partially_helped

print(f"**Appeals completely eliminated:** {completely_eliminated:,} ({(completely_eliminated/total_appeals*100):.1f}%)")
print(f"**Appeals partially helped:** {partially_helped:,} ({(partially_helped/total_appeals*100):.1f}%)")
print(f"**Total appeals impacted:** {total_impacted:,} ({(total_impacted/total_appeals*100):.1f}%)")
print()
print(f"**Reduction in ZBA caseload:** {(completely_eliminated/13):.0f} appeals/year")
print()

# By-right rate improvement
current_byright_rate = (total_permits / total_projects) * 100
new_appeals = total_appeals - completely_eliminated
new_total = new_appeals + total_permits
new_byright_rate = (total_permits / new_total) * 100

print(f"**Current by-right rate:** {current_byright_rate:.1f}%")
print(f"**New by-right rate:** {new_byright_rate:.1f}%")
print(f"**Improvement:** +{(new_byright_rate - current_byright_rate):.1f} percentage points")
print()

# Final recommendations
print("=" * 100)
print("FINAL RECOMMENDATIONS (CORRECTED)")
print("=" * 100)
print()
print("**Corrected Priority Rankings:**")
print()
print(f"1. **ROOF DECKS** - {variance_counts['roof_deck']:,} appeals ({(variance_counts['roof_deck']/total_appeals*100):.1f}%), ~{variance_counts['roof_deck']/13:.0f}/year")
print(f"   Recommendation: Allow roof decks by-right")
print()
print(f"2. **PARKING** - {variance_counts['parking']:,} appeals ({(variance_counts['parking']/total_appeals*100):.1f}%), ~{variance_counts['parking']/13:.0f}/year")
print(f"   Recommendation: Eliminate parking minimums citywide")
print()
print(f"3. **COMMERCIAL** - {variance_counts['commercial']:,} appeals ({(variance_counts['commercial']/total_appeals*100):.1f}%), ~{variance_counts['commercial']/13:.0f}/year")
print(f"   Recommendation: Expand neighborhood commercial allowances")
print()
print(f"4. **HEIGHT** - {variance_counts['height']:,} appeals ({(variance_counts['height']/total_appeals*100):.1f}%), ~{variance_counts['height']/13:.0f}/year")
print(f"   Recommendation: Allow 4 stories (45-48 feet) by-right")
print(f"   Note: Only {len(height_values)} explicitly state story count, most say 'maximum height'")
print()
print(f"5. **DWELLING UNITS** - {variance_counts['dwelling_units']:,} appeals ({(variance_counts['dwelling_units']/total_appeals*100):.1f}%), ~{variance_counts['dwelling_units']/13:.0f}/year")
print(f"   Recommendation: Allow fourplexes (4 units) by-right")
print()
print("**COMBINED IMPACT:** These five reforms would eliminate ~{:.0f} appeals/year".format(completely_eliminated/13))
print(f"and improve by-right rate from {current_byright_rate:.1f}% to {new_byright_rate:.1f}%")
print()
