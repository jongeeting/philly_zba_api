import requests
import re
from collections import defaultdict

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("Fetching multifamily + parking appeals...")

query = """
SELECT appealgrounds, EXTRACT(YEAR FROM createddate) as year
FROM appeals
WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
    AND createddate >= '2013-01-01'
    AND (appealgrounds ~* '\\d+\\s*(?:dwelling|family|unit)'
         OR appealgrounds ~* 'duplex|triplex|fourplex|sixplex'
         OR appealgrounds ILIKE '%multi%family%')
    AND appealgrounds ILIKE '%parking%'
"""

response = requests.get(CARTO_API, params={'q': query}, timeout=120)
data = response.json()

appeals = data['rows']
print(f"Found {len(appeals)} multifamily + parking appeals\n")

# Improved extraction patterns
def extract_units(text):
    """Extract dwelling unit count with multiple patterns"""
    text_upper = text.upper()
    
    # Pattern 1: "X DWELLING UNITS" or "X UNITS"
    patterns = [
        r'(\d+)\s*DWELLING\s*UNITS?',
        r'(\d+)\s*FAMILY\s*DWELLING',
        r'(?:TOTAL\s+OF\s+)?(\d+)\s*UNITS?\s*\)',  # "(9 UNITS)" or "(TOTAL NINE (9) DWELLING UNITS)"
        r'MULTI[-\s]?FAMILY\s*\((\d+)\s*UNITS?\)',
        r'CONTAINING\s+(\d+)\s+DWELLING\s+UNITS',
        r'WITH\s+(\d+)\s+DWELLING\s+UNITS',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 2 <= units <= 200:  # Reasonable range for multifamily
                return units
    
    # Special handling for written numbers: "TWENTY-SIX (26)"
    number_words = {
        'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7,
        'EIGHT': 8, 'NINE': 9, 'TEN': 10, 'ELEVEN': 11, 'TWELVE': 12,
        'SIXTEEN': 16, 'TWENTY': 20, 'THIRTY': 30, 'FORTY': 40, 'FIFTY': 50,
        'NINETY': 90
    }
    
    for word, num in number_words.items():
        if word in text_upper and 'UNIT' in text_upper:
            # Check if there's a number following in parens
            pattern = rf'{word}[- ]?\(?(\d+)\)?\s+.*?UNIT'
            match = re.search(pattern, text_upper)
            if match:
                return int(match.group(1))
    
    return None

def extract_parking(text):
    """Extract parking space count with multiple patterns"""
    text_upper = text.upper()
    
    # Skip bicycle parking
    if 'BICYCLE' in text_upper or 'BIKE' in text_upper:
        # Try to find vehicle parking specifically
        pass
    
    patterns = [
        r'(\d+)\s*(?:ACCESSORY\s+)?(?:OFF[-\s]?STREET\s+)?(?:VEHICLE\s+)?PARKING\s*SPACES?',
        r'(\d+)\s*(?:INTERIOR|EXTERIOR|SURFACE)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',
        r'(\d+)\s*VEHICLE\s+PARKING',
        r'PARKING\s*SPACES?\s*\(.*?(\d+)\s*(?:SPACE|VAN|ACCESSIBLE)',
        r'WITH\s+(\d+)\s+ACCESSORY\s+PARKING',
        r'TOTAL\s+(?:OF\s+)?(\d+)\s+(?:ACCESSORY\s+)?PARKING',
        r'\(TOTAL\s+(\d+)\s+PARKING\s+SPACES',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_upper)
        if matches:
            # Get the last/largest number mentioned
            counts = [int(m) if isinstance(m, str) else int(m[0]) for m in matches]
            parking = max(counts)
            if 0 <= parking <= 500:  # Reasonable range
                return parking
    
    return None

# Extract data
results = []
extraction_stats = {'units_only': 0, 'parking_only': 0, 'both': 0, 'neither': 0}

for appeal in appeals:
    text = appeal['appealgrounds']
    year = appeal['year']
    
    units = extract_units(text)
    parking = extract_parking(text)
    
    if units and parking:
        extraction_stats['both'] += 1
        ratio = parking / units
        results.append({
            'units': units,
            'parking': parking,
            'ratio': ratio,
            'year': year,
            'text': text[:200]
        })
    elif units:
        extraction_stats['units_only'] += 1
    elif parking:
        extraction_stats['parking_only'] += 1
    else:
        extraction_stats['neither'] += 1

print("=" * 80)
print("EXTRACTION RESULTS")
print("=" * 80)
print(f"Total appeals: {len(appeals)}")
print(f"  Both units and parking: {extraction_stats['both']} ({extraction_stats['both']/len(appeals)*100:.1f}%)")
print(f"  Units only: {extraction_stats['units_only']} ({extraction_stats['units_only']/len(appeals)*100:.1f}%)")
print(f"  Parking only: {extraction_stats['parking_only']} ({extraction_stats['parking_only']/len(appeals)*100:.1f}%)")
print(f"  Neither: {extraction_stats['neither']} ({extraction_stats['neither']/len(appeals)*100:.1f}%)")

print(f"\n✓ Successfully extracted {len(results)} projects with both unit and parking data")
print(f"  (Improvement from 25 to {len(results)} = {len(results)/25:.1f}x better)")

# Analyze ratios
results.sort(key=lambda x: x['ratio'])

print("\n" + "=" * 80)
print("PARKING RATIO DISTRIBUTION")
print("=" * 80)

ratio_buckets = {
    '0-0.49': 0,
    '0.50-0.99': 0,
    '1.00': 0,
    '1.01-1.49': 0,
    '1.50-1.99': 0,
    '2.00+': 0
}

for r in results:
    ratio = r['ratio']
    if ratio < 0.5:
        ratio_buckets['0-0.49'] += 1
    elif ratio < 1.0:
        ratio_buckets['0.50-0.99'] += 1
    elif ratio == 1.0:
        ratio_buckets['1.00'] += 1
    elif ratio < 1.5:
        ratio_buckets['1.01-1.49'] += 1
    elif ratio < 2.0:
        ratio_buckets['1.50-1.99'] += 1
    else:
        ratio_buckets['2.00+'] += 1

total = len(results)
for bucket, count in ratio_buckets.items():
    pct = count / total * 100
    bar = '█' * int(pct / 2)
    print(f"{bucket:15} {count:4} ({pct:5.1f}%) {bar}")

below_one = ratio_buckets['0-0.49'] + ratio_buckets['0.50-0.99']
print(f"\nProjects with <1.0 ratio: {below_one} ({below_one/total*100:.1f}%)")
print(f"Average parking ratio: {sum(r['ratio'] for r in results)/len(results):.2f} spaces/unit")

# Show examples of low-ratio projects
print("\n" + "=" * 80)
print("EXAMPLES OF LOW-PARKING PROJECTS (<0.5 spaces/unit)")
print("=" * 80)

low_ratio = [r for r in results if r['ratio'] < 0.5]
for i, r in enumerate(low_ratio[:15], 1):
    print(f"\n{i}. {r['units']} units, {r['parking']} spaces (ratio: {r['ratio']:.2f})")
    print(f"   {r['text'][:150]}...")

# Annual statistics
print("\n" + "=" * 80)
print("LOW-PARKING APPEALS BY YEAR")
print("=" * 80)

by_year = defaultdict(int)
for r in results:
    if r['ratio'] < 1.0:
        by_year[r['year']] += 1

for year in sorted(by_year.keys()):
    print(f"  {int(year)}: {by_year[year]} appeals")

total_low = sum(by_year.values())
years = len(by_year)
print(f"\nTotal: {total_low} appeals over {years} years = {total_low/years:.1f} per year")

