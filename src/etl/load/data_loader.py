#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class Location(Base):
    """Location dimension table"""
    __tablename__ = 'dim_locations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_code = Column(String(50), unique=True, nullable=False, index=True)
    location_name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    hotel_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    hotels = relationship("Hotel", back_populates="location")

    def __repr__(self):
        return f"<Location(code='{self.location_code}', name='{self.location_name}')>"

class Hotel(Base):
    """Hotel dimension table"""
    __tablename__ = 'dim_hotels'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hotel_key = Column(String(255), unique=True, nullable=False, index=True)  # url hash
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False, unique=True)

    # Location relationship
    location_id = Column(Integer, ForeignKey('dim_locations.id'), nullable=False, index=True)
    location = relationship("Location", back_populates="hotels")

    # Basic attributes
    star_rating = Column(Float)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))

    # Price information
    min_price = Column(Float)
    max_price = Column(Float)
    avg_price = Column(Float)
    currency = Column(String(10), default='VND')

    # Metadata
    data_quality_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    details = relationship("HotelDetail", back_populates="hotel", uselist=False)

    def __repr__(self):
        return f"<Hotel(name='{self.name}', location='{self.location.location_name if self.location else None}')>"

class HotelDetail(Base):
    """Hotel details fact table"""
    __tablename__ = 'fact_hotel_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey('dim_hotels.id'), nullable=False, index=True)
    hotel = relationship("Hotel", back_populates="details")

    # Extraction metadata
    extraction_date = Column(DateTime, nullable=False)
    extraction_method = Column(String(50))
    ai_extraction_success = Column(Boolean, default=False)
    basic_extraction_success = Column(Boolean, default=False)
    data_quality_score = Column(Float, default=0.0)

    # Detailed information
    description = Column(Text)
    room_descriptions = Column(JSON)  # Array of room descriptions
    complex_amenities = Column(JSON)  # Array of complex amenities
    basic_amenities = Column(JSON)   # Array of basic amenities
    policies = Column(JSON)          # Check-in/out policies, cancellation, etc.
    nearby_attractions = Column(JSON)  # Array of nearby attractions
    photos = Column(JSON)            # Array of photo URLs

    # Additional attributes
    contact_info = Column(JSON)      # Additional contact information
    location_details = Column(JSON)  # Detailed location information

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<HotelDetail(hotel_id={self.hotel_id}, extraction_date={self.extraction_date})>"

