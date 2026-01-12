"""
Philadelphia ZBA Appeals API Client

Fetches and filters appeals from the Philadelphia Zoning Board of Adjustment.
"""

import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dateutil import parser


class ZBAApiClient:
    """Client for fetching ZBA appeals from Philadelphia's Carto API."""

    BASE_URL = "https://phl.carto.com/api/v2/sql"

    # Keywords that suggest multifamily housing projects
    MULTIFAMILY_KEYWORDS = [
        'multifamily',
        'multi-family',
        'apartment',
        'apartments',
        'dwelling units',
        'mixed use',
        'mixed-use',
        'units)',  # Catches patterns like "(28 DWELLING UNITS)"
        'family dwelling',  # Catches "two family dwelling", "three family dwelling", etc.
    ]

    def __init__(self):
        """Initialize the API client."""
        self.session = requests.Session()

    def fetch_appeals(
        self,
        limit: Optional[int] = None,
        days_back: Optional[int] = None,
        order_by: str = "createddate DESC"
    ) -> List[Dict]:
        """
        Fetch ZBA appeals from the API.

        Args:
            limit: Maximum number of appeals to fetch
            days_back: Only fetch appeals from the last N days
            order_by: SQL ORDER BY clause

        Returns:
            List of appeal records as dictionaries
        """
        # Build the SQL query
        query = """
            SELECT
                address,
                createddate,
                appealgrounds,
                zip,
                council_district,
                appealstatus,
                scheduleddate,
                decision,
                decisiondate,
                appealnumber,
                primaryappellant
            FROM appeals
            WHERE applicationtype = 'RB_ZBA'
        """

        if days_back:
            # Note: The dataset only goes to March 2020, so this filter may not be useful
            # for current data, but it's here for when the dataset is updated
            query += f" AND createddate >= NOW() - INTERVAL '{days_back} days'"

        query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        # Make the API request
        params = {"q": query}
        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("rows", [])

    def is_multifamily(self, appeal: Dict) -> bool:
        """
        Check if an appeal is likely related to multifamily housing.

        Args:
            appeal: Appeal record dictionary

        Returns:
            True if the appeal likely involves multifamily housing
        """
        description = appeal.get("appealgrounds", "").lower()

        # Check for any multifamily keywords
        for keyword in self.MULTIFAMILY_KEYWORDS:
            if keyword.lower() in description:
                return True

        return False

    def calculate_days_since_filing(self, appeal: Dict) -> Optional[int]:
        """
        Calculate the number of days since the appeal was filed.

        Args:
            appeal: Appeal record dictionary

        Returns:
            Number of days since filing, or None if date is not available
        """
        created_date_str = appeal.get("createddate")
        if not created_date_str:
            return None

        created_date = parser.parse(created_date_str)
        now = datetime.now(timezone.utc)

        delta = now - created_date
        return delta.days

    def enrich_appeal(self, appeal: Dict) -> Dict:
        """
        Add computed fields to an appeal record.

        Args:
            appeal: Appeal record dictionary

        Returns:
            Enriched appeal dictionary with additional fields
        """
        enriched = appeal.copy()
        enriched["is_multifamily"] = self.is_multifamily(appeal)
        enriched["days_since_filing"] = self.calculate_days_since_filing(appeal)
        return enriched

    def fetch_multifamily_appeals(
        self,
        limit: Optional[int] = None,
        days_back: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch ZBA appeals and filter for multifamily projects.

        Args:
            limit: Maximum number of appeals to fetch (before filtering)
            days_back: Only fetch appeals from the last N days

        Returns:
            List of multifamily appeal records with enriched data
        """
        appeals = self.fetch_appeals(limit=limit, days_back=days_back)

        # Enrich and filter for multifamily
        multifamily_appeals = []
        for appeal in appeals:
            enriched = self.enrich_appeal(appeal)
            if enriched["is_multifamily"]:
                multifamily_appeals.append(enriched)

        return multifamily_appeals
