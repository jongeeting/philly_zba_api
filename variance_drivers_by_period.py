#!/usr/bin/env python3
"""
Analyze variance drivers by time period
"""

import requests
import re
import time

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*80)
print("TABLE 2: VARIANCE DRIVERS BY TIME PERIOD")
print("="*80)

def extract_variance_issues(text):
    """Extract variance issues from appeal text."""
    if not text:
        return {}
    
    text_upper = text.upper()
    issues = {}
    
    # Height detection
    height_match = re.search(r'(\d+)\s*(?:STOR(?:IES|Y)|FT|FEET|\')', text_upper)
    if height_match:
        stories = int(height_match.group(1))
        if stories > 0 and stories <= 20:  # Reasonable range
            issues['height'] = stories
    
    # Dwelling units detection
    unit_patterns = [
        r'(\d+)\s*(?:DWELLING|FAMILY|UNIT)',
        r'(\d+)\s*D\.?U\.?',
        r'(\d+)\s*F\.?A\.?M\.?',
    ]
    for pattern in unit_patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if units > 0 and units <= 100:
                issues['dwelling_units'] = units
                break
    
    # Parking detection
    if re.search(r'\bPARK(?:ING)?\b', text_upper):
        issues['parking'] = True
    
    # Roof deck detection
    if re.search(r'\bROOF\s*DECK', text_upper):
        issues['roof_deck'] = True
    
    return issues

# Define periods
periods = {
    "Pre-reform (2007-2012)": ("2007-01-01", "2013-01-01"),
    "Post-reform (2013-2018)": ("2013-01-01", "2019-01-01"),
    "Recent (2019-2025)": ("2019-01-01", "2026-01-01"),
}

results = {}

for period_name, (start_date, end_date) in periods.items():
    print(f"\nFetching {period_name}...")
    
    # Get all appeals for this period - use correct column names
    query = f"""
        SELECT appealdesc, refusaldesc
        FROM appeals
        WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND createddate >= '{start_date}'
            AND createddate < '{end_date}'
    """
    
    try:
        response = requests.get(CARTO_API, params={'q': query}, timeout=60)
        data = response.json()
        
        if 'rows' not in data:
            print(f"  Error: {data.get('error', 'Unknown error')}")
            continue
            
        total_appeals = len(data['rows'])
        print(f"  Found {total_appeals:,} appeals")
        
    except Exception as e:
        print(f"  Error fetching data: {e}")
        continue
    
    # Count variance drivers
    height_count = 0
    height_4stories_count = 0
    dwelling_units_count = 0
    duplex_count = 0
    triplex_count = 0
    parking_count = 0
    roof_deck_count = 0
    
    for row in data['rows']:
        combined_text = f"{row.get('appealdesc', '')} {row.get('refusaldesc', '')}"
        issues = extract_variance_issues(combined_text)
        
        if 'height' in issues:
            height_count += 1
            if issues['height'] <= 4:
                height_4stories_count += 1
        
        if 'dwelling_units' in issues:
            dwelling_units_count += 1
            if issues['dwelling_units'] == 2:
                duplex_count += 1
            elif issues['dwelling_units'] == 3:
                triplex_count += 1
        
        if 'parking' in issues:
            parking_count += 1
        
        if 'roof_deck' in issues:
            roof_deck_count += 1
    
    results[period_name] = {
        'total': total_appeals,
        'height': height_count,
        'height_4stories': height_4stories_count,
        'dwelling_units': dwelling_units_count,
        'duplex': duplex_count,
        'triplex': triplex_count,
        'parking': parking_count,
        'roof_deck': roof_deck_count,
    }
    
    time.sleep(1)  # Be nice to the API

# Print table
print("\n" + "="*80)
print("RESULTS")
print("="*80)

