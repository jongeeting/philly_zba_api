"""
Philadelphia Zoning Overlay Rules Engine - Example Scenarios

This module demonstrates the rules engine with real-world scenarios showing
how overlays are applied in the correct legal sequence.

Each example shows step-by-step logic:
"Base zoning allows X, Overlay A modifies to Y, Overlay B further modifies to Z,
therefore maximum buildable is Z."
"""

from zoning_rules_engine import ZoningRulesEngine, Parcel
from zoning_districts import load_districts_into_engine
import json


def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_parameter_table(envelope):
    """Print a formatted table of final parameters"""
    print("\nFINAL MAXIMUM BUILDABLE PARAMETERS:")
    print("-" * 80)
    print(f"{'Parameter':<30} {'Value':<20} {'Source':<30}")
    print("-" * 80)

    for param_name, param in envelope.final_parameters.items():
        value_str = str(param.value) + param.unit
        print(f"{param_name:<30} {value_str:<20} {param.source:<30}")

    print("-" * 80)


def print_step_by_step(envelope):
    """Print step-by-step application logic"""
    print("\nSTEP-BY-STEP APPLICATION SEQUENCE:")
    print("-" * 80)

    current_step_source = None
    for step in envelope.application_steps:
        # Print source header when it changes
        if step.source != current_step_source:
            print(f"\n{step.source}:")
            current_step_source = step.source

        # Format value display
        old_val = f"{step.old_value}" if step.old_value is not None else "N/A"
        new_val = f"{step.new_value}"

        # Print the change
        if step.old_value is None:
            print(f"  [{step.step_number}] Set {step.parameter} = {new_val}")
        else:
            print(f"  [{step.step_number}] Modified {step.parameter}: {old_val} → {new_val}")
        print(f"      Reason: {step.reason}")

    print("-" * 80)


def print_narrative(envelope):
    """Print human-readable narrative"""
    print("\nHUMAN-READABLE NARRATIVE:")
    print("-" * 80)
    narrative = envelope.get_narrative()
    # Wrap text at 80 characters
    words = narrative.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 80:
            line += word + " "
        else:
            print(line)
            line = word + " "
    if line:
        print(line)
    print("-" * 80)


# =============================================================================
# SCENARIO 1: CMX-3 + Central Delaware Overlay (No Bonuses)
# =============================================================================

def scenario_1_cmx3_cdo_no_bonuses():
    """
    Scenario 1: Waterfront parcel with base CMX-3 and /CDO overlay, no bonuses

    This demonstrates:
    - Overlay superseding base height (100' replaces 65')
    - Overlay adding new requirements (waterfront setback, open space)
    - Final buildable envelope without bonuses
    """
    print_section_header("SCENARIO 1: CMX-3 + /CDO (No Bonuses)")

    # Create engine and load districts
    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    # Create parcel
    parcel = Parcel(
        parcel_id="0123456789",
        address="123 Delaware Ave, Philadelphia PA 19123",
        base_zoning="CMX-3",
        overlays=["/CDO"],
        lot_area=10000  # 10,000 SF lot
    )

    print(f"Parcel: {parcel.address}")
    print(f"Parcel ID: {parcel.parcel_id}")
    print(f"Lot Area: {parcel.lot_area:,} SF")
    print(f"Base Zoning: {parcel.base_zoning}")
    print(f"Overlays: {', '.join(parcel.overlays)}")

    # Calculate maximum buildable
    envelope = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=False
    )

    # Display results
    print_step_by_step(envelope)
    print_parameter_table(envelope)
    print_narrative(envelope)

    return envelope


# =============================================================================
# SCENARIO 2: CMX-3 + Central Delaware Overlay + LEED Gold Bonus
# =============================================================================

