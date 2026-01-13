// components/ZoningMap3D.tsx
// Drop-in component for buildphillynow.vercel.app
// Shows 3D building envelopes on Mapbox map

'use client';

import { useState, useEffect, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { PolygonLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl';
import type { PickingInfo, MapViewState } from '@deck.gl/core';

interface BuildingEnvelope {
  parcel_id: string;
  address: string;
  base_zoning: string;
  overlays: string[];
  geometry: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  max_height: number;
  base_height: number;
  narrative: string;
  parameters: Record<string, any>;
  bonuses_applied: Array<{
    name: string;
    description: string;
    amount: number;
  }>;
}

interface ZoningMap3DProps {
  /** Initial map center */
  center?: [number, number];
  /** Initial zoom level */
  zoom?: number;
  /** Mapbox access token */
  mapboxToken: string;
  /** Callback when user clicks a building */
  onParcelClick?: (parcelId: string, envelope: BuildingEnvelope) => void;
  /** Show base envelope (without bonuses) */
  showBase?: boolean;
  /** Show maximum envelope (with bonuses) */
  showMax?: boolean;
  /** List of parcel IDs to display (if empty, fetches all in viewport) */
  parcelIds?: string[];
}

export default function ZoningMap3D({
  center = [-75.1652, 39.9526], // Philadelphia
  zoom = 15,
  mapboxToken,
  onParcelClick,
  showBase = true,
  showMax = true,
  parcelIds = [],
}: ZoningMap3DProps) {
  const [viewState, setViewState] = useState<MapViewState>({
    longitude: center[0],
    latitude: center[1],
    zoom,
    pitch: 45, // Tilt for 3D view
    bearing: 0,
    padding: { top: 0, bottom: 0, left: 0, right: 0 },
  });

  const [envelopes, setEnvelopes] = useState<BuildingEnvelope[]>([]);
  const [loading, setLoading] = useState(false);
  const [hoveredParcel, setHoveredParcel] = useState<string | null>(null);

  // Fetch building envelopes
  useEffect(() => {
    async function loadEnvelopes() {
      if (parcelIds.length === 0) return;

      setLoading(true);
      try {
        // Fetch envelopes for each parcel
        const promises = parcelIds.map(async (parcelId) => {
          const response = await fetch(
            `/api/zoning/envelope?parcel_id=${parcelId}&bonuses=true`
          );
          return response.json();
        });

        const results = await Promise.all(promises);
        setEnvelopes(results.filter((r) => !r.error));
      } catch (error) {
        console.error('Failed to load envelopes:', error);
      } finally {
        setLoading(false);
      }
    }

    loadEnvelopes();
  }, [parcelIds]);

  // Create Deck.gl layers
  const layers = useMemo(() => {
    const result = [];

    // Base envelope layer (lighter green, semi-transparent)
    if (showBase && envelopes.length > 0) {
      result.push(
        new PolygonLayer({
          id: 'base-envelope',
          data: envelopes,
          getPolygon: (d: BuildingEnvelope) => d.geometry.coordinates[0],
          getElevation: (d: BuildingEnvelope) => d.base_height,
          getFillColor: [100, 200, 100, 120], // Light green, transparent
          getLineColor: [34, 197, 94], // Green-500
          lineWidthMinPixels: 1,
          extruded: true,
          wireframe: true,
          material: {
            ambient: 0.35,
            diffuse: 0.6,
            shininess: 32,
            specularColor: [51, 51, 51],
          },
          pickable: true,
          autoHighlight: true,
          highlightColor: [34, 197, 94, 100],
        })
      );
    }

    // Maximum envelope layer (brighter green)
    if (showMax && envelopes.length > 0) {
      result.push(
        new PolygonLayer({
          id: 'max-envelope',
          data: envelopes,
          getPolygon: (d: BuildingEnvelope) => d.geometry.coordinates[0],
          getElevation: (d: BuildingEnvelope) => d.max_height,
          getFillColor: (d: BuildingEnvelope) => {
            const isHovered = hoveredParcel === d.parcel_id;
            return isHovered
              ? [34, 197, 94, 220] // Bright green when hovered
              : d.bonuses_applied.length > 0
              ? [0, 255, 100, 180] // Neon green if bonuses applied
              : [100, 200, 100, 160]; // Medium green otherwise
          },
          getLineColor: [34, 197, 94], // Green-500
          lineWidthMinPixels: 2,
          extruded: true,
          wireframe: true,
          material: {
            ambient: 0.35,
            diffuse: 0.6,
            shininess: 32,
            specularColor: [51, 51, 51],
          },
          pickable: true,
          autoHighlight: true,
          highlightColor: [34, 197, 94, 150],
          onHover: (info: PickingInfo) => {
            if (info.object) {
              setHoveredParcel(info.object.parcel_id);
            } else {
              setHoveredParcel(null);
            }
          },
          onClick: (info: PickingInfo) => {
            if (info.object && onParcelClick) {
              onParcelClick(info.object.parcel_id, info.object);
            }
          },
        })
      );
    }

    return result;
  }, [envelopes, showBase, showMax, hoveredParcel, onParcelClick]);

  // Tooltip component (matches your dark theme)
  const getTooltip = ({ object }: { object?: BuildingEnvelope }) => {
    if (!object) return null;

    const bonusHeight = object.max_height - object.base_height;
    const hasBonuses = object.bonuses_applied.length > 0;

    return {
      html: `
        <div class="bg-slate-900 border border-green-600/30 p-3 rounded-lg shadow-xl">
          <div class="font-bold text-white mb-1">${object.address}</div>
          <div class="text-sm text-slate-300 mb-2">${object.base_zoning} ${object.overlays.join(' ')}</div>

          <div class="space-y-1">
            <div class="text-xs text-slate-400">
              Base Height: <span class="text-green-400">${object.base_height}'</span>
            </div>
            ${
              hasBonuses
                ? `
              <div class="text-xs text-slate-400">
                + Bonuses: <span class="text-green-400">+${bonusHeight}'</span>
              </div>
              <div class="text-xs font-bold text-green-400 border-t border-green-600/30 pt-1 mt-1">
                Max Height: ${object.max_height}'
              </div>
            `
                : `
              <div class="text-xs font-bold text-green-400">
                Max Height: ${object.max_height}'
              </div>
            `
            }
          </div>

          ${
            hasBonuses
              ? `
            <div class="text-xs text-green-400 mt-2 pt-2 border-t border-green-600/30">
              ${object.bonuses_applied.map((b) => `• ${b.description}`).join('<br>')}
            </div>
          `
              : ''
          }

          <div class="text-xs text-slate-500 mt-2 pt-2 border-t border-slate-700">
            Click for details
          </div>
        </div>
      `,
      style: {
        backgroundColor: 'transparent',
        fontSize: '0.8em',
        pointerEvents: 'none',
      },
    };
  };

  return (
    <div className="relative w-full h-full">
      {/* Loading indicator */}
      {loading && (
        <div className="absolute top-4 left-4 z-10 bg-slate-900/90 px-4 py-2 rounded border border-green-600/30">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-green-400">Loading 3D models...</span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute top-4 right-4 z-10 bg-slate-900/90 p-4 rounded border border-green-600/30">
        <div className="text-sm font-bold mb-3 text-green-400">3D Building Envelopes</div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showBase}
              onChange={(e) => {
                // This would need to be lifted to parent component
                // or use a state management solution
              }}
              className="accent-green-600"
            />
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-600/40 border border-green-500" />
              <span className="text-slate-300">Base Zoning</span>
            </div>
          </label>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showMax}
              onChange={(e) => {
                // This would need to be lifted to parent component
              }}
              className="accent-green-600"
            />
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500/60 border border-green-400" />
              <span className="text-slate-300">Max with Bonuses</span>
            </div>
          </label>
        </div>

        <div className="mt-3 pt-3 border-t border-green-600/30">
          <div className="text-xs text-slate-400">
            <div>Pitch: {Math.round(viewState.pitch)}°</div>
            <div>Zoom: {viewState.zoom.toFixed(1)}</div>
          </div>
        </div>
      </div>

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 z-10 bg-slate-900/90 px-3 py-2 rounded border border-green-600/30">
        <div className="text-xs text-slate-400">
          <div>🖱️ Drag to rotate</div>
          <div>⌘/Ctrl + Drag to tilt</div>
          <div>Scroll to zoom</div>
        </div>
      </div>

      {/* Deck.gl Canvas */}
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState }) => setViewState(viewState)}
        controller={true}
        layers={layers}
        getTooltip={getTooltip}
        // Match your dark theme
        style={{ background: '#020617' }} // slate-950
      >
        <Map
          mapboxAccessToken={mapboxToken}
          mapStyle="mapbox://styles/mapbox/dark-v11" // Dark theme to match your site
          terrain={{ source: 'mapbox-dem', exaggeration: 1.5 }}
        >
          {/* Optional: Add 3D terrain for more realism */}
          <source
            id="mapbox-dem"
            type="raster-dem"
            url="mapbox://mapbox.mapbox-terrain-dem-v1"
            tileSize={512}
            maxzoom={14}
          />
        </Map>
      </DeckGL>
    </div>
  );
}
