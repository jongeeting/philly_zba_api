# Philadelphia ZBA Data Sources - Investigation Results

## Summary

After investigating multiple data sources for Philadelphia Zoning Board of Adjustment (ZBA) appeals, here's what we found:

### ✅ Best Available API: Philadelphia Carto API

**Base URL**: `https://phl.carto.com/api/v2/sql`

### Available Tables

| Table | Latest Data | Total Records | Use Case |
|-------|-------------|---------------|----------|
| `appeals` | March 2020 | 19,101 ZBA appeals | Full appeal details (address, description, grounds) |
| `board_decisions` | October 2023 | 55,462 decisions | Recent decisions (but limited details) |
| `court_appeals` | Unknown | Unknown | Court-level appeals |

### ⚠️ Data Freshness Problem

**The `appeals` table hasn't been updated since March 2020**, despite being the table with the most useful information (addresses, appeal grounds, descriptions). This is a significant limitation for current organizing work.

The `board_decisions` table has more recent data (through Oct 2023) but lacks critical information like:
- Property addresses
- Appeal descriptions/grounds
- ZIP codes
- Council districts

### Other Sources Investigated

#### 1. **Live ZBA Calendar**
- URL: https://li.phila.gov/zba-appeals-calendar
- **Status**: Vue.js web app, no public API discovered
- Has current 2024-2025 data but requires JavaScript
- Could potentially be scraped but no API endpoint found

#### 2. **OpenDataPhilly**
- URL: https://opendataphilly.org/datasets/licenses-and-inspections-appeals-of-code-violations-and-permit-refusals/
- Same Carto data as above
- Last updated: Created Sept 2016 (no recent update date shown)

#### 3. **PHL API**
- URL: http://phlapi.com/licenseapi.html
- **Status**: Site returned 503 error (down or deprecated)

#### 4. **GitHub Zoning Appeals Viewer**
- URL: https://cityofphiladelphia.github.io/zoning-appeals/
- Front-end viewer only, no API documentation found

## Recommendations

### Short Term (Use What We Have)

1. **Use the `appeals` table for historical analysis** (2007-2020)
   - Still useful for understanding patterns
   - Good for training/testing the system
   - 19,000+ records of historical data

2. **Track recent decisions via `board_decisions`** (through Oct 2023)
   - More current but less detailed
   - Can show which cases are being decided

### Medium Term (Get Current Data)

1. **Contact Philadelphia L&I directly**
   - Email: ligisteam@phila.gov
   - Phone: 215-686-8686 or 311
   - Ask about API access to current appeals data
   - Request updated exports or API documentation

2. **Investigate ZBA calendar scraping**
   - The live calendar at li.phila.gov/zba-appeals-calendar has current data
   - Could build a Selenium/Playwright scraper
   - Inspect network requests to find hidden API endpoints

3. **File an Open Data request**
   - Request that the city update the appeals table
   - Cite public interest in housing transparency

### Long Term (Alternative Approaches)

1. **RSS/Email monitoring**
   - Subscribe to ZBA meeting notices
   - Parse email notifications for new appeals

2. **Manual tracking with community input**
   - Crowdsource appeals from neighborhood groups
   - Use the tool to track manually-entered cases

3. **Partner with other civic tech groups**
   - Check if Code for Philly or OpenDataPhilly has insights
   - See if other YIMBY groups have found solutions

## Example Queries

### Get recent ZBA appeals (historical)
```sql
SELECT
  address,
  createddate,
  appealgrounds,
  zip,
  appealstatus,
  decision
FROM appeals
WHERE applicationtype = 'RB_ZBA'
  AND createddate >= '2019-01-01'
ORDER BY createddate DESC
```

### Get recent board decisions
```sql
SELECT
  internaljobid,
  appealnumber,
  decisiondate,
  decision,
  meetingremarks
FROM board_decisions
WHERE decisiondate >= '2023-01-01'
ORDER BY decisiondate DESC
```

### Try to join tables (usually empty for recent data)
```sql
SELECT
  a.address,
  a.appealgrounds,
  bd.decisiondate,
  bd.decision
FROM appeals a
JOIN board_decisions bd ON a.internaljobid = bd.internaljobid
WHERE bd.decisiondate >= '2023-01-01'
ORDER BY bd.decisiondate DESC
```

## References

- [OpenDataPhilly - L&I Appeals](https://opendataphilly.org/datasets/licenses-and-inspections-appeals-of-code-violations-and-permit-refusals/)
- [ZBA Official Page](https://www.phila.gov/departments/zoning-board-of-adjustment/)
- [ZBA Appeals Calendar](https://li.phila.gov/zba-appeals-calendar)
- [Data.gov - L&I Appeals](https://catalog.data.gov/dataset/licenses-and-inspections-appeals-of-code-violations-and-permit-refusals)
- [Philadelphia ZBA Appeal Process](https://www.phila.gov/services/zoning-planning-development/appeal-a-zoning-decision-to-the-zoning-board-of-adjustment-zba/)

## Next Steps for This Project

1. ✅ Built working API client with historical data (2007-2020)
2. ✅ Keyword detection for multifamily projects
3. ⏳ Contact L&I to request current data access
4. ⏳ Consider building a calendar scraper as backup
5. ⏳ Build database + web interface with available historical data
