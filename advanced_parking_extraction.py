import requests
import re
from collections import defaultdict

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
    'THIRTY-FIVE': 35, 'THIRTY-NINE': 39, 'FORTY': 40, 'FORTY-FIVE': 45,
    'FORTY-SIX': 46, 'FORTY-NINE': 49, 'FIFTY': 50, 'SIXTY': 60, 'SEVENTY': 70,
    'EIGHTY': 80, 'NINETY': 90, 'ONE HUNDRED': 100, 'TWO HUNDRED': 200
}

print("Fetching multifamily + parking appeals...")

query = """
SELECT appealgrounds, appealnumber, agendadescription
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

def extract_units_advanced(text):
    """Extract dwelling unit count with comprehensive patterns"""
    text_upper = text.upper()
    
    # Strategy 1: Direct digit patterns (most reliable)
    digit_patterns = [
        r'(?:TOTAL\s+(?:OF\s+)?)?(\d+)\s*DWELLING\s*UNITS?',
        r'(\d+)\s*FAMILY\s*DWELLING',
        r'(?:CONTAINING|WITH)\s+(\d+)\s+DWELLING\s+UNITS',
        r'MULTI[-\s]?FAMILY\s*\((\d+)\s*UNITS?\)',
        r'\((\d+)\s*DWELLING\s*UNITS?\)',
        r'(?:TOTAL\s+)?(\d+)\s*UNITS?\)',
        r'FOR\s+(\d+)\s+DWELLING\s+UNITS',
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
        # Look for "WORD (DIGIT) UNITS" or "WORD (DIGIT) DWELLING"
        pattern = rf'{re.escape(word)}\s*\((\d+)\)\s*(?:DWELLING\s*)?UNITS?'
        match = re.search(pattern, text_upper)
        if match:
            return int(match.group(1))
    
    # Strategy 3: Written numbers alone (less reliable, need context)
    for word, num in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):  # Longest first
        if num < 2:
            continue
        # Must have "units" or "dwelling" nearby
        pattern = rf'{re.escape(word)}\s+(?:DWELLING\s+)?UNITS?\b'
        if re.search(pattern, text_upper):
            return num
    
    return None

def extract_parking_advanced(text):
    """Extract parking space count with comprehensive patterns"""
    text_upper = text.upper()
    
    # Strategy 1: Direct digit patterns
    digit_patterns = [
        r'(\d+)\s*(?:ACCESSORY\s+)?(?:OFF[-\s]?STREET\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?',
        r'(\d+)\s*(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',
        r'PARKING\s+(?:FOR\s+)?(\d+)\s+(?:VEHICLES?|SPACES?)',
        r'WITH\s+(\d+)\s+ACCESSORY\s+(?:OFF[-\s]?STREET\s+)?PARKING',
        r'TOTAL\s+(?:OF\s+)?(\d+)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',
        r'\(TOTAL\s+(\d+)\s+PARKING\s+SPACES',
        r'(\d+)\s+PARKING\s+SPACES?\s+\(',
        r'PROVIDE(?:S)?\s+(\d+)\s+(?:ACCESSORY\s+)?PARKING',
    ]
    
    parking_counts = []
    for pattern in digit_patterns:
        matches = re.findall(pattern, text_upper)
        if matches:
            for m in matches:
                count = int(m) if isinstance(m, str) else int(m[0])
                if 0 <= count <= 500:
                    parking_counts.append(count)
    
    # Strategy 2: Written numbers with digit in parentheses
    for word, num in NUMBER_WORDS.items():
        pattern = rf'{re.escape(word)}\s*\((\d+)\)\s+(?:ACCESSORY\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?'
        match = re.search(pattern, text_upper)
        if match:
            count = int(match.group(1))
            if 0 <= count <= 500:
                parking_counts.append(count)
    
    # Strategy 3: Written numbers alone for parking
    for word, num in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        pattern = rf'{re.escape(word)}\s+(?:ACCESSORY\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?\b'
        if re.search(pattern, text_upper):
            if 0 <= num <= 500:
                parking_counts.append(num)
    
    # Return the most commonly mentioned number, or the largest if tied
    if parking_counts:
        # Most parking descriptions mention the count once; if multiple, take max
        return max(parking_counts)
    
    return None

# Extract data from appealgrounds
results = []
extraction_stats = {'units_only': 0, 'parking_only': 0, 'both': 0, 'neither': 0}
extraction_details = []

for appeal in appeals:
    text = appeal['appealgrounds']
    agenda = appeal.get('agendadescription', '')
    appeal_num = appeal['appealnumber']
    
    # Try main text first
    units = extract_units_advanced(text)
    parking = extract_parking_advanced(text)
    
    # If parking not found in main text, try agenda description
    if units and not parking and agenda:
        parking = extract_parking_advanced(agenda)
    
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
                'text': text[:200]
            })
    elif units:
        extraction_stats['units_only'] += 1
        # Store first few failures for debugging
        if extraction_stats['units_only'] <= 5:
            extraction_details.append({
                'status': 'units_only',
                'units': units,
                'appeal_num': appeal_num,
                'text': text[:300]
            })
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
if len(results) > 60:
    print(f"  (Improvement from 60 to {len(results)} = {len(results)/60:.1f}x better)")

# Show a few examples where we found units but not parking (for debugging)
if extraction_details:
    print("\n" + "=" * 80)
    print("DEBUGGING: Examples where parking extraction failed")
    print("=" * 80)
    for detail in extraction_details:
        print(f"\nAppeal #{detail['appeal_num']}: {detail['units']} units")
        print(f"  {detail['text'][:250]}...")

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

# Show comprehensive examples
print("\n" + "=" * 80)
print("SAMPLE OF LOW-PARKING PROJECTS (<0.5 spaces/unit)")
print("=" * 80)

low_ratio = [r for r in results if r['ratio'] < 0.5]
print(f"Total: {len(low_ratio)} projects\n")

for i, r in enumerate(low_ratio[:20], 1):
    print(f"{i}. Appeal #{r['appeal_num']}: {r['units']} units, {r['parking']} spaces (ratio: {r['ratio']:.2f})")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total extracted: {len(results)} projects")
print(f"Low-parking (<1.0 ratio): {below_one} projects ({below_one/total*100:.1f}%)")
print(f"Extraction rate: {len(results)/len(appeals)*100:.1f}% of all multifamily+parking appeals")

