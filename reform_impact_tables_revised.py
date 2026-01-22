#!/usr/bin/env python3
"""
Calculate Tier 1 and Tier 2 reform impacts for 2013-2025 period
REVISED: Tier 1 = duplex, Tier 2 = fourplex (matches state bills)
"""

import requests
import re
from collections import defaultdict

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*100)
print("REFORM IMPACT ANALYSIS (POST-REFORM PERIOD: 2013-2025)")
print("REVISED TIERS: Tier 1 = Duplex, Tier 2 = Fourplex")
print("="*100)

def extract_all_issues(text):
    """Extract all variance issues from appeal text."""
    if not text:
        return {}
    
    text_upper = text.upper()
    issues = {}
    
    # HEIGHT / STORIES
    height_match = re.search(r'(\d+)\s*STOR(?:Y|IES)', text_upper)
    if height_match:
        stories = int(height_match.group(1))
        if 1 <= stories <= 20:
            issues['height'] = stories
    
    # DWELLING UNITS
    unit_patterns = [
        r'(\d+)\s*(?:DWELLING|FAMILY|UNIT)',
        r'(\d+)\s*D\.?U\.?',
        r'(\d+)\s*F\.?A\.?M\.?',
    ]
    for pattern in unit_patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 1 <= units <= 100:
                issues['dwelling_units'] = units
                break
    
    # PARKING
    if re.search(r'\bPARK(?:ING)?\b', text_upper):
        issues['parking'] = True
    
    # ROOF DECK
    if re.search(r'\bROOF\s*DECK', text_upper):
        issues['roof_deck'] = True
    
    # COMMERCIAL/MIXED USE
    if re.search(r'\b(?:COMMERCIAL|RETAIL|OFFICE|STORE|SHOP|RESTAURANT)\b', text_upper):
        issues['commercial'] = True
    
    return issues

def would_be_allowed_tier1(issues):
    """Check if Tier 1 reforms would allow this project.
    Tier 1: Height ≤4 stories + Duplex (≤2 units) + Parking elimination
    """
    resolved = []
    remaining = []
    
    for issue_type, value in issues.items():
        if issue_type == 'height' and value <= 4:
            resolved.append(f'height_{value}stories')
        elif issue_type == 'dwelling_units' and value <= 2:  # CHANGED: 2 instead of 3
            resolved.append(f'duplex_{value}units')
        elif issue_type == 'parking':
            resolved.append('parking')
        else:
            remaining.append(issue_type)
    
    return len(remaining) == 0, resolved, remaining

def would_be_allowed_tier2(issues):
    """Check if Tier 2 reforms would help (in addition to Tier 1).
    Tier 2: Adds Roof decks + Fourplex (≤4 units) + Commercial/Mixed-use
    """
    # First apply Tier 1
    tier1_allowed, tier1_resolved, tier1_remaining = would_be_allowed_tier1(issues)
    
    if tier1_allowed:
        return True, tier1_resolved, []
    
    # Then apply Tier 2 to remaining issues
    resolved = tier1_resolved.copy()
    remaining = []
    
    for issue_type in tier1_remaining:
        if issue_type == 'roof_deck':
            resolved.append('roof_deck')
        elif issue_type == 'dwelling_units':
            # Tier 2: Allow up to 4 units (fourplex)  # CHANGED: 4 instead of 6
            if issues[issue_type] <= 4:
                resolved.append(f'fourplex_{issues[issue_type]}units')
            else:
                remaining.append(issue_type)
        elif issue_type == 'commercial':
            resolved.append('commercial')
        else:
            remaining.append(issue_type)
    
    return len(remaining) == 0, resolved, remaining

# Fetch appeals from 2013-2025
print("\nFetching appeals from 2013-2025...")

query = """
    SELECT 
        EXTRACT(YEAR FROM createddate) as year,
        appealgrounds
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
"""

response = requests.get(CARTO_API, params={'q': query}, timeout=60)
data = response.json()

