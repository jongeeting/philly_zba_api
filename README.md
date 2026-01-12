# Philadelphia ZBA Multifamily Housing Tracker

A comprehensive tool for Philadelphia YIMBY organizing to track Zoning Board of Adjustment (ZBA) appeals related to multifamily housing projects.

## Features

- ✅ Fetches ZBA appeals from Philadelphia's Open Data API (historical: 2007-2020)
- ✅ Web scraper for current ZBA calendar data (2024-2025)
- ✅ SQLite database for storing and querying appeals
- ✅ Automatic multifamily project detection using keyword matching
- ✅ Tracks days since filing (for 45-day neighborhood meeting window)
- ✅ Flask web interface with filtering by ZIP, date, and project type
- ✅ Highlights multifamily keywords in appeal descriptions

## Data Sources

- **API**: https://phl.carto.com/api/v2/sql
- **Primary Dataset**: `appeals` table (19,101 records through March 2020)
- **Secondary Dataset**: `board_decisions` table (55,462 records through October 2023)
- **Live Calendar**: https://li.phila.gov/zba-appeals-calendar (scraper included)

**⚠️ Data Freshness**: The `appeals` table (with full address and description data) was last updated **March 2020**. The included web scraper can fetch current 2024-2025 data from the live ZBA calendar.

**See [DATA_SOURCES.md](DATA_SOURCES.md)** for a complete analysis of available data sources.

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Chrome/Chromium (for web scraper)

The scraper uses Selenium with Chrome. Install Chrome or Chromium browser:

```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser chromium-chromedriver

# macOS
brew install --cask google-chrome
brew install chromedriver
```

## Usage

### Quick Start: View Sample Data

Test the API and see sample multifamily projects:

```bash
python sample_data.py
```

### Step 1: Populate the Database

Sync appeals from the API (historical data through March 2020):

```bash
# Sync all historical appeals (~19,000 records)
python sync_data.py --api-only

# Or test with a smaller sample first
python sync_data.py --api-only --limit 500
```

### Step 2: Add Current Data (Optional)

Scrape current appeals from the live ZBA calendar:

```bash
# This requires Chrome/Chromium installed
python sync_data.py --scraper-only
```

**Note**: The scraper is a work in progress and may need adjustment based on the current calendar page structure. It saves the HTML to `calendar_page.html` for inspection if appeals aren't found.

### Step 3: Run the Web Application

Start the Flask web server:

```bash
python app.py
```

Then open your browser to: **http://localhost:5000**

## Web Interface Features

The web interface provides:

- **Dashboard Statistics**: Total appeals, multifamily count, recent activity
- **Filtering**:
  - Multifamily projects only
  - By ZIP code
  - By date range (30/90/180 days or all time)
  - Search by address or description
- **Highlighted Appeals**: Multifamily projects are marked with green border
- **45-Day Window**: Appeals within the critical 45-day window are flagged
- **Keyword Highlighting**: Multifamily terms are highlighted in descriptions

## Project Structure

```
philly_zba_api/
├── zba_api.py           # API client for Carto API
├── models.py            # SQLAlchemy database models
├── scraper.py           # Selenium-based calendar scraper
├── sync_data.py         # Data sync script (API + scraper → database)
├── app.py               # Flask web application
├── sample_data.py       # Demo script for API testing
├── templates/
│   └── index.html       # Web interface template
├── DATA_SOURCES.md      # Data source investigation
├── requirements.txt     # Python dependencies
└── zba_appeals.db       # SQLite database (created by sync_data.py)
```

## Scripts Reference

### `sync_data.py` - Data Sync Script

```bash
# Sync from API only (historical data)
python sync_data.py --api-only

# Sync from scraper only (current data)
python sync_data.py --scraper-only

# Sync from both sources
python sync_data.py

# Limit records for testing
python sync_data.py --api-only --limit 100

# Use custom database path
python sync_data.py --db postgresql://user:pass@localhost/zba
```

### `scraper.py` - Calendar Scraper

Test the scraper independently:

```bash
python scraper.py
```

This runs in non-headless mode so you can see what it's doing. Adjust the class selectors in `_parse_appeal_element()` based on the actual HTML structure.

### `sample_data.py` - API Demo

```bash
python sample_data.py
```

Shows recent appeals, multifamily detection, and geographic distribution.

## API Endpoints

The Flask app provides these API endpoints:

- **`GET /api/appeals`** - List appeals with filtering
  - Query params: `multifamily_only`, `zip_code`, `days_back`, `search`, `limit`, `offset`
- **`GET /api/stats`** - Summary statistics
- **`GET /api/appeal/<appeal_number>`** - Get specific appeal details
- **`GET /health`** - Health check

Example:

```bash
curl "http://localhost:5000/api/appeals?multifamily_only=true&zip_code=19104&limit=10"
```

## Multifamily Detection Keywords

The system detects multifamily projects by searching for these keywords in appeal descriptions:

- `multifamily` / `multi-family`
- `apartment` / `apartments`
- `dwelling units`
- `mixed use` / `mixed-use`
- `family dwelling` (catches "two family", "three family", etc.)

## Getting Current Data

Since the API data is from 2020, here are your options:

### Option 1: Use the Scraper (Recommended)

The included scraper fetches current data from the live calendar:

```bash
python sync_data.py --scraper-only
```

### Option 2: Contact L&I

Request API access or data exports:

- **Email**: ligisteam@phila.gov
- **Phone**: 215-686-8686 or 311
- Ask about API access to current appeals data

### Option 3: File an Open Data Request

- Request that OpenDataPhilly update the appeals table
- Cite public interest in housing development transparency

## Development

### Run in Development Mode

```bash
# Flask debug mode
export FLASK_ENV=development
python app.py
```

### Database Schema

The database uses two tables:

- **`zba_appeals`** - Appeal records with address, description, dates, etc.
- **scraper_logs`** - Logs of sync runs for tracking

See `models.py` for the full schema.

## Contributing

This is a grassroots project for Philadelphia YIMBY organizing. Contributions welcome!

Areas for improvement:

- [ ] Improve scraper robustness for calendar page changes
- [ ] Add email notifications for new multifamily appeals
- [ ] Export to CSV/Excel
- [ ] Map view of appeals
- [ ] Integration with RCO boundaries
- [ ] Automated daily sync with cron/GitHub Actions

## License

MIT License - See LICENSE file

## Credits

Built for [Philadelphia YIMBY](https://philadelphiayimby.org)

Data from:
- [OpenDataPhilly](https://opendataphilly.org)
- [Philadelphia Department of Licenses & Inspections](https://www.phila.gov/departments/department-of-licenses-and-inspections/)

## Support

For questions or issues:

- Open an issue on GitHub
- Contact Philadelphia YIMBY
- Email L&I data team: ligisteam@phila.gov
