#!/usr/bin/env python3
"""
Next Tier Reform Analysis

After implementing the three main reforms (4 stories, triplex, citywide parking),
what would help the remaining complex projects?

Analyzes the 7,392 appeals NOT helped by the first three reforms to identify
the next most impactful changes.
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class NextTierAnalyzer:
    """Analyzes remaining appeals to identify next tier of reforms."""

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

    def first_tier_resolves(self, issues):
        """Check if first tier reforms (4 stories, triplex, citywide parking) resolve anything."""
        resolved = []

        if 'height' in issues:
            stories = issues.get('height_value')
            if stories and stories <= 4:
                resolved.append('height')

        if 'dwelling_units' in issues:
            units = issues.get('unit_count')
            if units and units <= 3:
                resolved.append('dwelling_units')

        if 'parking' in issues:
            resolved.append('parking')

        return len(resolved) > 0

    def analyze_next_tier(self):
        """Analyze remaining appeals to find next tier of reforms."""
        print("="*80)
        print("NEXT TIER REFORM ANALYSIS")
        print("="*80)
        print("\nAfter implementing:")
        print("  - 4 stories by-right")
        print("  - Triplex by-right")
        print("  - Citywide parking elimination")
        print("\nWhat would help the remaining complex projects?")
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

        # Find appeals NOT helped by first tier
        remaining_appeals = []

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']
            appeal_num = row['appealnumber']

            issues = self.extract_all_issues(text)

            # Skip if first tier reforms would help
            if not self.first_tier_resolves(issues):
                remaining_appeals.append((year, appeal_num, text, issues))

        print("="*80)
        print("REMAINING APPEALS AFTER FIRST TIER REFORMS")
        print("="*80)

        total = len(data['rows'])
        remaining = len(remaining_appeals)

        print(f"\nTotal appeals: {total:,}")
        print(f"Helped by first tier: {total - remaining:,} ({(total-remaining)/total*100:.1f}%)")
        print(f"Remaining: {remaining:,} ({remaining/total*100:.1f}%)")
        print(f"Annual remaining: ~{remaining/11:.0f} appeals/year")

        # Count issues in remaining appeals
        print("\n" + "="*80)
        print("WHAT ISSUES DO THE REMAINING APPEALS HAVE?")
        print("="*80)

        issue_counts = Counter()
        for year, num, text, issues in remaining_appeals:
            for issue_type, present in issues.items():
                if present and not issue_type.endswith('_value') and not issue_type.endswith('_count'):
                    issue_counts[issue_type] += 1

        print(f"\n{'Issue Type':<25} {'Count':>10} {'% of Remaining':>15} {'Appeals/Year':>15}")
        print("-"*80)
        for issue, count in issue_counts.most_common():
            pct = count / remaining * 100 if remaining > 0 else 0
            per_year = count / 11
            print(f"{issue:<25} {count:>10,} {pct:>14.1f}% {per_year:>14.0f}")

        # Single-issue analysis for remaining appeals
        print("\n" + "="*80)
        print("SINGLE-ISSUE APPEALS IN REMAINING")
        print("(These would be completely eliminated by addressing ONE issue)")
        print("="*80)

        single_issue_appeals = defaultdict(list)

        for year, num, text, issues in remaining_appeals:
            issue_list = [k for k, v in issues.items()
                         if v and not k.endswith('_value') and not k.endswith('_count')]

            if len(issue_list) == 1:
                single_issue_appeals[issue_list[0]].append((year, num, text))

        print(f"\n{'Issue Type':<25} {'Single-Issue Count':>20} {'% of Remaining':>15} {'Appeals/Year':>15}")
        print("-"*80)

        single_issue_counts = {k: len(v) for k, v in single_issue_appeals.items()}
        for issue in sorted(single_issue_counts.keys(), key=lambda x: single_issue_counts[x], reverse=True):
            count = single_issue_counts[issue]
            pct = count / remaining * 100 if remaining > 0 else 0
            per_year = count / 11
            print(f"{issue:<25} {count:>20,} {pct:>14.1f}% {per_year:>14.0f}")

        # Analyze specific issues
        print("\n" + "="*80)
        print("DETAILED ANALYSIS OF TOP ISSUES")
        print("="*80)

        # ROOF DECKS
        print("\n1. ROOF DECKS - Biggest Single Issue")
        print("-" * 40)
        roof_deck_appeals = [a for a in remaining_appeals if a[3].get('roof_deck')]
        roof_deck_single = len(single_issue_appeals.get('roof_deck', []))
        print(f"Total with roof deck: {len(roof_deck_appeals):,} ({len(roof_deck_appeals)/11:.0f}/year)")
        print(f"ONLY roof deck: {roof_deck_single:,} ({roof_deck_single/11:.0f}/year)")
        print(f"Single-issue rate: {roof_deck_single/len(roof_deck_appeals)*100:.1f}%")
        print("\nPotential reform: Allow roof decks by-right (with size/setback limits)")
        print(f"Impact: Would eliminate ~{roof_deck_single/11:.0f} appeals/year completely")
        print(f"       Would help another ~{(len(roof_deck_appeals)-roof_deck_single)/11:.0f} appeals/year partially")

        # COMMERCIAL/MIXED USE
        print("\n2. COMMERCIAL/MIXED-USE - Second Biggest")
        print("-" * 40)
        commercial_appeals = [a for a in remaining_appeals if a[3].get('commercial_use')]
        commercial_single = len(single_issue_appeals.get('commercial_use', []))
        print(f"Total with commercial: {len(commercial_appeals):,} ({len(commercial_appeals)/11:.0f}/year)")
        print(f"ONLY commercial: {commercial_single:,} ({commercial_single/11:.0f}/year)")
        print(f"Single-issue rate: {commercial_single/len(commercial_appeals)*100:.1f}%")
        print("\nPotential reforms:")
        print("  a) Allow ground-floor commercial by-right in more zones")
        print("  b) Allow home-based businesses by-right")
        print("  c) Expand mixed-use zones")
        print(f"Impact: Could eliminate ~{commercial_single/11:.0f}-{len(commercial_appeals)/11*.3:.0f} appeals/year")

        # LARGE MULTIFAMILY (4+ units)
        print("\n3. LARGE MULTIFAMILY (4+ units)")
        print("-" * 40)
        large_mf_appeals = [a for a in remaining_appeals if a[3].get('dwelling_units') and a[3].get('unit_count', 0) > 3]

        # Count by size
        size_distribution = Counter()
        for year, num, text, issues in large_mf_appeals:
            units = issues.get('unit_count', 0)
            if units == 4:
                size_distribution['4 units'] += 1
            elif units == 5:
                size_distribution['5 units'] += 1
            elif units == 6:
                size_distribution['6 units'] += 1
            elif units >= 7 and units <= 12:
                size_distribution['7-12 units'] += 1
            elif units > 12:
                size_distribution['13+ units'] += 1

        print(f"Total 4+ units: {len(large_mf_appeals):,} ({len(large_mf_appeals)/11:.0f}/year)")
        print("\nDistribution:")
        for size, count in size_distribution.most_common():
            print(f"  {size}: {count:,} ({count/11:.0f}/year)")

        print("\nPotential reform: Extend by-right to fourplex or six-plex")
        fourplex = size_distribution.get('4 units', 0)
        sixplex = fourplex + size_distribution.get('5 units', 0) + size_distribution.get('6 units', 0)
        print(f"  Fourplex (4 units) by-right: Would impact ~{fourplex/11:.0f} appeals/year")
        print(f"  Six-plex (6 units) by-right: Would impact ~{sixplex/11:.0f} appeals/year")

        # ADDITIONS
        print("\n4. ADDITIONS/EXPANSIONS")
        print("-" * 40)
        addition_appeals = [a for a in remaining_appeals if a[3].get('addition')]
        addition_single = len(single_issue_appeals.get('addition', []))
        print(f"Total with additions: {len(addition_appeals):,} ({len(addition_appeals)/11:.0f}/year)")
        print(f"ONLY additions: {addition_single:,} ({addition_single/11:.0f}/year)")
        print(f"Single-issue rate: {addition_single/len(addition_appeals)*100:.1f}%")
        print("\nPotential reforms:")
        print("  a) Increase allowable addition size without variance")
        print("  b) Relax setback requirements for additions")
        print(f"Impact: Could eliminate ~{addition_single/11:.0f} appeals/year")

        # SETBACKS
        print("\n5. SETBACKS/YARDS")
        print("-" * 40)
        setback_appeals = [a for a in remaining_appeals if a[3].get('setback')]
        setback_single = len(single_issue_appeals.get('setback', []))
        print(f"Total with setbacks: {len(setback_appeals):,} ({len(setback_appeals)/11:.0f}/year)")
        print(f"ONLY setbacks: {setback_single:,} ({setback_single/11:.0f}/year)")
        print(f"Single-issue rate: {setback_single/len(setback_appeals)*100:.1f}%")
        print("\nPotential reforms:")
        print("  a) Reduce setback requirements (especially side/rear)")
        print("  b) Allow infill buildings to match existing setbacks")
        print(f"Impact: Could eliminate ~{setback_single/11:.0f} appeals/year")

        # LOT DIMENSIONS
        print("\n6. LOT DIMENSIONS (area, width, coverage)")
        print("-" * 40)
        lot_appeals = [a for a in remaining_appeals if a[3].get('lot_dimensions')]
        lot_single = len(single_issue_appeals.get('lot_dimensions', []))
        print(f"Total with lot issues: {len(lot_appeals):,} ({len(lot_appeals)/11:.0f}/year)")
        print(f"ONLY lot issues: {lot_single:,} ({lot_single/11:.0f}/year)")
        print(f"Single-issue rate: {lot_single/len(lot_appeals)*100:.1f}%")
        print("\nPotential reforms:")
        print("  a) Reduce minimum lot area/width requirements")
        print("  b) Increase allowable lot coverage")
        print(f"Impact: Could eliminate ~{lot_single/11:.0f} appeals/year")

        # SUMMARY
        print("\n" + "="*80)
        print("RECOMMENDED NEXT TIER REFORMS (PRIORITY ORDER)")
        print("="*80)

        print("""
