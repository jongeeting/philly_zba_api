#!/usr/bin/env python3
"""
Multi-Issue Variance Analysis

Identifies whether appeals have single variance issues or multiple issues.

KEY QUESTION: If we allow 4 stories by-right, how many appeals would be
COMPLETELY eliminated vs how many would still need variances for other issues?

Example:
- "4-story building" → Would be eliminated (single issue)
- "4-story, 3-family with reduced parking" → Would NOT be eliminated (multi-issue)

This gives us conservative vs optimistic impact estimates.
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class MultiIssueAnalyzer:
    """Analyzes whether appeals have single or multiple variance issues."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    def extract_all_issues(self, text):
        """
        Extract ALL variance issues mentioned in an appeal.

        Returns dict with boolean flags for each issue type.
        """
        if not text:
            return {}

        text = text.upper()
        issues = {}

        # HEIGHT / STORIES
        if re.search(r'\d+.?STOR(Y|IES)', text) or re.search(r'(THREE|FOUR|FIVE|SIX|SEVEN|EIGHT).?STOR(Y|IES)', text):
            issues['height'] = True
            # Extract the number
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

    def count_issues(self, issues):
        """Count how many distinct variance issues are in this appeal."""
        # Count boolean flags (exclude the _value fields)
        issue_types = [k for k in issues.keys() if not k.endswith('_value') and not k.endswith('_count')]
        return len(issue_types)

    def analyze_single_vs_multi_issue(self):
        """
        Analyze appeals to determine single-issue vs multi-issue.

        This tells us the CONSERVATIVE impact estimate (only single-issue appeals
        would be completely eliminated by a code reform).
        """
        print("="*80)
        print("MULTI-ISSUE VARIANCE ANALYSIS")
        print("Question: How many appeals would be COMPLETELY eliminated by each reform?")
        print("="*80)

        # Get appeals with height or unit mentions (2015-2026)
        query = """
            SELECT
                EXTRACT(YEAR FROM createddate) as year,
                appealnumber,
                appealgrounds
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2015-01-01'
                AND (
                    UPPER(appealgrounds) LIKE '%STORY%' OR
                    UPPER(appealgrounds) LIKE '%STORIES%' OR
                    UPPER(appealgrounds) LIKE '%FAMILY%' OR
                    UPPER(appealgrounds) LIKE '%DWELLING UNIT%'
                )
            ORDER BY createddate DESC
        """

        print("\nFetching appeals with height or unit mentions...\n")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        print(f"Analyzing {len(data['rows']):,} appeals...\n")

        # Analyze each appeal
        height_only = []
        height_plus_other = []
        units_only = []
        units_plus_other = []

        height_appeals = defaultdict(lambda: {'only': 0, 'plus_other': 0, 'stories': Counter()})
        unit_appeals = defaultdict(lambda: {'only': 0, 'plus_other': 0, 'units': Counter()})

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']
            issues = self.extract_all_issues(text)
            num_issues = self.count_issues(issues)

            # HEIGHT analysis
            if 'height' in issues:
                stories = issues.get('height_value')
                if num_issues == 1:
                    # ONLY height issue
                    height_only.append((year, stories, text))
                    height_appeals[year]['only'] += 1
                    if stories:
                        height_appeals[year]['stories'][stories] += 1
                else:
                    # Height PLUS other issues
                    height_plus_other.append((year, stories, text, num_issues))
                    height_appeals[year]['plus_other'] += 1

            # DWELLING UNITS analysis
            if 'dwelling_units' in issues:
                units = issues.get('unit_count')
                if num_issues == 1:
                    # ONLY unit issue
                    units_only.append((year, units, text))
                    unit_appeals[year]['only'] += 1
                    if units:
                        unit_appeals[year]['units'][units] += 1
                else:
                    # Units PLUS other issues
                    units_plus_other.append((year, units, text, num_issues))
                    unit_appeals[year]['plus_other'] += 1

        # Print HEIGHT results
        print("="*80)
        print("HEIGHT / STORIES ANALYSIS")
        print("="*80)
        print(f"\nTotal height appeals: {len(height_only) + len(height_plus_other):,}")
        print(f"  ONLY height issue: {len(height_only):,} ({len(height_only)/(len(height_only)+len(height_plus_other))*100:.1f}%)")
        print(f"  Height + other issues: {len(height_plus_other):,} ({len(height_plus_other)/(len(height_only)+len(height_plus_other))*100:.1f}%)")

        print(f"\n{'Year':<6} {'Total':>7} {'Only Height':>12} {'%':>6} {'Height+Other':>13} {'%':>6}")
        print("-"*80)
        for year in sorted(height_appeals.keys()):
            total = height_appeals[year]['only'] + height_appeals[year]['plus_other']
            only = height_appeals[year]['only']
            plus_other = height_appeals[year]['plus_other']
            only_pct = only / total * 100 if total > 0 else 0
            plus_pct = plus_other / total * 100 if total > 0 else 0
            print(f"{year:<6} {total:>7,} {only:>12,} {only_pct:>5.1f}% {plus_other:>13,} {plus_pct:>5.1f}%")

        # Breakdown by story count (only single-issue appeals)
        print("\n" + "="*80)
        print("SINGLE-ISSUE HEIGHT APPEALS - Distribution by Stories")
        print("(These would be COMPLETELY eliminated by height reform)")
        print("="*80)

        stories_counter = Counter()
        for year, stories, text in height_only:
            if stories:
                stories_counter[stories] += 1

        print(f"\n{'Stories':<10} {'Single-Issue Count':>20} {'% of Single-Issue':>20}")
        print("-"*80)
        total_single = sum(stories_counter.values())
        for stories in sorted(stories_counter.keys()):
            count = stories_counter[stories]
            pct = count / total_single * 100 if total_single > 0 else 0
            print(f"{stories:<10} {count:>20,} {pct:>19.1f}%")

        # REFORM IMPACT for height
        print("\n" + "="*80)
        print("HEIGHT REFORM IMPACT ANALYSIS")
        print("="*80)

        print("\nCONSERVATIVE estimate (only single-issue appeals eliminated):")
        print(f"{'Allow up to':<12} {'Appeals Eliminated':>20} {'Appeals/Year':>15}")
        print("-"*80)
        for threshold in [3, 4, 5, 6]:
            eliminated = sum(count for stories, count in stories_counter.items() if stories <= threshold)
            per_year = eliminated / 11  # 2015-2025 = 11 years
            print(f"{threshold} stories {eliminated:>18,} {per_year:>14.0f}")

        print("\nOPTIMISTIC estimate (all appeals mentioning height, including multi-issue):")
        print("(Assumes developers would still proceed with other variances even if height is allowed)")
        print(f"{'Allow up to':<12} {'Appeals Affected':>20} {'Appeals/Year':>15}")
        print("-"*80)

        all_height_by_stories = Counter()
        for year, stories, text in height_only:
            if stories:
                all_height_by_stories[stories] += 1
        for year, stories, text, num in height_plus_other:
            if stories:
                all_height_by_stories[stories] += 1

        for threshold in [3, 4, 5, 6]:
            affected = sum(count for stories, count in all_height_by_stories.items() if stories <= threshold)
            per_year = affected / 11
            print(f"{threshold} stories {affected:>18,} {per_year:>14.0f}")

        # Print DWELLING UNITS results
        print("\n" + "="*80)
        print("DWELLING UNITS / FAMILY ANALYSIS")
        print("="*80)
        print(f"\nTotal unit appeals: {len(units_only) + len(units_plus_other):,}")
        print(f"  ONLY units issue: {len(units_only):,} ({len(units_only)/(len(units_only)+len(units_plus_other))*100:.1f}%)")
        print(f"  Units + other issues: {len(units_plus_other):,} ({len(units_plus_other)/(len(units_only)+len(units_plus_other))*100:.1f}%)")

        print(f"\n{'Year':<6} {'Total':>7} {'Only Units':>11} {'%':>6} {'Units+Other':>13} {'%':>6}")
        print("-"*80)
        for year in sorted(unit_appeals.keys()):
            total = unit_appeals[year]['only'] + unit_appeals[year]['plus_other']
            only = unit_appeals[year]['only']
            plus_other = unit_appeals[year]['plus_other']
            only_pct = only / total * 100 if total > 0 else 0
            plus_pct = plus_other / total * 100 if total > 0 else 0
            print(f"{year:<6} {total:>7,} {only:>11,} {only_pct:>5.1f}% {plus_other:>13,} {plus_pct:>5.1f}%")

        # Breakdown by unit count (only single-issue appeals)
        print("\n" + "="*80)
        print("SINGLE-ISSUE DWELLING UNIT APPEALS - Distribution by Unit Count")
        print("(These would be COMPLETELY eliminated by unit reforms)")
        print("="*80)

        units_counter = Counter()
        for year, units, text in units_only:
            if units:
                units_counter[units] += 1

        print(f"\n{'Units':<10} {'Single-Issue Count':>20} {'% of Single-Issue':>20}")
        print("-"*80)
        total_single_units = sum(units_counter.values())
        for units in sorted(units_counter.keys()):
            count = units_counter[units]
            pct = count / total_single_units * 100 if total_single_units > 0 else 0
            print(f"{units:<10} {count:>20,} {pct:>19.1f}%")

        # REFORM IMPACT for units
        print("\n" + "="*80)
        print("DWELLING UNIT REFORM IMPACT ANALYSIS")
        print("="*80)

        print("\nCONSERVATIVE estimate (only single-issue appeals eliminated):")
        print(f"{'Allow up to':<12} {'Appeals Eliminated':>20} {'Appeals/Year':>15}")
        print("-"*80)
        for threshold in [2, 3, 4, 5]:
            eliminated = sum(count for units, count in units_counter.items() if units <= threshold)
            per_year = eliminated / 11
            print(f"{threshold} units {eliminated:>20,} {per_year:>14.0f}")

        print("\nOPTIMISTIC estimate (all appeals mentioning units, including multi-issue):")
        print(f"{'Allow up to':<12} {'Appeals Affected':>20} {'Appeals/Year':>15}")
        print("-"*80)

        all_units_by_count = Counter()
        for year, units, text in units_only:
            if units:
                all_units_by_count[units] += 1
        for year, units, text, num in units_plus_other:
            if units:
                all_units_by_count[units] += 1

        for threshold in [2, 3, 4, 5]:
            affected = sum(count for units, count in all_units_by_count.items() if units <= threshold)
            per_year = affected / 11
            print(f"{threshold} units {affected:>20,} {per_year:>14.0f}")

        # Sample multi-issue appeals
        print("\n" + "="*80)
        print("SAMPLE MULTI-ISSUE APPEALS (showing why single reforms won't eliminate them)")
        print("="*80)

        print("\nSample 4-story appeals with OTHER issues:")
        count = 0
        for year, stories, text, num_issues in height_plus_other:
            if stories == 4 and count < 10:
                issues = self.extract_all_issues(text)
                issue_list = [k for k in issues.keys() if not k.endswith('_value') and not k.endswith('_count')]
                print(f"\n{year} - {num_issues} issues: {', '.join(issue_list)}")
                print(f"  {text[:200]}...")
                count += 1

        print("\n" + "="*80)
        print("SUMMARY RECOMMENDATIONS")
        print("="*80)

        # Height recommendations
        height_4_only = sum(count for stories, count in stories_counter.items() if stories <= 4)
        height_4_all = sum(count for stories, count in all_height_by_stories.items() if stories <= 4)

        print("\n1. ALLOW 4 STORIES BY-RIGHT:")
        print(f"   Conservative impact: {height_4_only:,} appeals eliminated (~{height_4_only/11:.0f}/year)")
        print(f"   Optimistic impact: {height_4_all:,} appeals affected (~{height_4_all/11:.0f}/year)")
        print(f"   Reality: Likely in between - some multi-issue projects would proceed with fewer variances")

        # Unit recommendations
        units_3_only = sum(count for units, count in units_counter.items() if units <= 3)
        units_3_all = sum(count for units, count in all_units_by_count.items() if units <= 3)

        print("\n2. ALLOW TRIPLEX (3 UNITS) BY-RIGHT:")
        print(f"   Conservative impact: {units_3_only:,} appeals eliminated (~{units_3_only/11:.0f}/year)")
        print(f"   Optimistic impact: {units_3_all:,} appeals affected (~{units_3_all/11:.0f}/year)")
        print(f"   Reality: Likely in between")

        # Combined
        print("\n3. COMBINED (4 stories + triplex):")
        print(f"   Conservative: ~{(height_4_only+units_3_only)/11:.0f} appeals/year eliminated")
        print(f"   Optimistic: ~{(height_4_all+units_3_all)/11:.0f} appeals/year affected")
        print("   (Note: Some overlap - appeals with both height and unit issues)")


def main():
    """Main entry point."""
    analyzer = MultiIssueAnalyzer()
    analyzer.analyze_single_vs_multi_issue()


if __name__ == "__main__":
    main()
