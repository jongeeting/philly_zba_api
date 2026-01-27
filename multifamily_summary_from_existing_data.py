#!/usr/bin/env python3
"""
Multifamily variance analysis using existing data

Based on our complete variance analysis, summarize findings
specifically relevant to multifamily housing.
"""

print("=" * 100)
print("MULTIFAMILY HOUSING BARRIERS - SUMMARY FROM EXISTING ANALYSIS")
print("=" * 100)
print()

# Data from our complete variance analysis
total_appeals = 16954
dwelling_unit_appeals = 921  # Appeals explicitly mentioning dwelling units
years = 13

print("OVERVIEW")
print("-" * 100)
print()
print(f"Total variance appeals (2013-2025): {total_appeals:,}")
print(f"Appeals explicitly mentioning dwelling units: {dwelling_unit_appeals:,} ({dwelling_unit_appeals/total_appeals*100:.1f}%)")
print(f"Per year: {dwelling_unit_appeals/years:.1f}")
print()

print("=" * 100)
print("DWELLING UNIT THRESHOLDS (from detailed analysis)")
print("=" * 100)
print()

# From our earlier analysis
unit_data = [
    (1, 6),
    (2, 22),
    (3, 247),
    (4, 108),
    (5, 43),
    (6, 58),
]

print(f"{'Units':>6} {'Appeals':>8} {'Cumulative':>12} {'% Resolved':>12}")
print("-" * 45)

cumulative = 0
total_with_units = sum(count for _, count in unit_data)

for units, count in unit_data:
    cumulative += count
    pct = (cumulative / total_with_units) * 100
    unit_name = {1: "Single", 2: "Duplex", 3: "Triplex", 4: "Fourplex", 5: "5-unit", 6: "Sixplex"}.get(units, f"{units}-unit")
    print(f"{units:>6} {count:>8,} {cumulative:>12,} {pct:>11.1f}%")

print()
print("KEY THRESHOLDS:")
print()

duplex = sum(count for u, count in unit_data if u <= 2)
triplex = sum(count for u, count in unit_data if u <= 3)
fourplex = sum(count for u, count in unit_data if u <= 4)
sixplex = sum(count for u, count in unit_data if u <= 6)

print(f"  Allow duplexes (≤2 units):    {duplex:,} appeals ({duplex/total_with_units*100:.1f}%)")
print(f"  Allow triplexes (≤3 units):   {triplex:,} appeals ({triplex/total_with_units*100:.1f}%)")
print(f"  Allow fourplexes (≤4 units):  {fourplex:,} appeals ({fourplex/total_with_units*100:.1f}%)")
print(f"  Allow sixplexes (≤6 units):   {sixplex:,} appeals ({sixplex/total_with_units*100:.1f}%)")
print()

print("=" * 100)
print("TOP VARIANCE GENERATORS AFFECTING MULTIFAMILY")
print("=" * 100)
print()

# From our complete analysis
variance_generators = [
    ("Roof decks", 4137, 24.4),
    ("Parking", 3521, 20.8),
    ("Commercial", 3737, 22.1),
    ("Height", 1259, 7.4),
    ("Dwelling units", 921, 5.4),
]

print(f"{'Variance Type':25} {'Total Appeals':>15} {'% of All':>10} {'Per Year':>10}")
print("-" * 70)

for var_type, count, pct in variance_generators:
    per_year = count / years
    print(f"{var_type:25} {count:>15,} {pct:>9.1f}% {per_year:>10.1f}")

print()
print("**Note:** These affect ALL development, but are particularly problematic for")
print("multifamily housing which often needs:")
print("  - Roof decks for amenity space")
print("  - Reduced parking (transit-oriented development)")
print("  - 4+ stories for viability")
print("  - More than single-family density")
print()

print("=" * 100)
print("MULTIFAMILY IN TOP ZONING DISTRICTS")
print("=" * 100)
print()

# From our zoning district analysis
districts = [
    ("RSA-5", "Residential Single-Family Attached", 6892, "Technically single-family, but conversions common"),
    ("RM-1", "Residential Multi-family", 2074, "EXPLICIT multifamily zone"),
    ("CMX-2", "Commercial Mixed-Use", 1757, "Allows multifamily mixed-use"),
    ("RSA-3", "Residential Single-Family Attached", 1250, "Technically single-family, but conversions common"),
]

print(f"{'District':10} {'Type':40} {'Appeals':>10} {'Notes':30}")
print("-" * 100)