def scenario_2_cmx3_cdo_with_bonuses():
    """
    Scenario 2: Same parcel but developer pursues LEED Gold and Waterfront Trail bonuses

    This demonstrates:
    - Same base + overlay application as Scenario 1
    - Bonuses applied AFTER overlay requirements
    - Cumulative bonuses (LEED Gold 36' + Trail 48' = 84' total)
    - Final height: 100' base + 84' bonus = 184' (within 244' max)
    """
    print_section_header("SCENARIO 2: CMX-3 + /CDO + Bonuses (LEED Gold + Trail)")

    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    parcel = Parcel(
        parcel_id="0123456789",
        address="123 Delaware Ave, Philadelphia PA 19123",
        base_zoning="CMX-3",
        overlays=["/CDO"],
        lot_area=10000
    )

    print(f"Parcel: {parcel.address}")
    print(f"Base Zoning: {parcel.base_zoning}")
    print(f"Overlays: {', '.join(parcel.overlays)}")
    print(f"Bonuses Pursued: LEED Gold Certification, Waterfront Trail")

    # Calculate with bonuses
    envelope = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=True,
        bonus_selections=['LEED_Gold', 'Waterfront_Trail']
    )

    print_step_by_step(envelope)
    print_parameter_table(envelope)
    print_narrative(envelope)

    print("\nBONUSES EARNED:")
    print("-" * 80)
    for bonus in envelope.bonuses_applied:
        print(f"  • {bonus.name}: +{bonus.modification_amount}' to {bonus.parameter_modified}")
        print(f"    Requirement: {bonus.description}")
    print("-" * 80)

    return envelope


# =============================================================================
# SCENARIO 3: CMX-3 + Multiple Overlays (/CDO + /CTR)
# =============================================================================

def scenario_3_cmx3_cdo_ctr_multiple_overlays():
    """
    Scenario 3: Parcel in both Central Delaware AND Center City overlays

    This demonstrates:
    - Multiple overlays applying to same parcel
    - Conflict resolution (stricter standard wins)
    - Cumulative design requirements (transparency from both overlays)
    - Parking maximum from /CTR limiting development
    """
    print_section_header("SCENARIO 3: CMX-3 + /CDO + /CTR (Multiple Overlays)")

    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    parcel = Parcel(
        parcel_id="0987654321",
        address="100 S Christopher Columbus Blvd, Philadelphia PA 19106",
        base_zoning="CMX-3",
        overlays=["/CDO", "/CTR"],  # Both overlays apply
        lot_area=15000
    )

    print(f"Parcel: {parcel.address}")
    print(f"Base Zoning: {parcel.base_zoning}")
    print(f"Overlays: {', '.join(parcel.overlays)}")
    print("\nNOTE: This parcel is in BOTH Central Delaware AND Center City overlays.")
    print("      When overlays conflict, the STRICTER standard applies.")

    envelope = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=False
    )

    print_step_by_step(envelope)
    print_parameter_table(envelope)
    print_narrative(envelope)

    print("\nCONFLICT RESOLUTION EXAMPLES:")
    print("-" * 80)
    print("Ground Floor Transparency:")
    print("  • /CDO requires: 60%")
    print("  • /CTR requires: 70%")
    print("  • RESULT: 70% applies (stricter/higher)")
    print("\nParking Maximum:")
    print("  • CMX-3 base: Unlimited")
    print("  • /CTR sets: 0.5 spaces/unit")
    print("  • RESULT: 0.5 spaces/unit (overlay supersedes base)")
    print("-" * 80)

    return envelope


# =============================================================================
# SCENARIO 4: CMX-4 + /MIN (Mixed Income Overlay)
# =============================================================================