if len(results) == 3:  # All periods fetched successfully
    print("\n| Variance Driver | Pre-reform (2007-2012) | Post-reform (2013-2018) | Recent (2019-2025) |")
    print("|-----------------|------------------------|-------------------------|--------------------|")

    # Total appeals
    print(f"| **Total Appeals** | **{results['Pre-reform (2007-2012)']['total']:,}** | **{results['Post-reform (2013-2018)']['total']:,}** | **{results['Recent (2019-2025)']['total']:,}** |")

    # Height (any)
    for period in results:
        pct = results[period]['height'] / results[period]['total'] * 100
        results[period]['height_pct'] = pct

    print(f"| Height (any) | {results['Pre-reform (2007-2012)']['height']:,} ({results['Pre-reform (2007-2012)']['height_pct']:.1f}%) | {results['Post-reform (2013-2018)']['height']:,} ({results['Post-reform (2013-2018)']['height_pct']:.1f}%) | {results['Recent (2019-2025)']['height']:,} ({results['Recent (2019-2025)']['height_pct']:.1f}%) |")

    # Height ≤4 stories (impacted by Tier 1)
    for period in results:
        pct = results[period]['height_4stories'] / results[period]['total'] * 100
        results[period]['height_4stories_pct'] = pct

    print(f"| Height ≤4 stories | {results['Pre-reform (2007-2012)']['height_4stories']:,} ({results['Pre-reform (2007-2012)']['height_4stories_pct']:.1f}%) | {results['Post-reform (2013-2018)']['height_4stories']:,} ({results['Post-reform (2013-2018)']['height_4stories_pct']:.1f}%) | {results['Recent (2019-2025)']['height_4stories']:,} ({results['Recent (2019-2025)']['height_4stories_pct']:.1f}%) |")

    # Dwelling units (any)
    for period in results:
        pct = results[period]['dwelling_units'] / results[period]['total'] * 100
        results[period]['dwelling_units_pct'] = pct

    print(f"| Dwelling Units (any) | {results['Pre-reform (2007-2012)']['dwelling_units']:,} ({results['Pre-reform (2007-2012)']['dwelling_units_pct']:.1f}%) | {results['Post-reform (2013-2018)']['dwelling_units']:,} ({results['Post-reform (2013-2018)']['dwelling_units_pct']:.1f}%) | {results['Recent (2019-2025)']['dwelling_units']:,} ({results['Recent (2019-2025)']['dwelling_units_pct']:.1f}%) |")

    # Duplex
    for period in results:
        pct = results[period]['duplex'] / results[period]['total'] * 100
        results[period]['duplex_pct'] = pct

    print(f"| Duplex (2 units) | {results['Pre-reform (2007-2012)']['duplex']:,} ({results['Pre-reform (2007-2012)']['duplex_pct']:.1f}%) | {results['Post-reform (2013-2018)']['duplex']:,} ({results['Post-reform (2013-2018)']['duplex_pct']:.1f}%) | {results['Recent (2019-2025)']['duplex']:,} ({results['Recent (2019-2025)']['duplex_pct']:.1f}%) |")

    # Triplex (Tier 1)
    for period in results:
        pct = results[period]['triplex'] / results[period]['total'] * 100
        results[period]['triplex_pct'] = pct

    print(f"| Triplex (3 units) | {results['Pre-reform (2007-2012)']['triplex']:,} ({results['Pre-reform (2007-2012)']['triplex_pct']:.1f}%) | {results['Post-reform (2013-2018)']['triplex']:,} ({results['Post-reform (2013-2018)']['triplex_pct']:.1f}%) | {results['Recent (2019-2025)']['triplex']:,} ({results['Recent (2019-2025)']['triplex_pct']:.1f}%) |")

    # Parking (Tier 1)
    for period in results:
        pct = results[period]['parking'] / results[period]['total'] * 100
        results[period]['parking_pct'] = pct

    print(f"| Parking | {results['Pre-reform (2007-2012)']['parking']:,} ({results['Pre-reform (2007-2012)']['parking_pct']:.1f}%) | {results['Post-reform (2013-2018)']['parking']:,} ({results['Post-reform (2013-2018)']['parking_pct']:.1f}%) | {results['Recent (2019-2025)']['parking']:,} ({results['Recent (2019-2025)']['parking_pct']:.1f}%) |")

    # Roof deck (Tier 2)
    for period in results:
        pct = results[period]['roof_deck'] / results[period]['total'] * 100
        results[period]['roof_deck_pct'] = pct

    print(f"| Roof Deck | {results['Pre-reform (2007-2012)']['roof_deck']:,} ({results['Pre-reform (2007-2012)']['roof_deck_pct']:.1f}%) | {results['Post-reform (2013-2018)']['roof_deck']:,} ({results['Post-reform (2013-2018)']['roof_deck_pct']:.1f}%) | {results['Recent (2019-2025)']['roof_deck']:,} ({results['Recent (2019-2025)']['roof_deck_pct']:.1f}%) |")

    print("\n**Notes:**")
    print("- Percentages show share of total appeals in that period")
    print("- **Tier 1 reforms**: Height ≤4 stories, Triplex, Parking")
    print("- **Tier 2 reforms**: Roof Deck, larger multifamily, commercial")
    print("- Overlapping categories: One appeal may have multiple variance drivers")
else:
    print("\nError: Not all periods could be fetched")

