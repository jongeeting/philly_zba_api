#!/usr/bin/env python3
"""
Advanced threshold analysis:
1. Break down thresholds by year to see trends
2. Analyze parking variance by project size
3. Check by-right permits to see if developers build exactly to minimums
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class AdvancedThresholdAnalyzer:
    """Advanced analysis of variance thresholds and by-right permit patterns."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    def extract_stories(self, text):
        """Extract number of stories from text."""
        if not text:
            return None
        text = text.upper()

        patterns = [r'(\d+).?STOR(Y|IES)', r'(THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN).?STOR(Y|IES)']
        word_to_num = {'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10}

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1)
                return int(num_str) if num_str.isdigit() else word_to_num.get(num_str)
        return None

    def extract_dwelling_units(self, text):
        """Extract number of dwelling units from text."""
        if not text:
            return None
        text = text.upper()

        patterns = [
            r'\((\d+)\)\s*DWELLING UNIT', r'\((\d+)\)\s*UNIT', r'(\d+)\s*DWELLING UNIT',
            r'(\d+).?FAMILY', r'(TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN).?FAMILY'
        ]
        word_to_num = {'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10}

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1)
                return int(num_str) if num_str.isdigit() else word_to_num.get(num_str)
        return None

    def has_parking_mention(self, text):
        """Check if parking is mentioned."""
        if not text:
            return False
        return bool(re.search(r'\bPARKING\b', text.upper()))

    def analyze_thresholds_by_year(self):
        """Analyze height and unit thresholds year by year."""
        print("="*80)
        print("THRESHOLD TRENDS OVER TIME")
        print("="*80)

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

        print("\nFetching appeals...")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        # Organize by year
        height_by_year = defaultdict(Counter)
        units_by_year = defaultdict(Counter)

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']

            stories = self.extract_stories(text)
            if stories:
                height_by_year[year][stories] += 1

            units = self.extract_dwelling_units(text)
            if units:
                units_by_year[year][units] += 1

        # Print height trends
        print("\nHEIGHT VARIANCE TRENDS (3-story and 4-story appeals by year):")
        print(f"{'Year':<6} {'Total Height':>13} {'3-story':>9} {'%':>6} {'4-story':>9} {'%':>6}")
        print("-"*80)

        for year in sorted(height_by_year.keys()):
            total = sum(height_by_year[year].values())
            three = height_by_year[year].get(3, 0)
            four = height_by_year[year].get(4, 0)
            three_pct = three / total * 100 if total > 0 else 0
            four_pct = four / total * 100 if total > 0 else 0

            print(f"{year:<6} {total:>13,} {three:>9,} {three_pct:>5.0f}% {four:>9,} {four_pct:>5.0f}%")

        # Print unit trends
        print("\nDWELLING UNIT VARIANCE TRENDS (2-3-4 family by year):")
        print(f"{'Year':<6} {'Total Units':>12} {'2-fam':>7} {'%':>5} {'3-fam':>7} {'%':>5} {'4-fam':>7} {'%':>5}")
        print("-"*80)

        for year in sorted(units_by_year.keys()):
            total = sum(units_by_year[year].values())
            two = units_by_year[year].get(2, 0)
            three = units_by_year[year].get(3, 0)
            four = units_by_year[year].get(4, 0)

            two_pct = two / total * 100 if total > 0 else 0
            three_pct = three / total * 100 if total > 0 else 0
            four_pct = four / total * 100 if total > 0 else 0

            print(f"{year:<6} {total:>12,} {two:>7,} {two_pct:>4.0f}% {three:>7,} {three_pct:>4.0f}% {four:>7,} {four_pct:>4.0f}%")

    def analyze_parking_by_project_size(self):
        """Analyze parking variance by project size (dwelling units)."""
        print("\n" + "="*80)
        print("PARKING VARIANCE BY PROJECT SIZE")
        print("="*80)

        query = """
            SELECT
                appealnumber,
                appealgrounds
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2015-01-01'
                AND UPPER(appealgrounds) LIKE '%PARKING%'
            LIMIT 2000
        """

        print("\nFetching parking appeals...")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        # Categorize by project size
        small_projects_parking = 0  # 1-3 units
        medium_projects_parking = 0  # 4-10 units
        large_projects_parking = 0   # 11+ units
        unknown_size_parking = 0

        for row in data['rows']:
            text = row['appealgrounds']
            units = self.extract_dwelling_units(text)

            if units is None:
                unknown_size_parking += 1
            elif units <= 3:
                small_projects_parking += 1
            elif units <= 10:
                medium_projects_parking += 1
            else:
                large_projects_parking += 1

        total = len(data['rows'])

        print(f"\nParking variances by project size (sample of {total:,} appeals):")
        print(f"  Small (1-3 units):    {small_projects_parking:4,} ({small_projects_parking/total*100:5.1f}%)")
        print(f"  Medium (4-10 units):  {medium_projects_parking:4,} ({medium_projects_parking/total*100:5.1f}%)")
        print(f"  Large (11+ units):    {large_projects_parking:4,} ({large_projects_parking/total*100:5.1f}%)")
        print(f"  Unknown size:         {unknown_size_parking:4,} ({unknown_size_parking/total*100:5.1f}%)")

        print("\nHypothesis test: Is parking more of an issue for larger projects?")
        if large_projects_parking > small_projects_parking:
            print("  ✓ YES - Large projects have more parking variances")
        else:
            print("  ✗ NO - Parking variances are spread across all project sizes")

    def analyze_byright_permits(self):
        """Analyze by-right permits to see if developers build exactly to minimums."""
        print("\n" + "="*80)
        print("BY-RIGHT PERMIT ANALYSIS")
        print("Question: Do developers build exactly to minimum parking requirements?")
        print("="*80)

        # Get zoning permits (by-right approvals)
        query = """
            SELECT
                permitnumber,
                approvedscopeofwork,
                typeofwork,
                numberofunits
            FROM permits
            WHERE permittype IN ('Zoning', 'ZP_ZON/USE', 'ZP_USE', 'ZP_ZONING')
                AND permitissuedate >= '2020-01-01'
                AND permitissuedate < '2024-01-01'
                AND status = 'Issued'
            LIMIT 5000
        """

        print("\nFetching by-right zoning permits (2020-2023)...")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        print(f"Loaded {len(data['rows'])} by-right permits\n")

        # Check for parking mentions in by-right permits
        has_parking_mention = 0
        zero_parking = 0
        total_with_units = 0

        for row in data['rows']:
            scope = (row.get('approvedscopeofwork') or '').upper()

            if 'PARKING' in scope:
                has_parking_mention += 1

                # Check for zero parking
                if 'ZERO PARKING' in scope or 'NO PARKING' in scope or '0 PARKING' in scope:
                    zero_parking += 1

            if row.get('numberofunits'):
                total_with_units += 1

        print(f"By-right permits with parking mentions: {has_parking_mention:,} ({has_parking_mention/len(data['rows'])*100:.1f}%)")
        print(f"Explicitly mentioning zero parking: {zero_parking:,}")
        print(f"Permits with unit counts: {total_with_units:,}")

        print("\nNote: By-right permits typically don't specify parking counts in text")
        print("This data is more commonly in separate permit records or not digitized")

        # Try to analyze by project type
        print("\nAnalyzing by project description...")

        multifamily_count = 0
        multifamily_with_parking = 0

        for row in data['rows']:
            scope = (row.get('approvedscopeofwork') or '').upper()

            if any(term in scope for term in ['MULTI-FAMILY', 'MULTIFAMILY', 'FAMILY DWELLING', 'DWELLING UNIT']):
                multifamily_count += 1
                if 'PARKING' in scope:
                    multifamily_with_parking += 1

        if multifamily_count > 0:
            print(f"\nMultifamily by-right permits: {multifamily_count:,}")
            print(f"  Mentioning parking: {multifamily_with_parking:,} ({multifamily_with_parking/multifamily_count*100:.1f}%)")
            print(f"  NOT mentioning parking: {multifamily_count - multifamily_with_parking:,} ({(multifamily_count-multifamily_with_parking)/multifamily_count*100:.1f}%)")

    def run_full_analysis(self):
        """Run all advanced analyses."""
        print("="*80)
        print("ADVANCED THRESHOLD ANALYSIS")
        print("="*80)

        self.analyze_thresholds_by_year()
        self.analyze_parking_by_project_size()
        self.analyze_byright_permits()


def main():
    """Main entry point."""
    analyzer = AdvancedThresholdAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