def scenario_4_cmx4_min_affordable_bonus():
    """
    Scenario 4: High-density base with Mixed Income Overlay and affordable housing bonus

    This demonstrates:
    - Higher-density base district (CMX-4)
    - /MIN overlay adding affordable housing incentives
    - Dwelling unit density bonus (20% more units for 20% affordable)
    - Height bonus for affordable units
    - Parking reduction for affordable projects
    """
    print_section_header("SCENARIO 4: CMX-4 + /MIN + Affordable Housing Bonus")

    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    parcel = Parcel(
        parcel_id="1122334455",
        address="1500 Market St, Philadelphia PA 19102",
        base_zoning="CMX-4",
        overlays=["/MIN"],
        lot_area=20000
    )

    print(f"Parcel: {parcel.address}")
    print(f"Lot Area: {parcel.lot_area:,} SF")
    print(f"Base Zoning: {parcel.base_zoning} (very high-density)")
    print(f"Overlays: {', '.join(parcel.overlays)}")
    print(f"Developer Commits: 20% affordable units at 60% AMI")

    # First calculate without bonus
    envelope_no_bonus = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=False
    )

    base_far = envelope_no_bonus.final_parameters['max_far'].value
    base_height = envelope_no_bonus.final_parameters['max_height'].value

    print(f"\nWITHOUT BONUS: {base_height}' height, {base_far} FAR")

    # Calculate with affordable housing bonus
    envelope = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=True,
        bonus_selections=['Affordable_20pct', 'Affordable_Height']
    )

    print_step_by_step(envelope)
    print_parameter_table(envelope)
    print_narrative(envelope)

    print("\nAFFORDABLE HOUSING BONUS IMPACT:")
    print("-" * 80)
    print(f"Height Bonus: +15' (from {base_height}' to {envelope.final_parameters['max_height'].value}')")
    print(f"Parking Reduction: From unlimited to 0.5 spaces/unit (encourages transit)")
    print(f"Benefit to Community: 20% of units affordable at 60% AMI for 30 years")
    print(f"Benefit to Developer: Additional height and reduced parking costs")
    print("-" * 80)

    return envelope


# =============================================================================
# SCENARIO 5: RSA-5 + /NE (Residential with Northeast Overlay)
# =============================================================================

def scenario_5_rsa5_ne_residential():
    """
    Scenario 5: Rowhouse district with Northeast Overlay

    This demonstrates:
    - Lower-density residential base (RSA-5)
    - /NE overlay increasing setbacks (more restrictive)
    - /NE adding lot dimension requirements
    - /NE adding landscaping requirements for parking
    - Use restrictions from overlay
    """
    print_section_header("SCENARIO 5: RSA-5 + /NE (Residential + Northeast Overlay)")

    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    parcel = Parcel(
        parcel_id="5566778899",
        address="9500 Bustleton Ave, Philadelphia PA 19115",
        base_zoning="RSA-5",
        overlays=["/NE"],
        lot_area=6000
    )

    print(f"Parcel: {parcel.address}")
    print(f"Lot Area: {parcel.lot_area:,} SF")
    print(f"Base Zoning: {parcel.base_zoning} (rowhouse district)")
    print(f"Overlays: {', '.join(parcel.overlays)}")
    print(f"Location: Northeast Philadelphia")

    envelope = engine.calculate_maximum_buildable(
        parcel=parcel,
        apply_bonuses=False
    )

    print_step_by_step(envelope)
    print_parameter_table(envelope)
    print_narrative(envelope)

    print("\nNORTHEAST OVERLAY IMPACT:")
    print("-" * 80)
    print("Setback Increases:")
    print("  • Front: 0' (base) → 20' (overlay) - 20' MORE RESTRICTIVE")
    print("  • Side: 0' (base) → 10' (overlay) - 10' MORE RESTRICTIVE")
    print("\nLot Requirements:")
    print("  • Min Width: 14' (base) → 50' (overlay) - STRICTER")
    print("  • Min Area: 1,000 SF (base) → 5,000 SF (overlay) - STRICTER")
    print("\nNew Requirements from Overlay:")
    print("  • Parking lot landscaping (20% of parking area)")
    print("  • Trees required every 8 parking spaces")
    print("  • Prohibited uses: auto repair, salvage yards, truck terminals")
    print("-" * 80)

    return envelope


# =============================================================================
# COMPARISON TABLE: Same Parcel, Different Scenarios
# =============================================================================