TIER 2 REFORMS (after 4 stories + triplex + parking):

🔴 Priority 1: Allow Roof Decks By-Right
   - Impact: ~57 appeals/year eliminated, ~248 appeals/year helped
   - Why: Highest volume issue (3,423 appeals)
   - Only 18.6% single-issue, but affects 305/year total
   - Reform: Allow roof decks by-right with reasonable size/setback limits
   - Low controversy: Aesthetic/privacy issue, not density

🔴 Priority 2: Expand Commercial/Mixed-Use Allowances
   - Impact: ~43 appeals/year eliminated, ~234 appeals/year helped
   - Why: Second highest volume (2,577 appeals)
   - Reforms:
     a) Ground-floor commercial by-right in residential zones
     b) Home-based businesses by-right
     c) Expand mixed-use zoning
   - Economic benefit: Walkable neighborhoods, local businesses

🟡 Priority 3: Extend to Fourplex or Six-Plex
   - Impact: ~46 appeals/year (fourplex) to ~85 appeals/year (six-plex)
   - Why: Natural extension of triplex reform
   - Lower controversy than going straight to large multifamily
   - "Missing middle" housing expansion

🟡 Priority 4: Reduce Setback Requirements
   - Impact: ~21 appeals/year eliminated, ~192 appeals/year helped
   - Why: Common issue with relatively simple fix
   - Reform: Allow infill to match existing setbacks on block
   - Enables better land use on small lots

