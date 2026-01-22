#!/usr/bin/env python3
"""
Improved Impact Categorization

Based on uncategorized appeals analysis, this adds better pattern detection for:
- Signs
- Fences
- Special exceptions
- Single-family household living
- More commercial use types
- Filters out procedural appeals
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class ImprovedCategorizationAnalyzer:
    """Improved categorization with better pattern detection."""

    CARTO_API = "https://phl.carto.com/api/v2/sql"

    def extract_all_issues_improved(self, text):
        """Extract ALL variance issues with improved patterns."""
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

        # SINGLE-FAMILY (NEW - catch single-family conversions)
        if re.search(r'\bSINGLE.?FAMILY', text) and not issues.get('dwelling_units'):
            issues['single_family'] = True

        # PARKING
        if re.search(r'\bPARKING', text):
            issues['parking'] = True

        # SIGNS (NEW)
        if re.search(r'\bSIGN', text):
            issues['signage'] = True

        # FENCES (NEW)
        if re.search(r'\bFENCE', text):
            issues['fence'] = True

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

        # NON-RESIDENTIAL USE (EXPANDED)
        commercial_keywords = [
            'RESTAURANT', 'OFFICE', 'RETAIL', 'COMMERCIAL', 'CAFE', 'BAR',
            'EATING', 'DRINKING', 'VISITOR ACCOMMODATION',
            'DAY CARE', 'DAYCARE', 'PREPARED FOOD',
            'FITNESS CENTER', 'ARTIST STUDIO', 'GROUP HOME', 'GROUP LIVING',
            'SINGLE ROOM RESIDENCE',
            'AUTO REPAIR', 'WAREHOUSE', 'INDUSTRIAL',
            'MEDICAL', 'DENTAL', 'HEALTH PRACTITIONER',
            'RELIGIOUS ASSEMBLY',
        ]
        if any(kw in text for kw in commercial_keywords):
            issues['commercial_use'] = True

        # SPECIAL EXCEPTION (NEW - track separately)
        if re.search(r'\bSPECIAL EXCEPTION\b', text):
            issues['special_exception'] = True

        # FAR / DENSITY
        if re.search(r'\bFLOOR AREA RATIO\b', text) or re.search(r'\bFAR\b', text):
            issues['far'] = True

        return issues

    def is_procedural_appeal(self, text):
        """Check if this is a procedural appeal (not a variance request)."""
        if not text:
            return False

        text_upper = text.upper()

        # Appeals against L&I decisions
        if 'APPEAL AGAINST L&I' in text_upper or 'APPEAL AGAINST L & I' in text_upper:
            return True

        # Remands from court
        if re.search(r'\bREMAND\b', text_upper) and len(text) < 200:
            return True

        # Created in error
        if 'CREATED IN ERROR' in text_upper:
            return True

        return False

    def would_be_allowed_citywide(self, issues):
        """Check if citywide reforms would eliminate this appeal."""
        resolved_issues = []
        remaining_issues = []

        for issue_type, present in issues.items():
            if not present or issue_type.endswith('_value') or issue_type.endswith('_count'):
                continue

            # Skip special_exception flag (it's a process type, not an issue)
            if issue_type == 'special_exception':
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

            elif issue_type == 'single_family':
                # Single-family allowed in all residential zones already
                # But might need variance for other reasons
                resolved_issues.append('single-family')

            elif issue_type == 'parking':
                resolved_issues.append('parking')

            elif issue_type == 'signage':
                # Signs not resolved by our reforms
                remaining_issues.append('signage')

            elif issue_type == 'fence':
                # Fences not resolved by our reforms
                remaining_issues.append('fence')

            elif issue_type == 'commercial_use':
                # Mark as resolved - our Tier 2 commercial/mixed-use reform would help
                # (For now, count as "would be helped" even though it's Tier 2)
                remaining_issues.append('commercial_use')

            else:
                remaining_issues.append(issue_type)

        would_be_allowed = len(remaining_issues) == 0 and len(resolved_issues) > 0
        return would_be_allowed, resolved_issues, remaining_issues

    def analyze_improved(self):
        """Analyze with improved categorization."""
        print("="*80)
        print("IMPROVED CATEGORIZATION ANALYSIS")
        print("="*80)
        print("\nNew patterns added:")
        print("  - Signs (flat wall, projecting, freestanding)")
        print("  - Fences")
        print("  - Single-family household living")
        print("  - Expanded commercial uses (day care, prepared food, etc.)")
        print("  - Special exceptions (tracked separately)")
        print("  - Filter out procedural appeals (Appeal Against L&I, remands)")
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

        # Categorize
        completely_eliminated = []
        procedural_appeals = []
        uncategorized_remaining = []

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']
            appeal_num = row['appealnumber']

            # Filter procedural appeals
            if self.is_procedural_appeal(text):
                procedural_appeals.append((year, appeal_num, text))
                continue

            issues = self.extract_all_issues_improved(text)
            allowed, resolved, remaining = self.would_be_allowed_citywide(issues)

            if allowed:
                completely_eliminated.append((year, appeal_num, text, resolved, issues))

                # Check if still uncategorized
                if len(resolved) == 0:
                    uncategorized_remaining.append((year, appeal_num, text))

        # Print results
        print("="*80)
        print("RESULTS - IMPROVED CATEGORIZATION")
        print("="*80)

        total = len(data['rows'])
        procedural = len(procedural_appeals)
        substantive = total - procedural
        eliminated = len(completely_eliminated)
        uncategorized = len(uncategorized_remaining)

        print(f"\nTotal appeals: {total:,}")
        print(f"  Procedural appeals (filtered out): {procedural:,} ({procedural/total*100:.1f}%)")
        print(f"  Substantive variance appeals: {substantive:,} ({substantive/total*100:.1f}%)")
        print(f"\nOf substantive appeals:")
        print(f"  Would be eliminated: {eliminated:,} ({eliminated/substantive*100:.1f}%)")
        print(f"  Still uncategorized: {uncategorized:,} ({uncategorized/eliminated*100 if eliminated > 0 else 0:.1f}% of eliminated)")

        # Breakdown of what gets eliminated
        print("\n" + "="*80)
        print("WHAT GETS ELIMINATED - IMPROVED BREAKDOWN")
        print("="*80)

        categories = Counter()
        special_exceptions_count = 0

        for year, num, text, resolved, issues in completely_eliminated:
            # Check if special exception
            if issues.get('special_exception'):
                special_exceptions_count += 1

            if len(resolved) > 0:
                category = ', '.join(sorted(resolved))
                categories[category] += 1
            else:
                categories['[uncategorized]'] += 1

        print(f"\n{'Category':<50} {'Count':>10} {'%':>8} {'Per Year':>10}")
        print("-"*80)
        for category, count in categories.most_common(30):
            pct = count / eliminated * 100 if eliminated > 0 else 0
            per_year = count / 11
            print(f"{category:<50} {count:>10,} {pct:>7.1f}% {per_year:>9.0f}")

        # Special exceptions
        print("\n" + "="*80)
        print("SPECIAL EXCEPTIONS")
        print("="*80)
        print(f"\nAppeals marked as 'Special Exception': {special_exceptions_count:,} ({special_exceptions_count/eliminated*100:.1f}% of eliminated)")
        print("\nNote: Special exceptions are a different approval process than variances.")
        print("If the use was allowed by-right, no special exception would be needed.")

        # Sample remaining uncategorized
        if uncategorized_remaining:
            print("\n" + "="*80)
            print("REMAINING UNCATEGORIZED SAMPLES (after improvements)")
            print("="*80)

            print(f"\n{len(uncategorized_remaining):,} appeals still uncategorized")
            print("\nSamples:")
            for i, (year, num, text) in enumerate(uncategorized_remaining[:20]):
                print(f"\n{i+1}. {year} - {num}")
                if text:
                    print(f"   {text[:150]}...")

        # Summary
        print("\n" + "="*80)
        print("COMPARISON: ORIGINAL vs IMPROVED")
        print("="*80)

        print(f"""
ORIGINAL CATEGORIZATION:
  - Uncategorized: 3,070 (48.3% of eliminated appeals)
  - Categories detected: Units, stories, parking, roof decks, etc.

IMPROVED CATEGORIZATION:
  - Procedural appeals filtered: {procedural:,} (not variance requests)
  - Uncategorized: {uncategorized:,} ({uncategorized/eliminated*100 if eliminated > 0 else 0:.1f}% of eliminated)
  - New categories detected: Signs, fences, single-family, special exceptions
  - Improved commercial detection

IMPROVEMENT: Reduced uncategorized by {3070 - uncategorized:,} appeals ({(3070 - uncategorized)/3070*100:.1f}% reduction)

NEXT STEPS:
  - Remaining {uncategorized:,} uncategorized appeals are likely:
    a) Appeals with very short/missing text
    b) Edge cases with unusual variance types
    c) May need additional data fields (not just appealgrounds)
        """)


def main():
    """Main entry point."""
    analyzer = ImprovedCategorizationAnalyzer()
    analyzer.analyze_improved()


if __name__ == "__main__":
    main()
