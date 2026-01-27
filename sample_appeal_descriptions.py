import requests
import random

CARTO_API = "https://phl.carto.com/api/v2/sql"

# Get sample of multifamily + parking appeals
query = """
SELECT appealgrounds, appealnumber
FROM appeals
WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
    AND createddate >= '2013-01-01'
    AND (appealgrounds ~* '\\d+\\s*(?:dwelling|family|unit)'
         OR appealgrounds ~* 'duplex|triplex|fourplex|sixplex'
         OR appealgrounds ILIKE '%multi%family%')
    AND appealgrounds ILIKE '%parking%'
LIMIT 50
"""

response = requests.get(CARTO_API, params={'q': query}, timeout=60)
data = response.json()

print("SAMPLE OF 50 MULTIFAMILY + PARKING APPEAL DESCRIPTIONS:")
print("=" * 80)

appeals = data['rows']
random.shuffle(appeals)

for i, appeal in enumerate(appeals[:20], 1):
    text = appeal['appealgrounds']
    num = appeal['appealnumber']
    
    # Truncate if very long
    if len(text) > 400:
        text = text[:400] + "..."
    
    print(f"\n{i}. Appeal #{num}")
    print(f"   {text}")
    print()

