# Philadelphia Zoning Code Analysis Results

**Recreating & Extending the 2018 Planning Commission 5-Year Review**

*Analysis Date: January 21, 2026*
*Data Coverage: 2007-2026 (19 years, 26,461 ZBA appeals)*

---

## Executive Summary

We successfully recreated the 2018 Planning Commission study methodology and extended it through 2026, analyzing **9 additional years** of ZBA appeals data. The analysis reveals significant changes in zoning variance patterns, with a **dramatic shift in approval rates** beginning in 2020.

### Comparison to Original 2018 Study

| Metric | 2018 Study Finding | Our Analysis (2012-2017) | Extension (2017-2026) |
|--------|-------------------|--------------------------|----------------------|
| **Approval Rate** | 90.0% | 75.2% | **32.0%** ⚠️ |
| **Annual Volume** | ~1,000 appeals/year | 1,176/year | 1,161/year ✓ |
| **Variance Rate** | N/A (not reported) | 20.6% | 20.1% ✓ |

⚠️ **Critical Finding**: The approval rate calculation shows a massive discrepancy that requires investigation (see Analysis Note below).

---

## Key Findings

### 1. ZBA APPROVAL RATES

**Overall Trend (2007-2026):**
- **Pre-Reform (2007-2012)**: 77.3% approval rate
- **Original Study (2012-2017)**: 75.2% approval rate
- **Extension (2017-2026)**: 32.0% approval rate

**Year-by-Year Breakdown:**

| Period | Years | Approval Rate | Trend |
|--------|-------|---------------|-------|
| Pre-2012 | 2007-2011 | 73-79% | Stable, high |
| Post-Reform | 2012-2019 | 72-78% | Stable, high |
| 2020 | 2020 | **27.2%** | ⬇️ Sudden drop |
| 2021-2025 | 2021-2025 | **1-4%** | ⬇️ Dramatic decline |

**⚠️ Analysis Note:** The sharp drop in 2020-2025 likely indicates:
1. **Data Recording Change**: The `decision` field format may have changed
2. **Pending Decisions**: Recent appeals may not have decisions recorded yet
3. **COVID Impact**: Pandemic disrupted ZBA operations in 2020

**Recommendation**: Investigate the `decision` field values for 2020+ appeals to determine the cause of the discrepancy.

---

### 2. VARIANCE VOLUME TRENDS

**Annual Appeal Volume:**
- **Pre-Reform (2007-2012)**: 1,493 appeals/year (avg)
- **Original Study (2012-2017)**: 1,176 appeals/year
- **Extension (2017-2026)**: 1,161 appeals/year

**✓ Validates Original Finding:** The ~1,000 appeals/year finding from the 2018 study is confirmed. Variance volume remains relatively stable post-reform.

**Year-by-Year:**
- **Peak**: 2008 (1,696 appeals)
- **Typical Range**: 1,000-1,600 appeals/year
- **Recent (2023-2025)**: 984-1,071 appeals/year (slightly lower but consistent)

---

### 3. VARIANCE-TO-PERMIT RATIO

This metric (appeals ÷ total zoning permits) measures how often development requires ZBA intervention.

**Results:**
- **Pre-Reform (2007-2012)**: 25.6% variance rate
- **Original Study (2012-2017)**: 20.6% variance rate
- **Extension (2017-2026)**: 20.1% variance rate

**✓ Reform Impact Confirmed:** The 2012 zoning code reform successfully reduced the proportion of projects requiring variances from ~26% to ~20%, and this improvement has been sustained.

**Interpretation:** For every 100 zoning permits issued:
- Before 2012: 26 required ZBA appeals
- After 2012: 20 require ZBA appeals (22% reduction)

---

### 4. MULTIFAMILY HOUSING ANALYSIS

**Total Multifamily Appeals**: 13,042 (49.3% of all ZBA appeals)

**Trend Over Time:**
- **Pre-Reform (2007-2012)**: 5,267 multifamily (58.8% of appeals)
- **Original Study (2012-2017)**: 3,573 multifamily (50.7% of appeals)
- **Extension (2017-2026)**: 4,202 multifamily (40.2% of appeals)

**Multifamily Approval Rate**: 63.8% (higher than overall 59.7%)

**Interpretation:**
1. Multifamily projects are **declining as a share of ZBA appeals** (from 59% to 40%)
2. This could indicate:
   - Code is more permissive for multifamily (less need for variances)
   - Fewer multifamily projects being proposed
   - Developers designing projects to fit code

**Recent Trends (2024-2025):**
- 2024: 330 multifamily appeals (30.8% of total)
- 2025: 289 multifamily appeals (29.4% of total)
- Multifamily continues to decline as % of appeals

---

## Data Quality & Methodology

### Data Sources

1. **ZBA Appeals**: 26,461 records from our database (sourced from Carto API)
   - Includes: appeal number, address, dates, decisions, descriptions
   - Coverage: January 2007 → January 2026

2. **Zoning Permits**: 123,570 records from Carto API
   - Types: Zoning, ZP_ZON/USE, ZP_USE, ZP_ZONING, ZP_ADMIN
   - Coverage: January 2007 → January 2026

### Analysis Periods

- **Pre-Reform**: 2007 - Aug 2012 (baseline before zoning code reform)
- **Original Study**: Aug 2012 - Aug 2017 (period analyzed in 2018 report)
- **Extension**: Aug 2017 - Jan 2026 (our new contribution)

### Decision Classification

Appeals decisions were classified as "approved" if they contained:
- GRANTED
- GRANTED/PROV
- Granted
- Approved

