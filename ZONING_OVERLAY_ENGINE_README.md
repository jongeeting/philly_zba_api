# Philadelphia Zoning Overlay Rules Engine

A legally-compliant rules engine that applies Philadelphia zoning overlay districts in the correct legal sequence to determine the maximum buildable project on a given parcel.

## Overview

Philadelphia parcels often have multiple overlays that stack on top of base zoning (e.g., Central Delaware Overlay, Center City Overlay, Mixed Income Neighborhoods Overlay). These overlays must be applied in a specific legal sequence, with each overlay potentially modifying what previous layers allow.

This rules engine implements the legal framework from **Philadelphia Code Title 14, Chapter 14-500** to correctly sequence and apply overlays, producing:

- **Step-by-step audit trail** showing how each overlay modifies the buildable envelope
- **Final maximum buildable parameters** (height, setbacks, FAR, lot coverage, etc.)
- **Human-readable narratives** explaining the legal logic
- **Bonus provision tracking** for optional public benefit incentives

## Key Legal Principles

The engine implements three critical legal principles from Philadelphia Code § 14-500:

### 1. Overlay Supremacy
> **Overlay district provisions override base zoning, regardless of whether more or less restrictive.**

Example: If CMX-3 allows 65' height but /CDO allows 100', the overlay's 100' applies.

### 2. Stricter Standard Among Overlays
> **When multiple overlays conflict, the stricter provision governs (unless specified otherwise).**

Example: If /CDO requires 60% ground floor transparency and /CTR requires 70%, then 70% applies.

### 3. Application Sequence
```
BASE ZONING → OVERLAY(S) → BONUSES → FINAL ENVELOPE
```

Bonuses are applied **after** all overlays and cannot violate overlay maximums.

## Installation

```bash
# No external dependencies required - uses Python standard library only
python3 examples_overlay_application.py  # Run examples
python3 test_zoning_rules_engine.py      # Run tests
```

## Quick Start

```python
from zoning_rules_engine import ZoningRulesEngine, Parcel
from zoning_districts import load_districts_into_engine

# Create and initialize engine
engine = ZoningRulesEngine()
load_districts_into_engine(engine)

# Define a parcel
parcel = Parcel(
    parcel_id="0123456789",
    address="123 Delaware Ave, Philadelphia PA 19123",
    base_zoning="CMX-3",
    overlays=["/CDO"],  # Central Delaware Overlay
    lot_area=10000
)

# Calculate maximum buildable envelope
envelope = engine.calculate_maximum_buildable(
    parcel=parcel,
    apply_bonuses=False
)

# Get human-readable narrative
print(envelope.get_narrative())
# Output: "Base zoning CMX-3 allows max height of 65', max far of 4.0,
#          front setback of 0'. Central Delaware Overlay modifies max height
#          to 100' and requires waterfront setback of 50' and requires
#          min open space of 40%. Therefore, maximum buildable envelope is:
#          max height of 100', max far of 4.0, front setback of 0',
#          min open space of 40%."

# Access final parameters
print(f"Max Height: {envelope.final_parameters['max_height'].value}'")
print(f"Max FAR: {envelope.final_parameters['max_far'].value}")
print(f"Waterfront Setback: {envelope.final_parameters['waterfront_setback'].value}'")
```

## Architecture

### Core Components

#### 1. **ZoningRulesEngine** (`zoning_rules_engine.py`)
The main rules engine that applies overlays in legally-correct sequence.

**Key Methods:**
- `calculate_maximum_buildable(parcel, apply_bonuses, bonus_selections)` - Main entry point
- `_apply_overlay(current_parameters, overlay, step_number)` - Apply single overlay
- `_apply_bonuses(current_parameters, parcel, bonus_selections, step_number)` - Apply bonuses

#### 2. **ZoningDistrict** (`zoning_districts.py`)
Database of actual Philadelphia zoning districts and overlays with their regulations.