class DataLoader:
    """Load transformed data into PostgreSQL database"""

    def __init__(self, connection_string: str = None):
        """Initialize database connection"""

        if not connection_string:
            # Try multiple connection options for different environments
            connection_strings = [
                "postgresql+psycopg2://airflow:airflow@localhost:5433/airflow",  # Local PostgreSQL on port 5433
                "postgresql+psycopg2://airflow:airflow@172.17.190.15:5433/airflow",  # WSL IP (common range)
                "postgresql+psycopg2://airflow:airflow@postgres/airflow",       # Docker container
                "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow", # Fallback to port 5432
            ]

            connection_string = None
            for conn_str in connection_strings:
                try:
                    test_engine = create_engine(conn_str, pool_pre_ping=True)
                    with test_engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                        connection_string = conn_str
                        logger.info(f"Connected to database: {conn_str}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to connect to {conn_str}: {e}")
                    continue

            if not connection_string:
                raise Exception("Could not connect to any PostgreSQL instance")

        # Create engine with connection pooling
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False  # Set to True for debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        logger.info("Database connection initialized")

    def create_tables(self):
        """Create all database tables"""

        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise

    def load_locations(self, locations_file: str) -> Dict[str, Any]:
        """Load locations data into database"""

        logger.info(f"Loading locations from {locations_file}")

        # Load data
        with open(locations_file, 'r', encoding='utf-8') as f:
            locations_data = json.load(f)

        session = self.SessionLocal()
        stats = {
            'total': len(locations_data),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        try:
            for loc_data in locations_data:
                try:
                    # Check if location already exists
                    existing = session.query(Location).filter_by(
                        location_code=loc_data['code']
                    ).first()

                    if existing:
                        # Update existing location
                        existing.location_name = loc_data['location_name']
                        existing.url = loc_data['url']
                        existing.hotel_count = loc_data.get('hotel_count', 0)
                        existing.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        # Create new location
                        location = Location(
                            location_code=loc_data['code'],
                            location_name=loc_data['location_name'],
                            url=loc_data['url'],
                            hotel_count=loc_data.get('hotel_count', 0)
                        )
                        session.add(location)
                        stats['inserted'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Location {loc_data.get('code', 'unknown')}: {str(e)}")
                    continue

            session.commit()
            logger.info(f"✅ Locations loaded: {stats['inserted']} inserted, {stats['updated']} updated, {stats['errors']} errors")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to load locations: {e}")
            stats['error_details'].append(f"Transaction error: {str(e)}")
        finally:
            session.close()

        return stats

    def load_hotels(self, hotels_file: str) -> Dict[str, Any]:
        """Load hotels data into database"""

        logger.info(f"Loading hotels from {hotels_file}")

        # Load data
        with open(hotels_file, 'r', encoding='utf-8') as f:
            hotels_data = json.load(f)

        session = self.SessionLocal()
        stats = {
            'total': len(hotels_data),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        try:
            for hotel_data in hotels_data:
                try:
                    # Get location
                    location = session.query(Location).filter_by(
                        location_code=hotel_data['location_code']
                    ).first()

                    if not location:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Location not found: {hotel_data['location_code']}")
                        continue

                    # Create hotel key from URL
                    hotel_key = str(hash(hotel_data['url']))

                    # Check if hotel already exists
                    existing = session.query(Hotel).filter_by(hotel_key=hotel_key).first()

                    if existing:
                        # Update existing hotel
                        existing.name = hotel_data['name']
                        existing.url = hotel_data['url']
                        existing.location_id = location.id
                        existing.data_quality_score = hotel_data.get('data_quality_score', 0.0)
                        existing.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        # Create new hotel
                        hotel = Hotel(
                            hotel_key=hotel_key,
                            name=hotel_data['name'],
                            url=hotel_data['url'],
                            location_id=location.id,
                            data_quality_score=hotel_data.get('data_quality_score', 0.0)
                        )
                        session.add(hotel)
                        stats['inserted'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Hotel {hotel_data.get('name', 'unknown')}: {str(e)}")
                    continue

            session.commit()
            logger.info(f"✅ Hotels loaded: {stats['inserted']} inserted, {stats['updated']} updated, {stats['errors']} errors")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to load hotels: {e}")
            stats['error_details'].append(f"Transaction error: {str(e)}")
        finally:
            session.close()

        return stats

    def load_hotel_details(self, details_file: str) -> Dict[str, Any]:
        """Load hotel details data into database"""

        logger.info(f"Loading hotel details from {details_file}")

        # Load data
        with open(details_file, 'r', encoding='utf-8') as f:
            details_data = json.load(f)

        session = self.SessionLocal()
        stats = {
            'total': len(details_data),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        try:
            for detail_data in details_data:
                try:
                    # Find hotel by URL
                    hotel_url = detail_data['basic_info']['url']
                    hotel_key = str(hash(hotel_url))

                    hotel = session.query(Hotel).filter_by(hotel_key=hotel_key).first()
                    if not hotel:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Hotel not found for URL: {hotel_url}")
                        continue

                    # Extract data
                    extracted_data = detail_data.get('extracted_data', {})

                    # Prepare detail data
                    detail_record = {
                        'hotel_id': hotel.id,
                        'extraction_date': datetime.fromisoformat(detail_data.get('extraction_date', datetime.utcnow().isoformat())),
                        'extraction_method': detail_data.get('extraction_method', 'unknown'),
                        'ai_extraction_success': detail_data.get('ai_extraction_success', False),
                        'basic_extraction_success': detail_data.get('basic_extraction_success', False),
                        'data_quality_score': detail_data.get('data_quality_score', 0.0),
                        'description': extracted_data.get('description'),
                        'room_descriptions': extracted_data.get('room_descriptions', []),
                        'complex_amenities': extracted_data.get('complex_amenities', []),
                        'basic_amenities': extracted_data.get('basic_amenities', []),
                        'policies': extracted_data.get('policies', {}),
                        'nearby_attractions': extracted_data.get('nearby_attractions', []),
                        'photos': extracted_data.get('photos', [])
                    }

                    # Update hotel with additional attributes
                    if extracted_data.get('address'):
                        hotel.address = extracted_data['address']
                    if extracted_data.get('phone'):
                        hotel.phone = extracted_data['phone']
                    if extracted_data.get('star_rating'):
                        hotel.star_rating = extracted_data['star_rating']

                    # Update price information
                    price_analysis = extracted_data.get('price_analysis')
                    if price_analysis:
                        hotel.min_price = price_analysis.get('min_price')
                        hotel.max_price = price_analysis.get('max_price')
                        hotel.avg_price = price_analysis.get('avg_price')
                        hotel.currency = price_analysis.get('currency', 'VND')

                    # Check if detail already exists
                    existing_detail = session.query(HotelDetail).filter_by(hotel_id=hotel.id).first()

                    if existing_detail:
                        # Update existing detail
                        for key, value in detail_record.items():
                            setattr(existing_detail, key, value)
                        existing_detail.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        # Create new detail
                        detail = HotelDetail(**detail_record)
                        session.add(detail)
                        stats['inserted'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Detail for hotel {detail_data.get('basic_info', {}).get('name', 'unknown')}: {str(e)}")
                    continue

            session.commit()
            logger.info(f"✅ Hotel details loaded: {stats['inserted']} inserted, {stats['updated']} updated, {stats['errors']} errors")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to load hotel details: {e}")
            stats['error_details'].append(f"Transaction error: {str(e)}")
        finally:
            session.close()

        return stats

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""

        session = self.SessionLocal()

        try:
            stats = {
                'locations_count': session.query(Location).count(),
                'hotels_count': session.query(Hotel).count(),
                'details_count': session.query(HotelDetail).count(),
                'last_updated': datetime.utcnow().isoformat()
            }

            # Get quality metrics
            quality_stats = session.query(
                Hotel.data_quality_score,
                HotelDetail.data_quality_score
            ).join(HotelDetail, isouter=True).all()

            if quality_stats:
                hotel_scores = [q[0] for q in quality_stats if q[0] is not None]
                detail_scores = [q[1] for q in quality_stats if q[1] is not None]

                stats['avg_hotel_quality'] = sum(hotel_scores) / len(hotel_scores) if hotel_scores else 0
                stats['avg_detail_quality'] = sum(detail_scores) / len(detail_scores) if detail_scores else 0

            return stats

        finally:
            session.close()

    def close(self):
        """Close database connections"""
        self.engine.dispose()
        logger.info("Database connections closed")