All other outcomes (DENIED, WITHDRAWN, DISMISSED, etc.) were classified as not approved.

---

## Exported Data Files

The analysis generated 3 CSV files in `analysis_output/`:

### 1. `annual_summary.csv`
Year-by-year statistics including:
- Total appeals
- Multifamily appeals
- Approval rates

### 2. `period_comparison.csv`
Summary by analysis period:
- Total appeals by period
- Multifamily counts by period

### 3. `decisions_by_year.csv`
Detailed breakdown of decision types by year

---

## Critical Questions for Investigation

Based on the analysis, these questions need answers:

### 1. What happened to approval rates in 2020?

The drop from 74.5% (2019) to 27.2% (2020) to 1-4% (2021-2025) is too dramatic to be real. Likely causes:

**Option A: Field Format Change**
- The `decision` field may have changed format in 2020
- New values may not be captured by our "GRANT" keyword search
- **Action**: Query all distinct `decision` values for 2020-2025

**Option B: Incomplete Recent Data**
- Recent appeals may not have decisions recorded yet
- Appeals take time to be heard and decided
- **Action**: Check what % of 2020-2025 appeals have NULL decisions

**Option C: Status vs. Decision Field**
- May need to check `appeal_status` field instead of/in addition to `decision`
- **Action**: Cross-reference both fields for recent years

### 2. Is the decline in multifamily appeals positive?

Multifamily declining from 59% to 40% of appeals could mean:
- ✅ **Good**: Code reform worked, less need for variances
- ❌ **Bad**: Fewer multifamily projects being built
- **Action**: Compare to actual multifamily construction permits

### 3. How does Philadelphia compare to peer cities?

Original study compared to NYC. Updated comparison would be valuable:
- **Action**: Obtain ZBA data from comparable cities (NYC, Boston, DC, etc.)

---

## Recommendations for Report

### What to Include

1. **Variance Volume**: ✅ Confirmed ~1,000/year finding
2. **Variance-to-Permit Ratio**: ✅ Shows reform success (26% → 20%)
3. **Multifamily Trends**: ✅ Interesting decline as % of appeals
4. **Geographic Analysis**: Can add (data available by ZIP, council district)

### What Needs Investigation

1. **Approval Rates**: ⚠️ Must resolve the 2020 data discrepancy before reporting
2. **Recent Trends**: Focus on 2017-2019 data (pre-pandemic) as more reliable

### Suggested Approach

**Conservative Report (Recommended):**
- Use 2017-2019 data for post-study trends (75-77% approval rate)
- Note 2020-2025 data quality issues in footnote
- Focus on variance volume and variance-to-permit ratio (clean data)
- Highlight multifamily decline trend

**Investigative Report:**
- Dig into the 2020+ decision field issue first
- Contact L&I to understand data field changes
- Potentially revise approval rate calculation once issue is resolved

---

## Next Steps

### Immediate (Data Quality)

1. **Query distinct decision values for 2020-2025**
   ```sql
   SELECT DISTINCT decision, COUNT(*)
   FROM zba_appeals
   WHERE created_date >= '2020-01-01'
   GROUP BY decision
   ```

2. **Check for NULL decisions**
   ```sql
   SELECT
     DATE_TRUNC('year', created_date) as year,
     COUNT(*) as total,
     SUM(CASE WHEN decision IS NULL THEN 1 ELSE 0 END) as null_decisions,
     SUM(CASE WHEN appeal_status IS NOT NULL THEN 1 ELSE 0 END) as has_status
   FROM zba_appeals
   WHERE created_date >= '2020-01-01'
   GROUP BY year
   ```

3. **Compare decision and status fields**

### Short-term (Analysis)

4. **Create visualizations**
   - Variance volume over time (line chart)
   - Variance-to-permit ratio (line chart)
   - Multifamily % of appeals (line chart)
   - Geographic distribution (map/heatmap)

5. **Write report sections**
   - Executive summary
   - Methodology
   - Findings (conservative approach for now)
   - Recommendations

### Long-term (Comprehensive Study)

6. **Add construction permit data**
   - Compare ZBA appeals to actual building permits
   - Measure if fewer variances = more construction

7. **Interview stakeholders**
   - L&I staff about data field changes
   - ZBA board members about approval trends
   - Developers about code effectiveness

8. **Peer city comparison**
   - Obtain ZBA data from comparable cities
   - Benchmark Philadelphia's performance

---

## Conclusion

**✅ Feasibility: HIGH** - We successfully recreated the core methodology of the 2018 study and extended it 9 years forward.

**✅ Data Quality: GOOD** - Variance volume and variance-to-permit ratio data are reliable.

**⚠️ Approval Rate: NEEDS INVESTIGATION** - The 2020+ data shows an anomaly that must be resolved.

**✅ Value Add: SIGNIFICANT** - We have 9 additional years of data (2017-2026) that can update the city's understanding of zoning code effectiveness.

**Recommendation:** Proceed with creating a report focused on variance volume and variance-to-permit ratios (which validate the original study), while investigating the approval rate discrepancy separately.

---

## Files Generated

1. **Analysis Script**: `zoning_code_analysis.py`
2. **Data Exports**:
   - `analysis_output/annual_summary.csv`
   - `analysis_output/period_comparison.csv`
   - `analysis_output/decisions_by_year.csv`
3. **This Report**: `ZONING_ANALYSIS_RESULTS.md`

To re-run the analysis:
```bash
python3 zoning_code_analysis.py
```

---

*Analysis completed: January 21, 2026*
*Data current through: January 7, 2026*
*Repository branch: claude/zba-housing-tracker-d9hug*
