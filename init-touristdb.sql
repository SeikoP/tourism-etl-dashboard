-- Init script for touristdb
-- This script runs when PostgreSQL container starts

-- Create touristdb database
CREATE DATABASE touristdb;

-- Connect to touristdb and create tables
\c touristdb;

-- Create tourism schema tables
CREATE TABLE IF NOT EXISTS dim_locations (
    id SERIAL PRIMARY KEY,
    location_code VARCHAR(50) UNIQUE NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    hotel_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_hotels (
    id SERIAL PRIMARY KEY,
    hotel_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    location_id INTEGER NOT NULL REFERENCES dim_locations(id),
    star_rating FLOAT,
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    min_price FLOAT,
    max_price FLOAT,
    avg_price FLOAT,
    currency VARCHAR(10) DEFAULT 'VND',
    data_quality_score FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_hotel_details (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES dim_hotels(id),
    extraction_date TIMESTAMP NOT NULL,
    extraction_method VARCHAR(50),
    ai_extraction_success BOOLEAN DEFAULT FALSE,
    basic_extraction_success BOOLEAN DEFAULT FALSE,
    data_quality_score FLOAT DEFAULT 0.0,
    description TEXT,
    room_descriptions JSONB,
    complex_amenities JSONB,
    basic_amenities JSONB,
    policies JSONB,
    nearby_attractions JSONB,
    photos JSONB,
    contact_info JSONB,
    location_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_dim_locations_code ON dim_locations(location_code);
CREATE INDEX IF NOT EXISTS idx_dim_hotels_key ON dim_hotels(hotel_key);
CREATE INDEX IF NOT EXISTS idx_dim_hotels_location ON dim_hotels(location_id);
CREATE INDEX IF NOT EXISTS idx_fact_details_hotel ON fact_hotel_details(hotel_id);
CREATE INDEX IF NOT EXISTS idx_fact_details_extraction ON fact_hotel_details(extraction_date);

-- Grant permissions to airflow user
GRANT ALL PRIVILEGES ON DATABASE touristdb TO airflow;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airflow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airflow;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO airflow;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO airflow;