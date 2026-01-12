# Philadelphia ZBA Multifamily Housing Tracker

A tool for Philadelphia YIMBY organizing to track Zoning Board of Adjustment (ZBA) appeals related to multifamily housing projects.

## Features

- Fetches ZBA appeals from Philadelphia's Open Data API
- Filters for potential multifamily projects using keyword detection
- Tracks days since filing (important for 45-day neighborhood meeting window)
- Web interface to browse and filter appeals

## Data Source

- API: https://phl.carto.com/api/v2/sql
- Dataset: `appeals` table
- Filter: `applicationtype = 'RB_ZBA'`

**Note**: The current dataset appears to be updated through March 2020. Check with the city for more recent data sources.

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
- `app.py` - Flask web application (coming soon)
- `models.py` - Database models (coming soon)
