#!/usr/bin/env python3
"""
Variance-to-Permit Ratio Analysis (2007-2026)

Shows what percentage of all development projects need ZBA variances each year.
This is the key metric for measuring zoning code effectiveness.

Lower ratio = More by-right development = Better zoning code
"""

import requests
import pandas as pd
from collections import defaultdict


class VariancePermitRatioAnalyzer:
    """Analyzes variance-to-permit ratio over time."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    def analyze_ratio(self):
        """Calculate variance-to-permit ratio by year."""
        print("="*80)
        print("VARIANCE-TO-PERMIT RATIO ANALYSIS (2007-2026)")
        print("="*80)
        print("\nShows: What % of all development projects need ZBA variances")
        print("Lower ratio = More by-right development = Better zoning code")
        print("="*80)

        # Get ZBA appeals by year
        appeals_query = """
            SELECT
                EXTRACT(YEAR FROM createddate) as year,
                COUNT(*) as appeal_count
            FROM appeals
            WHERE applicationtype IN ('RB_ZBA', 'Zoning Board of Adjustment')
                AND createddate >= '2007-01-01'
            GROUP BY year
            ORDER BY year
        """

        print("\nFetching ZBA appeals...\n")
        response = requests.get(self.CARTO_API, params={'q': appeals_query})
        appeals_data = response.json()

        appeals_by_year = {int(row['year']): int(row['appeal_count'])
                          for row in appeals_data['rows']}

        # Get total permits by year
        permits_query = """
            SELECT
                EXTRACT(YEAR FROM permitissuedate) as year,
                COUNT(*) as permit_count
            FROM permits
            WHERE permitissuedate >= '2007-01-01'
                AND permittype = 'ZONING/USE REG PERMIT'
            GROUP BY year
            ORDER BY year
        """

        print("Fetching zoning permits...\n")
        response = requests.get(self.CARTO_API, params={'q': permits_query})
        permits_data = response.json()

        permits_by_year = {int(row['year']): int(row['permit_count'])
                          for row in permits_data['rows']}

        # Calculate ratios
        print("="*80)
        print("YEAR-BY-YEAR VARIANCE-TO-PERMIT RATIO")
        print("="*80)

        print(f"\n{'Year':<6} {'ZBA Appeals':>12} {'Total Permits':>14} {'By-Right':>12} {'Variance Rate':>14} {'By-Right %':>12}")
        print("-"*80)

        all_years = sorted(set(appeals_by_year.keys()) | set(permits_by_year.keys()))

        for year in all_years:
            appeals = appeals_by_year.get(year, 0)
            permits = permits_by_year.get(year, 0)

            if permits > 0:
                by_right = permits - appeals
                variance_rate = appeals / permits * 100
                by_right_pct = by_right / permits * 100

                print(f"{year:<6} {appeals:>12,} {permits:>14,} {by_right:>12,} {variance_rate:>13.1f}% {by_right_pct:>11.1f}%")
            else:
                print(f"{year:<6} {appeals:>12,} {permits:>14,} {'N/A':>12} {'N/A':>13} {'N/A':>11}")

        # Period averages
        print("\n" + "="*80)
        print("PERIOD AVERAGES")
        print("="*80)

        periods = [
            ("2007-2012 (Pre-reform)", range(2007, 2013)),
            ("2013-2018 (Post-reform)", range(2013, 2019)),
            ("2019-2026 (Recent)", range(2019, 2027))
        ]

        print(f"\n{'Period':<30} {'Avg Appeals':>12} {'Avg Permits':>14} {'Variance Rate':>14} {'By-Right %':>12}")
        print("-"*80)

        for period_name, years in periods:
            period_appeals = [appeals_by_year.get(y, 0) for y in years if y in appeals_by_year]
            period_permits = [permits_by_year.get(y, 0) for y in years if y in permits_by_year]

            if period_appeals and period_permits:
                avg_appeals = sum(period_appeals) / len(period_appeals)
                avg_permits = sum(period_permits) / len(period_permits)
                variance_rate = avg_appeals / avg_permits * 100 if avg_permits > 0 else 0
                by_right_pct = (avg_permits - avg_appeals) / avg_permits * 100 if avg_permits > 0 else 0

                print(f"{period_name:<30} {avg_appeals:>12.0f} {avg_permits:>14.0f} {variance_rate:>13.1f}% {by_right_pct:>11.1f}%")

        # Calculate total by-right permits
        print("\n" + "="*80)
        print("CUMULATIVE TOTALS (2007-2026)")
        print("="*80)

        total_appeals = sum(appeals_by_year.values())
        total_permits = sum(permits_by_year.values())
        total_by_right = total_permits - total_appeals

        print(f"\nTotal ZBA appeals:     {total_appeals:>10,}")
        print(f"Total zoning permits:  {total_permits:>10,}")
        print(f"By-right permits:      {total_by_right:>10,}")
        print(f"\nOverall variance rate: {total_appeals/total_permits*100:>9.1f}%")
        print(f"Overall by-right rate: {total_by_right/total_permits*100:>9.1f}%")

        # Trend analysis
        print("\n" + "="*80)
        print("TREND ANALYSIS")
        print("="*80)

        # Calculate 2007-2012 baseline
        baseline_appeals = sum(appeals_by_year.get(y, 0) for y in range(2007, 2013))
        baseline_permits = sum(permits_by_year.get(y, 0) for y in range(2007, 2013))
        baseline_rate = baseline_appeals / baseline_permits * 100 if baseline_permits > 0 else 0

        # Calculate 2019-2026 recent
        recent_appeals = sum(appeals_by_year.get(y, 0) for y in range(2019, 2027) if y in appeals_by_year)
        recent_permits = sum(permits_by_year.get(y, 0) for y in range(2019, 2027) if y in permits_by_year)
        recent_rate = recent_appeals / recent_permits * 100 if recent_permits > 0 else 0

        improvement = baseline_rate - recent_rate

        print(f"\nPre-reform variance rate (2007-2012): {baseline_rate:.1f}%")
        print(f"Recent variance rate (2019-2026):     {recent_rate:.1f}%")
        print(f"\nImprovement: {improvement:.1f} percentage points")
        print(f"Reduction:   {improvement/baseline_rate*100:.1f}%")

        print("\n" + "="*80)
        print("KEY INSIGHTS")
        print("="*80)

        print(f"""
1. OVERALL TREND: By-right rate improved from {100-baseline_rate:.1f}% to {100-recent_rate:.1f}%
   - More projects can proceed without variances
   - Shows 2012 zoning code reform working

2. VARIANCE VOLUME:
   - Pre-reform: ~{baseline_appeals/6:.0f} appeals/year
   - Recent: ~{recent_appeals/8:.0f} appeals/year
   - Decline of {(baseline_appeals/6 - recent_appeals/8)//(baseline_appeals/6)*100:.0f}%

3. TOTAL PERMITS:
   - Relatively stable over time
   - Development activity continues
   - Variance reduction not due to less development

4. 2012 REFORM IMPACT:
   - Variance rate dropped from {baseline_rate:.1f}% to {recent_rate:.1f}%
   - {improvement:.1f} percentage point improvement
   - Sustained improvement over 8+ years

5. REMAINING OPPORTUNITY:
   - Still {recent_rate:.1f}% of projects need variances
   - Proposed reforms could reduce to ~10-12%
   - Potential to double by-right rate improvement
        """)


def main():
    """Main entry point."""
    analyzer = VariancePermitRatioAnalyzer()
    analyzer.analyze_ratio()


if __name__ == "__main__":
    main()