🟡 Priority 5: Relax Addition/Expansion Limits
   - Impact: ~25 appeals/year eliminated, ~119 appeals/year helped
   - Why: Homeowners expanding existing structures
   - Reform: Increase allowable addition size without variance

COMBINED TIER 2 IMPACT (estimated conservative):
  - Additional ~200-300 appeals/year eliminated
  - Another ~300-400 appeals/year partially helped
  - Total program (Tier 1 + Tier 2): ~500-600 appeals/year eliminated
  - From ~1,300 appeals/year → ~700-800 appeals/year

Note: Some overlap between issues, so combined impact less than sum.
        """)

        # Samples
        print("\n" + "="*80)
        print("SAMPLE REMAINING APPEALS")
        print("="*80)

        print("\nRoof deck only (would be eliminated by roof deck reform):")
        for i, (year, num, text) in enumerate(single_issue_appeals.get('roof_deck', [])[:5]):
            print(f"\n{i+1}. {year} - {num}")
            if text:
                print(f"   {text[:120]}...")

        print("\nCommercial use only (would be eliminated by commercial reforms):")
        for i, (year, num, text) in enumerate(single_issue_appeals.get('commercial_use', [])[:5]):
            print(f"\n{i+1}. {year} - {num}")
            if text:
                print(f"   {text[:120]}...")


def main():
    """Main entry point."""
    analyzer = NextTierAnalyzer()
    analyzer.analyze_next_tier()


if __name__ == "__main__":
    main()