for code, type_desc, appeals, notes in districts:
    print(f"{code:10} {type_desc:40} {appeals:>10,} {notes:30}")

print()
print("**Key insight:** RM-1 is the PRIMARY multifamily zone and has 2,074 appeals (12.4% of total)")
print("This shows that even zones DESIGNED for multifamily require variances frequently")
print()

print("=" * 100)
print("RM-1 (MULTIFAMILY ZONE) DETAILED ANALYSIS")
print("=" * 100)
print()

# From our earlier output
rm1_sample_data = {
    'total_2022_2025': 312,
    'appeals_2013_2025': 2074,
    # Note: We'd need to re-run to get variance breakdowns for RM-1 specifically
}

print(f"RM-1 total appeals (2013-2025): {rm1_sample_data['appeals_2013_2025']:,}")
print(f"Average per year: {rm1_sample_data['appeals_2013_2025']/years:.1f}")
print()
print("**Trend noted:** RM-1 had a sharp drop after 2017 (119/year → 71/year)")
print("This may indicate:")
print("  - A zoning change that made some projects by-right")
print("  - Data quality issues")
print("  - Reduced multifamily development pressure")
print()

print("=" * 100)
print("REFORM IMPACT ON MULTIFAMILY HOUSING")
print("=" * 100)
print()

print("SCENARIO 1: Allow Fourplexes by-right (≤4 units)")
print(f"  Unit-related appeals eliminated: {fourplex:,}")
print(f"  Per year: {fourplex/years:.1f}")
print(f"  % of unit-specific appeals: {fourplex/total_with_units*100:.1f}%")
print()

print("SCENARIO 2: Fourplex + No Parking + 4 Stories + Roof Decks")
print("  This is our 'Tier 2' reform package")
print(f"  Total appeals eliminated: ~661/year")
print(f"  This includes:")
print(f"    - {fourplex/years:.1f}/year from allowing fourplexes")
print(f"    - ~271/year from eliminating parking minimums")
print(f"    - ~97/year from allowing 4 stories")
print(f"    - ~318/year from allowing roof decks")
print("  (Note: Some overlap between categories)")
print()

print("SCENARIO 3: Focus on RM-1 (Multifamily Zone)")
print(f"  Current: {rm1_sample_data['appeals_2013_2025']/years:.1f} appeals/year in RM-1")
print("  If we fixed RM-1 rules (parking, height, roof decks):")
print(f"    Estimated 40-50% reduction → ~40-50 appeals/year eliminated")
print()

print("=" * 100)
print("SUMMARY: MULTIFAMILY HOUSING BARRIERS")
print("=" * 100)
print()

print("THE PROBLEM:")
print()
print(f"  1. Even multifamily zones (RM-1) require 160 variances/year")
print(f"  2. Single-family zones (RSA-5) block conversions (530 appeals/year)")
print(f"  3. Dwelling unit limits force 71 variances/year for density")
print(f"  4. Parking minimums add 271 variances/year (many for multifamily)")
print(f"  5. Height limits add 97 variances/year (many for 4+ story multifamily)")
print()

print("THE SOLUTION:")
print()
print(f"  1. Allow fourplexes by-right → eliminates {fourplex/years:.0f} unit-related appeals/year")
print(f"  2. Eliminate parking minimums → eliminates 271 appeals/year")
print(f"  3. Allow 4 stories → eliminates 97 appeals/year")
print(f"  4. Allow roof decks → eliminates 318 appeals/year")
print()
print(f"  COMBINED: ~598 appeals/year eliminated (46% of total)")
print()

print("WHY THIS MATTERS FOR MULTIFAMILY:")
print()
print("  • Small multifamily (2-4 units) is 'naturally affordable' housing")
print("  • Doesn't require subsidies or government programs")
print("  • Matches Philadelphia's historic building patterns (rowhouse conversions)")
print("  • Current rules force most small multifamily through variance process")
print("  • Costs $5,000-15,000 and 3-6 months per variance")
print("  • Makes small-scale development economically marginal")
print()

print("THE ASK:")
print()
print("  1. Allow fourplexes by-right in RSA and RM zones")
print("  2. Eliminate parking minimums (let market decide)")
print("  3. Allow 4 stories in residential zones")
print("  4. Allow roof decks by-right (common amenity)")
print()
print("  Result: 46% fewer variance appeals, faster multifamily production")
print()
print("=" * 100)
