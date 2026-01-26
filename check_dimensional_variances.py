#!/usr/bin/env python3
"""
Check if height variances are captured in dimensional variance or FAR categories
"""

import requests

CARTO_API = "https://phl.carto.com/api/v2/sql"

print("=" * 100)
print("CHECKING HOW HEIGHT VARIANCES ARE CAPTURED")
print("=" * 100)
print()

# Use SQL to count directly rather than fetching all data
searches = {
    'dimensional': "appealgrounds ILIKE '%dimensional%'",
    'FAR (exact)': "appealgrounds ~* '\\bFAR\\b'",
    'floor area ratio': "appealgrounds ILIKE '%floor area ratio%' OR appealgrounds ILIKE '%floor-area-ratio%'",
    'building envelope': "appealgrounds ILIKE '%building envelope%'",
    'height (any mention)': "appealgrounds ILIKE '%height%'",
    'stories (X stories)': "appealgrounds ~* '\\d+\\s*stor(y|ies)'",
    'maximum height': "appealgrounds ILIKE '%maximum height%' OR appealgrounds ILIKE '%max height%'",
    'maximum building height': "appealgrounds ILIKE '%maximum building height%'",
    'building height': "appealgrounds ILIKE '%building height%'",
}

results = {}

for term, condition in searches.items():
    query = f"""
        SELECT COUNT(*) as count
        FROM appeals
        WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND createddate >= '2013-01-01'
            AND createddate < '2026-01-01'
            AND ({condition})
    """

    try:
        response = requests.get(CARTO_API, params={'q': query}, timeout=30)
        data = response.json()
        count = data['rows'][0]['count']
        results[term] = count
        print(f"✓ {term}: {count:,}")
    except Exception as e:
        print(f"✗ {term}: Error - {e}")
        results[term] = 0

print()
print("=" * 100)
print("FREQUENCY TABLE")
print("=" * 100)
print()

# Get total for percentages
total_query = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
        AND createddate >= '2013-01-01'
        AND createddate < '2026-01-01'
"""
response = requests.get(CARTO_API, params={'q': total_query}, timeout=30)
total_appeals = response.json()['rows'][0]['count']

print(f"Total appeals: {total_appeals:,}")
print()
print(f"| Term | Appeals | % of Total | Per Year |")
print(f"|------|---------|------------|----------|")
for term, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
    pct = (count / total_appeals) * 100
    per_year = count / 13
    print(f"| {term:25} | {count:7,} | {pct:9.1f}% | {per_year:8.0f} |")

print()
print()

# Get examples for most common terms
print("=" * 100)
print("EXAMPLES")
print("=" * 100)
print()

for term, condition in [('dimensional', "appealgrounds ILIKE '%dimensional%'"),
                         ('height', "appealgrounds ILIKE '%height%'"),
                         ('FAR', "appealgrounds ~* '\\bFAR\\b'")]:
    query = f"""
        SELECT appealgrounds
        FROM appeals
        WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
            AND createddate >= '2013-01-01'
            AND createddate < '2026-01-01'
            AND ({condition})
        LIMIT 3
    """

    try:
        response = requests.get(CARTO_API, params={'q': query}, timeout=30)
        examples = response.json()['rows']

        print(f"**{term.upper()} examples:**")
        print()
        for i, ex in enumerate(examples, 1):
            text = ex['appealgrounds'][:300]
            print(f"{i}. {text}...")
            print()
    except Exception as e:
        print(f"Error fetching {term} examples: {e}")
        print()
