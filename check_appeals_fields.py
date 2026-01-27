import requests
import json

CARTO_API = "https://phl.carto.com/api/v2/sql"

# Get a sample record with all fields
query = """
SELECT *
FROM appeals
WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
    AND appealgrounds ILIKE '%parking%'
    AND appealgrounds ~* '\\d+\\s*(?:dwelling|unit)'
LIMIT 1
"""

response = requests.get(CARTO_API, params={'q': query}, timeout=60)
data = response.json()

print("SAMPLE RECORD FIELDS:")
print("=" * 80)
if 'rows' in data and data['rows']:
    record = data['rows'][0]
    for key in sorted(record.keys()):
        print(f"  {key}")
    
    print("\n\nSAMPLE VALUES (non-empty fields):")
    print("=" * 80)
    for key, value in sorted(record.items()):
        if value and key != 'the_geom':  # Skip empty and geometry fields
            val_str = str(value)
            if len(val_str) > 300:
                val_str = val_str[:300] + "..."
            print(f"\n{key}:")
            print(f"  {val_str}")
