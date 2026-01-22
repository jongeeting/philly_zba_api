#!/usr/bin/env python3
"""
Uncategorized Appeals Analysis

Looks at the appeals that would be eliminated by reforms but don't have
clear detected issues. Helps identify missing keywords and patterns.
"""

import requests
import pandas as pd
import re
from collections import Counter, defaultdict


class UncategorizedAnalyzer:
    """Analyzes uncategorized appeals to find missing patterns."""

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

    def would_be_allowed_citywide(self, issues):
        """Check if citywide reforms would eliminate this appeal."""
        resolved_issues = []
        remaining_issues = []

        for issue_type, present in issues.items():
            if not present or issue_type.endswith('_value') or issue_type.endswith('_count'):
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

            elif issue_type == 'parking':
                resolved_issues.append('parking')

            else:
                remaining_issues.append(issue_type)

        would_be_allowed = len(remaining_issues) == 0
        return would_be_allowed, resolved_issues, remaining_issues

    def analyze_uncategorized(self):
        """Analyze uncategorized appeals to find missing patterns."""
        print("="*80)
        print("UNCATEGORIZED APPEALS ANALYSIS")
        print("="*80)
        print("\nFinding appeals eliminated by reforms but with no detected issues")
        print("This helps identify missing keywords and patterns")
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

        # Find uncategorized appeals
        uncategorized = []

        for row in data['rows']:
            year = int(row['year'])
            text = row['appealgrounds']
            appeal_num = row['appealnumber']

            issues = self.extract_all_issues(text)
            allowed, resolved, remaining = self.would_be_allowed_citywide(issues)

            # Only look at appeals that WOULD be eliminated but have NO detected resolved issues
            if allowed and len(resolved) == 0:
                uncategorized.append((year, appeal_num, text, issues))

        print("="*80)
        print("RESULTS")
        print("="*80)

        total_eliminated = len([r for r in data['rows']
                               if self.would_be_allowed_citywide(self.extract_all_issues(r['appealgrounds']))[0]])

        print(f"\nTotal appeals eliminated by reforms: {total_eliminated:,}")
        print(f"Uncategorized (no detected issues): {len(uncategorized):,} ({len(uncategorized)/total_eliminated*100:.1f}%)")

        # Sample the text
        print("\n" + "="*80)
        print("SAMPLE UNCATEGORIZED APPEALS")
        print("="*80)

        print("\nLet's look at 50 random samples to identify patterns:")

        import random
        samples = random.sample(uncategorized, min(50, len(uncategorized)))

        for i, (year, num, text, issues) in enumerate(samples):
            print(f"\n{i+1}. {year} - {num}")
            if text:
                print(f"   {text[:200]}")
            else:
                print("   [No text]")

        # Look for common words/phrases
        print("\n" + "="*80)
        print("KEYWORD FREQUENCY ANALYSIS")
        print("="*80)

        print("\nMost common words in uncategorized appeals:")

        all_text = ' '.join([text.upper() if text else '' for year, num, text, issues in uncategorized])

        # Common zoning keywords to look for
        keywords = [
            'SPECIAL EXCEPTION',
            'APPEAL AGAINST',
            'REMAND',
            'HOUSEHOLD LIVING',
            'SINGLE-FAMILY',
            'MULTI-FAMILY',
            'DWELLING',
            'ERECTION',
            'PERMIT',
            'USE',
            'VARIANCE',
            'ZONING',
            'L&I',
            'ISSUANCE',
            'DEMOLITION',
            'ALTERATION',
            'EXISTING',
            'STRUCTURE',
            'LOT',
            'FENCE',
            'SIGN',
            'ACCESSORY',
            'NON-ACCESSORY',
        ]

        keyword_counts = {}
        for keyword in keywords:
            count = all_text.count(keyword)
            if count > 0:
                keyword_counts[keyword] = count

        print(f"\n{'Keyword':<25} {'Count':>10} {'% of Uncategorized':>20}")
        print("-"*80)
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(uncategorized) * 100
            print(f"{keyword:<25} {count:>10,} {pct:>19.1f}%")

        # Check appeal types
        print("\n" + "="*80)
        print("APPEAL TYPE ANALYSIS")
        print("="*80)

        appeal_types = Counter()
        for year, num, text, issues in uncategorized:
            if not text:
                appeal_types['[No text]'] += 1
            elif 'APPEAL AGAINST L&I' in text.upper():
                appeal_types['Appeal Against L&I'] += 1
            elif 'SPECIAL EXCEPTION' in text.upper():
                appeal_types['Special Exception'] += 1
            elif 'REMAND' in text.upper():
                appeal_types['Remand'] += 1
            elif len(text) < 50:
                appeal_types['Very short text'] += 1
            else:
                appeal_types['Other'] += 1

        print(f"\n{'Type':<30} {'Count':>10} {'%':>8}")
        print("-"*80)
        for appeal_type, count in appeal_types.most_common():
            pct = count / len(uncategorized) * 100
            print(f"{appeal_type:<30} {count:>10,} {pct:>7.1f}%")

        # Look for specific patterns we might be missing
        print("\n" + "="*80)
        print("POTENTIAL MISSING PATTERNS")
        print("="*80)

        # Check for appeals without specific variance keywords
        no_variance_text = []
        for year, num, text, issues in uncategorized:
            if text:
                text_upper = text.upper()
                has_variance_keywords = any(kw in text_upper for kw in
                    ['VARIANCE', 'REFUSAL', 'PERMIT', 'ERECTION', 'USE', 'DWELLING'])
                if not has_variance_keywords:
                    no_variance_text.append((year, num, text))

        print(f"\nAppeals without typical variance keywords: {len(no_variance_text):,}")
        if no_variance_text:
            print("\nSamples:")
            for i, (year, num, text) in enumerate(no_variance_text[:10]):
                print(f"\n{i+1}. {year} - {num}")
                print(f"   {text[:150]}")

        # Recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS FOR IMPROVED CATEGORIZATION")
        print("="*80)

        print("""
Based on the analysis above, here are potential improvements:

1. SPECIAL EXCEPTIONS vs VARIANCES:
   - Many "uncategorized" may be special exceptions (different process)
   - Consider separating these from variance appeals
   - They may be eliminated by reforms but aren't traditional variances

2. APPEALS AGAINST L&I:
   - These are procedural appeals, not variance requests
   - Should potentially be excluded from the analysis
   - Or categorized separately

3. REMANDS:
   - Cases being sent back from court
   - May not represent new variance requests
   - Consider filtering out

4. MISSING PATTERNS TO ADD:
   - Look for "HOUSEHOLD LIVING" without unit counts (single-family)
   - "DEMOLITION" might indicate variance for replacement structure
   - "FENCE" or "SIGN" might be dimensional variances
   - "ALTERATION" might indicate expansion/modification

5. TEXT QUALITY:
   - Some appeals have very short or missing text
   - May need to pull from other fields (decision, refusal reasons, etc.)

Next steps:
- Review samples above to identify specific patterns
- Add new regex patterns for common uncategorized types
- Consider filtering special exceptions/appeals/remands separately
- Potentially pull additional data fields for better categorization
        """)


def main():
    """Main entry point."""
    analyzer = UncategorizedAnalyzer()
    analyzer.analyze_uncategorized()


if __name__ == "__main__":
    main()
