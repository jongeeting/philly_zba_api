#!/usr/bin/env python3
"""
Complete vs Partial Impact Analysis

Shows two impact measures:
1. COMPLETELY ELIMINATED - All variance issues resolved (conservative)
2. IMPACTED/AFFECTED - At least one variance issue resolved (optimistic)

This helps communicate both the guaranteed impact (complete elimination)
and the broader benefit (partial help for complex projects).
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class CompleteVsPartialAnalyzer:
    """Analyzes both complete elimination and partial impact."""

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

    def check_citywide_impact(self, issues):
        """
        Check if reforms would help this appeal (completely or partially).

        Returns: (completely_eliminated, partially_helped, resolved_issues, remaining_issues)
        """
        resolved_issues = []
        remaining_issues = []

        for issue_type, present in issues.items():
            if not present or issue_type.endswith('_value') or issue_type.endswith('_count'):
                continue

            # HEIGHT - Would 4 stories be allowed?
            if issue_type == 'height':
                stories = issues.get('height_value')
                if stories and stories <= 4:
                    resolved_issues.append(f'{stories} stories')
                else:
                    remaining_issues.append(f'{stories} stories' if stories else 'height')

            # DWELLING UNITS - Would triplex be allowed?
            elif issue_type == 'dwelling_units':
                units = issues.get('unit_count')
                if units and units <= 3:
                    resolved_issues.append(f'{units} units')
                else:
                    remaining_issues.append(f'{units} units' if units else 'dwelling units')

            # PARKING - Citywide elimination resolves ALL parking
            elif issue_type == 'parking':
                resolved_issues.append('parking')

            # All other issues would still require variances
            else:
                remaining_issues.append(issue_type)

        completely_eliminated = len(remaining_issues) == 0 and len(resolved_issues) > 0
        partially_helped = len(resolved_issues) > 0 and len(remaining_issues) > 0

        return completely_eliminated, partially_helped, resolved_issues, remaining_issues

    def analyze_complete_vs_partial(self):
        """Analyze both complete elimination and partial impact."""
        print("="*80)
        print("COMPLETE vs PARTIAL IMPACT ANALYSIS")
        print("="*80)
        print("\nReforms: 4 stories + triplex + citywide parking elimination")
        print("\nTwo impact measures:")
        print("  1. COMPLETELY ELIMINATED - All variance issues resolved")
        print("  2. IMPACTED/AFFECTED - At least one issue resolved (but may still need variances)")
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

        # Categorize appeals
        completely_eliminated = []
        partially_helped = []
        not_helped = []

        by_year_complete = defaultdict(int)
        by_year_partial = defaultdict(int)
        by_year_total_helped = defaultdict(int)

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']
            appeal_num = row['appealnumber']

            issues = self.extract_all_issues(text)
            complete, partial, resolved, remaining = self.check_citywide_impact(issues)

            if complete:
                completely_eliminated.append((year, appeal_num, text, resolved))
                by_year_complete[year] += 1
                by_year_total_helped[year] += 1
            elif partial:
                partially_helped.append((year, appeal_num, text, resolved, remaining))
                by_year_partial[year] += 1
                by_year_total_helped[year] += 1
            else:
                not_helped.append((year, appeal_num, text))

        # Print results
        print("="*80)
        print("RESULTS")
        print("="*80)

        total_appeals = len(data['rows'])
        num_complete = len(completely_eliminated)
        num_partial = len(partially_helped)
        num_total_helped = num_complete + num_partial
        num_not_helped = len(not_helped)

        print(f"\nTotal appeals (2015-2026): {total_appeals:,}")
        print(f"\n1. COMPLETELY ELIMINATED (all issues resolved):")
        print(f"   Count: {num_complete:,} ({num_complete/total_appeals*100:.1f}%)")
        print(f"   Annual: ~{num_complete/11:.0f} appeals/year")

        print(f"\n2. PARTIALLY HELPED (some issues resolved, but still need variances):")
        print(f"   Count: {num_partial:,} ({num_partial/total_appeals*100:.1f}%)")
        print(f"   Annual: ~{num_partial/11:.0f} appeals/year")

        print(f"\n3. TOTAL IMPACTED (completely + partially):")
        print(f"   Count: {num_total_helped:,} ({num_total_helped/total_appeals*100:.1f}%)")
        print(f"   Annual: ~{num_total_helped/11:.0f} appeals/year")

        print(f"\n4. NOT HELPED BY THESE REFORMS:")
        print(f"   Count: {num_not_helped:,} ({num_not_helped/total_appeals*100:.1f}%)")
        print(f"   Examples: Commercial uses, roof decks, setbacks, 4+ units, 5+ stories")

        # Year by year
        print(f"\n{'Year':<6} {'Total':>7} {'Complete':>10} {'%':>6} {'Partial':>9} {'%':>6} {'Total Impact':>13} {'%':>6}")
        print("-"*80)

        for year in sorted(by_year_complete.keys()):
            total = len([r for r in data['rows'] if int(r['year']) == year])
            complete = by_year_complete[year]
            partial = by_year_partial[year]
            total_helped = by_year_total_helped[year]

            complete_pct = complete / total * 100 if total > 0 else 0
            partial_pct = partial / total * 100 if total > 0 else 0
            total_pct = total_helped / total * 100 if total > 0 else 0

            print(f"{year:<6} {total:>7,} {complete:>10,} {complete_pct:>5.1f}% {partial:>9,} {partial_pct:>5.1f}% {total_helped:>13,} {total_pct:>5.1f}%")

        # Sample partially helped appeals
        print("\n" + "="*80)
        print("SAMPLE PARTIALLY HELPED APPEALS")
        print("(These get SOME benefit but still need variances for other issues)")
        print("="*80)

        print("\nExamples of appeals that benefit but aren't completely eliminated:")
        for i, (year, num, text, resolved, remaining) in enumerate(partially_helped[:15]):
            print(f"\n{i+1}. {year} - {num}")
            print(f"   ✓ RESOLVED: {', '.join(resolved)}")
            print(f"   ✗ STILL NEED: {', '.join(remaining)}")
            if text:
                print(f"   {text[:120]}...")

        # What gets partially resolved?
        print("\n" + "="*80)
        print("WHAT ISSUES GET PARTIALLY RESOLVED?")
        print("="*80)

        resolved_categories = Counter()
        for year, num, text, resolved, remaining in partially_helped:
            for issue in resolved:
                resolved_categories[issue] += 1

        print(f"\nFor the {num_partial:,} partially helped appeals, these issues were resolved:")
        print(f"\n{'Issue Resolved':<30} {'Count':>10} {'%':>8}")
        print("-"*80)
        for issue, count in resolved_categories.most_common(15):
            pct = count / num_partial * 100 if num_partial > 0 else 0
            print(f"{issue:<30} {count:>10,} {pct:>7.1f}%")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        print(f"""
