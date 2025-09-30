# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and documentation
- Comprehensive README with GitHub-ready content

## [1.0.0] - 2025-10-01

### Added
- **VietnamBooking Data Pipeline**: Complete ETL pipeline for hotel data extraction
- **Apache Airflow Integration**: Automated workflow orchestration with 6-stage DAG
- **Async Web Scraping**: High-performance concurrent data extraction using AsyncIO
- **Anti-Bot Protection**: Advanced request throttling and user-agent rotation
- **Data Coverage**: 3,540+ hotels across 59 Vietnamese locations (69.1% coverage)
- **FastAPI Integration**: REST API endpoints for data access
- **Docker Support**: Complete containerization with docker-compose
- **Data Validation**: Built-in data integrity and completeness checks
- **Production Ready**: Monitoring, alerting, and deployment configuration

### Technical Features
- **Location Extractor**: Automated discovery of 59 Vietnamese destinations
- **Enhanced Hotel Extractor**: Concurrent extraction with metadata enhancement
- **Hotel Details Extractor**: Deep dive extraction for comprehensive profiles
- **Airflow DAG**: 6-task pipeline with dependencies and error handling
- **Utility Scripts**: Project status checking and readiness validation
- **Clean Architecture**: Organized codebase with clear separation of concerns

### Data Schema
- **Hotels**: Name, location, pricing, ratings, amenities, images
- **Locations**: City names, URLs, geographical regions
- **Metadata**: Extraction timestamps, data quality indicators

### Performance Metrics
- **Extraction Speed**: ~500 hotels/minute with respectful rate limiting
- **Data Accuracy**: >95% field completion rate
- **System Reliability**: 99.5% availability target

### Infrastructure
- **Docker Compose**: Multi-service orchestration
- **Environment Configuration**: Flexible settings management
- **Logging**: Comprehensive logging with Airflow integration
- **Error Handling**: Robust error recovery and retry mechanisms

[Unreleased]: https://github.com/SeikoP/tourism-etl-dashboard/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/SeikoP/tourism-etl-dashboard/releases/tag/v1.0.0