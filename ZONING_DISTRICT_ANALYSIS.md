# Variance Appeals by Zoning District (2024 Sample)

## Overview

Successfully linked 1,060 variance appeals from 2024 to their zoning districts using spatial joins. This allows us to see which zoning categories generate the most variance appeals.

**Important Note:** The variance "rates" shown below use polygon record counts as the denominator, not actual parcel counts. Therefore, **focus on the absolute appeal counts** rather than the calculated rates. To get true variance rates, we would need to join to the full PWD parcels dataset.

---

## Appeals by Individual Zoning District (2024)

**Top 15 zoning districts by appeal volume:**

| Rank | Zoning Code | Zoning Group | 2024 Appeals | Notes |
|------|-------------|--------------|--------------|-------|
| 1 | **RSA-5** | Residential/Residential Mixed-Use | 446 | By far the highest |
| 2 | **RM-1** | Residential/Residential Mixed-Use | 109 | |
| 3 | **CMX-2** | Commercial/Commercial Mixed-Use | 100 | |
| 4 | **RSA-3** | Residential/Residential Mixed-Use | 89 | |
| 5 | **CMX-1** | Commercial/Commercial Mixed-Use | 57 | |
| 6 | **I-2** | Industrial/Industrial Mixed-Use | 41 | Surprisingly high for industrial |
| 7 | **CMX-2.5** | Commercial/Commercial Mixed-Use | 33 | |
| 8 | **ICMX** | Industrial/Industrial Mixed-Use | 24 | |
| 9 | **CMX-5** | Commercial/Commercial Mixed-Use | 21 | |
| 10 | **RSA-2** | Residential/Residential Mixed-Use | 21 | |
| 11 | **RSD-3** | Residential/Residential Mixed-Use | 15 | |
| 12 | **CMX-3** | Commercial/Commercial Mixed-Use | 15 | |
| 13 | **RTA-1** | Residential/Residential Mixed-Use | 14 | |
| 14 | **CA-1** | Commercial/Commercial Mixed-Use | 12 | |
| 15 | **CMX-4** | Commercial/Commercial Mixed-Use | 10 | |

---

## Appeals by Zoning Group (2024)

| Zoning Group | 2024 Appeals | % of Total |
|--------------|--------------|------------|
| **Residential/Residential Mixed-Use** | 713 | 67.3% |
| **Commercial/Commercial Mixed-Use** | 257 | 24.2% |
| **Industrial/Industrial Mixed-Use** | 78 | 7.4% |
| **Special Purpose** | 12 | 1.1% |
| **Total** | 1,060 | 100% |

---

## Key Findings

### 1. RSA-5 Dominates Variance Appeals

**RSA-5 generated 446 appeals in 2024 - 42% of all variance appeals in the sample.**

This single zoning district is responsible for nearly half of all variance cases. Understanding what makes RSA-5 so problematic is critical:

- **What is RSA-5?** Residential Single-Family Attached district (typically rowhouses)
- **Why so many variances?** Likely due to:
  - Restrictive height limits (35 feet / 3 stories typical)
  - Parking requirements
  - Lot coverage restrictions
  - Limitations on accessory structures (roof decks)
  - Density restrictions

**Policy implication:** Reforms targeting RSA-5 specifically could eliminate a huge portion of variance appeals.

### 2. Residential Zones Drive Most Variances

Residential/residential mixed-use zones account for **67.3% of all variance appeals**, despite Philadelphia being a mixed-use city. This suggests:
- Residential zoning rules are too restrictive
- The 2012 zoning reform didn't go far enough for residential zones
- "Missing middle" housing reforms would have outsized impact

### 3. Commercial Mixed-Use Zones Also Significant

CMX zones (CMX-1, CMX-2, CMX-2.5, CMX-3, CMX-4, CMX-5) collectively generated **236 appeals** in 2024 (22.3% of total). These are supposed to be flexible mixed-use districts, yet they still require many variances.

### 4. Industrial Zones Have Variance Issues Too

78 appeals (7.4%) came from industrial/industrial mixed-use zones. This is notable because:
- Industrial zones typically have fewer restrictions
- Suggests even "permissive" zones have problems
- May indicate conversion/adaptive reuse barriers

---

## Which Reforms Would Help Which Districts?

Based on our earlier variance generator analysis, here's how reforms would likely impact different zoning districts:

