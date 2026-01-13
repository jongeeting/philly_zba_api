"""
Philadelphia Zoning Districts Database

This module contains the actual zoning regulations for Philadelphia base districts
and overlay districts, encoded as ZoningDistrict objects.

Legal Authority: Philadelphia Code Title 14

Data Sources:
- Philadelphia Code § 14-400 (Base Districts)
- Philadelphia Code § 14-500 (Overlay Districts)
- Philadelphia Code § 14-700 (Development Standards)
"""

from zoning_rules_engine import (
    ZoningDistrict, ZoningParameter, BonusProvision,
    ParameterType, ModificationType, create_parameter
)


# =============================================================================
# BASE ZONING DISTRICTS
# =============================================================================

def create_cmx3_district() -> ZoningDistrict:
    """
    CMX-3 Commercial Mixed-Use District

    High-density mixed-use district typical in Center City and major corridors.
    Allows residential, commercial, and institutional uses.

    Legal Reference: Philadelphia Code § 14-402(3)
    """
    parameters = {
        'max_height': create_parameter('max_height', 65, "'", ParameterType.DIMENSIONAL),
        'max_height_stories': create_parameter('max_height_stories', 6, " stories", ParameterType.DIMENSIONAL),
        'max_far': create_parameter('max_far', 4.0, "", ParameterType.DIMENSIONAL),
        'max_lot_coverage': create_parameter('max_lot_coverage', 100, "%", ParameterType.DIMENSIONAL),
        'front_setback': create_parameter('front_setback', 0, "'", ParameterType.DIMENSIONAL),
        'side_setback': create_parameter('side_setback', 0, "'", ParameterType.DIMENSIONAL),
        'rear_setback': create_parameter('rear_setback', 0, "'", ParameterType.DIMENSIONAL),
        'min_open_space': create_parameter('min_open_space', 0, "%", ParameterType.DIMENSIONAL),
        'ground_floor_uses': create_parameter(
            'ground_floor_uses',
            ['retail', 'restaurant', 'office', 'residential'],
            "",
            ParameterType.USE
        ),
        'parking_min': create_parameter('parking_min', 0, " spaces/unit", ParameterType.DIMENSIONAL),
        'parking_max': create_parameter('parking_max', 999, " spaces/unit", ParameterType.DIMENSIONAL),
    }

    return ZoningDistrict(
        code='CMX-3',
        name='Commercial Mixed-Use 3',
        is_overlay=False,
        parameters=parameters,
        description='High-density mixed-use district for urban centers and major corridors'
    )


def create_cmx4_district() -> ZoningDistrict:
    """
    CMX-4 Commercial Mixed-Use District

    Very high-density mixed-use district for Center City core.

    Legal Reference: Philadelphia Code § 14-402(4)
    """
    parameters = {
        'max_height': create_parameter('max_height', 120, "'", ParameterType.DIMENSIONAL),
        'max_height_stories': create_parameter('max_height_stories', 12, " stories", ParameterType.DIMENSIONAL),
        'max_far': create_parameter('max_far', 10.0, "", ParameterType.DIMENSIONAL),
        'max_lot_coverage': create_parameter('max_lot_coverage', 100, "%", ParameterType.DIMENSIONAL),
        'front_setback': create_parameter('front_setback', 0, "'", ParameterType.DIMENSIONAL),
        'side_setback': create_parameter('side_setback', 0, "'", ParameterType.DIMENSIONAL),
        'rear_setback': create_parameter('rear_setback', 0, "'", ParameterType.DIMENSIONAL),
        'min_open_space': create_parameter('min_open_space', 0, "%", ParameterType.DIMENSIONAL),
        'ground_floor_uses': create_parameter(
            'ground_floor_uses',
            ['retail', 'restaurant', 'office', 'residential', 'cultural'],
            "",
            ParameterType.USE
        ),
        'parking_min': create_parameter('parking_min', 0, " spaces/unit", ParameterType.DIMENSIONAL),
        'parking_max': create_parameter('parking_max', 999, " spaces/unit", ParameterType.DIMENSIONAL),
    }

    return ZoningDistrict(
        code='CMX-4',
        name='Commercial Mixed-Use 4',
        is_overlay=False,
        parameters=parameters,
        description='Very high-density mixed-use district for Center City core'
    )


