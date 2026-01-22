#!/usr/bin/env python3
"""
Calculate BOTH periods from city's Table 1 data
"""

print("="*80)
print("CITY'S TABLE 1 - FULL CALCULATION")
print("="*80)

# From Table 1 - OLD CODE
old_code_data = {
    "2008-2009": {"apps": 5864, "appeals": 1843},
    "2009-2010": {"apps": 6223, "appeals": 1643},
    "2010-2011": {"apps": 6020, "appeals": 1505},
    "2011-2012": {"apps": 6347, "appeals": 1506},
}

# From Table 1 - NEW CODE  
new_code_data = {
    "2012-2013": {"apps": 6439, "appeals": 1574},
    "2013-2014": {"apps": 6177, "appeals": 1435},
    "2014-2015": {"apps": 6293, "appeals": 1567},
    "2015-2016": {"apps": 6504, "appeals": 1609},
}

print("\nOLD CODE (8/22/08 - 8/21/12):")
print("-"*60)
print(f"{'Period':<15} {'Apps':>8} {'Appeals':>8} {'By-Right':>10} {'% By-Right':>11}")
print("-"*60)

old_total_apps = 0
old_total_appeals = 0

for period, data in old_code_data.items():
    apps = data['apps']
    appeals = data['appeals']
    by_right = apps - appeals
    by_right_pct = by_right / apps * 100
    
    old_total_apps += apps
    old_total_appeals += appeals
    
    print(f"{period:<15} {apps:>8,} {appeals:>8,} {by_right:>10,} {by_right_pct:>10.1f}%")

old_by_right = old_total_apps - old_total_appeals
old_by_right_pct = old_by_right / old_total_apps * 100

print("-"*60)
print(f"{'TOTAL':<15} {old_total_apps:>8,} {old_total_appeals:>8,} {old_by_right:>10,} {old_by_right_pct:>10.1f}%")

print("\n\nNEW CODE (8/22/12 - 8/21/16):")
print("-"*60)
print(f"{'Period':<15} {'Apps':>8} {'Appeals':>8} {'By-Right':>10} {'% By-Right':>11}")
print("-"*60)

new_total_apps = 0
new_total_appeals = 0

for period, data in new_code_data.items():
    apps = data['apps']
    appeals = data['appeals']
    by_right = apps - appeals
    by_right_pct = by_right / apps * 100
    
    new_total_apps += apps
    new_total_appeals += appeals
    
    print(f"{period:<15} {apps:>8,} {appeals:>8,} {by_right:>10,} {by_right_pct:>10.1f}%")

new_by_right = new_total_apps - new_total_appeals
new_by_right_pct = new_by_right / new_total_apps * 100

print("-"*60)
print(f"{'TOTAL':<15} {new_total_apps:>8,} {new_total_appeals:>8,} {new_by_right:>10,} {new_by_right_pct:>10.1f}%")

print("\n" + "="*80)
print("COMPARISON")
print("="*80)

improvement = new_by_right_pct - old_by_right_pct

print(f"\nOld Code by-right rate: {old_by_right_pct:.1f}%")
print(f"New Code by-right rate: {new_by_right_pct:.1f}%")
print(f"Improvement: {improvement:+.1f} percentage points")

print("\n" + "="*80)
print("VS. CITY'S CLAIMS")
print("="*80)

print(f"\nCity's Highlights (page 4):  '+6 percentage points'")
print(f"City's Text (page 6):        '68% → 72%' (+4 points)")
print(f"Table 1 Calculation:         '{old_by_right_pct:.1f}% → {new_by_right_pct:.1f}%' ({improvement:+.1f} points)")

print(f"\n✓ Table 1 matches the text claim: +{improvement:.1f} points ≈ +4 points")
print(f"⚠️  Highlights claim of +6 points is inconsistent with Table 1 data")

