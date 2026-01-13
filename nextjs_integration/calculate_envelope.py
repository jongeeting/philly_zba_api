#!/usr/bin/env python3
"""
Zoning Envelope Calculator for Next.js API

This script is called by the Next.js API route to calculate building envelopes.
It outputs JSON to stdout for consumption by the Node.js process.

Usage:
    python calculate_envelope.py --parcel-id 123 --base-zoning CMX-3 --overlays /CDO --apply-bonuses
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path to import zoning engine
sys.path.insert(0, str(Path(__file__).parent.parent))

from zoning_rules_engine import ZoningRulesEngine, Parcel
from zoning_districts import load_districts_into_engine


def calculate_envelope(parcel_id: str, base_zoning: str, overlays: list[str],
                       apply_bonuses: bool = False, bonus_selections: list[str] = None):
    """
    Calculate maximum buildable envelope for a parcel.

    Returns JSON structure compatible with Deck.gl 3D visualization.
    """
    # Initialize engine
    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    # Create parcel
    # Note: In production, you'd fetch actual parcel data from database
    parcel = Parcel(
        parcel_id=parcel_id,
        address=f"Parcel {parcel_id}",  # Would come from DB
        base_zoning=base_zoning,
        overlays=overlays,
        lot_area=10000  # Would calculate from geometry
    )

    # Calculate maximum buildable envelope
    envelope = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=apply_bonuses,
        bonus_selections=bonus_selections
    )

    # Also calculate base (without bonuses) for comparison
    base_envelope = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=False
    )

    # Extract key parameters
    max_height = envelope.final_parameters.get('max_height')
    base_height = base_envelope.final_parameters.get('max_height')
    max_far = envelope.final_parameters.get('max_far')
    front_setback = envelope.final_parameters.get('front_setback')
    side_setback = envelope.final_parameters.get('side_setback')
    rear_setback = envelope.final_parameters.get('rear_setback')
    waterfront_setback = envelope.final_parameters.get('waterfront_setback')
    min_open_space = envelope.final_parameters.get('min_open_space')

    # Format output for 3D visualization
    result = {
        'parcel_id': parcel_id,
        'address': parcel.address,
        'base_zoning': base_zoning,
        'overlays': overlays,

        # Heights
        'max_height': max_height.value if max_height else 0,
        'base_height': base_height.value if base_height else 0,
        'height_unit': max_height.unit if max_height else "'",

        # Dimensional parameters
        'max_far': max_far.value if max_far else 0,
        'setbacks': {
            'front': front_setback.value if front_setback else 0,
            'side': side_setback.value if side_setback else 0,
            'rear': rear_setback.value if rear_setback else 0,
            'waterfront': waterfront_setback.value if waterfront_setback else None,
        },
        'min_open_space': min_open_space.value if min_open_space else 0,

        # All parameters (for detailed view)
        'parameters': {
            name: {
                'value': param.value,
                'unit': param.unit,
                'source': param.source,
                'type': param.parameter_type.value,
            }
            for name, param in envelope.final_parameters.items()
        },

        # Narrative explanation
        'narrative': envelope.get_narrative(),

        # Application steps (audit trail)
        'application_steps': [
            {
                'step': step.step_number,
                'source': step.source,
                'parameter': step.parameter,
                'old_value': step.old_value,
                'new_value': step.new_value,
                'reason': step.reason,
            }
            for step in envelope.application_steps
        ],

        # Bonuses applied
        'bonuses_applied': [
            {
                'name': bonus.name,
                'description': bonus.description,
                'parameter': bonus.parameter_modified,
                'amount': bonus.modification_amount,
            }
            for bonus in envelope.bonuses_applied
        ],

        # Visualization hints
        'visualization': {
            'color': [0, 255, 100] if apply_bonuses else [100, 200, 100],
            'opacity': 0.7,
            'wireframe': True,
        },

        # Placeholder geometry (would come from real parcel data)
        # This is a simple rectangle - replace with actual parcel footprint
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [-75.140, 39.950],
                [-75.140, 39.951],
                [-75.141, 39.951],
                [-75.141, 39.950],
                [-75.140, 39.950],
            ]]
        }
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='Calculate zoning building envelope')
    parser.add_argument('--parcel-id', required=True, help='Parcel ID')
    parser.add_argument('--base-zoning', required=True, help='Base zoning district code')
    parser.add_argument('--overlays', required=True, help='Comma-separated overlay codes')
    parser.add_argument('--apply-bonuses', action='store_true', help='Apply bonus provisions')
    parser.add_argument('--bonus-selections', help='Comma-separated bonus names to apply')

    args = parser.parse_args()

    # Parse overlays
    overlays = [o.strip() for o in args.overlays.split(',') if o.strip()]

    # Parse bonus selections
    bonus_selections = None
    if args.bonus_selections:
        bonus_selections = [b.strip() for b in args.bonus_selections.split(',') if b.strip()]

    try:
        result = calculate_envelope(
            parcel_id=args.parcel_id,
            base_zoning=args.base_zoning,
            overlays=overlays,
            apply_bonuses=args.apply_bonuses,
            bonus_selections=bonus_selections
        )

        # Output JSON to stdout (Node.js will parse this)
        print(json.dumps(result, indent=2))

    except Exception as e:
        # Output error as JSON
        error_result = {
            'error': str(e),
            'parcel_id': args.parcel_id,
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