def create_rsa5_district() -> ZoningDistrict:
    """
    RSA-5 Residential Single-Family Attached District

    Rowhouse district typical of Philadelphia neighborhoods.

    Legal Reference: Philadelphia Code § 14-401(5)
    """
    parameters = {
        'max_height': create_parameter('max_height', 38, "'", ParameterType.DIMENSIONAL),
        'max_height_stories': create_parameter('max_height_stories', 3, " stories", ParameterType.DIMENSIONAL),
        'max_far': create_parameter('max_far', 1.0, "", ParameterType.DIMENSIONAL),
        'max_lot_coverage': create_parameter('max_lot_coverage', 80, "%", ParameterType.DIMENSIONAL),
        'front_setback': create_parameter('front_setback', 0, "'", ParameterType.DIMENSIONAL),
        'side_setback': create_parameter('side_setback', 0, "'", ParameterType.DIMENSIONAL),
        'rear_setback': create_parameter('rear_setback', 12, "'", ParameterType.DIMENSIONAL),
        'min_open_space': create_parameter('min_open_space', 20, "%", ParameterType.DIMENSIONAL),
        'min_lot_width': create_parameter('min_lot_width', 14, "'", ParameterType.DIMENSIONAL),
        'min_lot_area': create_parameter('min_lot_area', 1000, " SF", ParameterType.DIMENSIONAL),
        'ground_floor_uses': create_parameter(
            'ground_floor_uses',
            ['single-family', 'two-family'],
            "",
            ParameterType.USE
        ),
        'parking_min': create_parameter('parking_min', 0, " spaces/unit", ParameterType.DIMENSIONAL),
    }

    return ZoningDistrict(
        code='RSA-5',
        name='Residential Single-Family Attached 5',
        is_overlay=False,
        parameters=parameters,
        description='Rowhouse district typical of Philadelphia neighborhoods'
    )


# =============================================================================
# OVERLAY DISTRICTS
# =============================================================================

def create_central_delaware_overlay() -> ZoningDistrict:
    """
    /CDO - Central Delaware Riverfront Overlay District

    Regulates development along the Delaware River waterfront from
    Allegheny Avenue to Oregon Avenue.

    Key Features:
    - 100' base height (supersedes base zoning)
    - Up to 144' of height bonuses available (max 244' total)
    - 50' waterfront setback
    - 40% open space requirement for lots > 5,000 SF
    - Active ground floor uses required

    Legal Reference: Philadelphia Code § 14-507
    """
    parameters = {
        # HEIGHT: Supersedes base zoning - overlay wins
        'max_height': create_parameter('max_height', 100, "'", ParameterType.DIMENSIONAL),

        # SETBACKS: Adds waterfront setback requirement
        'waterfront_setback': create_parameter('waterfront_setback', 50, "'", ParameterType.DIMENSIONAL),

        # OPEN SPACE: Adds requirement for riverfront parcels
        'min_open_space': create_parameter('min_open_space', 40, "%", ParameterType.DIMENSIONAL),

        # GROUND FLOOR: Supersedes base - requires active uses
        'ground_floor_uses': create_parameter(
            'ground_floor_uses',
            ['retail', 'restaurant', 'cultural', 'public_access'],
            "",
            ParameterType.USE
        ),

        # DESIGN: Adds ground floor transparency requirement
        'ground_floor_transparency': create_parameter(
            'ground_floor_transparency',
            60,
            "%",
            ParameterType.DESIGN
        ),
    }

    # Height bonuses available in /CDO
    bonuses = [
        BonusProvision(
            name='LEED_Silver',
            description='LEED Silver Certification',
            parameter_modified='max_height',
            modification_amount=24,
            requirements=['Achieve LEED Silver certification'],
            source_overlay='/CDO',
            can_combine=True,
            max_cumulative=144
        ),
        BonusProvision(
            name='LEED_Gold',
            description='LEED Gold Certification',
            parameter_modified='max_height',
            modification_amount=36,
            requirements=['Achieve LEED Gold certification'],
            source_overlay='/CDO',
            can_combine=True,
            max_cumulative=144
        ),
        BonusProvision(
            name='LEED_Platinum',
            description='LEED Platinum Certification',
            parameter_modified='max_height',
            modification_amount=48,
            requirements=['Achieve LEED Platinum certification'],
            source_overlay='/CDO',
            can_combine=True,
            max_cumulative=144
        ),
        BonusProvision(
            name='Waterfront_Trail',
            description='Construct segment of waterfront trail',
            parameter_modified='max_height',
            modification_amount=48,
            requirements=['Construct and dedicate waterfront trail segment per City specifications'],
            source_overlay='/CDO',
            can_combine=True,
            max_cumulative=144
        ),
        BonusProvision(
            name='Public_Plaza',
            description='Provide public park or plaza',
            parameter_modified='max_height',
            modification_amount=36,
            requirements=['Provide publicly-accessible park or plaza, minimum 5,000 SF'],
            source_overlay='/CDO',
            can_combine=True,
            max_cumulative=144
        ),
        BonusProvision(
            name='Mixed_Income',
            description='Mixed-income housing (20% affordable)',
            parameter_modified='max_height',
            modification_amount=24,
            requirements=['Provide 20% of dwelling units affordable at 60% AMI'],
            source_overlay='/CDO',
            can_combine=True,
            max_cumulative=144
        ),
    ]

    return ZoningDistrict(
        code='/CDO',
        name='Central Delaware Riverfront Overlay',
        is_overlay=True,
        parameters=parameters,
        bonuses=bonuses,
        description='Regulates Delaware River waterfront development'
    )


