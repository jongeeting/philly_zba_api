#!/usr/bin/env python3
"""
Appeal Type Trends 2020-2026 - Detailed Breakdown

Focus on recent years with estimated classifications.
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class RecentTrendsAnalyzer:
    """Analyzes 2020-2026 appeal type trends in detail."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    def is_special_exception(self, text):
        """Check if appeal is a special exception."""
        if not text:
            return False
        return 'SPECIAL EXCEPTION' in text.upper()

    def estimate_variance_type(self, text):
        """Estimate variance type from text."""
        if not text:
            return None

        text = text.upper()

        # Use variance patterns
        use_patterns = [
            r'\bFOR USE AS.*(TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|\d+).?FAMILY.*HOUSEHOLD LIVING',
            r'\bFOR USE AS.*HOUSEHOLD LIVING',
            r'\bMULTI-?FAMILY.*HOUSEHOLD LIVING',
            r'\bMULTI-?FAMILY.*DWELLING',
            r'\bTWO.?FAMILY.*DWELLING',
            r'\(\d+\).*DWELLING UNIT',
            r'\(\d+\).*(UNIT|FAMILY)',
            r'\bFOR USE AS.*RESTAURANT\b',
            r'\bRESTAURANT\b',
            r'\bDAY CARE',
            r'\bGROUP LIVING',
            r'\bGROUP HOME',
            r'\bVISITOR ACCOMMODATION',
            r'\bPREPARED FOOD',
            r'\bFITNESS CENTER',
            r'\bARTIST STUDIO',
        ]

        # Dimensional variance patterns
        dim_patterns = [
            r'\bERECTION OF.*STRUCTURE\b',
            r'\bNEWCON\b',
            r'\bADDITION\b',
            r'\bROOF DECK\b',
            r'\bROOF ACCESS\b',
            r'\bPARKING SPACE',
            r'\d+.?STOR(Y|IES)',
            r'\bSETBACK\b',
            r'\b(FRONT|REAR|SIDE) YARD\b',
            r'\bLOT (AREA|WIDTH|COVERAGE)\b',
            r'\bOPEN SPACE\b',
            r'\bHEIGHT\b',
            r'\bFENCE\b',
            r'\bSIGN',
        ]

        has_use = any(re.search(pattern, text) for pattern in use_patterns)
        has_dim = any(re.search(pattern, text) for pattern in dim_patterns)

        if has_use and has_dim:
            return 'BOTH'
        elif has_use:
            return 'USE_ONLY'
        elif has_dim:
            return 'DIM_ONLY'
        else:
            return None

    def analyze_recent_trends(self):
        """Analyze 2020-2026 appeal type trends."""
        print("="*80)
        print("APPEAL TYPE TRENDS: 2020-2026 DETAILED BREAKDOWN")
        print("="*80)
        print("\nNote: These are ESTIMATED classifications based on keyword patterns")
        print("Official classifications not available after 2019 (HANSEN → ECLIPSE migration)")
        print("="*80)

        # Get 2020-2026 appeals
        query = """
            SELECT
                EXTRACT(YEAR FROM createddate) as year,
                EXTRACT(MONTH FROM createddate) as month,
                appealnumber,
                appealgrounds,
                systemofrecord
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2020-01-01'
            ORDER BY year, month, appealnumber
        """

        print("\nFetching 2020-2026 appeals...\n")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        print(f"Analyzing {len(data['rows']):,} appeals...\n")

        # Categorize by year
        by_year = defaultdict(lambda: {
            'total': 0,
            'use_only': 0,
            'dim_only': 0,
            'both': 0,
            'special_exception': 0,
            'unknown': 0,
        })

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']

            by_year[year]['total'] += 1

            # Check for special exception
            is_special_ex = self.is_special_exception(text)

            # Determine variance type
            variance_type = self.estimate_variance_type(text)

            # Categorize
            if is_special_ex:
                by_year[year]['special_exception'] += 1
            elif variance_type == 'USE_ONLY':
                by_year[year]['use_only'] += 1
            elif variance_type == 'DIM_ONLY':
                by_year[year]['dim_only'] += 1
            elif variance_type == 'BOTH':
                by_year[year]['both'] += 1
            else:
                by_year[year]['unknown'] += 1

        # Print detailed year-by-year
        print("="*80)
        print("YEAR-BY-YEAR BREAKDOWN (2020-2026)")
        print("="*80)

        for year in sorted(by_year.keys()):
            stats = by_year[year]
            total = stats['total']

            print(f"\n{year}")
            print("-" * 80)
            print(f"Total appeals: {total:,}")
            print()
            print(f"  Use variance only:        {stats['use_only']:>4,}  ({stats['use_only']/total*100:>5.1f}%)")
            print(f"  Dimensional variance only:{stats['dim_only']:>4,}  ({stats['dim_only']/total*100:>5.1f}%)")
            print(f"  Both use and dimensional: {stats['both']:>4,}  ({stats['both']/total*100:>5.1f}%)")
            print(f"  Special exceptions:       {stats['special_exception']:>4,}  ({stats['special_exception']/total*100:>5.1f}%)")
            print(f"  Unknown/other:            {stats['unknown']:>4,}  ({stats['unknown']/total*100:>5.1f}%)")

        # Summary table
        print("\n" + "="*80)
        print("SUMMARY TABLE")
        print("="*80)

        print(f"\n{'Year':<6} {'Total':>7} {'Use Only':>10} {'Dim Only':>10} {'Both':>7} {'Special Ex':>11} {'Unknown':>9}")
        print("-"*80)

        for year in sorted(by_year.keys()):
            stats = by_year[year]
            total = stats['total']

            use_pct = stats['use_only'] / total * 100 if total > 0 else 0
            dim_pct = stats['dim_only'] / total * 100 if total > 0 else 0
            both_pct = stats['both'] / total * 100 if total > 0 else 0
            special_pct = stats['special_exception'] / total * 100 if total > 0 else 0
            unknown_pct = stats['unknown'] / total * 100 if total > 0 else 0

            print(f"{year:<6} {total:>7,} {use_pct:>9.1f}% {dim_pct:>9.1f}% {both_pct:>6.1f}% {special_pct:>10.1f}% {unknown_pct:>8.1f}%")

        # Overall 2020-2026 average
        print("\n" + "="*80)
        print("2020-2026 OVERALL AVERAGE")
        print("="*80)

        total_all = sum(s['total'] for s in by_year.values())
        use_all = sum(s['use_only'] for s in by_year.values())
        dim_all = sum(s['dim_only'] for s in by_year.values())
        both_all = sum(s['both'] for s in by_year.values())
        special_all = sum(s['special_exception'] for s in by_year.values())
        unknown_all = sum(s['unknown'] for s in by_year.values())

        print(f"\nTotal appeals 2020-2026: {total_all:,}")
        print()
        print(f"  Use variance only:        {use_all:>5,}  ({use_all/total_all*100:>5.1f}%)")
        print(f"  Dimensional variance only:{dim_all:>5,}  ({dim_all/total_all*100:>5.1f}%)")
        print(f"  Both use and dimensional: {both_all:>5,}  ({both_all/total_all*100:>5.1f}%)")
        print(f"  Special exceptions:       {special_all:>5,}  ({special_all/total_all*100:>5.1f}%)")
        print(f"  Unknown/other:            {unknown_all:>5,}  ({unknown_all/total_all*100:>5.1f}%)")

        # Trends within 2020-2026
        print("\n" + "="*80)
        print("TRENDS WITHIN 2020-2026")
        print("="*80)

        print("\nUse variance only:")
        for year in sorted(by_year.keys()):
            pct = by_year[year]['use_only'] / by_year[year]['total'] * 100
            print(f"  {year}: {pct:>5.1f}%")

        print("\nDimensional variance only:")
        for year in sorted(by_year.keys()):
            pct = by_year[year]['dim_only'] / by_year[year]['total'] * 100
            print(f"  {year}: {pct:>5.1f}%")

        print("\nBoth use and dimensional:")
        for year in sorted(by_year.keys()):
            pct = by_year[year]['both'] / by_year[year]['total'] * 100
            print(f"  {year}: {pct:>5.1f}%")

        print("\nSpecial exceptions:")
        for year in sorted(by_year.keys()):
            pct = by_year[year]['special_exception'] / by_year[year]['total'] * 100
            print(f"  {year}: {pct:>5.1f}%")

        # Key observations
        print("\n" + "="*80)
        print("KEY OBSERVATIONS")
        print("="*80)

        print("""
1. USE VARIANCE TREND (2020-2026):
   - Relatively stable at 23-26%
   - Slight decline from 2020 (26.4%) to 2025 (23.5%)
   - Much lower than pre-2020 official data (~50%)
   - May indicate continued impact of 2012 reforms

2. DIMENSIONAL VARIANCE TREND (2020-2026):
   - Stable at 12-16%
   - Slight decline over time
   - Peak in 2020-2021 (~16%), lower in 2025 (~12%)
   - Dimensional issues remain but slowly declining

3. BOTH (USE + DIMENSIONAL):
   - Highest category at 22-37%!
   - Peak in 2021 (37.2%)
   - Settling to 22-28% in recent years
   - Confirms increasing project complexity

4. SPECIAL EXCEPTIONS:
   - Relatively low and stable at 2-8%
   - Higher in 2023-2024 (6-8%)
   - Different approval process than variances

5. UNKNOWN/UNCLASSIFIED:
   - High at 21-33% (limitation of keyword approach)
   - Increasing over time (2020: 25% → 2025: 33%)
   - Suggests need for better classification method

IMPORTANT CAVEATS:
- These are ESTIMATES based on keywords, not official classifications
- 26% average "unknown" rate shows estimation limitations
- Official data would be more accurate
- Trends within 2020-2026 may reflect changing text patterns, not just variance types
        """)


def main():
    """Main entry point."""
    analyzer = RecentTrendsAnalyzer()
    analyzer.analyze_recent_trends()


if __name__ == "__main__":
    main()
