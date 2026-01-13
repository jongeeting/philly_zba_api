# Quick Integration Guide for buildphillynow.vercel.app

This guide shows how to add 3D building envelope visualization to your Next.js app in **under 30 minutes**.

---

## Step 1: Install Dependencies

```bash
cd your-nextjs-app

# Core 3D visualization
npm install deck.gl @deck.gl/react @deck.gl/layers @deck.gl/geo-layers
npm install react-map-gl mapbox-gl

# Optional: For standalone 3D viewer
npm install three @react-three/fiber @react-three/drei
```

---

## Step 2: Copy Files to Your Project

```bash
# From this repo to your Next.js app

# 1. Copy Python zoning engine
cp -r philly_zba_api/zoning_*.py your-nextjs-app/python/
cp -r philly_zba_api/docs your-nextjs-app/docs/

# 2. Copy Next.js integration files
cp philly_zba_api/nextjs_integration/api_route_example.ts \
   your-nextjs-app/app/api/zoning/envelope/route.ts

cp philly_zba_api/nextjs_integration/calculate_envelope.py \
   your-nextjs-app/python/calculate_envelope.py

cp philly_zba_api/nextjs_integration/ZoningMap3D.tsx \
   your-nextjs-app/components/ZoningMap3D.tsx
```

Your project structure should look like:

```
your-nextjs-app/
├── app/
│   └── api/
│       └── zoning/
│           └── envelope/
│               └── route.ts          ← API endpoint
├── components/
│   └── ZoningMap3D.tsx               ← 3D map component
├── python/
│   ├── calculate_envelope.py         ← CLI wrapper
│   ├── zoning_rules_engine.py        ← Core engine
│   ├── zoning_districts.py           ← District definitions
│   └── (other zoning files)
└── package.json
```

---

## Step 3: Add Environment Variables

Add to `.env.local`:

```bash
NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_mapbox_token_here
```

Get a free token at https://mapbox.com

---

## Step 4: Create a Test Page

Create `app/zoning/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import ZoningMap3D from '@/components/ZoningMap3D';

export default function ZoningPage() {
  const [selectedParcel, setSelectedParcel] = useState<string | null>(null);

  // Example: Parcels in Central Delaware area
  const testParcels = [
    '0123456789', // Would be real parcel IDs from your database
    '9876543210',
  ];

  return (
    <div className="flex flex-col h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-green-600/30 p-4">
        <h1 className="text-2xl font-bold text-green-400">
          Philadelphia Zoning Envelopes
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          3D visualization of maximum buildable projects
        </p>
      </div>

      {/* Map */}
      <div className="flex-1">
        <ZoningMap3D
          mapboxToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN!}
          parcelIds={testParcels}
          onParcelClick={(parcelId, envelope) => {
            setSelectedParcel(parcelId);
            console.log('Clicked parcel:', envelope);
            // Open sidebar, modal, etc.
          }}
        />
      </div>

      {/* Sidebar (optional) */}
      {selectedParcel && (
        <div className="absolute right-0 top-0 h-full w-96 bg-slate-900 border-l border-green-600/30 p-6">
          <h2 className="text-xl font-bold text-green-400 mb-4">
            Parcel Details
          </h2>
          <ParcelDetails parcelId={selectedParcel} />
        </div>
      )}
    </div>
  );
}

function ParcelDetails({ parcelId }: { parcelId: string }) {
  const [envelope, setEnvelope] = useState<any>(null);

  useEffect(() => {
    fetch(`/api/zoning/envelope?parcel_id=${parcelId}&bonuses=true`)
      .then((r) => r.json())
      .then(setEnvelope);
  }, [parcelId]);

  if (!envelope) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-bold text-green-400">Base Zoning</h3>
        <p className="text-slate-300">{envelope.base_zoning}</p>
      </div>

      <div>
        <h3 className="text-sm font-bold text-green-400">Overlays</h3>
        <p className="text-slate-300">{envelope.overlays.join(', ')}</p>
      </div>

      <div>
        <h3 className="text-sm font-bold text-green-400">Max Height</h3>
        <p className="text-2xl text-white font-bold">
          {envelope.max_height}
          <span className="text-sm text-slate-400">'</span>
        </p>
        <p className="text-xs text-slate-500">
          Base: {envelope.base_height}' + Bonuses: {envelope.max_height - envelope.base_height}'
        </p>
      </div>

      {envelope.bonuses_applied.length > 0 && (
        <div>
          <h3 className="text-sm font-bold text-green-400">Bonuses Applied</h3>
          <ul className="space-y-1 mt-2">
            {envelope.bonuses_applied.map((bonus, i) => (
              <li key={i} className="text-sm text-slate-300">
                • {bonus.description} <span className="text-green-400">+{bonus.amount}'</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h3 className="text-sm font-bold text-green-400">How We Calculated This</h3>
        <p className="text-sm text-slate-400 leading-relaxed">
          {envelope.narrative}
        </p>
      </div>

      <div>
        <h3 className="text-sm font-bold text-green-400">Application Steps</h3>
        <div className="space-y-2 mt-2 max-h-64 overflow-y-auto">
          {envelope.application_steps.map((step, i) => (
            <div key={i} className="text-xs bg-slate-800/50 p-2 rounded border border-slate-700">
              <div className="font-bold text-green-400">{step.source}</div>
              <div className="text-slate-300">
                {step.parameter}: {step.old_value} → {step.new_value}
              </div>
              <div className="text-slate-500">{step.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## Step 5: Test Locally

```bash
# Make sure Python 3 is available
python3 --version

