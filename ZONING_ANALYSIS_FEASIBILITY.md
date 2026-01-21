# Analysis Feasibility: Recreating & Extending the 2018 Zoning Code 5-Year Review

## Summary of Original Report Methodology (2012-2017)

Based on available information about the Philadelphia Planning Commission's 5-year review:

### Data Sources Used
1. **ZBA Appeals Data** - Tracked variance applications and decisions
2. **Zoning Permit Applications** - Total applications submitted to L&I
3. **ZBA Decision Records** - Approval/denial outcomes

### Key Metrics Analyzed
- **Variance Volume**: ~1,000 zoning appeals annually
- **Approval Rate**: 90% of ZBA cases approved
- **ZBA Review Rate**: Pre-2012: 35% of permits went to ZBA → Post-2012: Decreased but "not very dramatically"
- **Time Period**: August 2012 - August 2017 (5 years post-reform)
- **Baseline Comparison**: 2008-2012 data (pre-reform)

### Key Findings
1. Number of variances decreased slightly but not significantly
2. Approval rate remained consistently ~90%
3. Total permit applications increased post-2012
4. Variance as percentage of total permits declined somewhat

## What We Have: ZBA Appeals Data

### Our Current Dataset
✅ **Source**: `https://phl.carto.com/api/v2/sql` - `appeals` table
✅ **Records**: 26,461 ZBA appeals (2007-2026)
✅ **Date Range**: January 2007 → January 2026 (19 years!)
✅ **Update Frequency**: Nightly
✅ **Fields Available**:
- `appeal_number` - Unique ID
- `address` - Property location
- `created_date` - Filing date
- `scheduled_date` - Hearing date
- `decision_date` - Decision date
- `decision` - GRANTED, DENIED, WITHDRAWN, etc.
- `appeal_status` - OPEN, CLOSED
- `appeal_grounds` - Description of what's being appealed
- `application_type` - 'RB_ZBA' (old) or 'Zoning Board of Adjustment' (new)
- `zip_code` - Geographic filter
- `council_district` - Political geography

### Our Multifamily Detection
✅ 13,042 multifamily projects identified (49.3% of all appeals)
✅ Keyword-based detection already implemented

## Can We Recreate the Analysis? ✅ YES (Mostly)

### ✅ What We CAN Do

1. **Variance Volume Over Time**
   ```sql
   SELECT
     DATE_TRUNC('year', created_date) as year,
     COUNT(*) as total_appeals
   FROM appeals
   WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
   GROUP BY year
   ORDER BY year
   ```

2. **Approval Rates**
   ```sql
   SELECT
     decision,
     COUNT(*) as count,
     ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
   FROM appeals
   WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
     AND decision IS NOT NULL
   GROUP BY decision
   ```

3. **Pre vs Post Reform Comparison**
   - Pre-reform: 2007-2012 (our data available)
   - Post-reform: 2012-2017 (original study)
   - **Extension**: 2017-2026 (our NEW analysis!)

4. **Multifamily Variance Trends**
   ```sql
   SELECT
     DATE_TRUNC('year', created_date) as year,
     SUM(CASE WHEN is_multifamily THEN 1 ELSE 0 END) as multifamily_appeals,
     COUNT(*) as total_appeals,
     ROUND(SUM(CASE WHEN is_multifamily THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_multifamily
   FROM zba_appeals
   GROUP BY year
   ORDER BY year
   ```

5. **Geographic Distribution**
   - By ZIP code
   - By council district (where available)

6. **Time to Decision**
   ```sql
   SELECT
     AVG(decision_date - created_date) as avg_days_to_decision,
     DATE_TRUNC('year', created_date) as year
   FROM appeals
   WHERE decision_date IS NOT NULL AND created_date IS NOT NULL
   GROUP BY year
   ```

7. **Multifamily Approval Rates**
   ```sql
   SELECT
     decision,
     COUNT(*) as count
   FROM zba_appeals
   WHERE is_multifamily = TRUE AND decision IS NOT NULL
   GROUP BY decision
   ```

### ❌ What We CANNOT Do (Missing Data)

1. **Total Permit Applications**
   - Original study compared ZBA appeals to total permits
   - We don't have the denominator (total permits submitted)
   - **Need**: L&I permits dataset
   - **Availability**: Check OpenDataPhilly for "Licenses and Inspections Permits"

2. **Appeal Success by Type**
   - Original study may have categorized appeals by variance type
   - Our data has `appeal_grounds` (text) but not structured type field
   - **Workaround**: Could classify using keywords (use variance, dimensional variance, special exception, etc.)

3. **Comparison to Peer Cities**
   - Original study compared to NYC and other cities
   - We'd need to source data from other jurisdictions

4. **Neighborhood Opposition Outcomes**
   - Original tracked how often community opposition affected decisions
   - Our data doesn't have community testimony/opposition records
   - **Potential source**: ZBA meeting minutes (if digitized)

