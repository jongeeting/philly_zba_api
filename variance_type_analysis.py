#!/usr/bin/env python3
"""
Analyze variance types and code violations that drive ZBA appeals.

This script categorizes appeals by the type of zoning code issue being appealed,
such as parking, setbacks, height, FAR, use restrictions, etc.
"""

import requests
import pandas as pd
from models import get_session, ZBAAppeal
from collections import defaultdict, Counter
import re


class VarianceTypeAnalyzer:
    """Analyzes the types of code violations driving variance requests."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    # Keywords to identify different types of code violations
    VIOLATION_PATTERNS = {
        'Use Variance': [
            r'\buse\s+variance\b',
            r'\bUSEVAR\b',
            r'\bnon-conforming\s+use\b',
            r'\bprohibited\s+use\b',
        ],
        'Parking': [
            r'\bparking\b',
            r'\bvehicle\s+storage\b',
            r'\boff-street\s+parking\b',
            r'\bgarage\b',
            r'\bparking\s+spaces?\b',
        ],
        'Setback': [
            r'\bsetback\b',
            r'\byard\b',
            r'\bfront\s+yard\b',
            r'\brear\s+yard\b',
            r'\bside\s+yard\b',
            r'\bbuilding\s+line\b',
        ],
        'Height': [
            r'\bheight\b',
            r'\bstory\b',
            r'\bstories\b',
            r'\bfloors?\b',
            r'\belevation\b',
        ],
        'FAR / Density': [
            r'\bFAR\b',
            r'\bfloor\s+area\s+ratio\b',
            r'\bdensity\b',
            r'\blot\s+coverage\b',
            r'\bbuilding\s+coverage\b',
        ],
        'Lot Size / Dimensions': [
            r'\blot\s+size\b',
            r'\blot\s+area\b',
            r'\blot\s+width\b',
            r'\blot\s+frontage\b',
            r'\bminimum\s+lot\b',
            r'\blot\s+dimensions\b',
        ],
        'Accessory Structure': [
            r'\baccessory\b',
            r'\broof\s+deck\b',
            r'\bshed\b',
            r'\bfence\b',
            r'\bwall\b',
        ],
        'Signage': [
            r'\bsign\b',
            r'\bsignage\b',
            r'\bbillboard\b',
        ],
        'Loading / Service': [
            r'\bloading\b',
            r'\bservice\b',
            r'\bdelivery\b',
            r'\btrash\b',
            r'\brefuse\b',
        ],
    }

    APPEAL_TYPE_PATTERNS = {
        'Use Variance': r'APPEAL TYPE:\s*USEVAR',
        'Dimensional Variance': r'APPEAL TYPE:\s*ZONEVAR',
        'Certificate': r'APPEAL TYPE:\s*CERTIFICAT',
    }

    def __init__(self):
        self.session = get_session()
        self.appeals_df = None

    def load_appeals_with_permit_data(self):
        """Load appeals data including the relatedpermit field from API."""
        print("Loading appeals data with permit information...")

        # Get basic appeal data from database
        appeals = self.session.query(
            ZBAAppeal.appeal_number,
            ZBAAppeal.created_date,
            ZBAAppeal.decision,
            ZBAAppeal.appeal_grounds,
            ZBAAppeal.is_multifamily
        ).all()

        self.appeals_df = pd.DataFrame([{
            'appeal_number': a.appeal_number,
            'created_date': a.created_date,
            'decision': a.decision,
            'appeal_grounds': a.appeal_grounds or '',
            'is_multifamily': a.is_multifamily
        } for a in appeals])

        self.appeals_df['year'] = pd.to_datetime(self.appeals_df['created_date']).dt.year

        # Fetch relatedpermit field from API for appeal type classification
        print("Fetching appeal types from Carto API...")
        query = """
            SELECT appealnumber, relatedpermit
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND relatedpermit IS NOT NULL
        """

        response = requests.get(self.CARTO_API, params={'q': query})
        permit_data = response.json()

        # Create lookup dictionary
        permit_lookup = {
            row['appealnumber']: row['relatedpermit']
            for row in permit_data['rows']
        }

        self.appeals_df['relatedpermit'] = self.appeals_df['appeal_number'].map(permit_lookup)
        self.appeals_df['relatedpermit'] = self.appeals_df['relatedpermit'].fillna('')

        print(f"Loaded {len(self.appeals_df)} appeals")
        return self.appeals_df

    def classify_by_appeal_type(self):
        """Classify appeals by official appeal type (USEVAR, ZONEVAR, etc)."""
        print("\n" + "="*80)
        print("APPEAL TYPE CLASSIFICATION (from official records)")
        print("="*80)

        results = defaultdict(int)

        for _, row in self.appeals_df.iterrows():
            permit_text = row['relatedpermit']
            classified = False

            for appeal_type, pattern in self.APPEAL_TYPE_PATTERNS.items():
                if re.search(pattern, permit_text, re.IGNORECASE):
                    results[appeal_type] += 1
                    classified = True

            if not classified and permit_text:
                results['Other/Unknown'] += 1
            elif not permit_text:
                results['No Data'] += 1

        print("\nAppeal Type Distribution:")
        total = sum(results.values())
        for appeal_type in sorted(results.keys()):
            count = results[appeal_type]
            pct = count / total * 100 if total > 0 else 0
            print(f"  {appeal_type:30s}: {count:6,} ({pct:5.1f}%)")

        return results

    def classify_by_violation_type(self):
        """Classify appeals by type of code violation using keyword matching."""
        print("\n" + "="*80)
        print("CODE VIOLATION TYPE ANALYSIS (keyword-based)")
        print("="*80)

        # Combine appeal_grounds and relatedpermit for analysis
        self.appeals_df['search_text'] = (
            self.appeals_df['appeal_grounds'] + ' ' +
            self.appeals_df['relatedpermit']
        ).str.upper()

        violation_counts = defaultdict(int)
        year_violation_counts = defaultdict(lambda: defaultdict(int))

        for _, row in self.appeals_df.iterrows():
            text = row['search_text']
            year = row['year']

            # Check each violation type
            for violation_type, patterns in self.VIOLATION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        violation_counts[violation_type] += 1
                        year_violation_counts[year][violation_type] += 1
                        break  # Count each violation type only once per appeal

        print("\nViolation Type Distribution (All Years):")
        total_appeals = len(self.appeals_df)
        for violation_type in sorted(violation_counts.keys(), key=lambda x: violation_counts[x], reverse=True):
            count = violation_counts[violation_type]
            pct = count / total_appeals * 100
            print(f"  {violation_type:30s}: {count:6,} ({pct:5.1f}% of appeals)")

        # Year-by-year breakdown
        print("\n" + "="*80)
        print("VIOLATION TYPES BY YEAR")
        print("="*80)

        years = sorted(year_violation_counts.keys())
        violation_types = sorted(violation_counts.keys(), key=lambda x: violation_counts[x], reverse=True)

        # Print top 5 violation types by year
        top_violations = violation_types[:5]

        print(f"\n{'Year':<6}", end='')
        for vtype in top_violations:
            print(f" {vtype[:12]:>12}", end='')
        print()
        print("-" * 80)

        for year in years:
            if year < 2007:  # Skip invalid years
                continue
            year_total = self.appeals_df[self.appeals_df['year'] == year].shape[0]
            print(f"{int(year):<6}", end='')
            for vtype in top_violations:
                count = year_violation_counts[year].get(vtype, 0)
                pct = count / year_total * 100 if year_total > 0 else 0
                print(f" {count:5,}({pct:4.0f}%)", end='')
            print()

        return violation_counts, year_violation_counts

    def analyze_by_period(self):
        """Analyze violation types by reform period."""
        print("\n" + "="*80)
        print("VIOLATION TYPES BY REFORM PERIOD")
        print("="*80)

        def classify_period(year):
            if year < 2012:
                return 'Pre-Reform (2007-2012)'
            elif year <= 2017:
                return 'Original Study (2012-2017)'
            else:
                return 'Extension (2017-2026)'

        self.appeals_df['period'] = self.appeals_df['year'].apply(classify_period)

        period_violations = defaultdict(lambda: defaultdict(int))

        for _, row in self.appeals_df.iterrows():
            text = row['search_text']
            period = row['period']

            for violation_type, patterns in self.VIOLATION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        period_violations[period][violation_type] += 1
                        break

        periods = ['Pre-Reform (2007-2012)', 'Original Study (2012-2017)', 'Extension (2017-2026)']

        for period in periods:
            period_data = self.appeals_df[self.appeals_df['period'] == period]
            period_total = len(period_data)

            print(f"\n{period}:")
            print(f"  Total appeals: {period_total:,}")
            print(f"  Top violation types:")

            violations = period_violations[period]
            sorted_violations = sorted(violations.items(), key=lambda x: x[1], reverse=True)[:7]

            for violation_type, count in sorted_violations:
                pct = count / period_total * 100 if period_total > 0 else 0
                print(f"    {violation_type:30s}: {count:5,} ({pct:5.1f}%)")

    def analyze_multifamily_violations(self):
        """Analyze what violations are most common for multifamily projects."""
        print("\n" + "="*80)
        print("MULTIFAMILY PROJECT VIOLATION PATTERNS")
        print("="*80)

        mf_appeals = self.appeals_df[self.appeals_df['is_multifamily'] == True]
        other_appeals = self.appeals_df[self.appeals_df['is_multifamily'] == False]

        mf_violations = defaultdict(int)
        other_violations = defaultdict(int)

        for _, row in mf_appeals.iterrows():
            text = row['search_text']
            for violation_type, patterns in self.VIOLATION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        mf_violations[violation_type] += 1
                        break

        for _, row in other_appeals.iterrows():
            text = row['search_text']
            for violation_type, patterns in self.VIOLATION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        other_violations[violation_type] += 1
                        break

        print(f"\nMultifamily projects: {len(mf_appeals):,} appeals")
        print(f"Other projects: {len(other_appeals):,} appeals")

        print(f"\n{'Violation Type':<30} {'Multifamily':>15} {'Other':>15} {'MF Rate':>10}")
        print("-" * 75)

        all_types = set(mf_violations.keys()) | set(other_violations.keys())
        sorted_types = sorted(all_types, key=lambda x: mf_violations.get(x, 0), reverse=True)

        for vtype in sorted_types:
            mf_count = mf_violations.get(vtype, 0)
            other_count = other_violations.get(vtype, 0)
            mf_rate = mf_count / len(mf_appeals) * 100 if len(mf_appeals) > 0 else 0
            other_rate = other_count / len(other_appeals) * 100 if len(other_appeals) > 0 else 0

            print(f"{vtype:<30} {mf_count:6,}({mf_rate:5.1f}%) {other_count:6,}({other_rate:5.1f}%) ", end='')

            if mf_rate > other_rate * 1.5:
                print("**MF-heavy**")
            elif other_rate > mf_rate * 1.5:
                print("  (less MF)")
            else:
                print("")

    def export_results(self, output_dir='analysis_output'):
        """Export violation type analysis to CSV."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n\nExporting violation analysis to {output_dir}/...")

        # Create detailed breakdown
        violation_data = []

        for _, row in self.appeals_df.iterrows():
            text = row['search_text']
            violations = []

            for violation_type, patterns in self.VIOLATION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        violations.append(violation_type)
                        break

            violation_data.append({
                'appeal_number': row['appeal_number'],
                'year': row['year'],
                'is_multifamily': row['is_multifamily'],
                'violations': '; '.join(violations) if violations else 'Unclassified'
            })

        df = pd.DataFrame(violation_data)
        df.to_csv(f'{output_dir}/violation_types_by_appeal.csv', index=False)
        print(f"  ✓ violation_types_by_appeal.csv")

        # Summary by year
        year_summary = self.appeals_df.groupby('year').size().reset_index(name='total_appeals')
        year_summary.to_csv(f'{output_dir}/violation_types_summary.csv', index=False)
        print(f"  ✓ violation_types_summary.csv")

    def run_full_analysis(self):
        """Run complete variance type analysis."""
        print("=" * 80)
        print("PHILADELPHIA ZBA VARIANCE TYPE ANALYSIS")
        print("Identifying Code Issues That Drive Variance Requests")
        print("=" * 80)

        self.load_appeals_with_permit_data()
        self.classify_by_appeal_type()
        self.classify_by_violation_type()
        self.analyze_by_period()
        self.analyze_multifamily_violations()
        self.export_results()

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("\nNext Steps:")
        print("1. Review violation patterns to identify reform opportunities")
        print("2. Compare to original 2018 study methodology")
        print("3. Identify which code sections drive the most variance activity")
        print("\n")


def main():
    """Main entry point."""
    analyzer = VarianceTypeAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