# Start your Next.js dev server
npm run dev

# Visit http://localhost:3000/zoning
```

You should see:
- 3D buildings on a dark Mapbox map
- Green-themed UI matching your site
- Interactive tooltips with zoning info
- Click to see detailed breakdown

---

## Step 6: Deploy to Vercel

### 6.1 Update `vercel.json`

Create or update `vercel.json` in your project root:

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_MAPBOX_TOKEN": "@mapbox-token"
  }
}
```

### 6.2 Ensure Python is Available

Vercel supports Python in serverless functions. No additional config needed.

### 6.3 Deploy

```bash
git add .
git commit -m "Add 3D zoning envelope visualization"
git push origin main
```

Vercel auto-deploys from your main branch.

### 6.4 Add Environment Variable

In Vercel dashboard:
1. Go to your project → Settings → Environment Variables
2. Add: `NEXT_PUBLIC_MAPBOX_TOKEN` = `your_token_here`
3. Redeploy

---

## Integration with Existing Features

### Option A: Add to Your Parcel Map

If you already have a parcel map, add the 3D layer:

```typescript
// In your existing map component
import { PolygonLayer } from '@deck.gl/layers';

// Add this layer to your existing Deck.gl layers array
const zoningEnvelopeLayer = new PolygonLayer({
  id: 'zoning-envelopes',
  data: parcelsWithZoning, // Fetch from /api/zoning/envelope
  getPolygon: (d) => d.geometry.coordinates[0],
  getElevation: (d) => d.max_height,
  getFillColor: [0, 255, 100, 180],
  extruded: true,
  wireframe: true,
});
```

### Option B: Add to Parcel Detail Pages

If you have detail pages for parcels (e.g., `/parcel/[id]`), add a 3D viewer:

```typescript
// app/parcel/[id]/page.tsx
import BuildingViewer3D from '@/components/BuildingViewer3D';

export default function ParcelPage({ params }) {
  return (
    <div>
      {/* Your existing content */}

      <section className="my-8">
        <h2 className="text-xl font-bold mb-4">Maximum Buildable Envelope</h2>
        <BuildingViewer3D parcelId={params.id} />
      </section>
    </div>
  );
}
```

### Option C: Add to ZBA Appeal Pages

Link zoning envelopes to ZBA appeals:

```typescript
// Show what COULD be built vs. what's being appealed
function ZBAAppealPage({ appeal }) {
  return (
    <div>
      <h1>ZBA Appeal #{appeal.appeal_number}</h1>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h2>What They're Appealing For</h2>
          <div>Height: {appeal.proposed_height}'</div>
        </div>

        <div>
          <h2>What's Actually Allowed</h2>
          <ZoningEnvelopeSummary parcelId={appeal.parcel_id} />
        </div>
      </div>

      <ZoningMap3D
        parcelIds={[appeal.parcel_id]}
        // Highlight if appeal exceeds zoning
      />
    </div>
  );
}
```

