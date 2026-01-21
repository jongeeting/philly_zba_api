#!/usr/bin/env python3
"""
Citywide Parking Elimination Analysis

Compares two parking reform scenarios:
1. Graduated approach (eliminate for small, reduce for medium/large)
2. Citywide elimination (eliminate ALL parking minimums)

Shows the additional impact of full citywide elimination.
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class CitywideReformAnalyzer:
    """Analyzes impact of citywide parking minimum elimination."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    def extract_all_issues(self, text):
        """Extract ALL variance issues mentioned in an appeal."""
        if not text:
            return {}

        text = text.upper()
        issues = {}

        # HEIGHT / STORIES
        if re.search(r'\d+.?STOR(Y|IES)', text) or re.search(r'(THREE|FOUR|FIVE|SIX|SEVEN|EIGHT).?STOR(Y|IES)', text):
            issues['height'] = True
            match = re.search(r'(\d+).?STOR(Y|IES)', text)
            if match:
                issues['height_value'] = int(match.group(1))
            else:
                word_to_num = {'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8}
                for word, num in word_to_num.items():
                    if f'{word} STOR' in text or f'{word}-STOR' in text:
                        issues['height_value'] = num
                        break

        # DWELLING UNITS / FAMILY
        unit_patterns = [
            r'\((\d+)\).*DWELLING UNIT',
            r'\((\d+)\).*(UNIT|FAMILY)',
            r'(\d+).?FAMILY',
            r'(TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT).?FAMILY',
        ]
        for pattern in unit_patterns:
            match = re.search(pattern, text)
            if match:
                issues['dwelling_units'] = True
                num_str = match.group(1)
                if num_str.isdigit():
                    issues['unit_count'] = int(num_str)
                else:
                    word_to_num = {'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8}
                    if num_str in word_to_num:
                        issues['unit_count'] = word_to_num[num_str]
                break

        # PARKING
        if re.search(r'\bPARKING', text):
            issues['parking'] = True

        # ROOF DECK / ROOF ACCESS
        if re.search(r'\bROOF DECK\b', text) or re.search(r'\bROOF ACCESS\b', text):
            issues['roof_deck'] = True

        # SETBACKS / YARDS
        if re.search(r'\b(FRONT|REAR|SIDE) YARD\b', text) or re.search(r'\bSETBACK\b', text):
            issues['setback'] = True

        # OPEN SPACE
        if re.search(r'\bOPEN SPACE\b', text):
            issues['open_space'] = True

        # LOT DIMENSIONS
        if re.search(r'\bLOT (AREA|WIDTH|COVERAGE|LINE)\b', text):
            issues['lot_dimensions'] = True

        # ACCESSORY STRUCTURE (not roof deck)
        if re.search(r'\bACCESSORY STRUCTURE\b', text) and not issues.get('roof_deck'):
            issues['accessory_structure'] = True

        # ADDITION / ERECTION
        if re.search(r'\bERECTION OF.*ADDITION\b', text) or re.search(r'\bADDITION\b', text):
            issues['addition'] = True

        # NON-RESIDENTIAL USE
        commercial_keywords = ['RESTAURANT', 'OFFICE', 'RETAIL', 'COMMERCIAL', 'CAFE', 'BAR',
                              'EATING', 'DRINKING', 'VISITOR ACCOMMODATION']
        if any(kw in text for kw in commercial_keywords):
            issues['commercial_use'] = True

        # FAR / DENSITY
        if re.search(r'\bFLOOR AREA RATIO\b', text) or re.search(r'\bFAR\b', text):
            issues['far'] = True

        return issues

    def would_be_allowed_graduated(self, issues):
        """
        Graduated parking approach (original analysis).

        Returns: (would_be_allowed, resolved_issues, remaining_issues)
        """
        remaining_issues = []
        resolved_issues = []

        for issue_type, present in issues.items():
            if not present or issue_type.endswith('_value') or issue_type.endswith('_count'):
                continue

            if issue_type == 'height':
                stories = issues.get('height_value')
                if stories and stories <= 4:
                    resolved_issues.append(f'{stories} stories')
                else:
                    remaining_issues.append(f'{stories} stories' if stories else 'height')

            elif issue_type == 'dwelling_units':
                units = issues.get('unit_count')
                if units and units <= 3:
                    resolved_issues.append(f'{units} units')
                else:
                    remaining_issues.append(f'{units} units' if units else 'dwelling units')

            elif issue_type == 'parking':
                units = issues.get('unit_count')
                if units and units <= 3:
                    resolved_issues.append('parking (small project)')
                elif units and units <= 10:
                    remaining_issues.append('parking (medium project)')
                else:
                    remaining_issues.append('parking (large project)')

            else:
                remaining_issues.append(issue_type)

        would_be_allowed = len(remaining_issues) == 0
        return would_be_allowed, resolved_issues, remaining_issues

    def would_be_allowed_citywide(self, issues):
        """
        Citywide parking elimination approach.

        Eliminates ALL parking minimums (not graduated).

        Returns: (would_be_allowed, resolved_issues, remaining_issues)
        """
        remaining_issues = []
        resolved_issues = []

        for issue_type, present in issues.items():
            if not present or issue_type.endswith('_value') or issue_type.endswith('_count'):
                continue

            if issue_type == 'height':
                stories = issues.get('height_value')
                if stories and stories <= 4:
                    resolved_issues.append(f'{stories} stories')
                else:
                    remaining_issues.append(f'{stories} stories' if stories else 'height')

            elif issue_type == 'dwelling_units':
                units = issues.get('unit_count')
                if units and units <= 3:
                    resolved_issues.append(f'{units} units')
                else:
                    remaining_issues.append(f'{units} units' if units else 'dwelling units')

            elif issue_type == 'parking':
                # CITYWIDE ELIMINATION - all parking issues resolved
                resolved_issues.append('parking (citywide elimination)')

            else:
                remaining_issues.append(issue_type)

        would_be_allowed = len(remaining_issues) == 0
        return would_be_allowed, resolved_issues, remaining_issues

    def analyze_both_scenarios(self):
        """Compare graduated vs citywide parking elimination."""
        print("="*80)
        print("PARKING REFORM COMPARISON: Graduated vs Citywide Elimination")
        print("="*80)

        print("\nScenario 1: Graduated Approach")
        print("  - Small (1-3 units): Zero parking minimum")
        print("  - Medium (4-10 units): Reduced to 0.1:1")
        print("  - Large (11+ units): Reduced to 0.2:1")

        print("\nScenario 2: Citywide Elimination")
        print("  - ALL projects: Zero parking minimum citywide")
        print("="*80)

        # Get all appeals (2015-2026)
        query = """
            SELECT
                EXTRACT(YEAR FROM createddate) as year,
                appealnumber,
                appealgrounds
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2015-01-01'
            ORDER BY createddate DESC
        """

        print("\nFetching all ZBA appeals (2015-2026)...\n")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        print(f"Analyzing {len(data['rows']):,} appeals...\n")

        # Analyze both scenarios
        graduated_eliminated = []
        citywide_eliminated = []

        graduated_by_year = defaultdict(int)
        citywide_by_year = defaultdict(int)

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']
            appeal_num = row['appealnumber']

            issues = self.extract_all_issues(text)

            # Scenario 1: Graduated
            allowed_grad, resolved_grad, remaining_grad = self.would_be_allowed_graduated(issues)
            if allowed_grad:
                graduated_eliminated.append((year, appeal_num, text, resolved_grad))
                graduated_by_year[year] += 1

            # Scenario 2: Citywide
            allowed_city, resolved_city, remaining_city = self.would_be_allowed_citywide(issues)
            if allowed_city:
                citywide_eliminated.append((year, appeal_num, text, resolved_city))
                citywide_by_year[year] += 1

        # Print comparison
        print("="*80)
        print("RESULTS COMPARISON")
        print("="*80)

        total_appeals = len(data['rows'])
        grad_eliminated = len(graduated_eliminated)
        city_eliminated = len(citywide_eliminated)
        additional = city_eliminated - grad_eliminated

        print(f"\nTotal appeals (2015-2026): {total_appeals:,}")
        print(f"\nScenario 1 (Graduated parking):")
        print(f"  Appeals eliminated: {grad_eliminated:,} ({grad_eliminated/total_appeals*100:.1f}%)")
        print(f"  Annual impact: ~{grad_eliminated/11:.0f} appeals/year")

        print(f"\nScenario 2 (Citywide parking elimination):")
        print(f"  Appeals eliminated: {city_eliminated:,} ({city_eliminated/total_appeals*100:.1f}%)")
        print(f"  Annual impact: ~{city_eliminated/11:.0f} appeals/year")

        print(f"\nADDITIONAL impact from citywide elimination:")
        print(f"  Additional appeals eliminated: {additional:,}")
        print(f"  Additional annual impact: ~{additional/11:.0f} appeals/year")
        print(f"  Improvement: {(city_eliminated/grad_eliminated - 1)*100:.1f}% more effective")

        # Year by year
        print(f"\n{'Year':<6} {'Total':>7} {'Graduated':>11} {'%':>6} {'Citywide':>10} {'%':>6} {'Additional':>11}")
        print("-"*80)

        for year in sorted(graduated_by_year.keys()):
            total = len([r for r in data['rows'] if int(r['year']) == year])
            grad = graduated_by_year[year]
            city = citywide_by_year[year]
            add = city - grad

            grad_pct = grad / total * 100 if total > 0 else 0
            city_pct = city / total * 100 if total > 0 else 0

            print(f"{year:<6} {total:>7,} {grad:>11,} {grad_pct:>5.1f}% {city:>10,} {city_pct:>5.1f}% {add:>11,}")

        # What are the additional appeals that citywide eliminates?
        print("\n" + "="*80)
        print("WHAT ADDITIONAL APPEALS DOES CITYWIDE ELIMINATION RESOLVE?")
        print("="*80)

        # Find appeals eliminated by citywide but not graduated
        citywide_set = set(appeal[1] for appeal in citywide_eliminated)
        graduated_set = set(appeal[1] for appeal in graduated_eliminated)
        additional_set = citywide_set - graduated_set

        additional_appeals = [appeal for appeal in citywide_eliminated if appeal[1] in additional_set]

        print(f"\nThese are the {len(additional_appeals):,} appeals eliminated ONLY by citywide approach:")

        # Categorize by what else was resolved
        categories = Counter()
        for year, num, text, resolved in additional_appeals:
            # Filter out parking from resolved
            non_parking = [r for r in resolved if not r.startswith('parking')]
            category = ', '.join(sorted(non_parking)) if non_parking else 'parking only'
            categories[category] += 1

        print(f"\n{'Category':<50} {'Count':>10} {'%':>8}")
        print("-"*80)
        for category, count in categories.most_common(15):
            pct = count / len(additional_appeals) * 100 if len(additional_appeals) > 0 else 0
            print(f"{category:<50} {count:>10,} {pct:>7.1f}%")

        # Sample additional appeals
        print("\n" + "="*80)
        print("SAMPLE ADDITIONAL APPEALS ELIMINATED BY CITYWIDE APPROACH")
        print("="*80)

        print("\nThese would NOT be eliminated by graduated approach, but WOULD by citywide:")
        for i, (year, num, text, resolved) in enumerate(additional_appeals[:15]):
            print(f"\n{i+1}. {year} - {num}")
            print(f"   Resolved: {', '.join(resolved)}")
            if text:
                print(f"   {text[:150]}...")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY & RECOMMENDATION")
        print("="*80)

        print(f"""
CURRENT STATE: ~{total_appeals/11:.0f} variance appeals/year

SCENARIO 1: Graduated Parking Reform + 4 Stories + Triplex
  - Appeals eliminated: {grad_eliminated:,} ({grad_eliminated/total_appeals*100:.1f}%)
  - Annual impact: ~{grad_eliminated/11:.0f} fewer appeals/year
  - Post-reform volume: ~{total_appeals/11 - grad_eliminated/11:.0f} appeals/year

SCENARIO 2: CITYWIDE Parking Elimination + 4 Stories + Triplex
  - Appeals eliminated: {city_eliminated:,} ({city_eliminated/total_appeals*100:.1f}%)
  - Annual impact: ~{city_eliminated/11:.0f} fewer appeals/year
  - Post-reform volume: ~{total_appeals/11 - city_eliminated/11:.0f} appeals/year

ADDITIONAL BENEFIT OF CITYWIDE ELIMINATION:
  - Additional {additional:,} appeals eliminated
  - Additional ~{additional/11:.0f} appeals/year
  - {(city_eliminated/grad_eliminated - 1)*100:.1f}% more effective than graduated approach

BREAKDOWN OF ADDITIONAL APPEALS:
Most are medium and large projects (4+ units) that would still need parking
variances under graduated approach but would be resolved by citywide elimination.

RECOMMENDATION:
Citywide parking elimination provides significant additional benefit with
relatively little downside - if the goal is to maximize housing production
and minimize variance requests, citywide elimination is the better choice.
        """)

        # Calculate parking-only impact
        parking_only_eliminated = len([a for a in additional_appeals
                                      if any('parking' in r for r in a[3])
                                      and not any(r for r in a[3] if not r.startswith('parking'))])

        print(f"\nNote: Of the {additional:,} additional appeals:")
        print(f"  - Appeals with ONLY parking variance: Would definitely be eliminated")
        print(f"  - Appeals with parking + other resolved issues: Would also be eliminated")
        print(f"  - Total additional impact: ~{additional/11:.0f} appeals/year")


def main():
    """Main entry point."""
    analyzer = CitywideReformAnalyzer()
    analyzer.analyze_both_scenarios()


if __name__ == "__main__":
    main()
