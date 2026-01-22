#!/usr/bin/env python3
"""
Create both summary tables for comparison document
"""

import requests
import re
import time

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("="*100)
print("TABLE 1: YEAR-BY-YEAR VARIANCE VS BY-RIGHT SHARE (2007-2025)")
print("="*100)

# Get ZBA appeals by year
appeals_query = """
    SELECT
        EXTRACT(YEAR FROM createddate) as year,
        COUNT(*) as appeal_count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2007-01-01'
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': appeals_query})
appeals_data = response.json()
appeals_by_year = {int(row['year']): int(row['appeal_count']) for row in appeals_data['rows']}

# Get zoning permits by year
permits_query = """
    SELECT
        EXTRACT(YEAR FROM permitissuedate) as year,
        COUNT(*) as permit_count
    FROM permits
    WHERE permitissuedate >= '2007-01-01'
        AND (permittype ILIKE '%ZON%' OR permittype ILIKE '%USE%')
    GROUP BY year
    ORDER BY year
"""

response = requests.get(CARTO_API, params={'q': permits_query})
permits_data = response.json()
permits_by_year = {int(row['year']): int(row['permit_count']) for row in permits_data['rows']}

print("\n| Year | ZBA Appeals | Zoning Permits | Total Projects | Variance Share | By-Right Share |")
print("|------|-------------|----------------|----------------|----------------|----------------|")

for year in range(2007, 2026):  # Exclude 2026 partial year
    appeals = appeals_by_year.get(year, 0)
    permits = permits_by_year.get(year, 0)
    total = appeals + permits
    
    if total > 0:
        var_share = appeals / total * 100
        by_right_share = permits / total * 100
        print(f"| {year} | {appeals:,} | {permits:,} | {total:,} | {var_share:.1f}% | {by_right_share:.1f}% |")

# Period averages (updated per user's request)
print("\n**Period Averages:**\n")

periods = {
    "Pre-reform (2007-2012)": range(2007, 2013),
    "Post-reform (2013-2018)": range(2013, 2019),
    "2019 only": range(2019, 2020),
    "Tax abatement uncertainty (2020-2021)": range(2020, 2022),
    "Post-abatement change (2022-2025)": range(2022, 2026),
}

print("| Period | Avg Appeals/Year | Avg Permits/Year | Avg Total | Variance Share | By-Right Share |")
print("|--------|------------------|------------------|-----------|----------------|----------------|")

for period_name, years in periods.items():
    total_appeals = sum(appeals_by_year.get(y, 0) for y in years)
    total_permits = sum(permits_by_year.get(y, 0) for y in years)
    total = total_appeals + total_permits
    
    avg_appeals = total_appeals / len(years)
    avg_permits = total_permits / len(years)
    avg_total = total / len(years)
    
    var_share = total_appeals / total * 100 if total > 0 else 0
    by_right_share = total_permits / total * 100 if total > 0 else 0
    
    print(f"| {period_name} | {avg_appeals:,.0f} | {avg_permits:,.0f} | {avg_total:,.0f} | {var_share:.1f}% | {by_right_share:.1f}% |")

print("\n" + "="*100)
print("TABLE 2: VARIANCE DRIVERS BY TIME PERIOD")
print("="*100)

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
periods_drivers = {
    "Pre-reform (2007-2012)": ("2007-01-01", "2013-01-01"),
    "Post-reform (2013-2018)": ("2013-01-01", "2019-01-01"),
    "Recent (2019-2025)": ("2019-01-01", "2026-01-01"),
}

results = {}

for period_name, (start_date, end_date) in periods_drivers.items():
    print(f"\nFetching {period_name}...")
    
    # Get all appeals for this period - use correct column name
    query = f"""
        SELECT appealgrounds
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
        text = row.get('appealgrounds', '')
        issues = extract_variance_issues(text)
        
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
print("\n" + "="*100)
print("RESULTS")
print("="*100)

if len(results) == 3:  # All periods fetched successfully
    print("\n| Variance Driver | Pre-reform (2007-2012) | Post-reform (2013-2018) | Recent (2019-2025) |")
    print("|-----------------|------------------------|-------------------------|--------------------|")

    # Total appeals
    print(f"| **Total Appeals** | **{results['Pre-reform (2007-2012)']['total']:,}** | **{results['Post-reform (2013-2018)']['total']:,}** | **{results['Recent (2019-2025)']['total']:,}** |")

    # Calculate percentages and print rows
    drivers = [
        ('Height (any)', 'height'),
        ('Height ≤4 stories', 'height_4stories'),
        ('Dwelling Units (any)', 'dwelling_units'),
        ('Duplex (2 units)', 'duplex'),
        ('Triplex (3 units)', 'triplex'),
        ('Parking', 'parking'),
        ('Roof Deck', 'roof_deck'),
    ]

    for label, key in drivers:
        row_parts = [f"| {label}"]
        for period in ['Pre-reform (2007-2012)', 'Post-reform (2013-2018)', 'Recent (2019-2025)']:
            count = results[period][key]
            total = results[period]['total']
            pct = count / total * 100 if total > 0 else 0
            row_parts.append(f"{count:,} ({pct:.1f}%)")
        row_parts.append("|")
        print(" | ".join(row_parts))

    print("\n**Notes:**")
    print("- Percentages show share of total appeals in that period")
    print("- **Tier 1 reforms**: Height ≤4 stories, Triplex (3 units), Parking")
    print("- **Tier 2 reforms**: Roof Deck, larger multifamily, commercial")
    print("- Overlapping categories: One appeal may have multiple variance drivers")
    print("- Tax abatement uncertainty period (2020-2021) grouped due to policy changes")
else:
    print("\nError: Not all periods could be fetched")