**Included Districts:**
- **Base Districts:** CMX-3, CMX-4, RSA-5
- **Overlays:** /CDO (Central Delaware), /CTR (Center City), /MIN (Mixed Income), /NE (Northeast)

Each district includes:
- Dimensional standards (height, FAR, setbacks, lot coverage)
- Use regulations (permitted/prohibited uses)
- Design standards (transparency, landscaping, materials)
- Bonus provisions (height/density bonuses for public benefits)

#### 3. **Data Models** (`zoning_rules_engine.py`)

**ZoningParameter**
```python
@dataclass
class ZoningParameter:
    name: str                        # e.g., "max_height"
    value: Any                       # e.g., 100
    unit: str                        # e.g., "'"
    parameter_type: ParameterType    # DIMENSIONAL, USE, DESIGN, PROCEDURAL
    source: str                      # Which district/overlay set this
    modification_type: ModificationType  # SUPERSEDE, ADD, NONE
```

**MaximumBuildableEnvelope**
```python
@dataclass
class MaximumBuildableEnvelope:
    parcel: Parcel
    final_parameters: Dict[str, ZoningParameter]
    application_steps: List[ApplicationStep]
    bonuses_applied: List[BonusProvision]
```

### Legal Framework Documentation

See `docs/OVERLAY_LEGAL_FRAMEWORK.md` for comprehensive documentation of:
- Legal hierarchy and application sequence
- Conflict resolution rules
- Overlay district details
- Parameters modified by overlays
- Worked examples with step-by-step logic

## Examples

The `examples_overlay_application.py` file includes 5 comprehensive scenarios:

### Scenario 1: CMX-3 + /CDO (No Bonuses)
Demonstrates basic overlay superseding base height and adding new requirements.

**Result:** 100' height (vs 65' base), 50' waterfront setback, 40% open space

### Scenario 2: CMX-3 + /CDO + Bonuses
Same parcel but developer pursues LEED Gold + Waterfront Trail bonuses.

**Result:** 184' height (100' base + 36' LEED + 48' trail), 4.0 FAR

### Scenario 3: CMX-3 + /CDO + /CTR (Multiple Overlays)
Multiple overlays with conflict resolution.

**Result:** Ground floor transparency 70% (stricter of 60% vs 70%), parking max 0.5 spaces/unit

### Scenario 4: CMX-4 + /MIN (Affordable Housing)
High-density base with affordable housing bonuses.

**Result:** 135' height (120' + 15' affordable bonus), parking reduced to 0.5 spaces/unit

### Scenario 5: RSA-5 + /NE (Residential + Northeast)
Rowhouse district with restrictive suburban overlay.

**Result:** Setbacks increased to 20' front / 10' side, min lot 50' wide × 5,000 SF

Run all examples:
```bash
python3 examples_overlay_application.py
```

## Testing

Comprehensive test suite validates all critical functionality:

```bash
python3 test_zoning_rules_engine.py
```

**Test Coverage:**
- ✅ Overlay supremacy over base zoning
- ✅ Stricter-wins conflict resolution
- ✅ Additive vs. superseding behavior
- ✅ Bonus application logic
- ✅ Cumulative bonuses with maximums
- ✅ Edge cases and error handling
- ✅ Real-world integration scenarios

## Central Delaware Overlay (/CDO) - Detailed Example

The /CDO is one of Philadelphia's most important overlays, regulating the Delaware River waterfront.

### Base Standards (§ 14-507)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Height** | 100 feet | Supersedes base zoning |
| **Waterfront Setback** | 50 feet | From top of bank |
| **Open Space** | 40% | For lots > 5,000 SF |
| **Ground Floor Uses** | Active uses required | Retail, restaurant, public access |

### Available Bonuses (§ 14-507(6))

