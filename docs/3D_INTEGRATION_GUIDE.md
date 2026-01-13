# 3D Building Envelope Integration Guide for Vercel/Next.js

## Recommended Stack for buildphillynow.vercel.app

Based on your existing Next.js + Tailwind + Mapbox stack, here's the optimal approach for integrating 3D building envelope visualization.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     NEXT.JS APP (Vercel)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────┐         ┌────────────────────────┐   │
│  │  API Route        │         │  Client Component      │   │
│  │  /api/zoning      │────────▶│  3D Viewer             │   │
│  │                   │  JSON   │  (React Three Fiber)   │   │
│  │  Python Engine    │         │  or Deck.gl            │   │
│  │  via subprocess   │         │                        │   │
│  └───────────────────┘         └────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Existing Map (Mapbox)                                │   │
│  │  + 3D Building Layer (Deck.gl overlay)                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Option 1: Deck.gl 3D Buildings on Map (RECOMMENDED FOR MVP)

**Best for:** Showing 3D buildings directly on your existing Mapbox map

### Why Deck.gl?
- ✅ Already works with Mapbox (you're likely using it)
- ✅ Renders thousands of buildings efficiently (WebGL)
- ✅ Has `PolygonLayer` with extrusion for 3D buildings
- ✅ Integrates seamlessly with Next.js
- ✅ Matches your dark theme aesthetic
- ✅ Can show parcel footprints + zoning envelopes simultaneously

### Installation

```bash
npm install deck.gl @deck.gl/react @deck.gl/layers @deck.gl/geo-layers
npm install react-map-gl  # If not already installed
```

### Example: 3D Building Layer Component

```typescript
// components/ZoningEnvelope3D.tsx
'use client';

import { useState, useEffect } from 'react';
import DeckGL from '@deck.gl/react';
import { PolygonLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl';
import type { MapViewState } from '@deck.gl/core';

interface BuildingEnvelope {
  parcel_id: string;
  address: string;
  geometry: number[][][]; // GeoJSON coordinates
  max_height: number;
  base_height?: number;
  color: [number, number, number];
  opacity: number;
}

export default function ZoningEnvelope3D() {
  const [viewState, setViewState] = useState<MapViewState>({
    longitude: -75.1652,
    latitude: 39.9526,
    zoom: 15,
    pitch: 45, // Tilt for 3D view
    bearing: 0,
  });

  const [envelopes, setEnvelopes] = useState<BuildingEnvelope[]>([]);

  // Fetch zoning envelopes from API
  useEffect(() => {
    async function loadEnvelopes() {
      const response = await fetch('/api/zoning/envelopes?bounds=...');
      const data = await response.json();
      setEnvelopes(data.envelopes);
    }
    loadEnvelopes();
  }, []);

  const layers = [
    // Base zoning envelope (lighter color)
    new PolygonLayer({
      id: 'base-envelope',
      data: envelopes.filter(e => e.base_height),
      getPolygon: (d: BuildingEnvelope) => d.geometry[0],
      getElevation: (d: BuildingEnvelope) => d.base_height || 0,
      getFillColor: [100, 200, 100, 150], // Green for base
      getLineColor: [0, 255, 0],
      lineWidthMinPixels: 2,
      extruded: true,
      wireframe: true,
      pickable: true,
    }),

    // Maximum envelope with bonuses (brighter)
    new PolygonLayer({
      id: 'max-envelope',
      data: envelopes,
      getPolygon: (d: BuildingEnvelope) => d.geometry[0],
      getElevation: (d: BuildingEnvelope) => d.max_height,
      getFillColor: (d: BuildingEnvelope) => [...d.color, d.opacity * 255],
      getLineColor: [0, 255, 100],
      lineWidthMinPixels: 2,
      extruded: true,
      wireframe: true,
      pickable: true,
      onHover: ({ object }) => {
        if (object) {
          // Show tooltip with zoning info
          console.log(`${object.address}: ${object.max_height}' max height`);
        }
      },
    }),
  ];

  return (
    <DeckGL
      viewState={viewState}
      onViewStateChange={({ viewState }) => setViewState(viewState)}
      controller={true}
      layers={layers}
      getTooltip={({ object }) =>
        object && {
          html: `
            <div class="bg-slate-900 border border-green-600/30 p-3 rounded">
              <div class="font-bold">${object.address}</div>
              <div class="text-sm">Max Height: ${object.max_height}'</div>
              <div class="text-sm text-green-400">Click for details</div>
            </div>
          `,
          style: {
            backgroundColor: 'transparent',
            fontSize: '0.8em',
          },
        }
      }
    >
      <Map
        mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN}
        mapStyle="mapbox://styles/mapbox/dark-v11" // Matches your dark theme
      />
    </DeckGL>
  );
}
```

### API Route to Generate Building Envelopes

```typescript
// app/api/zoning/envelopes/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const parcelId = searchParams.get('parcel_id');

  if (!parcelId) {
    return NextResponse.json(
      { error: 'parcel_id required' },
      { status: 400 }
    );
  }

  // Call Python zoning engine
  const result = await runZoningEngine(parcelId);

  return NextResponse.json(result);
}

