import requests
import re
from collections import defaultdict, Counter

CARTO_API = "https://phl.carto.com/api/v2/sql"

# Comprehensive number word mapping
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
    'FORTY-NINE': 49, 'FIFTY': 50, 'FIFTY-FIVE': 55, 'SIXTY': 60, 'SIXTY-SIX': 66,
    'SEVENTY': 70, 'EIGHTY': 80, 'NINETY': 90, 'ONE HUNDRED': 100, 'TWO HUNDRED': 200
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

def extract_units_maximum(text):
    """Extract dwelling unit count with maximum comprehensive patterns"""
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
        r'HOUSEHOLD\s+LIVING\s+CONTAINING\s+(\d+)\s+DWELLING\s+UNITS',
        r'AS\s+MULTI[-\s]?FAMILY\s+\((\d+)\s+UNITS?\)',
    ]

    for pattern in digit_patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 2 <= units <= 200:
                return units

    # Strategy 2: Written numbers with digit in parentheses
    for word, num in NUMBER_WORDS.items():
        if num < 2:
            continue
        patterns = [
            rf'{re.escape(word)}\s*\((\d+)\)\s*(?:DWELLING\s*)?UNITS?',
            rf'{re.escape(word)}\s*\((\d+)\)\s*DWELLING',
            rf'{re.escape(word)}\s*\((\d+)\)\s*RESIDENTIAL',
            rf'MULTI[-\s]?FAMILY\s+\({re.escape(word)}\s+UNITS?\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                return int(match.group(1)) if '(' in pattern and not 'MULTI' in pattern else num

    # Strategy 3: Written numbers alone (less reliable, need strong context)
    for word, num in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        if num < 2:
            continue
        patterns = [
            rf'\b{re.escape(word)}\s+(?:DWELLING\s+)?UNITS?\b',
            rf'\b{re.escape(word)}\s+RESIDENTIAL\s+UNITS?\b',
            rf'MULTI[-\s]?FAMILY\s+\({re.escape(word)}\s+UNITS?\)',
        ]
        for pattern in patterns:
            if re.search(pattern, text_upper):
                return num

    return None

def extract_parking_maximum(text):
    """Extract parking space count with maximum comprehensive patterns"""
    if not text:
        return None

    text_upper = text.upper()

    # Exclude bicycle parking mentions
    if re.search(r'\d+\s+(?:CLASS\s+1A\s+)?BICYCLE\s+PARKING', text_upper):
        # Check if there's also vehicle parking mentioned
        if not re.search(r'VEHICLE(?:ULAR)?\s+PARKING', text_upper):
            return None

    # Collect all potential parking counts
    parking_counts = []

    # Strategy 1: Direct digit patterns - MAXIMUM comprehensive
    digit_patterns = [
        # Standard patterns
        r'(\d+)\s*(?:ACCESSORY\s+)?(?:OFF[-\s]?STREET\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?',
        r'(\d+)\s*(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED|BASEMENT|UNDERGROUND)\s+(?:ACCESSORY\s+)?PARKING\s*(?:SPACES?|GARAGES?)',

        # "VEHICLE PARKING SPACES" (not "vehicular")
        r'(\d+)\s+VEHICLE\s+PARKING\s*SPACES?',

        # "PARKING GARAGES" instead of spaces
        r'(\d+)\s+(?:INTERIOR|EXTERIOR)?\s*PARKING\s+GARAGES?',

        # "FOR X SPACES" patterns
        r'PARKING\s+(?:FOR\s+)?(\d+)\s+(?:VEHICLES?|SPACES?)',
        r'FOR\s+(\d+)\s+(?:VEHICULAR\s+)?PARKING\s*SPACES?',
        r'SPACE\s+FOR\s+(\d+)\s+VEHICULAR\s+PARKING',

        # "WITH X ACCESSORY PARKING" patterns
        r'WITH\s+(\d+)\s+ACCESSORY\s+(?:OFF[-\s]?STREET\s+)?(?:STRUCTURED\s+)?PARKING(?:\s+SPACE)?',
        r'WITH\s+(\d+)\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+PARKING',

        # Total patterns
        r'TOTAL\s+(?:OF\s+)?(\d+)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',
        r'\(TOTAL\s+(\d+)\s+PARKING\s+SPACES',
        r'(\d+)\s+TOTAL\s+(?:INTERIOR|EXTERIOR)?\s*(?:PARKING)?',

        # Provide patterns
        r'PROVIDE(?:S)?\s+(\d+)\s+(?:ACCESSORY\s+)?PARKING',
        r'TO\s+PROVIDE.*?(\d+)\s+(?:VEHICULAR\s+)?PARKING\s*SPACES?',

        # Number before context
        r'(\d+)\s+PARKING\s+SPACES?\s+\(',
        r'(\d+)\s+ACCESSORY\s+PARKING\s*(?:SPACES?)?',
        r'(\d+)\s+VEHICULAR\s+PARKING\s*SPACES?',

        # "PARKING FOR X" patterns
        r'PARKING\s+FOR\s+(\d+)\s*(?:SPACES?|VEHICLES?)?',

        # Modified space counts
        r'(\d+)\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED|BASEMENT|UNDERGROUND)\s+ACCESSORY\s+PARKING',
        r'(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED|BASEMENT)\s+(?:ACCESSORY\s+)?PARKING\s+FOR\s+(\d+)',

        # "SPACES" without explicit "PARKING" nearby
        r'(?:STRUCTURED|SURFACE|ACCESSORY)\s+PARKING.*?FOR\s+(\d+)\s+SPACES',
        r'PARKING.*?(?:INCLUDING|WITH)\s+(\d+)\s+(?:STANDARD|ACCESSIBLE|COMPACT)',

        # Reduction patterns "reduce from X to Y"
        r'(?:REDUCE|REDUCED|REDUCING).*?(?:FROM\s+\d+\s+)?TO\s+(\d+)\s+(?:ACCESSORY\s+)?PARKING',
        r'(?:PROVIDE|PROVIDING)\s+(\d+)\s+SPACES\b',

        # Detailed breakdowns
        r'(\d+)\s+ACCESSORY\s+PARKING\s+SPACES?\s+\([^)]*\)',
        r'(\d+)\s+PARKING\s+SPACES?\s+\(INCLUDING',
        r'(\d+)\s+PARKING\s+SPACES?\s+\((?:ONE|TWO|THREE)',

        # "ONE ACCESSORY OFF-STREET PARKING SPACE" type
        r'\b(\d+)\s+ACCESSORY\s+OFF[-\s]STREET\s+PARKING\s+SPACE',

        # Interior/exterior variants
        r'(\d+)\s+INTERIOR\s+ACCESSORY\s+PARKING\s+SPACES?',
        r'ACCESSORY\s+STRUCTURED\s+PARKING.*?(\d+)\s+SPACES',

        # "X total interior" patterns
        r'(\d+)\s+TOTAL\s+INTERIOR\b',
        r'(\d+)\s+TOTAL\s+(?:INTERIOR\s+)?(?:PARKING)?.*?SPACES',

        # Includes patterns with counts
        r'INCLUDES?\s+(?:ACCESSORY\s+)?(?:STRUCTURED\s+)?PARKING.*?(\d+)',
        r'INCLUDES?\s+INTERIOR\s+PARKING\s+SPACES?\s+\((\d+)\s+TOTAL',
    ]

    for pattern in digit_patterns:
        matches = re.findall(pattern, text_upper)
        if matches:
            for m in matches:
                count = int(m) if isinstance(m, str) else int(m[0])
                if 0 <= count <= 500:
                    parking_counts.append(count)

    # Strategy 2: Written numbers with digit in parentheses - maximum patterns
    for word, num in NUMBER_WORDS.items():
        patterns = [
            # Standard word + digit patterns
            rf'{re.escape(word)}\s*\((\d+)\)\s+(?:ACCESSORY\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?',
            rf'{re.escape(word)}\s*\((\d+)\)\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+PARKING',
            rf'{re.escape(word)}\s*\((\d+)\)\s+VEHICLE\s+PARKING\s+SPACES?',

            # Reversed pattern: digit first
            rf'(\d+)\s*\({re.escape(word)}\)\s+PARKING',
            rf'FOR\s+{re.escape(word)}\s*\((\d+)\)\s+(?:VEHICULAR\s+)?PARKING',

            # Accessory variants
            rf'{re.escape(word)}\s*\((\d+)\)\s+ACCESSORY\s+(?:SURFACE\s+)?PARKING\s+SPACES?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                count = int(match.group(1))
                if 0 <= count <= 500:
                    parking_counts.append(count)

    # Strategy 3: Written numbers alone for parking (expanded)
    for word, num in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        patterns = [
            rf'\b{re.escape(word)}\s+(?:ACCESSORY\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?\b',
            rf'\b{re.escape(word)}\s+(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+PARKING\b',
            rf'WITH\s+{re.escape(word)}\s+ACCESSORY\s+PARKING(?:\s+SPACE)?',
            rf'\b{re.escape(word)}\s+ACCESSORY\s+OFF[-\s]STREET\s+PARKING\s+SPACE',
            rf'TO\s+INCLUDE\s+{re.escape(word)}\s+\((\d+)\)\s+ACCESSORY',
            rf'WITH\s+{re.escape(word)}\s+ACCESSORY\s+OFF[-\s]STREET',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                # If pattern has a capture group, use that; otherwise use the word value
                if match.groups():
                    count = int(match.group(1))
                else:
                    count = num
                if 0 <= count <= 500:
                    parking_counts.append(count)

    # Return the most commonly mentioned number, or the largest if tied
    if parking_counts:
        count_freq = Counter(parking_counts)
        most_common = count_freq.most_common(1)[0][0]
        return most_common

    return None

# Extract data from all available text fields
results = []
extraction_stats = {'units_only': 0, 'parking_only': 0, 'both': 0, 'neither': 0}
failed_extractions = []

for appeal in appeals:
    appealgrounds = appeal['appealgrounds'] or ''
    agendadescription = appeal.get('agendadescription', '') or ''
    proviso = appeal.get('proviso', '') or ''
    appeal_num = appeal['appealnumber']

    # Combine all text fields for extraction
    combined_text = f"{appealgrounds} {agendadescription} {proviso}"

    # Try extraction from combined text
    units = extract_units_maximum(combined_text)
    parking = extract_parking_maximum(combined_text)

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
        # Store some failures for analysis
        if extraction_stats['units_only'] <= 20 and 'PARKING' in appealgrounds.upper():
            failed_extractions.append({
                'appeal': appeal_num,
                'units': units,
                'text': appealgrounds[:300]
            })
    elif parking:
        extraction_stats['parking_only'] += 1
    else:
        extraction_stats['neither'] += 1

print("=" * 80)
print("MAXIMUM EXTRACTION RESULTS")
print("=" * 80)
print(f"Total appeals: {len(appeals)}")
print(f"  Both units and parking: {extraction_stats['both']} ({extraction_stats['both']/len(appeals)*100:.1f}%)")
print(f"  Units only: {extraction_stats['units_only']} ({extraction_stats['units_only']/len(appeals)*100:.1f}%)")
print(f"  Parking only: {extraction_stats['parking_only']} ({extraction_stats['parking_only']/len(appeals)*100:.1f}%)")
print(f"  Neither: {extraction_stats['neither']} ({extraction_stats['neither']/len(appeals)*100:.1f}%)")

print(f"\n✓ Successfully extracted {len(results)} projects with both unit and parking data")
print(f"  Previous best: 218 projects (22%)")
print(f"  Ultra-advanced: 272 projects (27%)")
print(f"  Maximum: {len(results)} projects ({len(results)/len(appeals)*100:.1f}%)")

if len(results) > 272:
    improvement = len(results) - 272
    print(f"  🎉 ADDITIONAL IMPROVEMENT: +{improvement} projects over ultra-advanced!")
    print(f"  🏆 TOTAL IMPROVEMENT: +{len(results) - 218} projects over original (+{(len(results) - 218) / 218 * 100:.1f}%)")
elif len(results) > 218:
    print(f"  ✓ Still improved over original: +{len(results) - 218} projects")
else:
    print(f"  ⚠️  No improvement over ultra-advanced")

# Show some failed extractions for debugging
if failed_extractions:
    print("\n" + "=" * 80)
    print("SAMPLE OF REMAINING FAILED PARKING EXTRACTIONS (for further improvement)")
    print("=" * 80)
    for i, fail in enumerate(failed_extractions[:10], 1):
        print(f"\n{i}. Appeal #{fail['appeal']} ({fail['units']} units found)")
        print(f"   {fail['text']}...")

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
print("EXTREME LOW-PARKING PROJECTS (Lowest 20)")
print("=" * 80)

for i, r in enumerate(results[:20], 1):
    pct_of_one = r['ratio'] * 100
    print(f"{i:2}. Appeal #{r['appeal_num']:20} {r['units']:3} units, {r['parking']:3} spaces (ratio: {r['ratio']:.2f} = {pct_of_one:.0f}% of 1.0 minimum)")

print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Total extracted: {len(results)} projects ({len(results)/len(appeals)*100:.1f}% of appeals)")
print(f"Low-parking (<1.0 ratio): {below_one} projects ({below_one/total*100:.1f}% of sample)")
print(f"Annual rate of below-minimum appeals: {total_below_one/num_years:.1f} per year")
print(f"\nImprovement over original (218 projects): +{len(results) - 218} projects (+{(len(results) - 218) / 218 * 100:.1f}%)")