Developers can earn **up to 144 feet** of additional height (max 244' total):

| Public Benefit | Height Bonus |
|----------------|--------------|
| LEED Silver | +24 feet |
| LEED Gold | +36 feet |
| LEED Platinum | +48 feet |
| Waterfront trail segment | +48 feet |
| Public park/plaza (5,000+ SF) | +36 feet |
| Mixed-income housing (20% affordable) | +24 feet |

**Bonuses can combine** (e.g., LEED Platinum + Trail = 96' bonus) but total cannot exceed 144'.

### Example Calculation

**Parcel:** 123 Delaware Ave (CMX-3 + /CDO)

**Step 1 - Base Zoning CMX-3:**
- Height: 65'
- FAR: 4.0
- Setbacks: 0' (urban)

**Step 2 - Apply /CDO Overlay:**
- Height: 100' (**supersedes** 65')
- FAR: 4.0 (unchanged)
- Waterfront Setback: 50' (**adds** new requirement)
- Open Space: 40% (**adds** new requirement)

**Step 3 - Apply Bonuses (LEED Gold + Trail):**
- Height: 100' + 36' + 48' = **184'**

**Final Maximum Buildable:**
- **Height:** 184 feet
- **FAR:** 4.0
- **Setbacks:** 50' waterfront, 0' other sides
- **Open Space:** 40% of lot
- **Ground Floor:** Active uses with 60% transparency

## API Reference

### ZoningRulesEngine.calculate_maximum_buildable()

```python
def calculate_maximum_buildable(
    parcel: Parcel,
    apply_bonuses: bool = False,
    bonus_selections: Optional[List[str]] = None
) -> MaximumBuildableEnvelope
```

**Parameters:**
- `parcel` - Parcel object with base zoning and overlay assignments
- `apply_bonuses` - Whether to apply bonus provisions
- `bonus_selections` - List of specific bonus names to apply (if None, applies all available)

**Returns:**
- `MaximumBuildableEnvelope` with final parameters, application steps, and bonuses applied

**Example:**
```python
envelope = engine.calculate_maximum_buildable(
    parcel=my_parcel,
    apply_bonuses=True,
    bonus_selections=['LEED_Gold', 'Waterfront_Trail']
)
```

### MaximumBuildableEnvelope.get_narrative()

```python
def get_narrative() -> str
```

Generates human-readable narrative explaining the overlay application process.

**Returns:**
- String describing the step-by-step logic

**Example Output:**
```
"Base zoning CMX-3 allows max height of 65', max far of 4.0. Central Delaware
Overlay modifies max height to 100' and requires waterfront setback of 50'.
LEED Gold Bonus increases max height to 136'. Therefore, maximum buildable
envelope is: max height of 136', max far of 4.0, front setback of 0',
waterfront setback of 50'."
```

## File Structure

```
philly_zba_api/
├── zoning_rules_engine.py           # Core rules engine
├── zoning_districts.py              # District/overlay definitions
├── examples_overlay_application.py  # Working examples
├── test_zoning_rules_engine.py      # Test suite
├── docs/
│   └── OVERLAY_LEGAL_FRAMEWORK.md   # Legal documentation
└── ZONING_OVERLAY_ENGINE_README.md  # This file
```

## Extending the Engine

### Adding a New Overlay District

1. **Create the district definition** in `zoning_districts.py`:

```python
def create_my_overlay() -> ZoningDistrict:
    """
    /MYO - My Custom Overlay
    """
    parameters = {
        'max_height': create_parameter('max_height', 150, "'", ParameterType.DIMENSIONAL),
        # ... more parameters
    }

    bonuses = [
        BonusProvision(
            name='My_Bonus',
            description='Bonus for providing X',
            parameter_modified='max_height',
            modification_amount=20,
            requirements=['Provide X'],
            source_overlay='/MYO',
            can_combine=True,
            max_cumulative=100
        ),
    ]

    return ZoningDistrict(
        code='/MYO',
        name='My Custom Overlay',
        is_overlay=True,
        parameters=parameters,
        bonuses=bonuses,
        description='Description of overlay'
    )
```

2. **Register in `get_all_districts()`**:

```python
def get_all_districts() -> dict:
    districts = {
        # ... existing districts
        '/MYO': create_my_overlay(),
    }
    return districts
```

3. **Test it**:

```python
parcel = Parcel(
    parcel_id="TEST",
    address="Test",
    base_zoning="CMX-3",
    overlays=["/MYO"]
)
envelope = engine.calculate_maximum_buildable(parcel)
```

### Adding a New Base District

Follow the same pattern but set `is_overlay=False`:

```python
def create_my_base_district() -> ZoningDistrict:
    return ZoningDistrict(
        code='MY-1',
        name='My Base District',
        is_overlay=False,  # ← Key difference
        parameters=parameters,
        description='...'
    )
```

## Integration with 3D Massing Models

This rules engine is designed as the **first step** toward 3D massing visualization. Next steps:

1. **Integrate with parcel GIS data** - Link parcels to actual geometries
2. **Connect to 3D engine** - Use final parameters to generate building envelopes
3. **Visualize step-by-step** - Show how each overlay modifies the 3D massing
4. **Add variance modeling** - Model impact of ZBA variances on envelope

### Example Integration Flow

```python
# 1. Get zoning envelope
envelope = engine.calculate_maximum_buildable(parcel)

# 2. Extract key parameters for 3D model
max_height = envelope.final_parameters['max_height'].value
max_far = envelope.final_parameters['max_far'].value
setbacks = {
    'front': envelope.final_parameters['front_setback'].value,
    'side': envelope.final_parameters.get('side_setback', {}).get('value', 0),
    'rear': envelope.final_parameters.get('rear_setback', {}).get('value', 0),
}

# 3. Generate 3D massing
# massing_model = generate_3d_envelope(
#     parcel_geometry=parcel.geometry,
#     max_height=max_height,
#     setbacks=setbacks,
#     max_far=max_far
# )

# 4. Visualize
# visualize_3d(massing_model)
```

## Known Limitations

1. **Partial overlay coverage** - Current implementation assumes full parcel is in overlay; doesn't handle parcels partially in overlay boundaries
2. **Temporal changes** - No tracking of zoning changes over time or sunset provisions
3. **Vested rights** - Doesn't model grandfathered uses or prior approvals
4. **Nonconforming uses** - Doesn't handle existing buildings that predate current code
5. **Special exceptions** - Doesn't model ZBA variances (could be added as future enhancement)

## Legal Disclaimer

This software is for informational and planning purposes only. For legally binding zoning determinations, consult:
- Official Philadelphia Code: https://codelibrary.amlegal.com/codes/philadelphia/
- Philadelphia Department of Licenses & Inspections
- A licensed attorney specializing in land use law

The rules engine represents a good-faith interpretation of Philadelphia zoning law based on publicly available sources as of January 2026.

## Data Sources

### Legal Authority
- **Philadelphia Code Title 14** - Zoning and Planning
- **Chapter 14-500** - Overlay Zoning Districts
- **§ 14-507** - Central Delaware Riverfront Overlay
- **§ 14-702** - Floor Area, Height, and Dwelling Unit Density Bonuses

### Supporting Documentation
- [Philadelphia Zoning Code Quick Guide (Sept 2022)](https://www.phila.gov/media/20220909084529/ZONING-QUICK-GUIDE_PCPC_9_9_22.pdf)
- [Central Delaware Overlay Resources](https://www.delawareriverwaterfront.com/planning/planning/central-delaware-overlay)
- Philadelphia City Planning Commission documentation

## Contributing

To add more overlay districts or base districts:

1. Research the legal requirements from Philadelphia Code Title 14
2. Add district definition to `zoning_districts.py`
3. Add tests to `test_zoning_rules_engine.py`
4. Add example scenario to `examples_overlay_application.py`
5. Update documentation

## License

This project is part of the Philadelphia ZBA Housing Tracker.

## Contact

For questions about the rules engine or to report issues, please open an issue on the project repository.

---

**Version:** 1.0
**Last Updated:** January 13, 2026
**Legal Framework:** Philadelphia Code Title 14 (as of January 2026)