### RSA-5 (446 appeals/year)
**Most likely variance drivers:**
- Roof decks (24.4% of all appeals) - RSA zones likely restrict accessory structures
- Height (7.4% of appeals) - RSA zones often cap at 35 feet (3 stories)
- Dwelling units (5.4% of appeals) - RSA-5 may limit conversions or additions
- Parking (20.8% of appeals) - Parking minimums in residential zones

**Recommended reforms for RSA-5:**
1. Allow roof decks by-right
2. Increase height limit to 45 feet (4 stories)
3. Allow duplexes/fourplexes by-right
4. Eliminate parking minimums

**Estimated impact:** Could eliminate 50%+ of RSA-5 variances (~200-225 appeals/year)

### CMX Districts (236 appeals/year total)
**Most likely variance drivers:**
- Commercial use restrictions (22.1% of all appeals)
- Parking (20.8% of appeals)
- Roof decks (24.4% of appeals)
- Height (7.4% of appeals)

**Recommended reforms for CMX:**
1. Expand allowed commercial uses
2. Eliminate parking minimums
3. Allow roof decks by-right
4. Increase height limits

**Estimated impact:** Could eliminate 40-50% of CMX variances (~95-120 appeals/year)

### RM-1 (109 appeals/year)
**Most likely variance drivers:**
- Dwelling unit restrictions (RM = Residential Multi-family, but may still be too restrictive)
- Height limits
- Parking
- Lot coverage

**Recommended reforms for RM-1:**
1. Allow larger multi-family buildings (increase unit cap)
2. Increase height limits
3. Eliminate parking minimums
4. Relax lot coverage rules

**Estimated impact:** Could eliminate 40-50% of RM-1 variances (~45-55 appeals/year)

---

## Next Steps for Analysis

### 1. Expand to Full 2013-2025 Period
Currently analyzing only 2024. Need to:
- Run spatial join for all 16,954 appeals (may need to batch by year)
- Identify trends over time by district
- See if certain districts are getting worse

### 2. Break Down Variance Types by District
Link our variance generator analysis (roof decks, parking, height, etc.) to specific zoning districts:
- Which variance types are most common in RSA-5?
- Do CMX districts have different patterns than RSA districts?
- Are height variances concentrated in specific districts?

### 3. Calculate True Variance Rates
Get actual parcel counts per district (from PWD parcels dataset) to calculate:
- Variance rate = Appeals / Total parcels in district
- This will show which districts have the highest per-parcel variance burden

### 4. Geographic/Council District Analysis
- Map variance appeals by neighborhood
- Calculate which City Council members' districts have the most variances
- Identify geographic patterns (Center City vs neighborhoods)

### 5. Reform Targeting
Simulate reform impacts by district:
- "If we allow roof decks in RSA-5, how many appeals eliminated?"
- "If we increase CMX height limits, what's the impact?"
- Create district-specific reform recommendations

---

## Questions to Answer

1. **Why is RSA-5 so problematic?**
   - Is it the most common residential zone? (need parcel counts)
   - Or does it have particularly restrictive rules?
   - Or both?

2. **Can we reform just a few districts and solve most problems?**
   - If RSA-5 reforms eliminated 50% of its variances, that's 225 appeals/year
   - Add CMX reforms (120 appeals/year) = 345 appeals/year eliminated
   - That's 32% of all appeals from just fixing 2 district types

3. **Do newer vs older neighborhoods have different patterns?**
   - Are variances concentrated in historic neighborhoods?
   - Or is it newer development areas?

4. **What do successful districts look like?**
   - Which districts have LOW variance rates?
   - What can we learn from them?

---

## Methodology Notes

**Data:**
- 1,060 variance appeals from 2024
- Linked to 30 zoning districts via spatial join (ST_Within)
- Zoning data from `zoning_basedistricts` CARTO table

**Join method:**
- `ST_Within(appeals.the_geom, zoning.the_geom)`
- Successful match rate: 1,060 of 1,071 2024 appeals (98.9%)

**Limitations:**
- Polygon counts used as proxy for parcel counts (not ideal)
- Only analyzed 2024 as test case, need full 2013-2025 data
- Some appeals (11) didn't match to zoning districts
- Cannot yet link variance types to specific districts

**Next data needed:**
- PWD parcels dataset for true parcel counts per district
- Full 2013-2025 appeals linked to districts
- Zoning code documents to understand district-specific rules