function runZoningEngine(parcelId: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(process.cwd(), 'api_wrapper.py');

    const python = spawn('python3', [pythonScript, parcelId]);

    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python script failed: ${error}`));
      } else {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${output}`));
        }
      }
    });
  });
}
```

### Python API Wrapper

```python
# api_wrapper.py
"""
Wrapper for Vercel serverless functions to call the zoning rules engine
"""

import sys
import json
from zoning_rules_engine import ZoningRulesEngine, Parcel
from zoning_districts import load_districts_into_engine

def generate_building_envelope(parcel_id: str, base_zoning: str, overlays: list,
                                geometry: list, apply_bonuses: bool = False):
    """
    Generate 3D building envelope from zoning parameters.

    Returns GeoJSON-compatible structure for Deck.gl rendering.
    """
    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    parcel = Parcel(
        parcel_id=parcel_id,
        address="",  # Would come from database
        base_zoning=base_zoning,
        overlays=overlays,
        lot_area=10000  # Would calculate from geometry
    )

    # Calculate maximum buildable
    envelope = engine.calculate_maximum_buildable(parcel, apply_bonuses=apply_bonuses)

    # Also calculate base (no bonuses) for comparison
    base_envelope = engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

    # Convert to 3D geometry
    max_height = envelope.final_parameters['max_height'].value
    base_height = base_envelope.final_parameters['max_height'].value

    # Apply setbacks to geometry
    setback_geometry = apply_setbacks_to_polygon(
        geometry,
        envelope.final_parameters
    )

    return {
        'parcel_id': parcel_id,
        'address': parcel.address,
        'geometry': setback_geometry,
        'max_height': max_height,
        'base_height': base_height,
        'color': [0, 255, 100] if apply_bonuses else [100, 200, 100],
        'opacity': 0.7,
        'parameters': {
            k: {
                'value': v.value,
                'unit': v.unit,
                'source': v.source
            }
            for k, v in envelope.final_parameters.items()
        },
        'narrative': envelope.get_narrative(),
        'bonuses_applied': [
            {
                'name': b.name,
                'description': b.description,
                'amount': b.modification_amount
            }
            for b in envelope.bonuses_applied
        ]
    }


def apply_setbacks_to_polygon(geometry: list, parameters: dict):
    """
    Apply setback requirements to shrink the building footprint.

    This is a simplified version - you'd want a proper geometry library
    like Shapely for production.
    """
    # For now, just return the original geometry
    # In production, you'd use Shapely to buffer inward by setback amounts
    return geometry


if __name__ == '__main__':
    # Called from Node.js with parcel_id as argument
    parcel_id = sys.argv[1]

    # In production, fetch parcel data from database
    # For demo, use hardcoded values
    result = generate_building_envelope(
        parcel_id=parcel_id,
        base_zoning='CMX-3',
        overlays=['/CDO'],
        geometry=[[
            [-75.140, 39.950],
            [-75.140, 39.951],
            [-75.141, 39.951],
            [-75.141, 39.950],
            [-75.140, 39.950],
        ]],
        apply_bonuses=True
    )

    print(json.dumps(result))
```

---

## Option 2: React Three Fiber - Standalone 3D Viewer

**Best for:** Detailed, interactive 3D building models in a modal/sidebar

### Why React Three Fiber?
- ✅ Full 3D control (rotate, zoom, inspect)
- ✅ Can show multiple scenarios side-by-side
- ✅ React-native API (perfect for Next.js)
- ✅ Great for detailed setback visualization
- ✅ Can animate transitions between base/bonus scenarios

### Installation

```bash
npm install three @react-three/fiber @react-three/drei
```

### Example: 3D Building Viewer Component

```typescript
// components/BuildingViewer3D.tsx
'use client';

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Text } from '@react-three/drei';
import { useEffect, useState } from 'react';

