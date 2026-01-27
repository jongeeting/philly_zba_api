import requests
import re
from collections import defaultdict

CARTO_API = "https://phl.carto.com/api/v2/sql"

# Comprehensive number word mapping (expanded)
NUMBER_WORDS = {
    'ZERO': 0, 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
    'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
    'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13, 'FOURTEEN': 14, 'FIFTEEN': 15,
    'SIXTEEN': 16, 'SEVENTEEN': 17, 'EIGHTEEN': 18, 'NINETEEN': 19, 'TWENTY': 20,
    'TWENTY-ONE': 21, 'TWENTY-TWO': 22, 'TWENTY-THREE': 23, 'TWENTY-FOUR': 24,
    'TWENTY-FIVE': 25, 'TWENTY-SIX': 26, 'TWENTY-SEVEN': 27, 'TWENTY-EIGHT': 28,
    'TWENTY-NINE': 29, 'THIRTY': 30, 'THIRTY-ONE': 31, 'THIRTY-TWO': 32,
    'THIRTY-THREE': 33, 'THIRTY-FOUR': 34, 'THIRTY-FIVE': 35, 'THIRTY-SIX': 36,
    'THIRTY-SEVEN': 37, 'THIRTY-EIGHT': 38, 'THIRTY-NINE': 39, 'FORTY': 40,
    'FORTY-ONE': 41, 'FORTY-TWO': 42, 'FORTY-THREE': 43, 'FORTY-FOUR': 44,
    'FORTY-FIVE': 45, 'FORTY-SIX': 46, 'FORTY-SEVEN': 47, 'FORTY-EIGHT': 48,
    'FORTY-NINE': 49, 'FIFTY': 50, 'FIFTY-FIVE': 55, 'SIXTY': 60, 'SEVENTY': 70,
    'EIGHTY': 80, 'NINETY': 90, 'ONE HUNDRED': 100, 'TWO HUNDRED': 200
}

print("Fetching multifamily + parking appeals...")

