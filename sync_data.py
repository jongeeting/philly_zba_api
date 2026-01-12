#!/usr/bin/env python3
"""
Sync script to populate database with ZBA appeals from API and scraper.

This script:
1. Fetches historical appeals from the Carto API (2007-2020)
2. Optionally scrapes current appeals from the ZBA calendar (2024-2025)
3. Stores all data in the SQLite database
4. Enriches appeals with multifamily detection and computed fields
"""

import argparse
from datetime import datetime, timezone
from dateutil import parser as date_parser
from sqlalchemy.exc import IntegrityError

from models import init_db, get_session, ZBAAppeal, ScraperLog
from zba_api import ZBAApiClient


def sync_from_api(session, limit=None):
    """
    Fetch appeals from the Carto API and store in database.

    Args:
        session: SQLAlchemy session
        limit: Optional limit on number of records to fetch

    Returns:
        Tuple of (records_fetched, records_added, records_updated)
    """
    print("Syncing data from Carto API...")

    client = ZBAApiClient()

    # Fetch all ZBA appeals (or limited set for testing)
    appeals = client.fetch_appeals(limit=limit)

    records_fetched = len(appeals)
    records_added = 0
    records_updated = 0

    print(f"Fetched {records_fetched} appeals from API")

    for appeal_data in appeals:
        try:
            # Check if appeal already exists
            existing = session.query(ZBAAppeal).filter_by(
                appeal_number=appeal_data.get('appealnumber')
            ).first()

            if existing:
                # Update existing record
                _update_appeal_from_api(existing, appeal_data, client)
                records_updated += 1
            else:
                # Create new record
                new_appeal = _create_appeal_from_api(appeal_data, client)
                session.add(new_appeal)
                records_added += 1

            # Commit in batches
            if (records_added + records_updated) % 100 == 0:
                session.commit()
                print(f"  Processed {records_added + records_updated} records...")

        except IntegrityError as e:
            print(f"  Integrity error for appeal {appeal_data.get('appealnumber')}: {e}")
            session.rollback()
            continue
        except Exception as e:
            print(f"  Error processing appeal {appeal_data.get('appealnumber')}: {e}")
            continue

    # Final commit
    session.commit()

    print(f"✓ Added {records_added} new appeals")
    print(f"✓ Updated {records_updated} existing appeals")

    return records_fetched, records_added, records_updated


def _create_appeal_from_api(data: dict, client: ZBAApiClient) -> ZBAAppeal:
    """Create a ZBAAppeal object from API data."""
    enriched = client.enrich_appeal(data)

    return ZBAAppeal(
        appeal_number=data.get('appealnumber'),
        internal_job_id=data.get('internaljobid'),
        address=data.get('address'),
        zip_code=data.get('zip'),
        council_district=data.get('council_district'),
        appeal_grounds=data.get('appealgrounds'),
        application_type=data.get('applicationtype'),
        appellant_name=data.get('primaryappellant'),
        appellant_type=data.get('appellanttype'),
        created_date=_parse_date(data.get('createddate')),
        scheduled_date=_parse_date(data.get('scheduleddate')),
        decision_date=_parse_date(data.get('decisiondate'), date_only=True),
        appeal_status=data.get('appealstatus'),
        decision=data.get('decision'),
        meeting_remarks=data.get('proviso'),
        is_multifamily=enriched.get('is_multifamily', False),
        days_since_filing=enriched.get('days_since_filing'),
        data_source='api',
        geocode_x=str(data.get('geocode_x')) if data.get('geocode_x') else None,
        geocode_y=str(data.get('geocode_y')) if data.get('geocode_y') else None,
        last_updated=datetime.now(timezone.utc)
    )


def _update_appeal_from_api(appeal: ZBAAppeal, data: dict, client: ZBAApiClient):
    """Update an existing ZBAAppeal with new data from API."""
    enriched = client.enrich_appeal(data)

    # Update fields that may have changed
    appeal.appeal_status = data.get('appealstatus') or appeal.appeal_status
    appeal.decision = data.get('decision') or appeal.decision
    appeal.scheduled_date = _parse_date(data.get('scheduleddate')) or appeal.scheduled_date
    appeal.decision_date = _parse_date(data.get('decisiondate'), date_only=True) or appeal.decision_date
    appeal.meeting_remarks = data.get('proviso') or appeal.meeting_remarks
    appeal.is_multifamily = enriched.get('is_multifamily', appeal.is_multifamily)
    appeal.days_since_filing = enriched.get('days_since_filing')
    appeal.last_updated = datetime.now(timezone.utc)


