# IMPORTANT DATA QUALITY NOTE

## Database Migration Impact on Variance Type Analysis

### Discovery (January 21, 2026)

Our initial finding that "use variances dropped to 0% in 2020" was **INCORRECT**. This was a data quality issue, not a policy change.

### What Happened:

In 2020, Philadelphia's ZBA appeals data migrated from **HANSEN** to **ECLIPSE** database system.

**Critical difference**:
- **HANSEN system** (2007-2019): Populated `relatedpermit` field with official APPEAL TYPE codes (USEVAR, ZONEVAR, CERTIFICAT, etc.)
- **ECLIPSE system** (2020-present): Does NOT populate `relatedpermit` field

### Data Completeness:

| Year | Total Appeals | System | Appeals with Official Type Data | % Complete |
|------|---------------|--------|--------------------------------|------------|
| 2018 | 1,501 | HANSEN | 1,477 | **98.4%** ✓ |
| 2019 | 1,593 | HANSEN | 1,271 | **79.8%** ✓ |
| **2020** | **1,096** | **Mixed** | **12** | **1.1%** ✗ |
| 2021 | 1,403 | ECLIPSE | 0 | **0.0%** ✗ |
| 2022 | 1,277 | ECLIPSE | 0 | **0.0%** ✗ |
| 2023 | 1,055 | ECLIPSE | 0 | **0.0%** ✗ |
| 2024 | 1,071 | ECLIPSE | 0 | **0.0%** ✗ |
| 2025 | 984 | ECLIPSE | 0 | **0.0%** ✗ |

**2020 breakdown**:
- HANSEN records: 17 appeals (12 have data = 70.6%)
- ECLIPSE records: 1,079 appeals (0 have data = 0.0%)

### Impact on Our Analysis:

#### ✓ **Still Valid**:
1. **By-right approval trend** - Based on variance-to-permit ratio (independent of appeal type)
   - Pre-reform: 74.4% by-right
   - 2017-2026: 79.9% by-right
   - Recent: 80.6% by-right

2. **Approval rates** - Based on decision field (still populated in ECLIPSE)
   - 2020-2025: 83-89% approval rate

3. **Overall variance volume** - Based on total appeal counts
   - ~1,000 appeals/year currently

#### ❌ **No Longer Reliable After 2019**:
1. **Official variance type classification** (USEVAR vs ZONEVAR vs CERTIFICAT)
   - Valid: 2007-2019 only
   - Invalid: 2020-2026

2. **"Use variances dropped to 0%"** claim
   - This was a data artifact from the system migration
   - We cannot determine actual use variance rates after 2019

#### ⚠️ **Less Precise After 2019**:
1. **Keyword-based classification** (parking, height, accessory structure, etc.)
   - Still works based on `appeal_grounds` field
   - But less precise than official codes
   - "Use" keyword appears in 73% of 2020 appeals but doesn't mean "use variance"

### Corrected Analysis Period:

**For variance type analysis, use 2007-2019 data only.**

| Variance Type | 2007-2019 Appeals | % of Appeals (2007-2019) |
|---------------|-------------------|--------------------------|
| Use Variance | 13,671 | 56.7% |
| Dimensional Variance | 7,427 | 30.8% |
| Certificate | 1,001 | 4.1% |

**Trend within reliable period (2007-2019)**:
- 2007-2012: 72.1% use variance
- 2012-2017: 69.6% use variance
- 2017-2019: 56.5% use variance (declining but not to 0%)

### Alternative Data Source Needed:

To continue variance type analysis post-2020, we would need:

1. **Access to ECLIPSE database** with full schema to find where appeal types are stored
2. **ZBA hearing records** which may have appeal type classifications
3. **Manual classification** of a sample of appeals to validate keyword approach
4. **Direct API access** to Philadelphia's L&I system

### Recommendations for Philadelphia:

**The city should restore official appeal type classification in ECLIPSE** or provide a mapping/export that includes:
- USEVAR (Use Variance)
- ZONEVAR (Dimensional Variance)
- SPECIALEX (Special Exception)
- CERTIFICAT (Certificate)
- AGAINSTL&I (Appeals of L&I decisions)

This data is critical for:
- Analyzing code effectiveness
- Identifying problematic regulations
- Tracking reform impacts
- Academic research
- Public transparency

### Updated Conclusions:

✓ **We CAN say**:
- By-right approval rate increased from 74% to 80% (2007-2026)
- Variance volume declined from 1,493/year to 1,161/year
- Use variance rate was declining 2007-2019 (72% → 70% → 57%)
- Open space/setbacks are major dimensional issue (per 2018 PCPC report)
- Height, accessory structures, and parking drive significant variance activity

✗ **We CANNOT say**:
- "Use variances dropped to 0% in 2020" (data artifact)
- Precise variance type distribution after 2019 (data unavailable)
- Whether use variance reforms continued post-2019 (cannot measure)

⚠️ **We can ESTIMATE** (less reliable):
- Keyword-based classification still shows general patterns
- Height/accessory/parking issues persist in 2020-2026 appeal descriptions
- But official classification not available

---

*Data quality issue discovered: January 21, 2026*
*Affects: Variance type analysis 2020-2026*
*Does not affect: By-right trends, approval rates, variance volume*