COMPLETE ELIMINATION (Conservative Impact):
  - Appeals: {num_complete:,} ({num_complete/total_appeals*100:.1f}%)
  - Annual: ~{num_complete/11:.0f} appeals/year
  - Post-reform volume: ~{total_appeals/11 - num_complete/11:.0f} appeals/year
  - These appeals become COMPLETELY UNNECESSARY

PARTIAL IMPACT (Additional Benefit):
  - Appeals: {num_partial:,} ({num_partial/total_appeals*100:.1f}%)
  - Annual: ~{num_partial/11:.0f} appeals/year
  - These appeals still need ZBA review, but with FEWER variance requests
  - Benefits: Faster processing, lower rejection risk, reduced complexity

TOTAL IMPACT (Conservative + Partial):
  - Appeals affected: {num_total_helped:,} ({num_total_helped/total_appeals*100:.1f}%)
  - Annual: ~{num_total_helped/11:.0f} appeals/year
  - This is the TOTAL number of appeals that benefit from these reforms

NOT HELPED ({num_not_helped:,} appeals):
  - Commercial uses, roof decks, setbacks, large projects (4+ units)
  - These are legitimately complex projects that need ZBA review
  - No overlap with the three reforms

MESSAGING:

Conservative: "These reforms eliminate {num_complete/11:.0f} variance appeals/year"
Optimistic: "These reforms impact {num_total_helped/11:.0f} appeals/year"
Truth: Both are correct - depends on whether you count partial benefits

The partial benefits ARE real:
  - Developers with fewer variance requests proceed more often
  - ZBA processing is faster with fewer issues to review
  - Lower risk of rejection when seeking fewer variances
  - Some developers might proceed who wouldn't with more variances
        """)


def main():
    """Main entry point."""
    analyzer = CompleteVsPartialAnalyzer()
    analyzer.analyze_complete_vs_partial()


if __name__ == "__main__":
    main()