if 'rows' not in data:
    print(f"Error: {data.get('error', 'Unknown error')}")
    exit(1)

print(f"Found {len(data['rows']):,} appeals")

# Analyze each appeal
tier1_complete = 0
tier1_partial = 0
tier1_no_help = 0

tier2_complete = 0
tier2_partial = 0
tier2_no_help = 0

by_year = defaultdict(lambda: {
    'total': 0,
    'tier1_complete': 0,
    'tier1_partial': 0,
    'tier2_complete': 0,
    'tier2_partial': 0
})

for row in data['rows']:
    year = int(row['year']) if row['year'] else 2025
    text = row.get('appealgrounds', '')
    issues = extract_all_issues(text)
    
    by_year[year]['total'] += 1
    
    if not issues:  # Can't determine issues
        tier1_no_help += 1
        tier2_no_help += 1
        continue
    
    # Tier 1 analysis
    tier1_allowed, tier1_resolved, tier1_remaining = would_be_allowed_tier1(issues)
    
    if tier1_allowed:
        tier1_complete += 1
        by_year[year]['tier1_complete'] += 1
    elif tier1_resolved:  # Helped but not completely
        tier1_partial += 1
        by_year[year]['tier1_partial'] += 1
    else:
        tier1_no_help += 1
    
    # Tier 2 analysis
    tier2_allowed, tier2_resolved, tier2_remaining = would_be_allowed_tier2(issues)
    
    if tier2_allowed:
        tier2_complete += 1
        by_year[year]['tier2_complete'] += 1
    elif tier2_resolved:  # Helped but not completely
        tier2_partial += 1
        by_year[year]['tier2_partial'] += 1
    else:
        tier2_no_help += 1

# Calculate totals
total_appeals = len(data['rows'])
tier1_total_impacted = tier1_complete + tier1_partial
tier2_total_impacted = tier2_complete + tier2_partial

# Print Tier 1 table
print("\n" + "="*100)
print("TIER 1 REFORMS IMPACT (4 Stories + Duplex + Parking Elimination)")
print("="*100)

print("\n| Impact Type | Appeals | % of Total | Appeals/Year |")
print("|-------------|---------|------------|--------------|")
print(f"| **Completely Eliminated** | {tier1_complete:,} | {tier1_complete/total_appeals*100:.1f}% | {tier1_complete/13:.0f} |")
print(f"| **Partially Helped** | {tier1_partial:,} | {tier1_partial/total_appeals*100:.1f}% | {tier1_partial/13:.0f} |")
print(f"| **Total Impacted** | {tier1_total_impacted:,} | {tier1_total_impacted/total_appeals*100:.1f}% | {tier1_total_impacted/13:.0f} |")
print(f"| Not Helped | {tier1_no_help:,} | {tier1_no_help/total_appeals*100:.1f}% | {tier1_no_help/13:.0f} |")
print(f"| **Total Appeals** | {total_appeals:,} | 100.0% | {total_appeals/13:.0f} |")

# Print Tier 2 table
print("\n" + "="*100)
print("TIER 1 + TIER 2 COMBINED (+ Roof Decks + Fourplex + Commercial)")
print("="*100)

print("\n| Impact Type | Appeals | % of Total | Appeals/Year |")
print("|-------------|---------|------------|--------------|")
print(f"| **Completely Eliminated** | {tier2_complete:,} | {tier2_complete/total_appeals*100:.1f}% | {tier2_complete/13:.0f} |")
print(f"| **Partially Helped** | {tier2_partial:,} | {tier2_partial/total_appeals*100:.1f}% | {tier2_partial/13:.0f} |")
print(f"| **Total Impacted** | {tier2_total_impacted:,} | {tier2_total_impacted/total_appeals*100:.1f}% | {tier2_total_impacted/13:.0f} |")
print(f"| Not Helped | {tier2_no_help:,} | {tier2_no_help/total_appeals*100:.1f}% | {tier2_no_help/13:.0f} |")
print(f"| **Total Appeals** | {total_appeals:,} | 100.0% | {total_appeals/13:.0f} |")