## Data Gaps to Fill

### High Priority (Needed for Full Recreation)

1. **L&I Permits Dataset**
   - Endpoint: Check `https://phl.carto.com/api/v2/sql`
   - Table: `permits` or `li_permits`
   - **Purpose**: Calculate variance rate as % of total permits

   ```sql
   -- Need to check if this table exists
   SELECT COUNT(*) FROM permits
   WHERE permit_type LIKE '%zoning%'
     AND issue_date BETWEEN '2012-01-01' AND '2017-12-31'
   ```

2. **Structured Appeal Type Field**
   - Currently have free-text `appeal_grounds`
   - Need to classify as: Use Variance, Dimensional Variance, Special Exception, etc.
   - **Workaround**: Text analysis/keyword matching

### Medium Priority (Nice to Have)

3. **Council District Data Completeness**
   - Many records missing `council_district`
   - **Workaround**: Geocode addresses to council districts

4. **Case Duration Metrics**
   - Some records missing `decision_date`
   - Some missing `scheduled_date`
   - **Impact**: Limits time-to-decision analysis

### Low Priority (For Enhanced Analysis)

5. **RCO (Registered Community Organization) Involvement**
   - Not in current dataset
   - Would show community engagement

6. **Appellant Type Patterns**
   - We have `primaryappellant` field
   - Could analyze: Property owners vs. developers vs. attorneys

## Recommended Approach

### Phase 1: Replicate Core Metrics (2012-2017)

Using our ZBA appeals data:

1. **Volume Analysis**
   - Total appeals by year (2007-2026)
   - Compare 2012-2017 to original findings

2. **Approval Rate Analysis**
   - Calculate % GRANTED, DENIED, WITHDRAWN
   - Compare to reported 90% approval rate

3. **Multifamily Trends**
   - Multifamily appeals over time
   - Multifamily approval rates

### Phase 2: Extend Analysis (2017-2026)

New contribution using our current data:

1. **Post-Review Trends**
   - Has approval rate changed since 2017?
   - Has variance volume continued to decline?
   - Multifamily development patterns

2. **COVID Impact**
   - 2020-2021 appeal volume changes
   - Approval rate changes during pandemic

3. **Recent Trends (2024-2026)**
   - Most current multifamily development patterns
   - Hot neighborhoods for development

### Phase 3: Fill Data Gaps

1. **Get L&I Permits Data**
   - Query Carto API for permits table
   - Calculate variance-to-permit ratio

2. **Classify Appeal Types**
   - Use keyword analysis on `appeal_grounds`
   - Categorize: Use Variance, Dimensional, Special Exception, etc.

3. **Geographic Enhancement**
   - Geocode missing council districts
   - Add neighborhood names

## Next Steps

### Immediate Actions

1. **Check for L&I Permits Data**
   ```bash
   curl "https://phl.carto.com/api/v2/sql?q=SELECT * FROM permits LIMIT 1"
   curl "https://phl.carto.com/api/v2/sql?q=SELECT * FROM li_permits LIMIT 1"
   ```

2. **Query Our Database for Baseline Statistics**
   ```python
   # Calculate 2012-2017 metrics from our data
   # Compare to original study findings
   ```

3. **Create Analysis Script**
   - Calculate all replicable metrics
   - Generate comparison tables
   - Produce visualizations

### Output Format

Recommend producing:

1. **Data Tables**: Year-over-year statistics
2. **Charts**:
   - Appeal volume over time
   - Approval rates by year
   - Multifamily trends
   - Geographic heatmaps
3. **Report**: Markdown/PDF extending original study through 2026

## Conclusion

### ✅ **FEASIBILITY: HIGH**

We can recreate most of the original analysis and significantly extend it through 2026 using the ZBA appeals data we already have.

### Key Strengths:
- 19 years of ZBA data (2007-2026)
- 26,461 appeals to analyze
- Clean, structured data
- Nightly updates

### Key Limitations:
- Missing total permit application data (denominator for variance rate)
- Need to classify appeal types from text
- Some missing council district data

### Recommendation:
**Proceed with the analysis!** We have enough data to produce a valuable update to the 2018 study. Start with what we can do now, then fill gaps with L&I permits data if available.

---

## Sources

Based on research of the original 2018 Philadelphia Planning Commission 5-Year Zoning Code Review:

- [City of Philadelphia Five-Year Review of the Zoning Code](https://www.phila.gov/documents/city-of-philadelphia-five-year-review-of-the-zoning-code/)
- [WHYY: Meet the broken system costing your neighborhood its voice](https://whyy.org/articles/meet-the-broken-system-costing-your-neighborhood-its-voice/)
- [Proposed ZBA Changes - Nochumson Law](https://nochumson.com/resources/proposed-zba-changes-concern-developers-investors)

Key finding from original study: **90% ZBA approval rate**, ~1,000 annual appeals, slight decline post-2012 reform but approval rate remained high.
