import requests
import re

CARTO_API = "https://phl.carto.com/api/v2/sql"

# Get sample of appeals that mention units AND parking but where we failed to extract parking count
query = """
SELECT appealgrounds
FROM appeals
WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
    AND createddate >= '2013-01-01'
    AND appealgrounds ~* '\\d+\\s*(?:dwelling|family|unit)'
    AND appealgrounds ILIKE '%parking%'
LIMIT 100
"""

response = requests.get(CARTO_API, params={'q': query}, timeout=60)
data = response.json()

def extract_units(text):
    text_upper = text.upper()
    patterns = [
        r'(\d+)\s*DWELLING\s*UNITS?',
        r'(\d+)\s*FAMILY\s*DWELLING',
        r'(\d+)\s*UNITS?\)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            return int(match.group(1))
    return None

def extract_parking(text):
    text_upper = text.upper()
    patterns = [
        r'(\d+)\s*(?:ACCESSORY\s+)?(?:OFF[-\s]?STREET\s+)?(?:VEHICLE\s+)?PARKING\s*SPACES?',
        r'(\d+)\s*VEHICLE\s+PARKING',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text_upper)
        if matches:
            return max([int(m) if isinstance(m, str) else int(m[0]) for m in matches])
    return None

print("EXAMPLES WHERE WE FOUND UNITS BUT NOT PARKING NUMBERS:")
print("=" * 80)

count = 0
for appeal in data['rows'][:30]:
    text = appeal['appealgrounds']
    units = extract_units(text)
    parking = extract_parking(text)
    
    if units and not parking:
        count += 1
        print(f"\n{count}. Units: {units}")
        print(f"   Text: {text[:300]}...")
        
        # Show what parking-related words appear
        text_upper = text.upper()
        parking_keywords = []
        if 'PARKING SPACE' in text_upper:
            parking_keywords.append('mentions "parking space"')
        if 'PARKING' in text_upper and 'SPACE' not in text_upper:
            parking_keywords.append('mentions "parking" (no count)')
        if 'VARIANCE' in text_upper and 'PARKING' in text_upper:
            parking_keywords.append('requests parking variance')
            
        if parking_keywords:
            print(f"   → {', '.join(parking_keywords)}")
        
        if count >= 15:
            break

