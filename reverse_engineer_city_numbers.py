#!/usr/bin/env python3
"""
Reverse engineer: If city has 68% by-right with ~6,497 appeals, what's the denominator?
"""

print("="*80)
print("REVERSE ENGINEERING CITY'S NUMBERS")
print("="*80)

# City's numbers
appeals = 6497
by_right_pct = 68  # They say 68% by-right

# Reverse calculate
# If by_right_pct = permits / (permits + appeals)
# Then: permits = by_right_pct * (permits + appeals)
# permits = by_right_pct * permits + by_right_pct * appeals
# permits - by_right_pct * permits = by_right_pct * appeals
# permits * (1 - by_right_pct) = by_right_pct * appeals
# permits = (by_right_pct * appeals) / (1 - by_right_pct)

permits = (by_right_pct * appeals) / (100 - by_right_pct)
total = permits + appeals

print(f"\nIf city found 68% by-right with {appeals:,} appeals:")
print(f"  Required permits: {permits:,.0f}")
print(f"  Total applications: {total:,.0f}")
print(f"  Variance rate: {appeals/total*100:.1f}%")

print(f"\nBut Table 1 shows:")
print(f"  Total applications: ~24,454")
print(f"  Our calculation shows: {total:,.0f}")
print(f"  Discrepancy: {24454 - total:,.0f}")

print("\n" + "="*80)
print("HYPOTHESIS: City's 68% might be calculated differently")
print("="*80)

# Maybe they calculate: appeals / total_apps = 32%?
print(f"\nIf appeals/total = 32% (inverse of 68% by-right):")
print(f"  With {appeals} appeals: total = {appeals/0.32:,.0f}")
print(f"  Permits = {appeals/0.32 - appeals:,.0f}")

# Or maybe there's rounding/averaging across years?
print(f"\n" + "="*80)
print("YEAR-BY-YEAR FROM CITY'S TABLE 1")  
print("="*80)

# From Table 1 in the report
city_data = {
    "2008-2009": {"apps": 5864, "appeals": 1843},
    "2009-2010": {"apps": 6223, "appeals": 1643},
    "2010-2011": {"apps": 6020, "appeals": 1505},
    "2011-2012": {"apps": 6347, "appeals": 1506},
}

print(f"\n{'Period':<15} {'Apps':>8} {'Appeals':>8} {'Appeals %':>10} {'By-Right %':>11}")
print("-"*60)

total_apps = 0
total_appeals = 0

for period, data in city_data.items():
    apps = data['apps']
    appeals = data['appeals']
    appeals_pct = appeals / apps * 100
    by_right_pct = (apps - appeals) / apps * 100
    
    total_apps += apps
    total_appeals += appeals
    
    print(f"{period:<15} {apps:>8,} {appeals:>8,} {appeals_pct:>9.1f}% {by_right_pct:>10.1f}%")

overall_appeals_pct = total_appeals / total_apps * 100
overall_by_right = (total_apps - total_appeals) / total_apps * 100

print("-"*60)
print(f"{'TOTAL':<15} {total_apps:>8,} {total_appeals:>8,} {overall_appeals_pct:>9.1f}% {overall_by_right:>10.1f}%")

print(f"\nCity says: 68% by-right")
print(f"Table calculation: {overall_by_right:.1f}% by-right")
print(f"Difference: {overall_by_right - 68:.1f} points")

print("\n💡 INSIGHT: City might be using different denominator than 'Completed Apps'")
print("   OR they're including incomplete/withdrawn applications")