def sync_from_scraper(session):
    """
    Scrape current appeals from ZBA calendar and store in database.

    Args:
        session: SQLAlchemy session

    Returns:
        Tuple of (records_fetched, records_added, records_updated)
    """
    print("\nSyncing data from ZBA calendar scraper...")

    try:
        from scraper import ZBACalendarScraper
    except ImportError as e:
        print(f"  Error: Could not import scraper: {e}")
        print("  Install Selenium: pip install selenium")
        return 0, 0, 0

    scraper = ZBACalendarScraper(headless=True)

    try:
        # Scrape last 90 days and next 30 days
        appeals = scraper.scrape_calendar(days_back=90, days_forward=30)
    except Exception as e:
        print(f"  Error scraping calendar: {e}")
        return 0, 0, 0

    records_fetched = len(appeals)
    records_added = 0
    records_updated = 0

    print(f"Scraped {records_fetched} appeals from calendar")

    for appeal_data in appeals:
        try:
            # Check if appeal already exists
            appeal_num = appeal_data.get('appeal_number')
            if not appeal_num:
                continue

            existing = session.query(ZBAAppeal).filter_by(
                appeal_number=appeal_num
            ).first()

            if existing:
                # Update existing record with scraped data
                _update_appeal_from_scraper(existing, appeal_data)
                records_updated += 1
            else:
                # Create new record
                new_appeal = _create_appeal_from_scraper(appeal_data)
                session.add(new_appeal)
                records_added += 1

            session.commit()

        except Exception as e:
            print(f"  Error processing scraped appeal: {e}")
            session.rollback()
            continue

    print(f"✓ Added {records_added} new appeals from scraper")
    print(f"✓ Updated {records_updated} existing appeals with scraped data")

    return records_fetched, records_added, records_updated


def _create_appeal_from_scraper(data: dict) -> ZBAAppeal:
    """Create a ZBAAppeal object from scraped data."""
    from zba_api import ZBAApiClient

    client = ZBAApiClient()
    is_multifamily = client.is_multifamily({'appealgrounds': data.get('appeal_grounds', '')})

    return ZBAAppeal(
        appeal_number=data.get('appeal_number'),
        address=data.get('address'),
        appeal_grounds=data.get('appeal_grounds'),
        scheduled_date=data.get('scheduled_date'),
        appeal_status=data.get('appeal_status', 'PENDING'),
        is_multifamily=is_multifamily,
        data_source='scraper',
        last_updated=datetime.now(timezone.utc)
    )


def _update_appeal_from_scraper(appeal: ZBAAppeal, data: dict):
    """Update an existing ZBAAppeal with scraped data."""
    from zba_api import ZBAApiClient

    # Update fields from scraper
    if data.get('appeal_grounds'):
        appeal.appeal_grounds = data['appeal_grounds']

        # Re-check multifamily status with new grounds
        client = ZBAApiClient()
        appeal.is_multifamily = client.is_multifamily({'appealgrounds': data['appeal_grounds']})

    if data.get('scheduled_date'):
        appeal.scheduled_date = data['scheduled_date']

    if data.get('appeal_status'):
        appeal.appeal_status = data['appeal_status']

    appeal.last_updated = datetime.now(timezone.utc)

    # If this was API data, note that we now have scraped data too
    if appeal.data_source == 'api':
        appeal.data_source = 'api+scraper'


def log_sync_run(session, source: str, fetched: int, added: int, updated: int, status: str, error: str = None):
    """Log a sync run to the database."""
    log = ScraperLog(
        source=source,
        records_fetched=fetched,
        records_added=added,
        records_updated=updated,
        status=status,
        error_message=error
    )
    session.add(log)
    session.commit()


def _parse_date(date_str, date_only=False):
    """Parse a date string, returning datetime or date object."""
    if not date_str:
        return None
    try:
        dt = date_parser.parse(date_str)
        return dt.date() if date_only else dt
    except (ValueError, TypeError):
        return None


def main():
    """Main sync script."""
    parser = argparse.ArgumentParser(description='Sync ZBA appeals data to database')
    parser.add_argument('--api-only', action='store_true', help='Only sync from API')
    parser.add_argument('--scraper-only', action='store_true', help='Only sync from scraper')
    parser.add_argument('--limit', type=int, help='Limit number of API records (for testing)')
    parser.add_argument('--db', default='sqlite:///zba_appeals.db', help='Database path')

    args = parser.parse_args()

    print("=" * 70)
    print("Philadelphia ZBA Appeals Data Sync")
    print("=" * 70)

    # Initialize database
    print("\nInitializing database...")
    engine = init_db(args.db)
    session = get_session(engine)

    # Sync from API (historical data)
    if not args.scraper_only:
        try:
            fetched, added, updated = sync_from_api(session, limit=args.limit)
            log_sync_run(session, 'api', fetched, added, updated, 'success')
        except Exception as e:
            print(f"Error syncing from API: {e}")
            log_sync_run(session, 'api', 0, 0, 0, 'error', str(e))

    # Sync from scraper (current data)
    if not args.api_only:
        try:
            fetched, added, updated = sync_from_scraper(session)
            if fetched > 0:
                log_sync_run(session, 'scraper', fetched, added, updated, 'success')
        except Exception as e:
            print(f"Error syncing from scraper: {e}")
            log_sync_run(session, 'scraper', 0, 0, 0, 'error', str(e))

    # Print summary
    print("\n" + "=" * 70)
    print("Sync Summary")
    print("=" * 70)

    total_appeals = session.query(ZBAAppeal).count()
    multifamily_appeals = session.query(ZBAAppeal).filter_by(is_multifamily=True).count()

    print(f"Total appeals in database: {total_appeals}")
    print(f"Multifamily appeals: {multifamily_appeals}")

    print("\nData sources:")
    api_count = session.query(ZBAAppeal).filter(
        ZBAAppeal.data_source.in_(['api', 'api+scraper'])
    ).count()
    scraper_count = session.query(ZBAAppeal).filter(
        ZBAAppeal.data_source.in_(['scraper', 'api+scraper'])
    ).count()

    print(f"  From API: {api_count}")
    print(f"  From scraper: {scraper_count}")

    session.close()

    print("\n✓ Sync complete!")


if __name__ == "__main__":
    main()
