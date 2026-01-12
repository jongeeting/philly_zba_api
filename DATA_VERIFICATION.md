# Comprehensive Data Source Verification - Final Report

## Investigation Summary

After thorough investigation of the Philadelphia L&I Appeals API, including checking large samples of unsorted data, I can confirm that **the Carto API data stops at March 2020** across all available tables.

## Tables Investigated

### 1. `appeals` table (original)
- **Total ZBA records**: 19,101
- **Date range**: January 22, 2007 → **March 12, 2020**
- **Latest appeal**: #40099 at 1800 Master St (March 12, 2020)

### 2. `li_appeals` table
- **Total ZBA records**: 20,205
- **Date range**: January 22, 2007 → **March 12, 2020**
- **Latest appeal_key**: 2671235 (March 12, 2020)
- **Latest appeal**: #40099 at 1800 Master St (March 12, 2020)

### 3. `board_decisions` table
- **Total decisions**: 55,462
- **Date range**: March 5, 2000 → **October 10, 2023**
- **Note**: Has more recent decisions but lacks property addresses and appeal descriptions

## Verification Methods Used

✅ **Checked aggregate functions**: `MAX(createddate)`, `MAX(processeddate)` across all records
✅ **Sampled different offsets**: Checked records at positions 0, 10000, 20000 to find any out-of-order 2024-2025 dates
✅ **Sorted by appeal_key**: Checked highest appeal keys (most recent) - all from March 2020
✅ **Filtered for recent dates**: Explicitly queried for `processeddate >= '2024-01-01'` - **zero results**
✅ **Checked both `appeals` and `li_appeals` tables**: Both stop at the same date

## Data Currency Status

**CONFIRMED**: The Philadelphia Carto API appeals data has **NOT been updated since March 12, 2020**.

This appears to be when the city stopped updating the open data portal, possibly due to COVID-19 disruptions or a change in data systems.

## Available Data by Recency

| Data Source | Latest Data | Has Addresses? | Has Descriptions? | Record Count |
|-------------|-------------|----------------|-------------------|--------------|
| `appeals` / `li_appeals` | March 2020 | ✅ Yes | ✅ Yes | ~20,000 |
| `board_decisions` | October 2023 | ❌ No | ❌ No | ~55,000 |
| ZBA Live Calendar | Current (2025) | ✅ Yes | ✅ Yes | Unknown (web scraping required) |

## Recommendations

### For Current 2024-2025 Data

1. **Use the web scraper** (already built in `scraper.py`)
   - Scrapes https://li.phila.gov/zba-appeals-calendar
   - Gets current appeals with full details
   - Requires Chrome/Chromium and Selenium

2. **Contact L&I directly**
   - **Email**: ligisteam@phila.gov
   - **Phone**: 215-686-8686 or 311
   - Request API access or bulk data export for 2020-present

3. **File open data request**
   - Submit to OpenDataPhilly to resume API updates
   - Cite public interest in housing transparency

### For Historical Analysis (2007-2020)

The existing API data is still valuable:
- **20,205 ZBA appeals** over 13 years
- Full address and description data
- All tracked in the database system we built
- Good for understanding patterns, hot neighborhoods, approval rates

## Next Steps

Since you wanted to verify the API had current data but it doesn't, here are your options:

**Option A**: Use the built scraper to get 2024-2025 data
**Option B**: Contact L&I to request current API access
**Option C**: Use historical API data for patterns/analysis
**Option D**: All of the above - historical + scraper + request API update

The good news: The system I built supports all these data sources and can integrate them into one database.

---

**Last Verified**: January 12, 2026
**Methodology**: Checked MAX() dates, sampled 20,000+ records, filtered for 2024+ dates across all tables
