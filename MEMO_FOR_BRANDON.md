# Memo: Philadelphia ZBA Multifamily Tracker - Vercel Integration

**To:** Brandon (Developer)
**From:** ZBA Tracker Development Team
**Date:** January 13, 2026
**Re:** Adding ZBA Appeals Tracker to Vercel App

---

## Executive Summary

Built a complete Philadelphia ZBA (Zoning Board of Adjustment) multifamily housing tracker with **26,461 appeals** (2007-2026) including **13,042 multifamily projects**. The system successfully fetches current data (updated nightly) from Philadelphia's Carto API and provides a web interface for filtering and tracking appeals.

**Critical Discovery:** Philadelphia changed the `applicationtype` field in 2020 from `'RB_ZBA'` to `'Zoning Board of Adjustment'`. The code queries both formats to get complete data.

---

## System Overview

### What's Built

1. **Python API Client** (`zba_api.py`)
   - Fetches from `https://phl.carto.com/api/v2/sql`
   - Queries both old and new `applicationtype` formats
   - Automatic multifamily keyword detection
   - Calculates days since filing

2. **Database Layer** (`models.py`)
   - SQLAlchemy ORM models
   - SQLite (default) or PostgreSQL support
   - Tables: `zba_appeals`, `scraper_logs`

3. **Data Sync Script** (`sync_data.py`)
   - Populates database from API
   - Tested: 26,461 appeals successfully synced
   - 13,042 multifamily projects identified (49.3%)

4. **Flask API** (`app.py`)
   - RESTful endpoints with filtering
   - JSON responses for frontend integration

5. **Web Interface** (`templates/index.html`)
   - Standalone HTML/CSS/JS interface
   - Can be adapted for React/Next.js

---

## API Data Source

### Endpoint
```
https://phl.carto.com/api/v2/sql
```

### Critical SQL Query
```sql
SELECT * FROM appeals
WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
ORDER BY createddate DESC
```

**Why Both Values?**
- `'RB_ZBA'`: Old format (2007-2020) - 19,101 appeals
- `'Zoning Board of Adjustment'`: New format (2020-2026) - 7,378 appeals
- **Total**: 26,479 appeals

### Update Frequency
**Nightly** - API is current through January 7, 2026

---

## Data Schema

### Appeal Record Structure

```json
{
  "appeal_number": "ZP-2025-012719",
  "address": "1959 BRIDGE ST",
  "zip_code": "19121-0000",
  "appeal_grounds": "PERMIT FOR THE ERECTION OF AN ATTACHED STRUCTURE...",
  "created_date": "2026-01-07T18:22:24Z",
  "scheduled_date": null,
  "decision_date": null,
  "appeal_status": "OPEN",
  "decision": null,
  "is_multifamily": true,
  "days_since_filing": 6
}
```

### Key Fields

| Field | Description | Example |
|-------|-------------|---------|
| `appeal_number` | Unique identifier | `ZP-2025-012719` |
| `address` | Property address | `1959 BRIDGE ST` |
| `zip_code` | ZIP code | `19121-0000` |
| `appeal_grounds` | Description of appeal | Full text description |
| `created_date` | Filing date | `2026-01-07T18:22:24Z` |
| `is_multifamily` | Auto-detected flag | `true/false` |
| `days_since_filing` | Days since filed | `6` |

---

## Vercel Integration Options

### Option 1: API Routes (Recommended)

Create Next.js API routes in `pages/api/` or `app/api/`:

```typescript
// app/api/zba/appeals/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const multifamilyOnly = searchParams.get('multifamily_only');
  const zipCode = searchParams.get('zip_code');
  const daysBack = searchParams.get('days_back') || '90';

  // Build Carto API query
  let query = `
    SELECT address, createddate, appealgrounds, zip, appealnumber, decision
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
  `;

  // Add filters
  if (daysBack !== 'all') {
    query += ` AND createddate >= NOW() - INTERVAL '${daysBack} days'`;
  }

  if (zipCode) {
    query += ` AND zip LIKE '${zipCode}%'`;
  }

  query += ' ORDER BY createddate DESC LIMIT 100';

  const response = await fetch(
    `https://phl.carto.com/api/v2/sql?q=${encodeURIComponent(query)}`
  );

  const data = await response.json();

  // Add multifamily detection
  const enriched = data.rows.map(appeal => ({
    ...appeal,
    is_multifamily: detectMultifamily(appeal.appealgrounds)
  }));

  // Filter if needed
  const filtered = multifamilyOnly === 'true'
    ? enriched.filter(a => a.is_multifamily)
    : enriched;

  return NextResponse.json({ appeals: filtered });
}

function detectMultifamily(description: string): boolean {
  if (!description) return false;
  const keywords = [
    'multifamily', 'multi-family', 'apartment', 'dwelling units',
    'mixed use', 'mixed-use', 'family dwelling'
  ];
  const lower = description.toLowerCase();
  return keywords.some(keyword => lower.includes(keyword));
}
```

### Option 2: Serverless Functions

Convert Python code to Vercel serverless functions:

```python
# api/appeals.py
from http.server import BaseHTTPRequestHandler
import requests
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query params
        # Query Carto API
        # Return JSON response
        pass