interface EnvelopeData {
  max_height: number;
  base_height: number;
  setbacks: {
    front: number;
    side: number;
    rear: number;
  };
  footprint: [number, number][]; // Building footprint after setbacks
  parcel_footprint: [number, number][]; // Original parcel
}

function BuildingMesh({
  footprint,
  height,
  color,
  opacity = 0.7
}: {
  footprint: [number, number][];
  height: number;
  color: string;
  opacity?: number;
}) {
  // Convert 2D footprint to 3D extruded shape
  const shape = new THREE.Shape();
  footprint.forEach((point, i) => {
    if (i === 0) {
      shape.moveTo(point[0], point[1]);
    } else {
      shape.lineTo(point[0], point[1]);
    }
  });

  return (
    <mesh position={[0, height / 2, 0]} castShadow receiveShadow>
      <extrudeGeometry
        args={[
          shape,
          {
            depth: height,
            bevelEnabled: false,
          },
        ]}
      />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={opacity}
        wireframe={false}
      />
    </mesh>
  );
}

export default function BuildingViewer3D({
  parcelId
}: {
  parcelId: string
}) {
  const [envelopeData, setEnvelopeData] = useState<EnvelopeData | null>(null);
  const [showBase, setShowBase] = useState(true);
  const [showMax, setShowMax] = useState(true);

  useEffect(() => {
    async function loadData() {
      const response = await fetch(`/api/zoning/envelopes?parcel_id=${parcelId}`);
      const data = await response.json();
      setEnvelopeData(data);
    }
    loadData();
  }, [parcelId]);

  if (!envelopeData) return <div>Loading 3D model...</div>;

  return (
    <div className="w-full h-[600px] bg-slate-950 rounded-lg border border-green-600/30">
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 bg-slate-900/90 p-4 rounded border border-green-600/30">
        <div className="text-sm font-bold mb-2 text-green-400">Layers</div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={showBase}
            onChange={(e) => setShowBase(e.target.checked)}
            className="accent-green-600"
          />
          Base Zoning ({envelopeData.base_height}')
        </label>
        <label className="flex items-center gap-2 text-sm mt-2">
          <input
            type="checkbox"
            checked={showMax}
            onChange={(e) => setShowMax(e.target.checked)}
            className="accent-green-600"
          />
          Max with Bonuses ({envelopeData.max_height}')
        </label>
      </div>

      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [100, 100, 100], fov: 50 }}
        shadows
      >
        <color attach="background" args={['#020617']} />

        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1}
          castShadow
        />

        {/* Grid ground plane */}
        <Grid
          args={[200, 200]}
          cellColor="#22c55e"
          sectionColor="#16a34a"
          fadeDistance={300}
          fadeStrength={1}
        />

        {/* Parcel outline (lot boundary) */}
        <lineSegments>
          <edgesGeometry
            args={[
              new THREE.ShapeGeometry(
                new THREE.Shape(
                  envelopeData.parcel_footprint.map(
                    ([x, y]) => new THREE.Vector2(x, y)
                  )
                )
              ),
            ]}
          />
          <lineBasicMaterial color="#22c55e" linewidth={2} />
        </lineSegments>

        {/* Base envelope */}
        {showBase && (
          <BuildingMesh
            footprint={envelopeData.footprint}
            height={envelopeData.base_height}
            color="#64d487"
            opacity={0.5}
          />
        )}

        {/* Maximum envelope with bonuses */}
        {showMax && (
          <BuildingMesh
            footprint={envelopeData.footprint}
            height={envelopeData.max_height}
            color="#00ff66"
            opacity={0.7}
          />
        )}

        {/* Height labels */}
        <Text
          position={[0, envelopeData.max_height + 10, 0]}
          fontSize={8}
          color="#22c55e"
          anchorX="center"
          anchorY="middle"
        >
          {envelopeData.max_height}' MAX
        </Text>

        {/* Camera controls */}
        <OrbitControls makeDefault />
      </Canvas>
    </div>
  );
}
```

---

## Option 3: Hybrid Approach (RECOMMENDED FOR FULL FEATURES)

Combine both approaches:

1. **Map View (Deck.gl):** Show all buildings in neighborhood with 3D extrusion
2. **Detail View (React Three Fiber):** Click a parcel to see detailed 3D model in modal/sidebar

### Page Component Example

```typescript
// app/zoning/[parcel_id]/page.tsx
'use client';

import { useState } from 'react';
import ZoningEnvelope3D from '@/components/ZoningEnvelope3D';
import BuildingViewer3D from '@/components/BuildingViewer3D';

