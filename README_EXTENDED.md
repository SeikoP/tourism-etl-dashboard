## 📊 Data Pipeline

### Extraction Process

The TourismFlow pipeline extracts comprehensive tourism data through a sophisticated 3-stage process:

#### Stage 1: Location Discovery
- **Source**: VietnamBooking.com location pages
- **Output**: 59 Vietnamese destinations with metadata
- **Data Points**: City names, URLs, geographical regions

#### Stage 2: Hotel Extraction  
- **Process**: Async concurrent extraction across all locations
- **Output**: 3,540+ hotels with enhanced metadata
- **Coverage**: 69.1% of total available hotels
- **Features**: Name, location, pricing, ratings, amenities

#### Stage 3: Detailed Information
- **Process**: Deep extraction of hotel-specific data
- **Output**: Comprehensive hotel profiles
- **Features**: Descriptions, facilities, policies, images

### Pipeline Architecture

```mermaid
graph TD
    A[Location Extractor] --> B[Hotel Extractor]
    B --> C[Hotel Details Extractor]
    C --> D[Data Merger]
    D --> E[Validation]
    E --> F[Processed Data]
    
    G[Airflow Scheduler] --> A
    G --> B  
    G --> C
    G --> D
    G --> E
```

## 🔧 Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | Apache Airflow 2.7+ | Workflow management & scheduling |
| **Web Framework** | FastAPI 0.104+ | REST API endpoints |
| **Async Processing** | AsyncIO + aiohttp | Concurrent web scraping |
| **Data Storage** | JSON + File System | Raw & processed data storage |
| **Containerization** | Docker + Docker Compose | Service deployment |
| **Language** | Python 3.12+ | Core development language |

## 📈 Performance Metrics

- **Data Volume**: 3,540+ hotels across 59 locations
- **Extraction Speed**: ~500 hotels/minute (with rate limiting)
- **Data Accuracy**: >95% field completion rate
- **Update Frequency**: Daily automated refreshes
- **System Uptime**: 99.5% availability target

## 🛠️ Development

### Local Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

### Running Individual Components

```bash
# Extract locations only
python src/etl/extract/vietnambooking/extract_locations.py

# Extract hotels for specific locations
python src/etl/extract/vietnambooking/enhanced_hotel_extractor.py

# Extract hotel details
python src/etl/extract/vietnambooking/hotel_details_extractor.py

# Check pipeline status
python utils/check_airflow_readiness.py
```

## 📚 API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/hotels` | GET | List all hotels |
| `/hotels/{id}` | GET | Get hotel details |
| `/locations` | GET | List all locations |
| `/stats` | GET | Pipeline statistics |

### Example Usage

```python
import requests

# Get all hotels
response = requests.get("http://localhost:8000/hotels")
hotels = response.json()

# Get specific hotel
hotel_id = "hotel_123"
response = requests.get(f"http://localhost:8000/hotels/{hotel_id}")
hotel_details = response.json()

# Get pipeline statistics
response = requests.get("http://localhost:8000/stats")
stats = response.json()
```

## 🔍 Monitoring & Observability

### Airflow Monitoring

- **DAG Status**: Monitor pipeline execution status
- **Task Logs**: Detailed execution logs for debugging
- **Performance Metrics**: Execution time and success rates
- **Alerting**: Email notifications for failures

### Data Quality Checks

- **Completeness**: Verify all expected fields are present
- **Consistency**: Check data format and value ranges
- **Freshness**: Ensure data is updated within expected timeframes
- **Accuracy**: Validate against known data sources

## 🚀 Production Deployment

### Docker Deployment

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3

# Monitor logs
docker-compose logs -f
```

### Environment Variables

```env
# Core Settings
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow

# Security
AIRFLOW__CORE__FERNET_KEY=your_fernet_key_here
AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key_here

# Performance
AIRFLOW__CORE__PARALLELISM=32
AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=16
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards

- Follow **PEP 8** style guidelines
- Add **type hints** for all functions
- Include **docstrings** for classes and methods
- Write **unit tests** for new features
- Ensure **>90% test coverage**

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(extractor): add hotel amenities extraction`
- `fix(api): resolve timeout issue in hotel details endpoint`
- `docs(readme): update installation instructions`

## 📊 Data Schema

### Hotel Data Structure

```json
{
  "id": "hotel_unique_id",
  "name": "Hotel Name",
  "location": {
    "city": "Ho Chi Minh City",
    "district": "District 1",
    "address": "Full address"
  },
  "pricing": {
    "min_price": 500000,
    "max_price": 2000000,
    "currency": "VND"
  },
  "rating": {
    "score": 8.5,
    "max_score": 10,
    "review_count": 245
  },
  "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
  "images": ["url1", "url2", "url3"],
  "extracted_at": "2025-01-01T00:00:00Z"
}
```

## 🔒 Security & Compliance

- **Rate Limiting**: Respectful crawling with configurable delays
- **User Agent Rotation**: Prevent detection and blocking
- **Data Privacy**: No personal information collection
- **Legal Compliance**: Adherence to robots.txt and ToS

## 📞 Support & Documentation

- **Issues**: [GitHub Issues](https://github.com/SeikoP/tourism-etl-dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SeikoP/tourism-etl-dashboard/discussions)
- **Wiki**: [Project Wiki](https://github.com/SeikoP/tourism-etl-dashboard/wiki)
- **Email**: support@tourismflow.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **VietnamBooking.com** for providing comprehensive hotel data
- **Apache Airflow** community for excellent workflow orchestration
- **FastAPI** team for the high-performance web framework
- **Python AsyncIO** for enabling efficient concurrent processing

## 📈 Roadmap

### Phase 1: Current (Q4 2025)
- ✅ Core data extraction pipeline
- ✅ Airflow orchestration
- ✅ Basic API endpoints
- ✅ Docker containerization

### Phase 2: Enhancement (Q1 2026)
- 🔄 Real-time data streaming
- 🔄 Advanced analytics dashboard
- 🔄 Multi-source data integration
- 🔄 Machine learning price prediction

### Phase 3: Scale (Q2 2026)  
- 🔄 Kubernetes deployment
- 🔄 Multi-region support
- 🔄 Advanced monitoring & alerting
- 🔄 Data lake integration

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by the TourismFlow Team

</div>