def create_center_city_overlay() -> ZoningDistrict:
    """
    /CTR - Center City Overlay District

    Manages density and design in Center City core.

    Key Features:
    - Parking maximums (limits parking to encourage transit)
    - Ground floor transparency requirements
    - Through-block connection incentives
    - Height bonuses for public plazas

    Legal Reference: Philadelphia Code § 14-508
    """
    parameters = {
        # PARKING: Supersedes base - limits parking
        'parking_max': create_parameter('parking_max', 0.5, " spaces/unit", ParameterType.DIMENSIONAL),

        # DESIGN: Adds transparency requirement
        'ground_floor_transparency': create_parameter(
            'ground_floor_transparency',
            70,
            "%",
            ParameterType.DESIGN
        ),

        # DESIGN: Loading berth screening required
        'loading_screening': create_parameter(
            'loading_screening',
            ['Must screen loading areas from public view', 'No loading on primary street frontage'],
            "",
            ParameterType.DESIGN
        ),
    }

    bonuses = [
        BonusProvision(
            name='Public_Plaza_CTR',
            description='Provide publicly-accessible plaza',
            parameter_modified='max_height',
            modification_amount=30,
            requirements=['Provide plaza accessible to public 24/7, minimum 3,000 SF'],
            source_overlay='/CTR',
            can_combine=True,
            max_cumulative=None
        ),
        BonusProvision(
            name='Through_Block_Connection',
            description='Create through-block pedestrian connection',
            parameter_modified='max_height',
            modification_amount=20,
            requirements=['Create publicly-accessible through-block connection'],
            source_overlay='/CTR',
            can_combine=True,
            max_cumulative=None
        ),
    ]

    return ZoningDistrict(
        code='/CTR',
        name='Center City Overlay',
        is_overlay=True,
        parameters=parameters,
        bonuses=bonuses,
        description='Manages density and design in Center City core'
    )