```

### Option 3: Use Database (Recommended for Production)

**Vercel Postgres Setup:**

```sql
CREATE TABLE zba_appeals (
    id SERIAL PRIMARY KEY,
    appeal_number VARCHAR(50) UNIQUE,
    address VARCHAR(255),
    zip_code VARCHAR(10),
    appeal_grounds TEXT,
    created_date TIMESTAMP,
    scheduled_date TIMESTAMP,
    decision_date DATE,
    appeal_status VARCHAR(50),
    decision VARCHAR(100),
    is_multifamily BOOLEAN DEFAULT FALSE,
    days_since_filing INTEGER,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_created_date ON zba_appeals(created_date DESC);
CREATE INDEX idx_multifamily ON zba_appeals(is_multifamily);
CREATE INDEX idx_zip ON zba_appeals(zip_code);
```

**Sync Script (Run via Vercel Cron):**

```typescript
// app/api/cron/sync-appeals/route.ts
export async function GET() {
  // Fetch from Carto API
  // Upsert to Vercel Postgres
  // Return sync stats
}
```

Configure in `vercel.json`:
```json
{
  "crons": [{
    "path": "/api/cron/sync-appeals",
    "schedule": "0 2 * * *"
  }]
}
```

---

## Frontend Integration

### React Component Example

```tsx
// components/ZBATracker.tsx
'use client';

import { useState, useEffect } from 'react';

interface Appeal {
  appeal_number: string;
  address: string;
  zip_code: string;
  appeal_grounds: string;
  created_date: string;
  is_multifamily: boolean;
  days_since_filing: number;
}

export default function ZBATracker() {
  const [appeals, setAppeals] = useState<Appeal[]>([]);
  const [multifamilyOnly, setMultifamilyOnly] = useState(true);
  const [zipCode, setZipCode] = useState('');
  const [daysBack, setDaysBack] = useState('90');

  useEffect(() => {
    fetchAppeals();
  }, [multifamilyOnly, zipCode, daysBack]);

  async function fetchAppeals() {
    const params = new URLSearchParams({
      multifamily_only: multifamilyOnly.toString(),
      days_back: daysBack,
      ...(zipCode && { zip_code: zipCode })
    });

    const res = await fetch(`/api/zba/appeals?${params}`);
    const data = await res.json();
    setAppeals(data.appeals);
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">
        Philadelphia ZBA Multifamily Tracker
      </h1>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <label>
          <input
            type="checkbox"
            checked={multifamilyOnly}
            onChange={(e) => setMultifamilyOnly(e.target.checked)}
          />
          Multifamily Only
        </label>

        <input
          type="text"
          placeholder="ZIP Code"
          value={zipCode}
          onChange={(e) => setZipCode(e.target.value)}
          className="border px-3 py-2 rounded"
        />

        <select
          value={daysBack}
          onChange={(e) => setDaysBack(e.target.value)}
          className="border px-3 py-2 rounded"
        >
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
          <option value="180">Last 180 days</option>
          <option value="all">All time</option>
        </select>
      </div>

      {/* Appeals List */}
      <div className="space-y-4">
        {appeals.map(appeal => (
          <div
            key={appeal.appeal_number}
            className={`border p-4 rounded ${
              appeal.is_multifamily ? 'border-l-4 border-l-green-500' : ''
            }`}
          >
            <h3 className="text-xl font-semibold">{appeal.address}</h3>
            <p className="text-sm text-gray-600">
              ZIP: {appeal.zip_code} • Filed: {new Date(appeal.created_date).toLocaleDateString()}
              {appeal.days_since_filing <= 45 && (
                <span className="ml-2 bg-yellow-200 px-2 py-1 rounded text-xs">
                  ⚠️ 45-Day Window
                </span>
              )}
            </p>
            {appeal.is_multifamily && (
              <span className="inline-block mt-2 bg-green-500 text-white px-3 py-1 rounded text-sm">
                🏢 Multifamily
              </span>
            )}
            <p className="mt-2 text-sm">{appeal.appeal_grounds.substring(0, 200)}...</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Key Files to Reference

### From Repository: `claude/zba-housing-tracker-d9hug`

| File | Purpose | Use in Vercel |
|------|---------|---------------|
| `zba_api.py` | Python API client | Convert to TypeScript API route |
| `models.py` | Database schema | Use for Postgres schema |
| `app.py` | Flask endpoints | Reference for API route logic |
| `templates/index.html` | Web interface | Adapt to React components |
| `DATA_FIX.md` | Field name discovery | **Read this!** Explains the applicationtype issue |

---

## Deployment Checklist

### Phase 1: Basic API Integration
- [ ] Create `/api/zba/appeals` route
- [ ] Implement multifamily keyword detection
- [ ] Add filters (ZIP, date, multifamily)
- [ ] Test with sample queries

### Phase 2: Database Setup (Optional but Recommended)
- [ ] Set up Vercel Postgres
- [ ] Create `zba_appeals` table
- [ ] Create sync cron job
- [ ] Initial data load (26K records)

### Phase 3: Frontend
- [ ] Build React component
- [ ] Add filtering UI
- [ ] Implement pagination
- [ ] Style with Tailwind/your design system

### Phase 4: Production
- [ ] Add error handling
- [ ] Implement caching (SWR/React Query)
- [ ] Add loading states
- [ ] Monitor API rate limits

---

## Environment Variables

```env
# .env.local
DATABASE_URL=postgres://...  # Vercel Postgres
CARTO_API_URL=https://phl.carto.com/api/v2/sql
```

---

## Performance Considerations

### API Query Optimization
- **Limit results**: Default to 100, max 500
- **Add pagination**: Use OFFSET/LIMIT
- **Cache responses**: Use Vercel Edge caching
- **Index fields**: created_date, zip_code, is_multifamily

### Rate Limiting
The Carto API doesn't have documented rate limits, but consider:
- Cache API responses for 1 hour
- Use database for frequently accessed data
- Implement request debouncing on frontend

---

## Example Queries

### Recent Multifamily Projects
```sql
SELECT address, createddate, appealgrounds, zip
FROM appeals
WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
  AND createddate >= NOW() - INTERVAL '90 days'
  AND (
    LOWER(appealgrounds) LIKE '%multifamily%'
    OR LOWER(appealgrounds) LIKE '%dwelling units%'
    OR LOWER(appealgrounds) LIKE '%apartment%'
  )
ORDER BY createddate DESC
LIMIT 100
```

### Top ZIP Codes
```sql
SELECT
  SUBSTRING(zip, 1, 5) as zip_code,
  COUNT(*) as project_count
FROM appeals
WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
  AND LOWER(appealgrounds) LIKE '%multifamily%'
GROUP BY SUBSTRING(zip, 1, 5)
ORDER BY COUNT(*) DESC
LIMIT 10
```

---

## Testing

### Sample API Requests

```bash
# Get recent multifamily appeals
curl "https://phl.carto.com/api/v2/sql?q=SELECT%20*%20FROM%20appeals%20WHERE%20applicationtype%20IN%20('RB_ZBA',%20'Zoning%20Board%20of%20Adjustment')%20AND%20createddate%20%3E=%20NOW()%20-%20INTERVAL%20'90%20days'%20ORDER%20BY%20createddate%20DESC%20LIMIT%2010"

# Count by ZIP
curl "https://phl.carto.com/api/v2/sql?q=SELECT%20COUNT(*),%20zip%20FROM%20appeals%20WHERE%20applicationtype%20IN%20('RB_ZBA',%20'Zoning%20Board%20of%20Adjustment')%20GROUP%20BY%20zip%20ORDER%20BY%20COUNT(*)%20DESC%20LIMIT%2010"
```

### Expected Results
- Total appeals: ~26,500
- Multifamily: ~13,000 (49%)
- Latest date: January 7, 2026
- Top ZIPs: 19123, 19121, 19122

---

## Support & References

### Documentation
- **DATA_FIX.md**: Critical! Explains the applicationtype field change
- **DATA_SOURCES.md**: Investigation of data sources
- **README.md**: Full system documentation

### Contact
- Data source: ligisteam@phila.gov (City of Philadelphia L&I)
- OpenDataPhilly: https://opendataphilly.org

### Key Statistics
- **26,461** total ZBA appeals (2007-2026)
- **13,042** multifamily projects (49.3%)
- **189** appeals in last 90 days
- **52** multifamily in last 90 days
- **Updated nightly** from city API

---

## Quick Start Code Snippet

```typescript
// Minimal working example for Vercel
// app/api/zba/route.ts

export async function GET(request: Request) {
  const url = new URL(request.url);
  const zip = url.searchParams.get('zip') || '';

  const query = `
    SELECT address, createddate, appealgrounds, zip, appealnumber
    FROM appeals
    WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
    AND createddate >= NOW() - INTERVAL '90 days'
    ${zip ? `AND zip LIKE '${zip}%'` : ''}
    ORDER BY createddate DESC
    LIMIT 50
  `;

  const response = await fetch(
    `https://phl.carto.com/api/v2/sql?q=${encodeURIComponent(query)}`
  );

  const data = await response.json();

  return Response.json({
    appeals: data.rows.map(row => ({
      ...row,
      is_multifamily: /multifamily|dwelling units|apartment/i.test(row.appealgrounds || '')
    }))
  });
}
```

Test: `GET /api/zba?zip=19123`

---

**END OF MEMO**

Questions? Reference the full codebase in branch `claude/zba-housing-tracker-d9hug`