def comparison_table_bonuses():
    """
    Create a comparison table showing the same parcel with different bonus scenarios
    """
    print_section_header("COMPARISON: Impact of Different Bonus Strategies")

    engine = ZoningRulesEngine()
    load_districts_into_engine(engine)

    parcel = Parcel(
        parcel_id="COMP123",
        address="200 Delaware Ave, Philadelphia PA 19123",
        base_zoning="CMX-3",
        overlays=["/CDO"],
        lot_area=12000
    )

    print(f"Parcel: {parcel.address} (CMX-3 + /CDO)")
    print(f"Lot Area: {parcel.lot_area:,} SF\n")

    scenarios = [
        ("No Bonuses", False, None),
        ("LEED Silver Only", True, ['LEED_Silver']),
        ("LEED Gold Only", True, ['LEED_Gold']),
        ("LEED Platinum Only", True, ['LEED_Platinum']),
        ("Waterfront Trail Only", True, ['Waterfront_Trail']),
        ("LEED Gold + Trail", True, ['LEED_Gold', 'Waterfront_Trail']),
        ("Maximum Bonuses", True, ['LEED_Platinum', 'Waterfront_Trail', 'Public_Plaza']),
    ]

    print("COMPARISON TABLE:")
    print("-" * 100)
    print(f"{'Scenario':<30} {'Height':<15} {'Bonuses Applied':<55}")
    print("-" * 100)

    for scenario_name, apply_bonuses, bonus_selections in scenarios:
        envelope = engine.calculate_maximum_buildable(
            parcel=parcel,
            apply_bonuses=apply_bonuses,
            bonus_selections=bonus_selections
        )

        height = envelope.final_parameters['max_height'].value
        bonuses_str = ", ".join([b.name for b in envelope.bonuses_applied]) if envelope.bonuses_applied else "None"

        print(f"{scenario_name:<30} {str(height) + \"'\":<15} {bonuses_str:<55}")

    print("-" * 100)

    print("\nKEY INSIGHTS:")
    print("  • Base /CDO height: 100' (without any bonuses)")
    print("  • Maximum possible: 244' (100' base + 144' maximum bonus)")
    print("  • LEED Platinum + Trail + Plaza = 48' + 48' + 36' = 132' bonus → 232' total")
    print("  • Even with all bonuses, cannot exceed 244' total (100' + 144' max)")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_all_examples():
    """Run all example scenarios"""

    print("\n" + "#" * 80)
    print("#" + " " * 78 + "#")
    print("#  PHILADELPHIA ZONING OVERLAY RULES ENGINE - EXAMPLE SCENARIOS" + " " * 15 + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)

    print("\nThis demonstration shows how the rules engine applies Philadelphia zoning")
    print("overlays in the legally-correct sequence to determine maximum buildable projects.")

    # Run all scenarios
    scenario_1_cmx3_cdo_no_bonuses()
    input("\nPress Enter to continue to Scenario 2...")

    scenario_2_cmx3_cdo_with_bonuses()
    input("\nPress Enter to continue to Scenario 3...")

    scenario_3_cmx3_cdo_ctr_multiple_overlays()
    input("\nPress Enter to continue to Scenario 4...")

    scenario_4_cmx4_min_affordable_bonus()
    input("\nPress Enter to continue to Scenario 5...")

    scenario_5_rsa5_ne_residential()
    input("\nPress Enter to see Bonus Comparison Table...")

    comparison_table_bonuses()

    print_section_header("DEMONSTRATION COMPLETE")
    print("\nThe rules engine has successfully demonstrated:")
    print("  ✓ Base zoning application")
    print("  ✓ Overlay superseding base standards")
    print("  ✓ Multiple overlays with conflict resolution (stricter wins)")
    print("  ✓ Additive vs. superseding requirements")
    print("  ✓ Bonus provisions applied after overlays")
    print("  ✓ Cumulative bonuses with maximums")
    print("  ✓ Step-by-step audit trail of all decisions")
    print("  ✓ Human-readable narratives")
    print("\nThe engine is ready for integration with 3D massing models.")
    print("\nNext steps:")
    print("  • Integrate with parcel GIS data")
    print("  • Connect to 3D visualization engine")
    print("  • Add more overlay districts as needed")
    print("  • Implement variance/exception modeling")


if __name__ == "__main__":
    run_all_examples()