---

## Performance Tips

### 1. Cache Envelope Calculations

```typescript
// Use Next.js caching
export const revalidate = 3600; // Cache for 1 hour

// Or use SWR
import useSWR from 'swr';

function useZoningEnvelope(parcelId: string) {
  const { data, error } = useSWR(
    `/api/zoning/envelope?parcel_id=${parcelId}`,
    fetcher,
    { revalidateOnFocus: false }
  );

  return { envelope: data, isLoading: !error && !data };
}
```

### 2. Only Load Visible Parcels

```typescript
// Fetch envelopes based on map viewport
function ZoningMap3D() {
  const [viewState, setViewState] = useState(...);

  useEffect(() => {
    // Only fetch parcels in current viewport
    const bounds = getBounds(viewState);
    fetchParcelsInBounds(bounds).then(loadEnvelopes);
  }, [viewState]);
}
```

### 3. Progressive Loading

```typescript
// Load low-detail first, then high-detail
const [detailLevel, setDetailLevel] = useState('low');

// At low zoom, show simplified buildings (round to nearest 10')
// At high zoom, show exact heights
```

---

## Fetching Real Parcel Data

You'll need parcel geometries. Options:

### Option 1: OpenDataPhilly

Download parcel shapefile:
https://opendataphilly.org/datasets/pwd-parcels/

Convert to GeoJSON, load into PostGIS database.

### Option 2: City of Philadelphia API

```bash
# Fetch parcel data via their API
curl "https://phl.carto.com/api/v2/sql?q=SELECT * FROM opa_properties_public WHERE parcel_number='123456789'"
```

### Option 3: Pre-process and Store

```python
# Script to pre-calculate envelopes for all parcels
import psycopg2
from zoning_rules_engine import ZoningRulesEngine

engine = ZoningRulesEngine()

# Fetch all parcels from DB
parcels = fetch_all_parcels()

for parcel in parcels:
    envelope = engine.calculate_maximum_buildable(parcel)

    # Store in envelope_cache table
    store_envelope(parcel.id, envelope)
```

Then your API just reads from cache instead of calculating on-the-fly.

---

## Troubleshooting

### Python Not Found

```bash
# Vercel uses Amazon Linux, Python 3.9+ should be available
# If issues, specify in package.json:
{
  "engines": {
    "node": ">=18.0.0",
    "python": ">=3.9.0"
  }
}
```

### Deck.gl Not Rendering

Check browser console for WebGL support:

```javascript
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
console.log('WebGL supported:', !!gl);
```

### Mapbox Token Issues

Make sure token starts with `pk.` and has proper scopes:
- Styles: Read
- Fonts: Read
- Datasets: Read (if using)

---

## Next Steps

1. ✅ Add parcel geometry data to your database
2. ✅ Integrate with your existing parcel/zoning layers
3. ✅ Link to ZBA appeals (show what's allowed vs. what's appealed)
4. ✅ Add scenario comparison (base vs. max bonuses)
5. ✅ Add "contact developer" CTAs for parcels with high bonus potential
6. ✅ Generate leads for architects/developers

---

## Example Use Cases

### For Community Organizers
"See what COULD be built in your neighborhood under current zoning"

### For Developers
"Calculate maximum buildable project before purchasing land"

### For Planners
"Analyze cumulative impact of zoning overlays across the city"

### For ZBA Research
"Compare what's allowed (zoning envelope) vs. what's being appealed for (variance requests)"

---

## Support

Questions? Check:
- Full documentation: `/docs/3D_INTEGRATION_GUIDE.md`
- Legal framework: `/docs/OVERLAY_LEGAL_FRAMEWORK.md`
- Examples: `/examples_overlay_application.py`

Or open an issue on GitHub!

---

**Ready to build?** Start with Step 1 above! 🚀

The entire integration should take **< 30 minutes** if you already have Next.js + Mapbox set up.
