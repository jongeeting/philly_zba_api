"""
Philadelphia Zoning Overlay Rules Engine

This module implements the legally-correct sequencing and application of Philadelphia
zoning overlay districts to determine maximum buildable parameters for parcels.

Legal Authority: Philadelphia Code Title 14, Chapter 14-500 (Overlay Zoning Districts)

Key Principles:
1. Overlay provisions override base zoning (regardless of restrictiveness)
2. Among multiple overlays, stricter standard applies (unless specified otherwise)
3. Bonuses are applied AFTER overlays
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from decimal import Decimal


class ModificationType(Enum):
    """How an overlay modifies a base zoning parameter"""
    SUPERSEDE = "supersede"  # Replace base value entirely
    ADD = "add"  # Add new requirement alongside base
    NONE = "none"  # Overlay doesn't modify this parameter


class ParameterType(Enum):
    """Type of zoning parameter - determines conflict resolution logic"""
    DIMENSIONAL = "dimensional"  # Height, setback, FAR, lot coverage (stricter wins)
    USE = "use"  # Permitted uses (intersection of all allowed)
    DESIGN = "design"  # Design standards (cumulative, must satisfy all)
    PROCEDURAL = "procedural"  # Review processes (most stringent applies)


@dataclass
class ZoningParameter:
    """
    A single zoning parameter (e.g., height, setback, FAR)

    Attributes:
        name: Parameter identifier (e.g., "max_height", "front_setback")
        value: Current value (number, string, list, etc.)
        unit: Unit of measurement (feet, ratio, percent, etc.)
        parameter_type: Type of parameter for conflict resolution
        source: Which district/overlay set this value
        modification_type: How this was set (base, superseded, added)
    """
    name: str
    value: Any
    unit: str
    parameter_type: ParameterType
    source: str
    modification_type: ModificationType = ModificationType.NONE
    notes: str = ""

    def is_stricter_than(self, other: 'ZoningParameter') -> bool:
        """
        Determine if this parameter is stricter (more restrictive) than another.

        "Stricter" means more limiting to development rights:
        - Lower is stricter for: height, FAR, lot coverage, dwelling units
        - Higher is stricter for: setbacks, open space, parking minimums
        - Fewer is stricter for: permitted uses
        """
        if self.name != other.name:
            raise ValueError(f"Cannot compare different parameters: {self.name} vs {other.name}")

        # Define which parameters use "lower is stricter" vs "higher is stricter"
        lower_is_stricter = {
            'max_height', 'max_height_stories', 'max_far', 'max_lot_coverage',
            'max_dwelling_units', 'max_parking_spaces', 'max_stories'
        }

        higher_is_stricter = {
            'front_setback', 'side_setback', 'rear_setback', 'waterfront_setback',
            'min_open_space', 'min_parking_spaces', 'min_lot_width', 'min_lot_area'
        }

        if self.name in lower_is_stricter:
            return self.value < other.value
        elif self.name in higher_is_stricter:
            return self.value > other.value
        else:
            # For non-numeric or special cases, can't automatically determine
            # Return False (keep existing)
            return False


@dataclass
class BonusProvision:
    """
    A bonus that can be earned by providing public benefits.

    Bonuses are OPTIONAL enhancements applied AFTER overlay requirements.
    """
    name: str
    description: str
    parameter_modified: str  # Which parameter this bonus affects
    modification_amount: Any  # How much the parameter changes
    requirements: List[str]  # What must be provided to earn this bonus
    source_overlay: Optional[str] = None  # Which overlay provides this bonus
    can_combine: bool = True  # Can this bonus be combined with others?
    max_cumulative: Optional[Any] = None  # Maximum total bonus across all provisions


@dataclass
class ZoningDistrict:
    """
    Base zoning district or overlay district with all its regulations.

    This represents a complete set of zoning regulations from a single source
    (e.g., CMX-3 base district, or /CDO overlay).
    """
    code: str  # District code (e.g., "CMX-3", "/CDO")
    name: str  # Full name
    is_overlay: bool  # True if overlay, False if base district
    parameters: Dict[str, ZoningParameter]  # All zoning parameters
    bonuses: List[BonusProvision] = field(default_factory=list)  # Available bonuses
    description: str = ""

    def get_parameter(self, param_name: str) -> Optional[ZoningParameter]:
        """Get a specific parameter by name"""
        return self.parameters.get(param_name)

    def get_bonuses_for_parameter(self, param_name: str) -> List[BonusProvision]:
        """Get all bonuses that modify a specific parameter"""
        return [b for b in self.bonuses if b.parameter_modified == param_name]


@dataclass
class Parcel:
    """
    A real estate parcel with its zoning assignments.

    Attributes:
        parcel_id: Unique identifier (e.g., PIN)
        address: Street address
        base_zoning: Base zoning district code
        overlays: List of overlay district codes that apply
        lot_area: Parcel area in square feet
        geometry: Optional GIS geometry
    """
    parcel_id: str
    address: str
    base_zoning: str
    overlays: List[str] = field(default_factory=list)
    lot_area: Optional[float] = None
    geometry: Optional[Any] = None  # Could be shapely geometry
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplicationStep:
    """
    Records a single step in the overlay application process.

    This creates an audit trail showing how each regulation modified the result.
    """
    step_number: int
    source: str  # "BASE: CMX-3" or "OVERLAY: /CDO" or "BONUS: LEED Gold"
    parameter: str
    old_value: Any
    new_value: Any
    reason: str  # Explanation of why this change was made
    modification_type: ModificationType


@dataclass
class MaximumBuildableEnvelope:
    """
    The final output: maximum buildable parameters after applying all regulations.

    This represents the largest legally-compliant building that can be built
    on the parcel, showing the step-by-step logic of how overlays were applied.
    """
    parcel: Parcel
    final_parameters: Dict[str, ZoningParameter]
    application_steps: List[ApplicationStep]
    bonuses_applied: List[BonusProvision] = field(default_factory=list)

    def get_narrative(self) -> str:
        """
        Generate a human-readable narrative of the overlay application process.

        Returns a string like:
        "Base zoning CMX-3 allows 65' height and 4.0 FAR. Central Delaware Overlay
        increases height to 100' and requires 50' waterfront setback. LEED Gold bonus
        increases height to 136'. Therefore maximum buildable is 136' height, 4.0 FAR, ..."
        """
        narrative_parts = []

        # Group steps by source
        base_steps = [s for s in self.application_steps if s.source.startswith("BASE")]
        overlay_steps = [s for s in self.application_steps if s.source.startswith("OVERLAY")]
        bonus_steps = [s for s in self.application_steps if s.source.startswith("BONUS")]

        # Base zoning summary
        if base_steps:
            base_source = base_steps[0].source.replace("BASE: ", "")
            base_params = [f"{s.parameter.replace('_', ' ')} of {s.new_value}{self._get_unit(s.parameter)}"
                          for s in base_steps[:3]]  # Limit to top 3 for readability
            narrative_parts.append(f"Base zoning {base_source} allows {', '.join(base_params)}")

        # Overlay modifications
        overlay_groups = {}
        for step in overlay_steps:
            overlay_name = step.source.replace("OVERLAY: ", "")
            if overlay_name not in overlay_groups:
                overlay_groups[overlay_name] = []
            overlay_groups[overlay_name].append(step)

        for overlay_name, steps in overlay_groups.items():
            changes = []
            for step in steps:
                param_display = step.parameter.replace('_', ' ')
                if step.modification_type == ModificationType.SUPERSEDE:
                    changes.append(f"modifies {param_display} to {step.new_value}{self._get_unit(step.parameter)}")
                elif step.modification_type == ModificationType.ADD:
                    changes.append(f"requires {param_display} of {step.new_value}{self._get_unit(step.parameter)}")

            if changes:
                narrative_parts.append(f"{overlay_name} {' and '.join(changes)}")

        # Bonus modifications
        if bonus_steps:
            for step in bonus_steps:
                bonus_name = step.source.replace("BONUS: ", "")
                param_display = step.parameter.replace('_', ' ')
                narrative_parts.append(
                    f"{bonus_name} increases {param_display} to {step.new_value}{self._get_unit(step.parameter)}"
                )

        # Final summary
        key_params = ['max_height', 'max_far', 'front_setback', 'min_open_space']
        final_values = []
        for param_name in key_params:
            if param_name in self.final_parameters:
                param = self.final_parameters[param_name]
                final_values.append(f"{param_name.replace('_', ' ')} of {param.value}{param.unit}")

        narrative_parts.append(f"Therefore, maximum buildable envelope is: {', '.join(final_values)}")

        return ". ".join(narrative_parts) + "."

    def _get_unit(self, param_name: str) -> str:
        """Helper to get display unit for a parameter"""
        if param_name in self.final_parameters:
            return self.final_parameters[param_name].unit

        # Fallback defaults
        unit_map = {
            'max_height': "'",
            'max_far': "",
            'front_setback': "'",
            'side_setback': "'",
            'rear_setback': "'",
            'waterfront_setback': "'",
            'min_open_space': "%",
            'max_lot_coverage': "%",
        }
        return unit_map.get(param_name, "")


class ZoningRulesEngine:
    """
    Main rules engine that applies zoning overlays in legally-correct sequence.

    This engine implements Philadelphia Code § 14-500 precedence rules:
    1. Overlay provisions override base zoning (regardless of restrictiveness)
    2. Among multiple overlays, stricter standard applies (unless specified)
    3. Bonuses are applied after overlays
    """

    def __init__(self):
        self.districts: Dict[str, ZoningDistrict] = {}
        self.overlays: Dict[str, ZoningDistrict] = {}

    def register_district(self, district: ZoningDistrict):
        """Register a base zoning district"""
        if district.is_overlay:
            self.overlays[district.code] = district
        else:
            self.districts[district.code] = district

    def calculate_maximum_buildable(
        self,
        parcel: Parcel,
        apply_bonuses: bool = False,
        bonus_selections: Optional[List[str]] = None
    ) -> MaximumBuildableEnvelope:
        """
        Calculate the maximum buildable envelope for a parcel.

        This is the main entry point for the rules engine.

        Args:
            parcel: The parcel to analyze
            apply_bonuses: Whether to apply bonus provisions
            bonus_selections: List of specific bonus names to apply (if None, applies all available)

        Returns:
            MaximumBuildableEnvelope with final parameters and step-by-step logic
        """
        application_steps = []
        step_number = 0

        # Step 1: Get base zoning parameters
        base_district = self.districts.get(parcel.base_zoning)
        if not base_district:
            raise ValueError(f"Unknown base zoning district: {parcel.base_zoning}")

        # Initialize with base zoning
        current_parameters = {}
        for param_name, param in base_district.parameters.items():
            current_parameters[param_name] = ZoningParameter(
                name=param.name,
                value=param.value,
                unit=param.unit,
                parameter_type=param.parameter_type,
                source=f"BASE: {base_district.code}",
                modification_type=ModificationType.NONE,
                notes=f"From base district {base_district.code}"
            )

            step_number += 1
            application_steps.append(ApplicationStep(
                step_number=step_number,
                source=f"BASE: {base_district.code}",
                parameter=param_name,
                old_value=None,
                new_value=param.value,
                reason=f"Base zoning district {base_district.code}",
                modification_type=ModificationType.NONE
            ))

        # Step 2: Apply each overlay in sequence
        for overlay_code in parcel.overlays:
            overlay = self.overlays.get(overlay_code)
            if not overlay:
                print(f"Warning: Unknown overlay {overlay_code}, skipping")
                continue

            current_parameters, overlay_steps = self._apply_overlay(
                current_parameters=current_parameters,
                overlay=overlay,
                step_number=step_number
            )

            step_number = overlay_steps[-1].step_number if overlay_steps else step_number
            application_steps.extend(overlay_steps)

        # Step 3: Apply bonuses (if requested)
        bonuses_applied = []
        if apply_bonuses:
            current_parameters, bonus_steps, bonuses_applied = self._apply_bonuses(
                current_parameters=current_parameters,
                parcel=parcel,
                bonus_selections=bonus_selections,
                step_number=step_number
            )
            application_steps.extend(bonus_steps)

        return MaximumBuildableEnvelope(
            parcel=parcel,
            final_parameters=current_parameters,
            application_steps=application_steps,
            bonuses_applied=bonuses_applied
        )

    def _apply_overlay(
        self,
        current_parameters: Dict[str, ZoningParameter],
        overlay: ZoningDistrict,
        step_number: int
    ) -> Tuple[Dict[str, ZoningParameter], List[ApplicationStep]]:
        """
        Apply a single overlay to current parameters.

        Implements the legal rules:
        - Overlay provisions override base (SUPERSEDE)
        - If overlay adds new requirement, adds to parameters (ADD)
        - If multiple overlays conflict, stricter wins
        """
        steps = []
        updated_parameters = current_parameters.copy()

        for param_name, overlay_param in overlay.parameters.items():
            step_number += 1

            if param_name not in updated_parameters:
                # Overlay adds a NEW parameter not in base zoning
                updated_parameters[param_name] = ZoningParameter(
                    name=overlay_param.name,
                    value=overlay_param.value,
                    unit=overlay_param.unit,
                    parameter_type=overlay_param.parameter_type,
                    source=f"OVERLAY: {overlay.code}",
                    modification_type=ModificationType.ADD,
                    notes=f"Added by overlay {overlay.code}"
                )

                steps.append(ApplicationStep(
                    step_number=step_number,
                    source=f"OVERLAY: {overlay.code}",
                    parameter=param_name,
                    old_value=None,
                    new_value=overlay_param.value,
                    reason=f"Overlay {overlay.code} adds new requirement",
                    modification_type=ModificationType.ADD
                ))

            else:
                # Parameter exists - determine if overlay supersedes or adds
                current_param = updated_parameters[param_name]

                # For dimensional parameters, apply stricter standard
                if overlay_param.parameter_type == ParameterType.DIMENSIONAL:
                    overlay_zp = ZoningParameter(
                        name=overlay_param.name,
                        value=overlay_param.value,
                        unit=overlay_param.unit,
                        parameter_type=overlay_param.parameter_type,
                        source=f"OVERLAY: {overlay.code}",
                        modification_type=ModificationType.SUPERSEDE
                    )

                    # Overlays ALWAYS win over base, but among overlays stricter wins
                    if current_param.source.startswith("BASE") or overlay_zp.is_stricter_than(current_param):
                        old_value = current_param.value
                        updated_parameters[param_name] = ZoningParameter(
                            name=overlay_param.name,
                            value=overlay_param.value,
                            unit=overlay_param.unit,
                            parameter_type=overlay_param.parameter_type,
                            source=f"OVERLAY: {overlay.code}",
                            modification_type=ModificationType.SUPERSEDE,
                            notes=f"Overlay {overlay.code} supersedes {current_param.source}"
                        )

                        reason = f"Overlay {overlay.code} supersedes base zoning" if current_param.source.startswith("BASE") else f"Overlay {overlay.code} is stricter than {current_param.source}"

                        steps.append(ApplicationStep(
                            step_number=step_number,
                            source=f"OVERLAY: {overlay.code}",
                            parameter=param_name,
                            old_value=old_value,
                            new_value=overlay_param.value,
                            reason=reason,
                            modification_type=ModificationType.SUPERSEDE
                        ))

                # For design standards, they're cumulative (must satisfy all)
                elif overlay_param.parameter_type == ParameterType.DESIGN:
                    # Add to list of requirements
                    if isinstance(current_param.value, list):
                        new_value = current_param.value + [overlay_param.value]
                    else:
                        new_value = [current_param.value, overlay_param.value]

                    updated_parameters[param_name] = ZoningParameter(
                        name=overlay_param.name,
                        value=new_value,
                        unit=overlay_param.unit,
                        parameter_type=overlay_param.parameter_type,
                        source=f"{current_param.source} + OVERLAY: {overlay.code}",
                        modification_type=ModificationType.ADD,
                        notes=f"Cumulative design requirement from {overlay.code}"
                    )

                    steps.append(ApplicationStep(
                        step_number=step_number,
                        source=f"OVERLAY: {overlay.code}",
                        parameter=param_name,
                        old_value=current_param.value,
                        new_value=new_value,
                        reason=f"Overlay {overlay.code} adds cumulative design requirement",
                        modification_type=ModificationType.ADD
                    ))

        return updated_parameters, steps

    def _apply_bonuses(
        self,
        current_parameters: Dict[str, ZoningParameter],
        parcel: Parcel,
        bonus_selections: Optional[List[str]],
        step_number: int
    ) -> Tuple[Dict[str, ZoningParameter], List[ApplicationStep], List[BonusProvision]]:
        """
        Apply bonus provisions to increase development potential.

        Bonuses are OPTIONAL enhancements that require providing public benefits.
        """
        steps = []
        bonuses_applied = []
        updated_parameters = current_parameters.copy()

        # Collect all available bonuses from overlays that apply to this parcel
        available_bonuses = []
        for overlay_code in parcel.overlays:
            overlay = self.overlays.get(overlay_code)
            if overlay:
                available_bonuses.extend(overlay.bonuses)

        # Filter to selected bonuses if specified
        if bonus_selections:
            available_bonuses = [b for b in available_bonuses if b.name in bonus_selections]

        # Group bonuses by parameter they modify
        bonuses_by_param = {}
        for bonus in available_bonuses:
            if bonus.parameter_modified not in bonuses_by_param:
                bonuses_by_param[bonus.parameter_modified] = []
            bonuses_by_param[bonus.parameter_modified].append(bonus)

        # Apply bonuses to each parameter
        for param_name, bonuses in bonuses_by_param.items():
            if param_name not in updated_parameters:
                continue

            current_param = updated_parameters[param_name]
            cumulative_bonus = 0

            for bonus in bonuses:
                if bonus.can_combine or len(bonuses) == 1:
                    cumulative_bonus += bonus.modification_amount
                    bonuses_applied.append(bonus)

            # Check maximum cumulative bonus
            max_bonus = bonuses[0].max_cumulative if bonuses else None
            if max_bonus and cumulative_bonus > max_bonus:
                cumulative_bonus = max_bonus

            # Apply bonus
            old_value = current_param.value
            new_value = old_value + cumulative_bonus

            step_number += 1
            updated_parameters[param_name] = ZoningParameter(
                name=current_param.name,
                value=new_value,
                unit=current_param.unit,
                parameter_type=current_param.parameter_type,
                source=current_param.source + " + BONUS",
                modification_type=ModificationType.ADD,
                notes=f"Bonus of {cumulative_bonus}{current_param.unit} applied"
            )

            steps.append(ApplicationStep(
                step_number=step_number,
                source=f"BONUS: {', '.join([b.name for b in bonuses_applied[-len(bonuses):]])}",
                parameter=param_name,
                old_value=old_value,
                new_value=new_value,
                reason=f"Earned bonus by providing: {', '.join([b.description for b in bonuses_applied[-len(bonuses):]])}",
                modification_type=ModificationType.ADD
            ))

        return updated_parameters, steps, bonuses_applied


def create_parameter(name: str, value: Any, unit: str = "", param_type: ParameterType = ParameterType.DIMENSIONAL) -> ZoningParameter:
    """Helper function to create a ZoningParameter"""
    return ZoningParameter(
        name=name,
        value=value,
        unit=unit,
        parameter_type=param_type,
        source="",
        modification_type=ModificationType.NONE
    )
