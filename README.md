# Philadelphia ZBA Multifamily Housing Tracker

A tool for Philadelphia YIMBY organizing to track Zoning Board of Adjustment (ZBA) appeals related to multifamily housing projects.

## Features

- Fetches ZBA appeals from Philadelphia's Open Data API
- Filters for potential multifamily projects using keyword detection
- Tracks days since filing (important for 45-day neighborhood meeting window)
- Web interface to browse and filter appeals

## Data Source

- API: https://phl.carto.com/api/v2/sql
- Primary Dataset: `appeals` table (19,101 records through March 2020)
- Secondary Dataset: `board_decisions` table (55,462 records through October 2023)
- Filter: `applicationtype = 'RB_ZBA'`

**⚠️ Data Freshness**: The `appeals` table (with full address and description data) was last updated **March 2020**. The `board_decisions` table has more recent data through October 2023 but lacks property details.

**See [DATA_SOURCES.md](DATA_SOURCES.md)** for a complete analysis of available data sources and recommendations for accessing current ZBA appeals.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Test the API and see sample multifamily projects
python sample_data.py
```

## Project Structure

- `zba_api.py` - API client for fetching ZBA appeals
- `sample_data.py` - Script to demonstrate API functionality
- `DATA_SOURCES.md` - Investigation of available data sources
- `app.py` - Flask web application (coming soon)
- `models.py` - Database models (coming soon)

## Getting Current Data

To access more recent ZBA appeals data:

1. **Contact L&I directly:**
   - Email: ligisteam@phila.gov
   - Phone: 215-686-8686 or 311 (inside city limits)
   - Ask about API access to current appeals or updated data exports

2. **Check the live ZBA calendar:**
   - https://li.phila.gov/zba-appeals-calendar
   - Has current 2024-2025 data (web interface only, no public API found)

3. **File an open data request:**
   - Request that OpenDataPhilly update the appeals table
   - Cite public interest in housing development transparency
