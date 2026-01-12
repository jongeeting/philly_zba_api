"""
Flask web application for Philadelphia ZBA Multifamily Housing Tracker.
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from models import get_engine, get_session, ZBAAppeal
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database setup
db_path = os.environ.get('DATABASE_URL', 'sqlite:///zba_appeals.db')
engine = get_engine(db_path)


@app.route('/')
def index():
    """Main page showing recent ZBA appeals."""
    return render_template('index.html')


@app.route('/api/appeals')
def get_appeals():
    """
    API endpoint to fetch appeals with filtering.

    Query parameters:
        - multifamily_only: bool - Only show multifamily projects
        - zip_code: str - Filter by ZIP code
        - council_district: str - Filter by council district
        - days_back: int - Only show appeals from last N days (default: 90)
        - status: str - Filter by appeal status
        - limit: int - Max results to return (default: 100)
        - offset: int - Pagination offset (default: 0)
    """
    session = get_session(engine)

    try:
        # Build query
        query = session.query(ZBAAppeal)

        # Filter by multifamily
        if request.args.get('multifamily_only', '').lower() == 'true':
            query = query.filter(ZBAAppeal.is_multifamily == True)

        # Filter by ZIP code
        zip_code = request.args.get('zip_code')
        if zip_code:
            # Support partial ZIP match (e.g., "19104" matches "19104-1234")
            query = query.filter(ZBAAppeal.zip_code.like(f'{zip_code}%'))

        # Filter by council district
        district = request.args.get('council_district')
        if district:
            query = query.filter(ZBAAppeal.council_district == district)

        # Filter by days back
        days_back = int(request.args.get('days_back', 90))
        if days_back > 0:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query = query.filter(ZBAAppeal.created_date >= cutoff_date)

        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(ZBAAppeal.appeal_status == status)

        # Filter by decision
        decision = request.args.get('decision')
        if decision:
            query = query.filter(ZBAAppeal.decision == decision)

        # Search by address or description
        search = request.args.get('search')
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    ZBAAppeal.address.like(search_pattern),
                    ZBAAppeal.appeal_grounds.like(search_pattern)
                )
            )

        # Order by created date (most recent first)
        query = query.order_by(ZBAAppeal.created_date.desc())

        # Get total count before pagination
        total_count = query.count()

        # Pagination
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500
        offset = int(request.args.get('offset', 0))

        appeals = query.limit(limit).offset(offset).all()

        # Convert to dictionaries
        results = [appeal.to_dict() for appeal in appeals]

        return jsonify({
            'appeals': results,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + len(results)) < total_count
        })

    finally:
        session.close()


@app.route('/api/stats')
def get_stats():
    """Get summary statistics about appeals."""
    session = get_session(engine)

    try:
        total_appeals = session.query(ZBAAppeal).count()
        multifamily_count = session.query(ZBAAppeal).filter_by(is_multifamily=True).count()

        # Recent appeals (last 90 days)
        cutoff = datetime.now() - timedelta(days=90)
        recent_count = session.query(ZBAAppeal).filter(
            ZBAAppeal.created_date >= cutoff
        ).count()

        recent_multifamily = session.query(ZBAAppeal).filter(
            and_(
                ZBAAppeal.created_date >= cutoff,
                ZBAAppeal.is_multifamily == True
            )
        ).count()

        # Top ZIP codes for multifamily
        from sqlalchemy import func
        zip_counts = session.query(
            ZBAAppeal.zip_code,
            func.count(ZBAAppeal.id).label('count')
        ).filter(
            ZBAAppeal.is_multifamily == True
        ).group_by(
            ZBAAppeal.zip_code
        ).order_by(
            func.count(ZBAAppeal.id).desc()
        ).limit(10).all()

        # Data freshness
        latest_api = session.query(func.max(ZBAAppeal.created_date)).filter(
            ZBAAppeal.data_source.in_(['api', 'api+scraper'])
        ).scalar()

        latest_scraper = session.query(func.max(ZBAAppeal.created_date)).filter(
            ZBAAppeal.data_source.in_(['scraper', 'api+scraper'])
        ).scalar()

        stats = {
            'total_appeals': total_appeals,
            'multifamily_count': multifamily_count,
            'multifamily_percentage': round(multifamily_count / total_appeals * 100, 1) if total_appeals > 0 else 0,
            'recent_appeals_90d': recent_count,
            'recent_multifamily_90d': recent_multifamily,
            'top_zips': [{'zip': z[0] or 'Unknown', 'count': z[1]} for z in zip_counts],
            'latest_api_date': latest_api.isoformat() if latest_api else None,
            'latest_scraper_date': latest_scraper.isoformat() if latest_scraper else None,
        }

        return jsonify(stats)

    finally:
        session.close()


@app.route('/api/appeal/<appeal_number>')
def get_appeal_detail(appeal_number):
    """Get details for a specific appeal."""
    session = get_session(engine)

    try:
        appeal = session.query(ZBAAppeal).filter_by(appeal_number=appeal_number).first()

        if not appeal:
            return jsonify({'error': 'Appeal not found'}), 404

        return jsonify(appeal.to_dict())

    finally:
        session.close()


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