# Additional impact from Tier 2
tier2_additional_complete = tier2_complete - tier1_complete
tier2_additional_partial = tier2_partial - tier1_partial
tier2_additional_total = tier2_additional_complete + tier2_additional_partial

print("\n**Additional Impact from Tier 2 (beyond Tier 1):**")
print(f"- Additional complete eliminations: {tier2_additional_complete:,} ({tier2_additional_complete/13:.0f}/year)")
print(f"- Additional partial help: {tier2_additional_partial:,} ({tier2_additional_partial/13:.0f}/year)")
print(f"- Total additional impact: {tier2_additional_total:,} ({tier2_additional_total/13:.0f}/year)")

# Year-by-year breakdown
print("\n" + "="*100)
print("YEAR-BY-YEAR BREAKDOWN (2013-2025)")
print("="*100)

print("\n| Year | Total | Tier 1 Complete | Tier 1 Partial | Tier 2 Complete | Tier 2 Partial |")
print("|------|-------|-----------------|----------------|-----------------|----------------|")

for year in sorted(by_year.keys()):
    stats = by_year[year]
    print(f"| {year} | {stats['total']:,} | {stats['tier1_complete']:,} ({stats['tier1_complete']/stats['total']*100:.1f}%) | {stats['tier1_partial']:,} ({stats['tier1_partial']/stats['total']*100:.1f}%) | {stats['tier2_complete']:,} ({stats['tier2_complete']/stats['total']*100:.1f}%) | {stats['tier2_partial']:,} ({stats['tier2_partial']/stats['total']*100:.1f}%) |")

print("\n**Notes:**")
print("- **Completely Eliminated**: Appeals with ONLY issues addressed by reforms (single-issue)")
print("- **Partially Helped**: Appeals where reforms address some but not all issues (multi-issue)")
print("- **Total Impacted**: All appeals that would benefit from reforms (complete + partial)")
print("- Analysis based on keyword detection from appeal descriptions")
print("- **Tier 1**: Height ≤4 stories, Duplex (≤2 units), Parking elimination")
print("- **Tier 2**: Adds Roof Decks, Fourplex (≤4 units), Commercial/Mixed-Use")
print("- **REVISED to match state zoning reform bills**")

# Calculate by-right improvement
print("\n" + "="*100)
print("BY-RIGHT DEVELOPMENT IMPACT")
print("="*100)

current_by_right = 83.2  # From our analysis
current_variance = 16.8
current_appeals_year = total_appeals / 13

tier1_new_appeals = current_appeals_year - (tier1_complete / 13)
tier1_new_variance_rate = tier1_new_appeals / (current_appeals_year / (current_variance/100)) * 100
tier1_new_by_right = 100 - tier1_new_variance_rate

tier2_new_appeals = current_appeals_year - (tier2_complete / 13)
tier2_new_variance_rate = tier2_new_appeals / (current_appeals_year / (current_variance/100)) * 100
tier2_new_by_right = 100 - tier2_new_variance_rate

print(f"\n**Current (2019-2025):**")
print(f"  By-right rate: {current_by_right:.1f}%")
print(f"  Appeals/year: {current_appeals_year:.0f}")

print(f"\n**After Tier 1 Reforms (Duplex):**")
print(f"  Completely eliminated: {tier1_complete/13:.0f} appeals/year")
print(f"  New appeals/year: {tier1_new_appeals:.0f}")
print(f"  New by-right rate: {tier1_new_by_right:.1f}%")
print(f"  Improvement: +{tier1_new_by_right - current_by_right:.1f} percentage points")

print(f"\n**After Tier 1 + Tier 2 Combined (Fourplex):**")
print(f"  Completely eliminated: {tier2_complete/13:.0f} appeals/year")
print(f"  New appeals/year: {tier2_new_appeals:.0f}")
print(f"  New by-right rate: {tier2_new_by_right:.1f}%")
print(f"  Improvement: +{tier2_new_by_right - current_by_right:.1f} percentage points")

