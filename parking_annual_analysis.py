import requests
import re
from collections import defaultdict

CARTO_API = "https://phl.carto.com/api/v2/sql"

NUMBER_WORDS = {
    'ZERO': 0, 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
    'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
    'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13, 'FOURTEEN': 14, 'FIFTEEN': 15,
    'SIXTEEN': 16, 'SEVENTEEN': 17, 'EIGHTEEN': 18, 'NINETEEN': 19, 'TWENTY': 20,
    'TWENTY-ONE': 21, 'TWENTY-TWO': 22, 'TWENTY-THREE': 23, 'TWENTY-FOUR': 24,
    'TWENTY-FIVE': 25, 'TWENTY-SIX': 26, 'THIRTY': 30, 'THIRTY-FIVE': 35,
    'FORTY': 40, 'FORTY-FIVE': 45, 'FIFTY': 50, 'SIXTY': 60, 'SEVENTY': 70,
    'EIGHTY': 80, 'NINETY': 90, 'ONE HUNDRED': 100, 'TWO HUNDRED': 200
}

def extract_units_advanced(text):
    text_upper = text.upper()
    digit_patterns = [
        r'(?:TOTAL\s+(?:OF\s+)?)?(\d+)\s*DWELLING\s*UNITS?',
        r'(\d+)\s*FAMILY\s*DWELLING',
        r'(?:CONTAINING|WITH)\s+(\d+)\s+DWELLING\s+UNITS',
        r'MULTI[-\s]?FAMILY\s*\((\d+)\s*UNITS?\)',
        r'\((\d+)\s*DWELLING\s*UNITS?\)',
        r'FOR\s+(\d+)\s+DWELLING\s+UNITS',
    ]
    for pattern in digit_patterns:
        match = re.search(pattern, text_upper)
        if match:
            units = int(match.group(1))
            if 2 <= units <= 200:
                return units
    for word, num in NUMBER_WORDS.items():
        if num < 2:
            continue
        pattern = rf'{re.escape(word)}\s*\((\d+)\)\s*(?:DWELLING\s*)?UNITS?'
        match = re.search(pattern, text_upper)
        if match:
            return int(match.group(1))
    return None

def extract_parking_advanced(text):
    text_upper = text.upper()
    digit_patterns = [
        r'(\d+)\s*(?:ACCESSORY\s+)?(?:OFF[-\s]?STREET\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?',
        r'(\d+)\s*(?:INTERIOR|EXTERIOR|SURFACE|STRUCTURED)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',
        r'PARKING\s+(?:FOR\s+)?(\d+)\s+(?:VEHICLES?|SPACES?)',
        r'WITH\s+(\d+)\s+ACCESSORY\s+(?:OFF[-\s]?STREET\s+)?PARKING',
        r'TOTAL\s+(?:OF\s+)?(\d+)\s+(?:ACCESSORY\s+)?PARKING\s*SPACES?',
    ]
    parking_counts = []
    for pattern in digit_patterns:
        matches = re.findall(pattern, text_upper)
        if matches:
            for m in matches:
                count = int(m) if isinstance(m, str) else int(m[0])
                if 0 <= count <= 500:
                    parking_counts.append(count)
    for word, num in NUMBER_WORDS.items():
        pattern = rf'{re.escape(word)}\s*\((\d+)\)\s+(?:ACCESSORY\s+)?(?:VEHICLE\s+|VEHICULAR\s+)?PARKING\s*SPACES?'
        match = re.search(pattern, text_upper)
        if match:
            count = int(match.group(1))
            if 0 <= count <= 500:
                parking_counts.append(count)
    if parking_counts:
        return max(parking_counts)
    return None

print("Fetching with year data...")

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

by_year_low = defaultdict(int)
by_year_medium = defaultdict(int)
by_year_high = defaultdict(int)
by_year_all = defaultdict(int)

for appeal in data['rows']:
    text = appeal['appealgrounds']
    year = int(appeal['year'])
    
    units = extract_units_advanced(text)
    parking = extract_parking_advanced(text)
    
    if units and parking:
        ratio = parking / units
        if ratio <= 5.0:
            by_year_all[year] += 1
            if ratio < 0.5:
                by_year_low[year] += 1
            elif ratio < 1.0:
                by_year_medium[year] += 1
            else:
                by_year_high[year] += 1

print("=" * 80)
print("LOW-PARKING MULTIFAMILY APPEALS BY YEAR")
print("=" * 80)
print(f"{'Year':<6} {'<0.5 ratio':<12} {'0.5-0.99':<12} {'≥1.0 ratio':<12} {'Total':<8}")
print("-" * 80)

total_low = 0
total_medium = 0
total_high = 0
total_all = 0

for year in sorted(by_year_all.keys()):
    low = by_year_low[year]
    med = by_year_medium[year]
    high = by_year_high[year]
    total = by_year_all[year]
    print(f"{year:<6} {low:<12} {med:<12} {high:<12} {total:<8}")
    total_low += low
    total_medium += med
    total_high += high
    total_all += total

years = len(by_year_all)
print("-" * 80)
print(f"{'TOTAL':<6} {total_low:<12} {total_medium:<12} {total_high:<12} {total_all:<8}")
print(f"{'AVG':<6} {total_low/years:<12.1f} {total_medium/years:<12.1f} {total_high/years:<12.1f} {total_all/years:<12.1f}")

print("\n" + "=" * 80)
print("KEY STATISTICS")
print("=" * 80)
print(f"Low-parking (<0.5 ratio): {total_low} appeals over {years} years = {total_low/years:.1f} per year")
print(f"Medium (<1.0 ratio): {total_medium} appeals over {years} years = {total_medium/years:.1f} per year")
print(f"Below-minimum (<1.0 total): {total_low + total_medium} appeals = {(total_low + total_medium)/years:.1f} per year")
print(f"Total extracted: {total_all} appeals = {total_all/years:.1f} per year")
print(f"\nPercentage below 1.0 ratio: {(total_low + total_medium)/total_all*100:.1f}%")