export default function ParcelZoningPage({
  params
}: {
  params: { parcel_id: string }
}) {
  const [selectedParcel, setSelectedParcel] = useState(params.parcel_id);
  const [showDetailViewer, setShowDetailViewer] = useState(false);

  return (
    <div className="flex h-screen">
      {/* Map with 3D buildings */}
      <div className="flex-1">
        <ZoningEnvelope3D
          onParcelClick={(parcelId) => {
            setSelectedParcel(parcelId);
            setShowDetailViewer(true);
          }}
        />
      </div>

      {/* Sidebar with detailed 3D viewer */}
      {showDetailViewer && (
        <div className="w-[500px] bg-slate-900 border-l border-green-600/30 p-6 overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-green-400">
              Building Envelope
            </h2>
            <button
              onClick={() => setShowDetailViewer(false)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <BuildingViewer3D parcelId={selectedParcel} />

          <ZoningParameters parcelId={selectedParcel} />
        </div>
      )}
    </div>
  );
}
```

---

## Database Schema for Parcel Geometries

You'll need to store parcel footprints. Add to your database:

```sql
-- Add to existing zba_appeals or create new parcels table
CREATE TABLE parcels (
    parcel_id TEXT PRIMARY KEY,
    address TEXT,
    base_zoning TEXT,
    overlays TEXT[], -- Array of overlay codes
    geometry GEOMETRY(POLYGON, 4326), -- PostGIS geometry
    lot_area REAL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Spatial index for fast lookups
CREATE INDEX idx_parcels_geometry ON parcels USING GIST(geometry);

-- Link to ZBA appeals
ALTER TABLE zba_appeals ADD COLUMN parcel_id TEXT REFERENCES parcels(parcel_id);
```

---

## Deployment to Vercel

### 1. Add Python Runtime

Create `vercel.json`:

```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9"
    }
  }
}
```

### 2. Python Dependencies

Create `requirements.txt` in project root:

```
# requirements.txt
# (No external dependencies needed for zoning engine - uses stdlib only)
```

### 3. Environment Variables

Add to Vercel dashboard:

```
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
DATABASE_URL=your_database_url (if using Postgres)
```

### 4. Deploy

```bash
git add .
git commit -m "Add 3D building envelope visualization"
git push origin main
# Vercel auto-deploys from main branch
```

---

## Performance Optimizations

### 1. Cache Envelope Calculations

```typescript
// Use SWR for client-side caching
import useSWR from 'swr';

function useZoningEnvelope(parcelId: string) {
  const { data, error } = useSWR(
    `/api/zoning/envelopes?parcel_id=${parcelId}`,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000, // Cache for 1 minute
    }
  );

  return { envelope: data, isLoading: !error && !data, error };
}
```

### 2. Pre-generate Common Scenarios

Run zoning calculations offline and store results in database:

```sql
CREATE TABLE envelope_cache (
    parcel_id TEXT,
    scenario TEXT, -- 'base', 'max_bonuses', etc.
    max_height REAL,
    parameters JSONB,
    narrative TEXT,
    geometry GEOMETRY(POLYGON, 4326),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (parcel_id, scenario)
);
```

### 3. Level of Detail (LOD)

Show simplified buildings when zoomed out, detailed when zoomed in:

```typescript
const layers = [
  new PolygonLayer({
    id: 'buildings-lod',
    // ... other props
    getElevation: (d) => {
      // Simplify at low zoom levels
      return zoom < 14 ? Math.round(d.max_height / 10) * 10 : d.max_height;
    },
  }),
];
```

---

## Example User Flow

1. **User browses map** → Sees all parcels with 3D building envelopes (Deck.gl)
2. **User clicks parcel** → Sidebar opens with detailed 3D viewer (React Three Fiber)
3. **User toggles bonus scenarios** → "Show LEED Gold", "Add Waterfront Trail"
4. **Building animates** → Smoothly grows to show new height with bonuses
5. **User sees step-by-step** → Narrative explains: "Base CMX-3 allows 65', CDO increases to 100', LEED bonus adds 36', final: 136'"
6. **User exports** → Download parameters for architect/developer

---

## Next Steps

1. ✅ **Set up Deck.gl map layer** (quickest win - shows 3D on your existing map)
2. ✅ **Create API route** to call Python zoning engine
3. ✅ **Fetch parcel geometries** from Philadelphia's OpenDataPhilly or City API
4. ✅ **Add React Three Fiber viewer** for detailed inspections
5. ✅ **Integrate with your existing dashboard** UI/UX

Would you like me to create a working implementation for any of these options?
