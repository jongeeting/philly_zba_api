"""
Web scraper for Philadelphia ZBA Appeals Calendar.

Scrapes current appeals from https://li.phila.gov/zba-appeals-calendar
since the API data is outdated (only goes to March 2020).
"""

import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


class ZBACalendarScraper:
    """Scraper for the Philadelphia ZBA Appeals Calendar."""

    BASE_URL = "https://li.phila.gov/zba-appeals-calendar"

    def __init__(self, headless=True):
        """
        Initialize the scraper.

        Args:
            headless: Run browser in headless mode (no GUI)
        """
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        """Set up Selenium WebDriver with Chrome."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)

    def _teardown_driver(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def build_url(self, days_back=90, days_forward=30) -> str:
        """
        Build URL with date range parameters.

        Args:
            days_back: How many days back to search
            days_forward: How many days forward to search

        Returns:
            URL with date parameters
        """
        today = datetime.now()
        from_date = today - timedelta(days=days_back)
        to_date = today + timedelta(days=days_forward)

        from_str = from_date.strftime("%m-%d-%Y")
        to_str = to_date.strftime("%m-%d-%Y")

        return f"{self.BASE_URL}?from={from_str}&to={to_str}&region=all"

    def scrape_calendar(self, days_back=90, days_forward=30) -> List[Dict]:
        """
        Scrape ZBA appeals from the calendar.

        Args:
            days_back: How many days back to search
            days_forward: How many days forward to search

        Returns:
            List of appeal dictionaries
        """
        appeals = []

        try:
            self._setup_driver()

            url = self.build_url(days_back, days_forward)
            print(f"Fetching calendar from: {url}")

            self.driver.get(url)

            # Wait for the Vue app to load and render appeals
            print("Waiting for page to load...")
            time.sleep(5)  # Give Vue.js time to render

            # Try to wait for appeal elements to appear
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "appeal-item"))
                )
            except TimeoutException:
                # Try alternative selectors
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='appeal']"))
                    )
                except TimeoutException:
                    print("Warning: Could not find appeal elements with expected selectors")

            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            # NOTE: The actual selectors will need to be adjusted based on
            # the real structure of the calendar page. This is a template.

            # Look for appeal items (adjust selectors as needed)
            appeal_elements = soup.find_all(class_=re.compile(r'appeal', re.I))

            if not appeal_elements:
                # Try alternative approach: look for any structured data
                appeal_elements = soup.find_all(attrs={'data-appeal-id': True})

            if not appeal_elements:
                print(f"No appeals found. Page might use different structure.")
                print(f"Found {len(soup.find_all())} total elements")
                # Save HTML for debugging
                with open('calendar_page.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print("Saved page HTML to calendar_page.html for inspection")

            for element in appeal_elements:
                try:
                    appeal = self._parse_appeal_element(element)
                    if appeal:
                        appeals.append(appeal)
                except Exception as e:
                    print(f"Error parsing appeal element: {e}")
                    continue

            print(f"Scraped {len(appeals)} appeals")

        except Exception as e:
            print(f"Error scraping calendar: {e}")
            raise

        finally:
            self._teardown_driver()

        return appeals

    def _parse_appeal_element(self, element) -> Optional[Dict]:
        """
        Parse an appeal element from the page.

        NOTE: This is a template. The actual parsing logic will need to be
        adjusted based on the real HTML structure of the calendar page.

        Args:
            element: BeautifulSoup element containing appeal data

        Returns:
            Dictionary with appeal data, or None if parsing fails
        """
        try:
            appeal = {}

            # These selectors are placeholders and will need to be updated
            # based on the actual page structure

            # Try to extract appeal number
            appeal_num = element.find(class_=re.compile(r'appeal.?number', re.I))
            appeal['appeal_number'] = appeal_num.get_text(strip=True) if appeal_num else None

            # Try to extract address
            address = element.find(class_=re.compile(r'address', re.I))
            appeal['address'] = address.get_text(strip=True) if address else None

            # Try to extract description
            desc = element.find(class_=re.compile(r'description|grounds', re.I))
            appeal['appeal_grounds'] = desc.get_text(strip=True) if desc else None

            # Try to extract dates
            date_elem = element.find(class_=re.compile(r'date|scheduled', re.I))
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                appeal['scheduled_date'] = self._parse_date(date_text)

            # Try to extract status
            status = element.find(class_=re.compile(r'status|decision', re.I))
            appeal['appeal_status'] = status.get_text(strip=True) if status else 'PENDING'

            # Mark as scraped data
            appeal['data_source'] = 'scraper'

            # Only return if we have at least an address or appeal number
            if appeal.get('address') or appeal.get('appeal_number'):
                return appeal

            return None

        except Exception as e:
            print(f"Error parsing appeal: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse a date string into datetime object.

        Args:
            date_str: Date string to parse

        Returns:
            datetime object or None
        """
        if not date_str:
            return None

        # Try common date formats
        formats = [
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def get_appeal_detail(self, appeal_id: str) -> Optional[Dict]:
        """
        Scrape details for a specific appeal.

        Args:
            appeal_id: Appeal ID or number

        Returns:
            Dictionary with appeal details
        """
        try:
            self._setup_driver()

            url = f"{self.BASE_URL}/appeal?Id={appeal_id}"
            self.driver.get(url)

            time.sleep(3)  # Wait for page to load

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            # Parse detail page (structure TBD based on actual page)
            appeal = {}
            # Add parsing logic here based on detail page structure

            return appeal

        except Exception as e:
            print(f"Error fetching appeal detail: {e}")
            return None

        finally:
            self._teardown_driver()


def main():
    """Test the scraper."""
    print("Philadelphia ZBA Calendar Scraper")
    print("=" * 60)

    scraper = ZBACalendarScraper(headless=False)  # Show browser for testing

    print("\nScraping last 90 days of appeals...")
    appeals = scraper.scrape_calendar(days_back=90, days_forward=30)

    print(f"\nFound {len(appeals)} appeals")

    if appeals:
        print("\nSample appeals:")
        for i, appeal in enumerate(appeals[:5], 1):
            print(f"\n{i}. Appeal #{appeal.get('appeal_number', 'Unknown')}")
            print(f"   Address: {appeal.get('address', 'N/A')}")
            print(f"   Status: {appeal.get('appeal_status', 'N/A')}")
            if appeal.get('appeal_grounds'):
                desc = appeal['appeal_grounds'][:100]
                print(f"   Description: {desc}...")
    else:
        print("\n⚠️  No appeals found. The page structure may have changed.")
        print("Check calendar_page.html to inspect the actual HTML structure.")


if __name__ == "__main__":
    main()
