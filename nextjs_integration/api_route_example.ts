// app/api/zoning/envelope/route.ts
// Place this in your Next.js app's app/api/zoning/envelope/ directory

import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

/**
 * API Route: Calculate Zoning Envelope
 *
 * GET /api/zoning/envelope?parcel_id=123&bonuses=true
 *
 * Returns building envelope parameters for 3D visualization
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const parcelId = searchParams.get('parcel_id');
  const applyBonuses = searchParams.get('bonuses') === 'true';
  const baseZoning = searchParams.get('base_zoning') || 'CMX-3';
  const overlays = searchParams.get('overlays')?.split(',') || ['/CDO'];

  if (!parcelId) {
    return NextResponse.json(
      { error: 'parcel_id parameter required' },
      { status: 400 }
    );
  }

  try {
    // Call Python zoning engine
    const result = await calculateEnvelope({
      parcelId,
      baseZoning,
      overlays,
      applyBonuses,
    });

    return NextResponse.json(result, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600', // Cache for 1 hour
      },
    });
  } catch (error) {
    console.error('Zoning calculation error:', error);
    return NextResponse.json(
      { error: 'Failed to calculate zoning envelope' },
      { status: 500 }
    );
  }
}

interface EnvelopeParams {
  parcelId: string;
  baseZoning: string;
  overlays: string[];
  applyBonuses: boolean;
}

function calculateEnvelope(params: EnvelopeParams): Promise<any> {
  return new Promise((resolve, reject) => {
    // Path to your Python script (adjust based on your deployment)
    const scriptPath = path.join(
      process.cwd(),
      'python',
      'calculate_envelope.py'
    );

    const args = [
      scriptPath,
      '--parcel-id', params.parcelId,
      '--base-zoning', params.baseZoning,
      '--overlays', params.overlays.join(','),
    ];

    if (params.applyBonuses) {
      args.push('--apply-bonuses');
    }

    const python = spawn('python3', args);

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
        reject(new Error(`Python process exited with code ${code}: ${error}`));
      } else {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${output}`));
        }
      }
    });

    // Timeout after 10 seconds
    setTimeout(() => {
      python.kill();
      reject(new Error('Zoning calculation timed out'));
    }, 10000);
  });
}

// Alternative: If you want to avoid Python subprocess,
// you could port the engine to TypeScript or use a serverless Python function