def create_mixed_income_overlay() -> ZoningDistrict:
    """
    /MIN - Mixed Income Neighborhoods Overlay

    Incentivizes creation of affordable housing through density bonuses.

    Key Features:
    - Dwelling unit density bonuses (20% more units for affordable housing)
    - Height bonuses for affordable units
    - Parking requirement reductions
    - Fast-track review process

    Legal Reference: Philadelphia Code § 14-519
    """
    parameters = {
        # PARKING: Reduces minimum parking for affordable projects
        'parking_min': create_parameter('parking_min', 0.5, " spaces/unit", ParameterType.DIMENSIONAL),
    }

    bonuses = [
        BonusProvision(
            name='Affordable_20pct',
            description='20% affordable units at 60% AMI',
            parameter_modified='max_dwelling_units',
            modification_amount=0.2,  # 20% increase in units
            requirements=['Provide 20% of units affordable at 60% AMI for 30 years'],
            source_overlay='/MIN',
            can_combine=False,
            max_cumulative=None
        ),
        BonusProvision(
            name='Affordable_30pct',
            description='30% affordable units at 60% AMI',
            parameter_modified='max_dwelling_units',
            modification_amount=0.3,  # 30% increase in units
            requirements=['Provide 30% of units affordable at 60% AMI for 30 years'],
            source_overlay='/MIN',
            can_combine=False,
            max_cumulative=None
        ),
        BonusProvision(
            name='Affordable_Height',
            description='Height bonus for affordable housing',
            parameter_modified='max_height',
            modification_amount=15,
            requirements=['Provide 20% affordable units at 60% AMI'],
            source_overlay='/MIN',
            can_combine=True,
            max_cumulative=45
        ),
    ]

    return ZoningDistrict(
        code='/MIN',
        name='Mixed Income Neighborhoods Overlay',
        is_overlay=True,
        parameters=parameters,
        bonuses=bonuses,
        description='Incentivizes affordable housing creation through density bonuses'
    )


def create_northeast_overlay() -> ZoningDistrict:
    """
    /NE - Northeast Overlay District

    Controls development in Northeast Philadelphia.

    Key Features:
    - Increased setbacks for residential uses
    - Landscaping requirements for parking lots
    - Prohibition on certain commercial uses
    - Minimum lot sizes

    Legal Reference: Philadelphia Code § 14-515
    """
    parameters = {
        # SETBACKS: Increases from base
        'front_setback': create_parameter('front_setback', 20, "'", ParameterType.DIMENSIONAL),
        'side_setback': create_parameter('side_setback', 10, "'", ParameterType.DIMENSIONAL),

        # LOT STANDARDS: Adds minimum dimensions
        'min_lot_width': create_parameter('min_lot_width', 50, "'", ParameterType.DIMENSIONAL),
        'min_lot_area': create_parameter('min_lot_area', 5000, " SF", ParameterType.DIMENSIONAL),

        # DESIGN: Parking lot landscaping
        'parking_landscaping': create_parameter(
            'parking_landscaping',
            ['20% of parking lot area must be landscaped', 'Trees required every 8 parking spaces'],
            "",
            ParameterType.DESIGN
        ),

        # USES: Prohibits certain commercial
        'prohibited_uses': create_parameter(
            'prohibited_uses',
            ['auto_repair', 'salvage_yard', 'truck_terminal'],
            "",
            ParameterType.USE
        ),
    }

    return ZoningDistrict(
        code='/NE',
        name='Northeast Overlay District',
        is_overlay=True,
        parameters=parameters,
        description='Controls development in Northeast Philadelphia'
    )


# =============================================================================
# DISTRICT REGISTRY
# =============================================================================

def get_all_districts() -> dict:
    """
    Get all defined zoning districts and overlays.

    Returns:
        Dictionary mapping district codes to ZoningDistrict objects
    """
    districts = {
        # Base districts
        'CMX-3': create_cmx3_district(),
        'CMX-4': create_cmx4_district(),
        'RSA-5': create_rsa5_district(),

        # Overlay districts
        '/CDO': create_central_delaware_overlay(),
        '/CTR': create_center_city_overlay(),
        '/MIN': create_mixed_income_overlay(),
        '/NE': create_northeast_overlay(),
    }

    return districts


def load_districts_into_engine(engine):
    """
    Load all districts into a ZoningRulesEngine instance.

    Args:
        engine: ZoningRulesEngine instance to load districts into
    """
    districts = get_all_districts()
    for district in districts.values():
        engine.register_district(district)