query = """
SELECT appealgrounds, agendadescription, proviso, appealnumber, createddate
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

def extract_units_ultra_advanced(text):
    """Extract dwelling unit count with ultra-comprehensive patterns"""
    if not text:
        return None

    text_upper = text.upper()

    # Strategy 1: Direct digit patterns (most reliable)
    digit_patterns = [
        r'(?:TOTAL\s+(?:OF\s+)?)?(\d+)\s*DWELLING\s*UNITS?',
        r'(\d+)\s*FAMILY\s*DWELLING',
        r'(?:CONTAINING|WITH|TO INCLUDE)\s+(\d+)\s+DWELLING\s+UNITS',
        r'MULTI[-\s]?FAMILY\s*(?:HOUSEHOLD\s+LIVING\s*)?\((\d+)\s*UNITS?\)',
        r'MULTI[-\s]?FAMILY\s*(?:HOUSEHOLD\s+LIVING\s*)?\((\d+)\s*DWELLING\s+UNITS?\)',
        r'\((\d+)\s*DWELLING\s*UNITS?\)',
        r'(?:TOTAL\s+)?(\d+)\s*UNITS?\s*\)',
        r'FOR\s+(\d+)\s+DWELLING\s+UNITS',
        r'(\d+)\s*RESIDENTIAL\s+UNITS?',
        r'LIVING\s*\((\d+)\s+DWELLING\s+UNITS?\)',
        r'(\d+)\s+DWELLING\s+UNITS?\s+(?:WITH|AND)',
        r'(\d+)\s*UNIT\s*BUILDING',
        r'BUILDING.*?(\d+)\s*UNITS?',
        r'(\d+)[-\s]UNIT\s+(?:BUILDING|STRUCTURE)',
    ]

    for pattern in digit_patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 2 <= units <= 200:
                return units

    # Strategy 2: Written numbers with digit in parentheses "TWENTY-SIX (26)"
    for word, num in NUMBER_WORDS.items():
        if num < 2:
            continue
        patterns = [
            rf'{re.escape(word)}\s*\((\d+)\)\s*(?:DWELLING\s*)?UNITS?',
            rf'{re.escape(word)}\s*\((\d+)\)\s*DWELLING',
            rf'{re.escape(word)}\s*\((\d+)\)\s*RESIDENTIAL',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                return int(match.group(1))

    # Strategy 3: Written numbers alone (less reliable, need context)
    for word, num in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        if num < 2:
            continue
        patterns = [
            rf'\b{re.escape(word)}\s+(?:DWELLING\s+)?UNITS?\b',
            rf'\b{re.escape(word)}\s+RESIDENTIAL\s+UNITS?\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text_upper):
                return num

    return None

def extract_parking_ultra_advanced(text):
    """Extract parking space count with ultra-comprehensive patterns"""
    if not text:
        return None

    text_upper = text.upper()

    # Collect all potential parking counts
    parking_counts = []

    # Strategy 1: Direct digit patterns - MUCH more comprehensive
    digit_patterns = [
        # Standard patterns
        r'(\d+)\s*(?:ACCESSORY\s+)?(?:OFF[-\s]?STREET\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?',
        r'(\d+)\s*(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED|BASEMENT)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',

        # "FOR X SPACES" patterns
        r'PARKING\s+(?:FOR\s+)?(\d+)\s+(?:VEHICLES?|SPACES?)',
        r'FOR\s+(\d+)\s+(?:VEHICULAR\s+)?PARKING\s*SPACES?',

        # "WITH X ACCESSORY PARKING" patterns
        r'WITH\s+(\d+)\s+ACCESSORY\s+(?:OFF[-\s]?STREET\s+)?(?:STRUCTURED\s+)?PARKING',
        r'WITH\s+(\d+)\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+PARKING',

        # Total patterns
        r'TOTAL\s+(?:OF\s+)?(\d+)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',
        r'\(TOTAL\s+(\d+)\s+PARKING\s+SPACES',

        # Provide patterns
        r'PROVIDE(?:S)?\s+(\d+)\s+(?:ACCESSORY\s+)?PARKING',
        r'TO\s+PROVIDE.*?(\d+)\s+(?:VEHICULAR\s+)?PARKING\s*SPACES?',

        # Number before context
        r'(\d+)\s+PARKING\s+SPACES?\s+\(',
        r'(\d+)\s+ACCESSORY\s+PARKING\s*SPACES?',
        r'(\d+)\s+VEHICULAR\s+PARKING\s*SPACES?',

        # "PARKING FOR X" patterns
        r'PARKING\s+FOR\s+(\d+)\s*(?:SPACES?|VEHICLES?)?',

        # Modified space counts (interior, exterior, etc)
        r'(\d+)\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED|BASEMENT|UNDERGROUND)\s+ACCESSORY\s+PARKING',
        r'(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED|BASEMENT)\s+(?:ACCESSORY\s+)?PARKING\s+FOR\s+(\d+)',

        # "SPACES" without explicit "PARKING" nearby
        r'(?:STRUCTURED|SURFACE|ACCESSORY)\s+PARKING.*?FOR\s+(\d+)\s+SPACES',
        r'PARKING.*?(?:INCLUDING|WITH)\s+(\d+)\s+(?:STANDARD|ACCESSIBLE|COMPACT)',

        # Reduction patterns "reduce from X to Y"
        r'(?:REDUCE|REDUCED|REDUCING).*?(?:FROM\s+\d+\s+)?TO\s+(\d+)\s+(?:ACCESSORY\s+)?PARKING',
        r'(?:PROVIDE|PROVIDING)\s+(\d+)\s+SPACES',

        # Seven parking spaces patterns (with details in parens)
        r'(\d+)\s+ACCESSORY\s+PARKING\s+SPACES?\s+\([^)]*\)',
        r'(\d+)\s+PARKING\s+SPACES?\s+\(INCLUDING',
    ]

    for pattern in digit_patterns:
        matches = re.findall(pattern, text_upper)
        if matches:
            for m in matches:
                count = int(m) if isinstance(m, str) else int(m[0])
                if 0 <= count <= 500:
                    parking_counts.append(count)

    # Strategy 2: Written numbers with digit in parentheses - more patterns
    for word, num in NUMBER_WORDS.items():
        patterns = [
            # Standard word + digit patterns
            rf'{re.escape(word)}\s*\((\d+)\)\s+(?:ACCESSORY\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?',
            rf'{re.escape(word)}\s*\((\d+)\)\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+PARKING',

            # Reversed pattern: digit comes first, then word
            rf'(\d+)\s*\({re.escape(word)}\)\s+PARKING',
            rf'FOR\s+{re.escape(word)}\s*\((\d+)\)\s+(?:VEHICULAR\s+)?PARKING',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                count = int(match.group(1))
                if 0 <= count <= 500:
                    parking_counts.append(count)

    # Strategy 3: Written numbers alone for parking
    for word, num in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        patterns = [
            rf'\b{re.escape(word)}\s+(?:ACCESSORY\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?\b',
            rf'\b{re.escape(word)}\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+PARKING',
            rf'WITH\s+{re.escape(word)}\s+ACCESSORY\s+PARKING',
        ]

        for pattern in patterns:
            if re.search(pattern, text_upper):
                if 0 <= num <= 500:
                    parking_counts.append(num)

    # Return the most commonly mentioned number, or the largest if tied
    if parking_counts:
        # If we found multiple counts, take the most frequent one
        # If tied, take the maximum (usually the total)
        from collections import Counter
        count_freq = Counter(parking_counts)
        most_common = count_freq.most_common(1)[0][0]
        return most_common

    return None

# Extract data from all available text fields
results = []
extraction_stats = {'units_only': 0, 'parking_only': 0, 'both': 0, 'neither': 0}
field_usage = {'appealgrounds': 0, 'agendadescription': 0, 'proviso': 0}

for appeal in appeals:
    appealgrounds = appeal['appealgrounds'] or ''
    agendadescription = appeal.get('agendadescription', '') or ''
    proviso = appeal.get('proviso', '') or ''
    appeal_num = appeal['appealnumber']

    # Combine all text fields for extraction
    combined_text = f"{appealgrounds} {agendadescription} {proviso}"

    # Try extraction from combined text
    units = extract_units_ultra_advanced(combined_text)
    parking = extract_parking_ultra_advanced(combined_text)

    # Track which fields contributed to successful extraction
    if units and parking:
        if extract_units_ultra_advanced(appealgrounds) and extract_parking_ultra_advanced(appealgrounds):
            field_usage['appealgrounds'] += 1
        elif agendadescription and (extract_units_ultra_advanced(agendadescription) or extract_parking_ultra_advanced(agendadescription)):
            field_usage['agendadescription'] += 1
        elif proviso and (extract_units_ultra_advanced(proviso) or extract_parking_ultra_advanced(proviso)):
            field_usage['proviso'] += 1

    if units and parking:
        extraction_stats['both'] += 1
        ratio = parking / units
        # Filter out obvious extraction errors (ratios > 5.0)
        if ratio <= 5.0:
            results.append({
                'units': units,
                'parking': parking,
                'ratio': ratio,
                'appeal_num': appeal_num,
                'year': int(appeal['createddate'][:4]),
                'text': appealgrounds[:200]
            })
    elif units:
        extraction_stats['units_only'] += 1
    elif parking:
        extraction_stats['parking_only'] += 1
    else:
        extraction_stats['neither'] += 1

print("=" * 80)
print("ULTRA-ADVANCED EXTRACTION RESULTS")
print("=" * 80)
print(f"Total appeals: {len(appeals)}")
print(f"  Both units and parking: {extraction_stats['both']} ({extraction_stats['both']/len(appeals)*100:.1f}%)")
print(f"  Units only: {extraction_stats['units_only']} ({extraction_stats['units_only']/len(appeals)*100:.1f}%)")
print(f"  Parking only: {extraction_stats['parking_only']} ({extraction_stats['parking_only']/len(appeals)*100:.1f}%)")
print(f"  Neither: {extraction_stats['neither']} ({extraction_stats['neither']/len(appeals)*100:.1f}%)")

print(f"\n✓ Successfully extracted {len(results)} projects with both unit and parking data")
print(f"  Previous best: 218 projects (22%)")
print(f"  New extraction: {len(results)} projects ({len(results)/len(appeals)*100:.1f}%)")
if len(results) > 218:
    improvement = (len(results) - 218) / 218 * 100
    print(f"  🎉 IMPROVEMENT: +{len(results) - 218} projects (+{improvement:.1f}%)")
else:
    print(f"  No improvement (may need pattern refinement)")

print("\n" + "=" * 80)
print("FIELD CONTRIBUTION TO SUCCESSFUL EXTRACTIONS")
print("=" * 80)
print(f"  appealgrounds: {field_usage['appealgrounds']} ({field_usage['appealgrounds']/max(1,len(results))*100:.1f}%)")
print(f"  agendadescription: {field_usage['agendadescription']} ({field_usage['agendadescription']/max(1,len(results))*100:.1f}%)")
print(f"  proviso: {field_usage['proviso']} ({field_usage['proviso']/max(1,len(results))*100:.1f}%)")

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
    '2.00-2.99': 0,
    '3.00+': 0
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
    elif ratio < 3.0:
        ratio_buckets['2.00-2.99'] += 1
    else:
        ratio_buckets['3.00+'] += 1

total = len(results)
for bucket, count in ratio_buckets.items():
    pct = count / total * 100
    bar = '█' * int(pct / 2)
    print(f"{bucket:15} {count:4} ({pct:5.1f}%) {bar}")

below_one = ratio_buckets['0-0.49'] + ratio_buckets['0.50-0.99']
print(f"\nProjects with <1.0 ratio: {below_one} ({below_one/total*100:.1f}%)")
print(f"Average parking ratio: {sum(r['ratio'] for r in results)/len(results):.2f} spaces/unit")
print(f"Median parking ratio: {results[len(results)//2]['ratio']:.2f} spaces/unit")

# Annual analysis
print("\n" + "=" * 80)
print("ANNUAL BREAKDOWN (Below-Minimum Projects)")
print("=" * 80)

years = defaultdict(lambda: {'<0.5': 0, '0.5-0.99': 0, '>=1.0': 0, 'total': 0})

for r in results:
    year = r['year']
    years[year]['total'] += 1
    if r['ratio'] < 0.5:
        years[year]['<0.5'] += 1
    elif r['ratio'] < 1.0:
        years[year]['0.5-0.99'] += 1
    else:
        years[year]['>=1.0'] += 1

print(f"{'Year':<6} {'<0.5':>6} {'0.5-0.99':>8} {'>=1.0':>6} {'Total':>6}")
print("-" * 40)
for year in sorted(years.keys()):
    data = years[year]
    print(f"{year:<6} {data['<0.5']:>6} {data['0.5-0.99']:>8} {data['>=1.0']:>6} {data['total']:>6}")

total_below_one = sum(years[y]['<0.5'] + years[y]['0.5-0.99'] for y in years)
num_years = len(years)
print(f"\nTotal below-minimum (<1.0): {total_below_one}")
print(f"Annual average: {total_below_one/num_years:.1f} per year")

# Show extreme examples
print("\n" + "=" * 80)
print("EXTREME LOW-PARKING PROJECTS (Lowest 15)")
print("=" * 80)

for i, r in enumerate(results[:15], 1):
    print(f"{i:2}. Appeal #{r['appeal_num']:20} {r['units']:3} units, {r['parking']:3} spaces (ratio: {r['ratio']:.2f})")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total extracted: {len(results)} projects ({len(results)/len(appeals)*100:.1f}% of appeals)")
print(f"Low-parking (<1.0 ratio): {below_one} projects ({below_one/total*100:.1f}% of sample)")
print(f"Annual rate of below-minimum appeals: {total_below_one/num_years:.1f} per year")

if len(results) > 218:
    print(f"\n🎉 NEW BEST: Extracted {len(results) - 218} additional projects!")
else:
    print(f"\n⚠️  Did not improve over previous best (218 projects)")
