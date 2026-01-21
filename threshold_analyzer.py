#!/usr/bin/env python3
"""
Threshold Analysis - Identify specific code thresholds driving variance requests.

Example: If 500 appeals are for 4-story buildings, raising the height limit from 3 to 4 stories
would eliminate ~500 variances per year.

This helps prioritize which code changes would have the biggest impact.
"""

import requests
import pandas as pd
import re
from collections import Counter
from models import get_session, ZBAAppeal


class ThresholdAnalyzer:
    """Analyzes specific numeric thresholds in variance requests."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    def __init__(self):
        self.session = get_session()

    def extract_stories(self, text):
        """Extract number of stories from appeal text."""
        if not text:
            return None

        text = text.upper()

        # Patterns for stories
        patterns = [
            r'(\d+).?STOR(Y|IES)',
            r'(THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN).?STOR(Y|IES)',
            r'(THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH) (FLOOR|STORY)',
        ]

        # Number word to digit mapping
        word_to_num = {
            'ONE': 1, 'FIRST': 1,
            'TWO': 2, 'SECOND': 2,
            'THREE': 3, 'THIRD': 3,
            'FOUR': 4, 'FOURTH': 4,
            'FIVE': 5, 'FIFTH': 5,
            'SIX': 6, 'SIXTH': 6,
            'SEVEN': 7, 'SEVENTH': 7,
            'EIGHT': 8, 'EIGHTH': 8,
            'NINE': 9, 'NINTH': 9,
            'TEN': 10, 'TENTH': 10,
        }

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1)
                if num_str.isdigit():
                    return int(num_str)
                elif num_str in word_to_num:
                    return word_to_num[num_str]

        return None

    def extract_dwelling_units(self, text):
        """Extract number of dwelling units from appeal text."""
        if not text:
            return None

        text = text.upper()

        # Patterns for dwelling units
        patterns = [
            r'\((\d+)\)\s*DWELLING UNIT',
            r'\((\d+)\)\s*UNIT',
            r'(\d+)\s*DWELLING UNIT',
            r'(\d+).?FAMILY',
            r'(TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN).?FAMILY',
        ]

        word_to_num = {
            'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
            'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        }

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1)
                if num_str.isdigit():
                    return int(num_str)
                elif num_str in word_to_num:
                    return word_to_num[num_str]

        return None

    def extract_parking_spaces(self, text):
        """Extract number of parking spaces from appeal text."""
        if not text:
            return None

        text = text.upper()

        # Patterns for parking spaces
        patterns = [
            r'\((\d+)\)\s*(PARKING|ACCESSORY)\s*SPACE',
            r'(\d+)\s*PARKING SPACE',
            r'(\d+)\s*ACCESSORY PARKING',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1)
                if num_str.isdigit():
                    return int(num_str)

        return None

    def analyze_story_thresholds(self):
        """Analyze appeals by number of stories requested."""
        print("="*80)
        print("STORY HEIGHT THRESHOLD ANALYSIS")
        print("="*80)

        # Get all appeals from API with story mentions
        query = """
            SELECT
                EXTRACT(YEAR FROM createddate) as year,
                appealnumber,
                appealgrounds,
                decision
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2015-01-01'
                AND (
                    UPPER(appealgrounds) LIKE '%STORY%' OR
                    UPPER(appealgrounds) LIKE '%STORIES%' OR
                    UPPER(appealgrounds) LIKE '%FLOOR%'
                )
            ORDER BY createddate DESC
        """

        print("\nFetching appeals with story/height mentions...")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        print(f"Found {len(data['rows'])} appeals mentioning stories/floors\n")

        # Extract story counts
        story_counts = Counter()
        story_by_year = {}

        for row in data['rows']:
            stories = self.extract_stories(row['appealgrounds'])
            if stories:
                story_counts[stories] += 1

                year = int(row['year'])
                if year not in story_by_year:
                    story_by_year[year] = Counter()
                story_by_year[year][stories] += 1

        print("Appeals by number of stories:")
        print(f"{'Stories':<10} {'Count':>8} {'% of Total':>12} {'Cumulative %':>15}")
        print("-"*80)

        total = sum(story_counts.values())
        cumulative = 0

        for stories in sorted(story_counts.keys()):
            count = story_counts[stories]
            pct = count / total * 100
            cumulative += pct
            print(f"{stories:<10} {count:>8,} {pct:>11.1f}% {cumulative:>14.1f}%")

        # Impact analysis
        print("\n" + "="*80)
        print("REFORM IMPACT ANALYSIS")
        print("="*80)

        print("\nIf you raised the height limit to allow X stories by-right:")
        print(f"{'Allow up to':<12} {'Variances Eliminated':>25} {'% of Story Variances':>25}")
        print("-"*80)

        for threshold in [3, 4, 5, 6]:
            eliminated = sum(count for stories, count in story_counts.items() if stories <= threshold)
            pct = eliminated / total * 100 if total > 0 else 0
            print(f"{threshold} stories {eliminated:>23,} {pct:>24.1f}%")

        # Trend over time
        print("\n" + "="*80)
        print("TREND: Appeals for 4+ stories by year")
        print("="*80)

        print(f"\n{'Year':<6} {'Total':>8} {'4-story':>8} {'5-story':>8} {'6+ story':>9}")
        print("-"*80)

        for year in sorted(story_by_year.keys()):
            year_total = sum(story_by_year[year].values())
            four = story_by_year[year].get(4, 0)
            five = story_by_year[year].get(5, 0)
            six_plus = sum(count for stories, count in story_by_year[year].items() if stories >= 6)

            print(f"{year:<6} {year_total:>8,} {four:>8,} {five:>8,} {six_plus:>9,}")

        return story_counts

    def analyze_dwelling_unit_thresholds(self):
        """Analyze appeals by number of dwelling units."""
        print("\n" + "="*80)
        print("DWELLING UNIT THRESHOLD ANALYSIS")
        print("="*80)

        query = """
            SELECT
                EXTRACT(YEAR FROM createddate) as year,
                appealnumber,
                appealgrounds,
                decision
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2015-01-01'
                AND (
                    UPPER(appealgrounds) LIKE '%FAMILY%' OR
                    UPPER(appealgrounds) LIKE '%DWELLING UNIT%' OR
                    UPPER(appealgrounds) LIKE '%UNIT%'
                )
            ORDER BY createddate DESC
        """

        print("\nFetching appeals with dwelling unit mentions...")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        print(f"Found {len(data['rows'])} appeals mentioning units/family\n")

        # Extract unit counts
        unit_counts = Counter()

        for row in data['rows']:
            units = self.extract_dwelling_units(row['appealgrounds'])
            if units:
                unit_counts[units] += 1

        print("Appeals by number of dwelling units:")
        print(f"{'Units':<10} {'Count':>8} {'% of Total':>12} {'Cumulative %':>15}")
        print("-"*80)

        total = sum(unit_counts.values())
        cumulative = 0

        for units in sorted(unit_counts.keys()):
            count = unit_counts[units]
            pct = count / total * 100
            cumulative += pct
            print(f"{units:<10} {count:>8,} {pct:>11.1f}% {cumulative:>14.1f}%")

        # Impact analysis
        print("\n" + "="*80)
        print("REFORM IMPACT ANALYSIS")
        print("="*80)

        print("\nIf you allowed X units by-right in more zones:")
        print(f"{'Allow up to':<12} {'Variances Eliminated':>25} {'% of Unit Variances':>25}")
        print("-"*80)

        for threshold in [2, 3, 4, 5, 6]:
            eliminated = sum(count for units, count in unit_counts.items() if units <= threshold)
            pct = eliminated / total * 100 if total > 0 else 0
            print(f"{threshold} units {eliminated:>25,} {pct:>24.1f}%")

        return unit_counts

    def analyze_parking_thresholds(self):
        """Analyze appeals by parking space requirements."""
        print("\n" + "="*80)
        print("PARKING SPACE THRESHOLD ANALYSIS")
        print("="*80)

        query = """
            SELECT
                appealnumber,
                appealgrounds
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2015-01-01'
                AND UPPER(appealgrounds) LIKE '%PARKING%'
            ORDER BY createddate DESC
            LIMIT 1000
        """

        print("\nFetching appeals with parking mentions...")
        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        print(f"Analyzing {len(data['rows'])} appeals mentioning parking\n")

        # Extract parking counts
        parking_counts = Counter()

        for row in data['rows']:
            spaces = self.extract_parking_spaces(row['appealgrounds'])
            if spaces:
                parking_counts[spaces] += 1

        if not parking_counts:
            print("Note: Parking space numbers not commonly specified in appeal text")
            print("Parking variances are typically about 'fewer than required' or 'zero parking'")
            return None

        print("Appeals by number of parking spaces:")
        for spaces in sorted(parking_counts.keys()):
            count = parking_counts[spaces]
            print(f"  {spaces} spaces: {count:,}")

        return parking_counts

    def run_full_analysis(self):
        """Run all threshold analyses."""
        print("="*80)
        print("ZONING CODE THRESHOLD IMPACT ANALYSIS")
        print("Identifying which code changes would eliminate the most variances")
        print("="*80)

        story_counts = self.analyze_story_thresholds()
        unit_counts = self.analyze_dwelling_unit_thresholds()
        parking_counts = self.analyze_parking_thresholds()

        # Summary recommendations
        print("\n" + "="*80)
        print("SUMMARY RECOMMENDATIONS")
        print("="*80)

        print("\n1. HEIGHT LIMITS:")
        total_stories = sum(story_counts.values())
        four_or_less = sum(count for stories, count in story_counts.items() if stories <= 4)
        print(f"   - {four_or_less:,} appeals ({four_or_less/total_stories*100:.1f}%) are for 4 stories or less")
        print(f"   - Allowing 4 stories by-right would eliminate these variances")
        print(f"   - Annual impact: ~{four_or_less/(2026-2015):.0f} fewer variance requests/year")

        print("\n2. DWELLING UNITS:")
        total_units = sum(unit_counts.values())
        three_or_less = sum(count for units, count in unit_counts.items() if units <= 3)
        print(f"   - {three_or_less:,} appeals ({three_or_less/total_units*100:.1f}%) are for 3 units or less")
        print(f"   - Allowing triplex by-right in more zones would help")
        print(f"   - Annual impact: ~{three_or_less/(2026-2015):.0f} fewer variance requests/year")

        print("\n3. PARKING:")
        print("   - Parking variances typically don't specify exact numbers")
        print("   - Most are 'fewer than required' or 'zero parking'")
        print("   - Eliminating parking minimums would address these")


def main():
    """Main entry point."""
    analyzer = ThresholdAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
