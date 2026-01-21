#!/usr/bin/env python3
"""
Philadelphia Zoning Code Analysis: Recreating & Extending the 2018 5-Year Review

This script analyzes ZBA appeals and zoning permits data to:
1. Recreate the metrics from the 2018 Planning Commission review (2012-2017)
2. Extend the analysis through 2026 (9 additional years)
3. Compare pre-reform (2007-2012) vs post-reform (2012-2017) vs recent (2017-2026)

Original study findings:
- 90% ZBA approval rate
- ~1,000 appeals annually
- Variance volume declined slightly post-2012 reform
"""

import requests
import pandas as pd
from datetime import datetime
from collections import defaultdict
from models import get_session, ZBAAppeal
from sqlalchemy import func, extract, case
import json


class ZoningCodeAnalysis:
    """Analyzes Philadelphia Zoning Code effectiveness using ZBA and permits data."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"
    REFORM_DATE = pd.Timestamp('2012-08-01')  # Zoning code reform effective Aug 2012
    REVIEW_END = pd.Timestamp('2017-08-31')  # Original study end date

    def __init__(self):
        self.session = get_session()
        self.appeals_df = None
        self.permits_df = None

    def load_appeals_data(self):
        """Load ZBA appeals from database."""
        print("Loading ZBA appeals data from database...")

        appeals = self.session.query(
            ZBAAppeal.id,
            ZBAAppeal.appeal_number,
            ZBAAppeal.address,
            ZBAAppeal.created_date,
            ZBAAppeal.decision_date,
            ZBAAppeal.decision,
            ZBAAppeal.appeal_status,
            ZBAAppeal.is_multifamily,
            ZBAAppeal.zip_code,
            ZBAAppeal.appeal_grounds
        ).all()

        self.appeals_df = pd.DataFrame([{
            'appeal_number': a.appeal_number,
            'address': a.address,
            'created_date': a.created_date,
            'decision_date': a.decision_date,
            'decision': a.decision,
            'appeal_status': a.appeal_status,
            'is_multifamily': a.is_multifamily,
            'zip_code': a.zip_code,
            'appeal_grounds': a.appeal_grounds
        } for a in appeals])

        # Add year and period columns
        self.appeals_df['year'] = pd.to_datetime(self.appeals_df['created_date']).dt.year
        self.appeals_df['period'] = self.appeals_df['created_date'].apply(self._classify_period)

        print(f"Loaded {len(self.appeals_df)} ZBA appeals")
        return self.appeals_df

    def load_permits_data(self):
        """Load zoning permits from Carto API."""
        print("Loading zoning permits data from Carto API...")

        query = """
            SELECT
                permitnumber,
                permitissuedate,
                permittype,
                status,
                typeofwork,
                address,
                zip
            FROM permits
            WHERE permittype IN ('Zoning', 'ZP_ZON/USE', 'ZP_USE', 'ZP_ZONING', 'ZP_ADMIN')
                AND permitissuedate >= '2007-01-01'
            ORDER BY permitissuedate
        """

        response = requests.get(self.CARTO_API, params={'q': query})
        data = response.json()

        self.permits_df = pd.DataFrame(data['rows'])
        self.permits_df['permitissuedate'] = pd.to_datetime(self.permits_df['permitissuedate'])
        self.permits_df['year'] = self.permits_df['permitissuedate'].dt.year
        self.permits_df['period'] = self.permits_df['permitissuedate'].apply(self._classify_period)

        print(f"Loaded {len(self.permits_df)} zoning permits")
        return self.permits_df

    def _classify_period(self, date):
        """Classify date into analysis period."""
        if pd.isna(date):
            return 'Unknown'

        # Convert to timezone-naive for comparison
        if hasattr(date, 'tz') and date.tz is not None:
            date = date.tz_localize(None)

        # Convert to timestamp for comparison
        date_ts = pd.Timestamp(date)

        if date_ts < self.REFORM_DATE:
            return 'Pre-Reform (2007-2012)'
        elif date_ts <= self.REVIEW_END:
            return 'Original Study (2012-2017)'
        else:
            return 'Extension (2017-2026)'

    def calculate_approval_rates(self):
        """Calculate ZBA approval rates overall and by period."""
        print("\n" + "="*80)
        print("APPROVAL RATE ANALYSIS")
        print("="*80)

        # Overall approval rates
        decisions = self.appeals_df[self.appeals_df['decision'].notna()]
        decision_counts = decisions['decision'].value_counts()
        decision_pcts = (decision_counts / len(decisions) * 100).round(1)

        print("\nOverall Decision Distribution (2007-2026):")
        print(f"Total appeals with decisions: {len(decisions):,}")
        for decision, count in decision_counts.items():
            pct = decision_pcts[decision]
            print(f"  {decision:20s}: {count:6,} ({pct:5.1f}%)")

        # Calculate "granted" rate (various forms of approval)
        # Note: Decision field format changed in 2020:
        # - Old: "GRANTED", "GRANTED/PROV"
        # - New: "Complete", "Granted", "Approved"
        approval_keywords = ['GRANT', 'Complete', 'Approved']
        granted = decisions[decisions['decision'].str.contains('|'.join(approval_keywords), case=False, na=False)]
        granted_rate = len(granted) / len(decisions) * 100
        print(f"\n✓ Overall Approval Rate: {granted_rate:.1f}%")
        print(f"  (Compare to 2018 study finding: 90%)")
        print(f"  Note: 'Complete' = approved (post-2020 format), 'GRANTED' = approved (pre-2020)")

        # By period
        print("\nApproval Rates by Period:")
        for period in ['Pre-Reform (2007-2012)', 'Original Study (2012-2017)', 'Extension (2017-2026)']:
            period_data = decisions[decisions['period'] == period]
            if len(period_data) > 0:
                period_granted = period_data[period_data['decision'].str.contains('|'.join(approval_keywords), case=False, na=False)]
                period_rate = len(period_granted) / len(period_data) * 100
                print(f"  {period:30s}: {period_rate:5.1f}% ({len(period_granted):,}/{len(period_data):,})")

        # By year
        print("\nApproval Rate by Year:")
        yearly_approval = []
        for year in sorted(decisions['year'].unique()):
            year_data = decisions[decisions['year'] == year]
            year_granted = year_data[year_data['decision'].str.contains('|'.join(approval_keywords), case=False, na=False)]
            approval_rate = len(year_granted) / len(year_data) * 100 if len(year_data) > 0 else 0
            yearly_approval.append({
                'year': year,
                'total': len(year_data),
                'granted': len(year_granted),
                'approval_rate': approval_rate
            })
            print(f"  {year}: {approval_rate:5.1f}% ({len(year_granted):,}/{len(year_data):,})")

        return pd.DataFrame(yearly_approval)

    def calculate_variance_volume(self):
        """Calculate variance volume trends over time."""
        print("\n" + "="*80)
        print("VARIANCE VOLUME ANALYSIS")
        print("="*80)

        # Annual variance volume
        annual_volume = self.appeals_df.groupby('year').size()

        print("\nAnnual ZBA Appeal Volume:")
        for year, count in annual_volume.items():
            print(f"  {year}: {count:,} appeals")

        # By period
        print("\nAverage Annual Volume by Period:")
        for period in ['Pre-Reform (2007-2012)', 'Original Study (2012-2017)', 'Extension (2017-2026)']:
            period_data = self.appeals_df[self.appeals_df['period'] == period]
            years = period_data['year'].nunique()
            avg = len(period_data) / years if years > 0 else 0
            print(f"  {period:30s}: {avg:7.1f} appeals/year ({len(period_data):,} total)")

        return annual_volume

    def calculate_variance_to_permit_ratio(self):
        """Calculate ratio of variances to total zoning permits."""
        print("\n" + "="*80)
        print("VARIANCE-TO-PERMIT RATIO ANALYSIS")
        print("="*80)

        # Merge appeals and permits by year
        appeals_by_year = self.appeals_df.groupby('year').size().reset_index(name='appeals')
        permits_by_year = self.permits_df.groupby('year').size().reset_index(name='permits')

        merged = appeals_by_year.merge(permits_by_year, on='year', how='outer').fillna(0)
        merged['ratio_pct'] = (merged['appeals'] / merged['permits'] * 100).round(1)

        print("\nYear-by-Year Variance Rate (Appeals ÷ Permits):")
        print(f"{'Year':<6} {'Appeals':>8} {'Permits':>10} {'Ratio':>8}")
        print("-" * 40)
        for _, row in merged.iterrows():
            year = int(row['year'])
            appeals = int(row['appeals'])
            permits = int(row['permits'])
            ratio = row['ratio_pct']
            print(f"{year:<6} {appeals:>8,} {permits:>10,} {ratio:>7.1f}%")

        # By period
        print("\nAverage Variance Rate by Period:")
        appeals_by_period = self.appeals_df.groupby('period').size()
        permits_by_period = self.permits_df.groupby('period').size()

        for period in ['Pre-Reform (2007-2012)', 'Original Study (2012-2017)', 'Extension (2017-2026)']:
            appeals = appeals_by_period.get(period, 0)
            permits = permits_by_period.get(period, 0)
            ratio = (appeals / permits * 100) if permits > 0 else 0
            print(f"  {period:30s}: {ratio:5.1f}% ({appeals:,}/{permits:,})")

        return merged

    def analyze_multifamily_trends(self):
        """Analyze multifamily housing variance trends."""
        print("\n" + "="*80)
        print("MULTIFAMILY HOUSING ANALYSIS")
        print("="*80)

        multifamily = self.appeals_df[self.appeals_df['is_multifamily'] == True]

        print(f"\nTotal Multifamily Appeals: {len(multifamily):,} ({len(multifamily)/len(self.appeals_df)*100:.1f}% of all appeals)")

        # By period
        print("\nMultifamily Appeals by Period:")
        for period in ['Pre-Reform (2007-2012)', 'Original Study (2012-2017)', 'Extension (2017-2026)']:
            period_all = self.appeals_df[self.appeals_df['period'] == period]
            period_mf = multifamily[multifamily['period'] == period]
            pct = len(period_mf) / len(period_all) * 100 if len(period_all) > 0 else 0
            print(f"  {period:30s}: {len(period_mf):,} ({pct:.1f}% of period)")

        # Multifamily approval rates
        mf_with_decision = multifamily[multifamily['decision'].notna()]
        approval_keywords = ['GRANT', 'Complete', 'Approved']
        mf_granted = mf_with_decision[mf_with_decision['decision'].str.contains('|'.join(approval_keywords), case=False, na=False)]
        mf_approval_rate = len(mf_granted) / len(mf_with_decision) * 100 if len(mf_with_decision) > 0 else 0

        print(f"\nMultifamily Approval Rate: {mf_approval_rate:.1f}%")
        print(f"  ({len(mf_granted):,}/{len(mf_with_decision):,} multifamily appeals approved)")

        # Annual multifamily trends
        print("\nMultifamily Appeals by Year:")
        mf_by_year = multifamily.groupby('year').size()
        all_by_year = self.appeals_df.groupby('year').size()

        for year in sorted(self.appeals_df['year'].unique()):
            mf_count = mf_by_year.get(year, 0)
            all_count = all_by_year.get(year, 0)
            pct = (mf_count / all_count * 100) if all_count > 0 else 0
            print(f"  {year}: {mf_count:,} multifamily ({pct:.1f}% of {all_count:,} total)")

        return multifamily

    def generate_summary_report(self):
        """Generate executive summary comparing to original study."""
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY: 2018 STUDY VS. 2026 EXTENSION")
        print("="*80)

        # Original study period (2012-2017)
        original = self.appeals_df[self.appeals_df['period'] == 'Original Study (2012-2017)']
        original_decisions = original[original['decision'].notna()]
        approval_keywords = ['GRANT', 'Complete', 'Approved']
        original_granted = original_decisions[original_decisions['decision'].str.contains('|'.join(approval_keywords), case=False, na=False)]
        original_approval = len(original_granted) / len(original_decisions) * 100 if len(original_decisions) > 0 else 0

        # Extension period (2017-2026)
        extension = self.appeals_df[self.appeals_df['period'] == 'Extension (2017-2026)']
        extension_decisions = extension[extension['decision'].notna()]
        extension_granted = extension_decisions[extension_decisions['decision'].str.contains('|'.join(approval_keywords), case=False, na=False)]
        extension_approval = len(extension_granted) / len(extension_decisions) * 100 if len(extension_decisions) > 0 else 0

        print("\nKEY FINDINGS:")
        print("\n1. ZBA APPROVAL RATE")
        print(f"   2018 Study Finding:       90.0%")
        print(f"   Original Period (2012-17): {original_approval:.1f}%")
        print(f"   Extension Period (2017-26): {extension_approval:.1f}%")

        print("\n2. ANNUAL VARIANCE VOLUME")
        print(f"   2018 Study Finding:       ~1,000 appeals/year")
        print(f"   Original Period (2012-17): {len(original)/6:.0f} appeals/year")
        print(f"   Extension Period (2017-26): {len(extension)/9:.0f} appeals/year")

        print("\n3. MULTIFAMILY HOUSING")
        original_mf = original[original['is_multifamily'] == True]
        extension_mf = extension[extension['is_multifamily'] == True]
        print(f"   Original Period (2012-17): {len(original_mf):,} multifamily appeals ({len(original_mf)/len(original)*100:.1f}%)")
        print(f"   Extension Period (2017-26): {len(extension_mf):,} multifamily appeals ({len(extension_mf)/len(extension)*100:.1f}%)")

        print("\n4. CONCLUSION")
        if abs(original_approval - extension_approval) < 5:
            print("   ➜ Approval rate remains ESSENTIALLY UNCHANGED")
        elif extension_approval > original_approval:
            print(f"   ➜ Approval rate INCREASED by {extension_approval - original_approval:.1f} percentage points")
        else:
            print(f"   ➜ Approval rate DECREASED by {original_approval - extension_approval:.1f} percentage points")

        print("\n" + "="*80)

    def export_data_tables(self, output_dir='analysis_output'):
        """Export analysis results as CSV files."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"\nExporting data tables to {output_dir}/...")

        # Annual summary
        annual_summary = self.appeals_df.groupby('year').agg({
            'appeal_number': 'count',
            'is_multifamily': 'sum'
        }).reset_index()
        annual_summary.columns = ['year', 'total_appeals', 'multifamily_appeals']

        # Add decisions
        approval_keywords = ['GRANT', 'Complete', 'Approved']
        decisions_by_year = self.appeals_df[self.appeals_df['decision'].notna()].groupby('year').apply(
            lambda x: (x['decision'].str.contains('|'.join(approval_keywords), case=False, na=False).sum() / len(x) * 100)
        ).reset_index(name='approval_rate')

        annual_summary = annual_summary.merge(decisions_by_year, on='year', how='left')
        annual_summary.to_csv(f'{output_dir}/annual_summary.csv', index=False)
        print(f"  ✓ annual_summary.csv")

        # Period comparison
        period_summary = self.appeals_df.groupby('period').agg({
            'appeal_number': 'count',
            'is_multifamily': 'sum'
        }).reset_index()
        period_summary.columns = ['period', 'total_appeals', 'multifamily_appeals']
        period_summary.to_csv(f'{output_dir}/period_comparison.csv', index=False)
        print(f"  ✓ period_comparison.csv")

        # Decision breakdown
        decision_breakdown = self.appeals_df[self.appeals_df['decision'].notna()].groupby(
            ['year', 'decision']
        ).size().reset_index(name='count')
        decision_breakdown.to_csv(f'{output_dir}/decisions_by_year.csv', index=False)
        print(f"  ✓ decisions_by_year.csv")

        print(f"\nData exported to {output_dir}/")

    def run_full_analysis(self):
        """Run complete analysis pipeline."""
        print("=" * 80)
        print("PHILADELPHIA ZONING CODE EFFECTIVENESS ANALYSIS")
        print("Recreating & Extending the 2018 Planning Commission 5-Year Review")
        print("=" * 80)
        print(f"\nAnalysis Date: {datetime.now().strftime('%B %d, %Y')}")
        print(f"Data Coverage: 2007-2026 (19 years)")

        # Load data
        self.load_appeals_data()
        self.load_permits_data()

        # Run analyses
        self.calculate_approval_rates()
        self.calculate_variance_volume()
        self.calculate_variance_to_permit_ratio()
        self.analyze_multifamily_trends()

        # Generate summary
        self.generate_summary_report()

        # Export results
        self.export_data_tables()

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("\nNext Steps:")
        print("1. Review exported CSV files in analysis_output/")
        print("2. Create visualizations using the data tables")
        print("3. Draft updated report comparing to 2018 findings")
        print("\n")


def main():
    """Main entry point."""
    analysis = ZoningCodeAnalysis()
    analysis.run_full_analysis()


if __name__ == "__main__":
    main()
