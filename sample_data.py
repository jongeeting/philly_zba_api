#!/usr/bin/env python3
"""
Sample script to demonstrate the ZBA API client.

This script fetches recent ZBA appeals and shows:
- All recent appeals
- Filtered multifamily projects
- Days since filing
- Summary statistics
"""

from zba_api import ZBAApiClient
from datetime import datetime
from dateutil import parser


def format_date(date_str):
    """Format a date string for display."""
    if not date_str:
        return "N/A"
    date = parser.parse(date_str)
    return date.strftime("%Y-%m-%d")


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def main():
    print("Philadelphia ZBA Multifamily Housing Tracker")
    print_separator()

    # Initialize the API client
    client = ZBAApiClient()

    # Fetch recent appeals
    print("Fetching recent ZBA appeals from the API...")
    recent_appeals = client.fetch_appeals(limit=50)

    print(f"✓ Fetched {len(recent_appeals)} recent appeals")

    # Find multifamily projects
    print("\nAnalyzing appeals for multifamily housing projects...")
    multifamily = [client.enrich_appeal(a) for a in recent_appeals if client.is_multifamily(a)]

    print(f"✓ Found {len(multifamily)} potential multifamily projects")

    print_separator()

    # Show summary statistics
    print("SUMMARY STATISTICS")
    print("-" * 80)
    print(f"Total appeals analyzed: {len(recent_appeals)}")
    print(f"Multifamily projects found: {len(multifamily)}")
    print(f"Percentage: {len(multifamily) / len(recent_appeals) * 100:.1f}%")

    # Status breakdown for multifamily
    if multifamily:
        statuses = {}
        for appeal in multifamily:
            status = appeal.get("decision") or appeal.get("appealstatus", "PENDING")
            statuses[status] = statuses.get(status, 0) + 1

        print("\nMultifamily Appeals by Status:")
        for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")

    print_separator()

    # Show detailed multifamily projects
    print("MULTIFAMILY HOUSING PROJECTS (Top 10)")
    print("-" * 80)

    for i, appeal in enumerate(multifamily[:10], 1):
        print(f"\n{i}. {appeal['address']}")
        print(f"   ZIP: {appeal['zip']}")
        print(f"   Filed: {format_date(appeal['createddate'])} ({appeal['days_since_filing']} days ago)")
        print(f"   Status: {appeal.get('decision') or appeal.get('appealstatus', 'PENDING')}")

        # Show description (truncated)
        description = appeal.get("appealgrounds", "")
        if len(description) > 200:
            description = description[:200] + "..."
        print(f"   Description: {description}")

        # Highlight if within 45-day window
        if appeal["days_since_filing"] and appeal["days_since_filing"] <= 45:
            print(f"   ⚠️  WITHIN 45-DAY NEIGHBORHOOD MEETING WINDOW!")

    print_separator()

    # Show appeals by neighborhood (using ZIP as proxy)
    print("MULTIFAMILY PROJECTS BY ZIP CODE")
    print("-" * 80)

    zip_counts = {}
    for appeal in multifamily:
        zip_code = appeal.get("zip", "Unknown")
        # Clean up ZIP (take first 5 digits)
        if zip_code and "-" in zip_code:
            zip_code = zip_code.split("-")[0]
        zip_counts[zip_code] = zip_counts.get(zip_code, 0) + 1

    for zip_code, count in sorted(zip_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {zip_code}: {count} projects")

    print_separator()

    # Show a few examples of keywords detected
    print("SAMPLE MULTIFAMILY DESCRIPTIONS")
    print("-" * 80)

    for i, appeal in enumerate(multifamily[:3], 1):
        print(f"\n{i}. {appeal['address']}")
        print(f"   {appeal.get('appealgrounds', 'N/A')[:300]}...")

    print_separator()

    print("""
NEXT STEPS:

1. ✓ API is working and returning data
2. ✓ Multifamily keyword detection is working

Next up:
- Set up a database to store appeals
- Create a daily fetch script
- Build a web interface to browse and filter projects

Note: The API dataset appears to only have data through March 2020.
You may want to check with the City of Philadelphia for more recent data sources.
""")


if __name__ == "__main__":
    main()
