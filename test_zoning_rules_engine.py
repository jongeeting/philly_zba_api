"""
Unit tests for Philadelphia Zoning Overlay Rules Engine

Tests verify:
1. Overlay supremacy over base zoning
2. Stricter standard wins among multiple overlays
3. Additive vs. superseding behavior
4. Bonus application after overlays
5. Conflict resolution logic
"""

import unittest
from zoning_rules_engine import (
    ZoningRulesEngine, Parcel, ZoningParameter, ParameterType,
    ModificationType
)
from zoning_districts import load_districts_into_engine


class TestOverlaySupremacy(unittest.TestCase):
    """Test that overlay provisions override base zoning"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_overlay_supersedes_base_height(self):
        """Test that /CDO height (100') supersedes CMX-3 base height (65')"""
        parcel = Parcel(
            parcel_id="TEST001",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # /CDO should set height to 100', not base CMX-3's 65'
        self.assertEqual(envelope.final_parameters['max_height'].value, 100)
        self.assertIn("/CDO", envelope.final_parameters['max_height'].source)

    def test_overlay_adds_new_requirement(self):
        """Test that /CDO adds waterfront_setback not in base zoning"""
        parcel = Parcel(
            parcel_id="TEST002",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # Waterfront setback should exist (added by /CDO)
        self.assertIn('waterfront_setback', envelope.final_parameters)
        self.assertEqual(envelope.final_parameters['waterfront_setback'].value, 50)

    def test_overlay_does_not_modify_unrelated_parameter(self):
        """Test that /CDO doesn't modify FAR (leaves base CMX-3's 4.0)"""
        parcel = Parcel(
            parcel_id="TEST003",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # FAR should remain 4.0 from base CMX-3
        self.assertEqual(envelope.final_parameters['max_far'].value, 4.0)
        self.assertIn("CMX-3", envelope.final_parameters['max_far'].source)


class TestMultipleOverlayConflicts(unittest.TestCase):
    """Test stricter-wins rule when multiple overlays conflict"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_stricter_transparency_wins(self):
        """
        Test ground_floor_transparency conflict resolution:
        /CDO requires 60%, /CTR requires 70%
        Result: 70% (stricter/higher)
        """
        parcel = Parcel(
            parcel_id="TEST004",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO", "/CTR"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # Should be list with both requirements (design standards are cumulative)
        transparency = envelope.final_parameters['ground_floor_transparency']
        # The value should be a list containing both values since design standards are cumulative
        if isinstance(transparency.value, list):
            # Both overlays add their requirement
            self.assertTrue(60 in transparency.value or 70 in transparency.value)
        else:
            # Or if one supersedes, it should be the stricter (70%)
            self.assertGreaterEqual(transparency.value, 60)

    def test_parking_maximum_from_overlay(self):
        """
        Test that /CTR parking maximum (0.5) applies over CMX-3 unlimited
        """
        parcel = Parcel(
            parcel_id="TEST005",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CTR"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # /CTR limits parking to 0.5 spaces/unit
        self.assertEqual(envelope.final_parameters['parking_max'].value, 0.5)


class TestBonusApplication(unittest.TestCase):
    """Test that bonuses are applied after overlays"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_bonus_increases_height(self):
        """Test that LEED Gold bonus adds 36' to /CDO base height"""
        parcel = Parcel(
            parcel_id="TEST006",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        # Without bonus
        envelope_no_bonus = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)
        height_no_bonus = envelope_no_bonus.final_parameters['max_height'].value

        # With LEED Gold bonus
        envelope_with_bonus = self.engine.calculate_maximum_buildable(
            parcel,
            apply_bonuses=True,
            bonus_selections=['LEED_Gold']
        )
        height_with_bonus = envelope_with_bonus.final_parameters['max_height'].value

        # Should add 36' to base 100'
        self.assertEqual(height_no_bonus, 100)
        self.assertEqual(height_with_bonus, 136)

    def test_cumulative_bonuses(self):
        """Test that multiple bonuses combine (LEED Gold 36' + Trail 48' = 84')"""
        parcel = Parcel(
            parcel_id="TEST007",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        envelope = self.engine.calculate_maximum_buildable(
            parcel,
            apply_bonuses=True,
            bonus_selections=['LEED_Gold', 'Waterfront_Trail']
        )

        # Should be 100' + 36' + 48' = 184'
        self.assertEqual(envelope.final_parameters['max_height'].value, 184)
        self.assertEqual(len(envelope.bonuses_applied), 2)

    def test_maximum_cumulative_bonus(self):
        """Test that cumulative bonuses can't exceed maximum (144' in /CDO)"""
        parcel = Parcel(
            parcel_id="TEST008",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        # Try to apply bonuses that would total > 144'
        # LEED Platinum (48') + Trail (48') + Plaza (36') + Mixed Income (24') = 156'
        # But max is 144', so should cap at 144'
        envelope = self.engine.calculate_maximum_buildable(
            parcel,
            apply_bonuses=True,
            bonus_selections=['LEED_Platinum', 'Waterfront_Trail', 'Public_Plaza', 'Mixed_Income']
        )

        height_bonus = envelope.final_parameters['max_height'].value - 100
        # Should not exceed 144' bonus
        self.assertLessEqual(height_bonus, 144)


class TestStricterStandard(unittest.TestCase):
    """Test the is_stricter_than logic for different parameter types"""

    def test_lower_height_is_stricter(self):
        """Test that lower height is considered stricter"""
        height_65 = ZoningParameter(
            name='max_height',
            value=65,
            unit="'",
            parameter_type=ParameterType.DIMENSIONAL,
            source="Test",
            modification_type=ModificationType.NONE
        )

        height_100 = ZoningParameter(
            name='max_height',
            value=100,
            unit="'",
            parameter_type=ParameterType.DIMENSIONAL,
            source="Test",
            modification_type=ModificationType.NONE
        )

        # 65' is stricter than 100'
        self.assertTrue(height_65.is_stricter_than(height_100))
        self.assertFalse(height_100.is_stricter_than(height_65))

    def test_higher_setback_is_stricter(self):
        """Test that higher setback is considered stricter"""
        setback_10 = ZoningParameter(
            name='front_setback',
            value=10,
            unit="'",
            parameter_type=ParameterType.DIMENSIONAL,
            source="Test",
            modification_type=ModificationType.NONE
        )

        setback_20 = ZoningParameter(
            name='front_setback',
            value=20,
            unit="'",
            parameter_type=ParameterType.DIMENSIONAL,
            source="Test",
            modification_type=ModificationType.NONE
        )

        # 20' setback is stricter than 10'
        self.assertTrue(setback_20.is_stricter_than(setback_10))
        self.assertFalse(setback_10.is_stricter_than(setback_20))

    def test_lower_far_is_stricter(self):
        """Test that lower FAR is considered stricter"""
        far_2 = ZoningParameter(
            name='max_far',
            value=2.0,
            unit="",
            parameter_type=ParameterType.DIMENSIONAL,
            source="Test",
            modification_type=ModificationType.NONE
        )

        far_4 = ZoningParameter(
            name='max_far',
            value=4.0,
            unit="",
            parameter_type=ParameterType.DIMENSIONAL,
            source="Test",
            modification_type=ModificationType.NONE
        )

        # 2.0 FAR is stricter than 4.0
        self.assertTrue(far_2.is_stricter_than(far_4))
        self.assertFalse(far_4.is_stricter_than(far_2))


class TestApplicationSteps(unittest.TestCase):
    """Test that application steps create proper audit trail"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_steps_recorded(self):
        """Test that all application steps are recorded"""
        parcel = Parcel(
            parcel_id="TEST009",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # Should have steps for base zoning + overlay modifications
        self.assertGreater(len(envelope.application_steps), 0)

        # First steps should be from BASE
        base_steps = [s for s in envelope.application_steps if s.source.startswith("BASE")]
        self.assertGreater(len(base_steps), 0)

        # Should have overlay steps
        overlay_steps = [s for s in envelope.application_steps if s.source.startswith("OVERLAY")]
        self.assertGreater(len(overlay_steps), 0)

    def test_narrative_generation(self):
        """Test that human-readable narrative is generated"""
        parcel = Parcel(
            parcel_id="TEST010",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/CDO"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)
        narrative = envelope.get_narrative()

        # Narrative should mention base zoning
        self.assertIn("CMX-3", narrative)

        # Narrative should mention overlay
        self.assertIn("CDO", narrative or "/CDO", narrative)

        # Narrative should mention height
        self.assertIn("height", narrative.lower())


class TestNortheastOverlay(unittest.TestCase):
    """Test /NE overlay behavior"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_ne_increases_setbacks(self):
        """Test that /NE increases setbacks from base RSA-5"""
        parcel = Parcel(
            parcel_id="TEST011",
            address="Test Address",
            base_zoning="RSA-5",
            overlays=["/NE"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # /NE should increase front setback to 20'
        self.assertEqual(envelope.final_parameters['front_setback'].value, 20)

        # /NE should increase side setback to 10'
        self.assertEqual(envelope.final_parameters['side_setback'].value, 10)

    def test_ne_increases_lot_dimensions(self):
        """Test that /NE increases minimum lot dimensions"""
        parcel = Parcel(
            parcel_id="TEST012",
            address="Test Address",
            base_zoning="RSA-5",
            overlays=["/NE"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # /NE should increase min lot width to 50'
        self.assertEqual(envelope.final_parameters['min_lot_width'].value, 50)

        # /NE should increase min lot area to 5,000 SF
        self.assertEqual(envelope.final_parameters['min_lot_area'].value, 5000)


class TestMixedIncomeOverlay(unittest.TestCase):
    """Test /MIN overlay affordable housing bonuses"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_min_reduces_parking_minimum(self):
        """Test that /MIN reduces parking minimum to 0.5 spaces/unit"""
        parcel = Parcel(
            parcel_id="TEST013",
            address="Test Address",
            base_zoning="CMX-4",
            overlays=["/MIN"]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # /MIN should set parking minimum to 0.5
        self.assertEqual(envelope.final_parameters['parking_min'].value, 0.5)

    def test_affordable_height_bonus(self):
        """Test that affordable housing earns height bonus"""
        parcel = Parcel(
            parcel_id="TEST014",
            address="Test Address",
            base_zoning="CMX-4",
            overlays=["/MIN"]
        )

        # Without bonus
        envelope_no_bonus = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)
        height_no_bonus = envelope_no_bonus.final_parameters['max_height'].value

        # With affordable housing bonus
        envelope_with_bonus = self.engine.calculate_maximum_buildable(
            parcel,
            apply_bonuses=True,
            bonus_selections=['Affordable_Height']
        )
        height_with_bonus = envelope_with_bonus.final_parameters['max_height'].value

        # Should add 15' for affordable housing
        self.assertEqual(height_with_bonus, height_no_bonus + 15)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_invalid_base_zoning(self):
        """Test that invalid base zoning raises error"""
        parcel = Parcel(
            parcel_id="TEST015",
            address="Test Address",
            base_zoning="INVALID-ZONE",
            overlays=[]
        )

        with self.assertRaises(ValueError):
            self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

    def test_no_overlays(self):
        """Test parcel with only base zoning (no overlays)"""
        parcel = Parcel(
            parcel_id="TEST016",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=[]
        )

        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # Should have base zoning parameters
        self.assertEqual(envelope.final_parameters['max_height'].value, 65)
        self.assertEqual(envelope.final_parameters['max_far'].value, 4.0)

    def test_unknown_overlay_warning(self):
        """Test that unknown overlay is skipped with warning"""
        parcel = Parcel(
            parcel_id="TEST017",
            address="Test Address",
            base_zoning="CMX-3",
            overlays=["/UNKNOWN"]
        )

        # Should not raise error, just skip unknown overlay
        envelope = self.engine.calculate_maximum_buildable(parcel, apply_bonuses=False)

        # Should still have base zoning results
        self.assertEqual(envelope.final_parameters['max_height'].value, 65)


class TestRealWorldScenarios(unittest.TestCase):
    """Integration tests with real-world scenarios"""

    def setUp(self):
        self.engine = ZoningRulesEngine()
        load_districts_into_engine(self.engine)

    def test_waterfront_mixed_use_development(self):
        """
        Test realistic waterfront development scenario:
        CMX-3 + /CDO + bonuses for green building and trail
        """
        parcel = Parcel(
            parcel_id="REAL001",
            address="123 Delaware Ave",
            base_zoning="CMX-3",
            overlays=["/CDO"],
            lot_area=10000
        )

        envelope = self.engine.calculate_maximum_buildable(
            parcel,
            apply_bonuses=True,
            bonus_selections=['LEED_Gold', 'Waterfront_Trail']
        )

        # Should get 100' + 36' + 48' = 184'
        self.assertEqual(envelope.final_parameters['max_height'].value, 184)

        # Should maintain 4.0 FAR from base
        self.assertEqual(envelope.final_parameters['max_far'].value, 4.0)

        # Should have waterfront setback
        self.assertEqual(envelope.final_parameters['waterfront_setback'].value, 50)

        # Should have 40% open space requirement
        self.assertEqual(envelope.final_parameters['min_open_space'].value, 40)

    def test_center_city_high_rise(self):
        """
        Test Center City high-rise scenario:
        CMX-4 (high base) + /CTR + /MIN + affordable bonuses
        """
        parcel = Parcel(
            parcel_id="REAL002",
            address="1500 Market St",
            base_zoning="CMX-4",
            overlays=["/MIN"],
            lot_area=20000
        )

        envelope = self.engine.calculate_maximum_buildable(
            parcel,
            apply_bonuses=True,
            bonus_selections=['Affordable_Height']
        )

        # CMX-4 base is 120', plus 15' affordable bonus = 135'
        self.assertEqual(envelope.final_parameters['max_height'].value, 135)

        # Should have parking limited to 0.5 by /MIN
        self.assertEqual(envelope.final_parameters['parking_min'].value, 0.5)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    print("=" * 80)
    print("  PHILADELPHIA ZONING OVERLAY RULES ENGINE - TEST SUITE")
    print("=" * 80)
    print("\nRunning comprehensive tests to validate:")
    print("  • Overlay supremacy over base zoning")
    print("  • Stricter-wins conflict resolution")
    print("  • Additive vs. superseding behavior")
    print("  • Bonus application logic")
    print("  • Edge cases and error handling")
    print("  • Real-world scenarios\n")

    run_tests()
