"""
Database models for Philadelphia ZBA appeals tracker.
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ZBAAppeal(Base):
    """Model for storing ZBA appeals."""

    __tablename__ = 'zba_appeals'

    # Primary key
    id = Column(Integer, primary_key=True)

    # Unique identifiers from city data
    appeal_number = Column(String(50), unique=True, index=True)
    internal_job_id = Column(Integer, index=True)

    # Address and location
    address = Column(String(255), index=True)
    zip_code = Column(String(10), index=True)
    council_district = Column(String(10), index=True)

    # Appeal details
    appeal_grounds = Column(Text)  # Description of what's being appealed
    application_type = Column(String(50))
    appellant_name = Column(String(255))
    appellant_type = Column(String(100))

    # Dates
    created_date = Column(DateTime, index=True)  # When appeal was filed
    scheduled_date = Column(DateTime)  # When hearing is scheduled
    decision_date = Column(Date)  # When decision was made

    # Status and decision
    appeal_status = Column(String(50))
    decision = Column(String(100))
    meeting_remarks = Column(Text)  # Provisos and conditions

    # Computed fields
    is_multifamily = Column(Boolean, default=False, index=True)
    days_since_filing = Column(Integer)

    # Metadata
    data_source = Column(String(50))  # 'api' or 'scraper'
    last_updated = Column(DateTime, default=datetime.now(timezone.utc))

    # Geographic coordinates (if available)
    geocode_x = Column(String(50))
    geocode_y = Column(String(50))

    def __repr__(self):
        return f"<ZBAAppeal {self.appeal_number}: {self.address}>"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'appeal_number': self.appeal_number,
            'address': self.address,
            'zip_code': self.zip_code,
            'council_district': self.council_district,
            'appeal_grounds': self.appeal_grounds,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
            'appeal_status': self.appeal_status,
            'decision': self.decision,
            'is_multifamily': self.is_multifamily,
            'days_since_filing': self.days_since_filing,
            'data_source': self.data_source,
        }


class ScraperLog(Base):
    """Log of scraper runs for tracking data freshness."""

    __tablename__ = 'scraper_logs'

    id = Column(Integer, primary_key=True)
    run_date = Column(DateTime, default=datetime.now(timezone.utc))
    source = Column(String(50))  # 'api' or 'calendar_scraper'
    records_fetched = Column(Integer)
    records_added = Column(Integer)
    records_updated = Column(Integer)
    status = Column(String(20))  # 'success' or 'error'
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ScraperLog {self.source} at {self.run_date}: {self.status}>"


# Database setup functions

def get_engine(db_path='sqlite:///zba_appeals.db'):
    """Create and return database engine."""
    return create_engine(db_path, echo=False)


def init_db(db_path='sqlite:///zba_appeals.db'):
    """Initialize the database, creating all tables."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    """Get a database session."""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
