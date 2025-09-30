# �️ Tourism ETL & Visualization Dashboard
> **Hệ thố## 🏗️ Kiến trúc Hệ thống

### 🔧 Kiến trúc Hiện tại (Giai đoạn 1)
```
tourism-etl-dashboard/
├── 📁 dags/                    # Apache Airflow DAGs
│   └── vietnambooking_pipeline.py
├── 📁 src/                     # Mã nguồn
│   ├── api/                    # FastAPI endpoints (basic)
│   ├── etl/extract/vietnambooking/  # Hotel booking extractors
│   │   ├── extract_locations.py
│   │   ├── enhanced_hotel_extractor.py
│   │   └── hotel_details_extractor.py
│   └── services/               # Business logic
├── 📁 data/                    # Data storage
│   ├── raw/vietnambooking/     # Raw hotel data
│   └── processed/              # Processed datasets
├── 📁 utils/                   # Utility scripts
├── 📁 config/                  # Configuration files
└── 📁 tests/                   # Test suites
```

### 🎯 Kiến trúc Mục tiêu (Full System)
```
tourism-etl-dashboard/
├── 📊 dashboards/              # Visualization dashboards
│   ├── streamlit_app.py        # Main dashboard
│   ├── components/             # Dashboard components
│   └── assets/                 # Static assets
├── 📁 dags/                    # Multi-source ETL DAGs
│   ├── vietnambooking_pipeline.py
│   ├── tripadvisor_pipeline.py
│   ├── government_data_pipeline.py
│   └── weather_data_pipeline.py
├── 📁 src/
│   ├── api/                    # Full REST API
│   ├── etl/                    # Multi-source extractors
│   │   ├── extract/            # Data extractors
│   │   ├── transform/          # Data transformers
│   │   └── load/               # Data loaders
│   ├── ml/                     # Machine learning models
│   ├── analytics/              # Analytics engines
│   └── services/               # Business services
├── 📁 data/                    # Data lake
│   ├── raw/                    # Raw data from all sources
│   ├── processed/              # Transformed data
│   ├── analytics/              # Analytics results
│   └── models/                 # ML model artifacts
└── 📁 infrastructure/          # Infrastructure as code
    ├── docker/                 # Docker configurations
    ├── kubernetes/             # K8s manifests
    └── terraform/              # Cloud infrastructure
```ữ liệu Du lịch & Văn hóa**

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.7+-green.svg)](https://airflow.apache.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-In%20Development-yellow.svg)]()
[![GitHub](https://img.shields.io/badge/GitHub-SeikoP-blue.svg)](https://github.com/SeikoP/tourism-etl-dashboard)

## 🎯 Mục tiêu Dự án

Xây dựng **hệ thống thu thập – xử lý – trực quan dữ liệu** từ nhiều nguồn mở (API, dữ liệu công khai, file CSV/Excel), nhằm phân tích xu hướng du lịch, điểm đến nổi bật, và hành vi của du khách.

### 👥 Đối tượng Hưởng lợi

- **🏢 Doanh nghiệp du lịch** → Tối ưu chiến dịch marketing
- **🏛️ Chính quyền địa phương** → Theo dõi lượng khách và xu hướng
- **👥 Người dùng** → Tham khảo điểm đến hot và xu hướng du lịch

## 📋 Tổng quan Hiện tại

**Tourism ETL Dashboard** hiện đang trong giai đoạn phát triển với focus vào việc xây dựng foundation ETL pipeline mạnh mẽ. **Giai đoạn 1** đã hoàn thành việc thu thập dữ liệu booking từ VietnamBooking.com với khả năng crawling bất đồng bộ tiên tiến và pipeline dữ liệu tự động.

### ✅ Tính năng Đã hoàn thành (Giai đoạn 1)

- **🔄 ETL Pipeline Foundation**: Quy trình ETL được điều phối bởi Apache Airflow
- **🚀 Hotel Booking Data Crawler**: Web scraping bất đồng bộ từ VietnamBooking.com
- **📊 Comprehensive Hotel Coverage**: 3,540+ khách sạn trên 59 địa điểm Việt Nam
- **🛡️ Anti-Bot Protection**: Điều tiết request và xoay user-agent thông minh
- **📈 Data Quality Validation**: Kiểm tra tính toàn vẹn và đầy đủ dữ liệu
- **🔧 Production-Ready Infrastructure**: Docker containerization
- **📱 Basic REST API**: FastAPI endpoints cho hotel booking data

### 🚧 Roadmap Phát triển

#### 📊 **Giai đoạn 2: Multi-Source Data Integration** 
- **🌐 API Integration**: TripAdvisor, Google Places, OpenWeather
- **� File Processing**: CSV/Excel từ Tổng cục Du lịch, GSO
- **🗄️ Database Integration**: PostgreSQL/MongoDB cho data lake
- **🔍 Data Enrichment**: Geolocalization, sentiment analysis

#### 📈 **Giai đoạn 3: Analytics & Visualization**
- **📊 Interactive Dashboard**: Streamlit/Dash cho data visualization  
- **📈 Trend Analysis**: Phân tích xu hướng du lịch theo mùa, địa điểm
- **🎯 Recommendation Engine**: AI-powered destination recommendations
- **📱 Mobile-Friendly Interface**: Responsive web dashboard

#### 🤖 **Giai đoạn 4: Intelligence & Automation**
- **🧠 Machine Learning Models**: Dự đoán xu hướng du lịch
- **🔔 Alert System**: Cảnh báo thay đổi thị trường
- **📧 Automated Reports**: Báo cáo tự động cho stakeholders
- **🔌 API Marketplace**: Open API cho third-party developers

## 🏗️ Kiến trúc

```
TourismFlow/
├── 📁 dags/                    # Apache Airflow DAGs
│   └── vietnambooking_pipeline.py
├── 📁 src/                     # Mã nguồn
│   ├── api/                    # FastAPI endpoints  
│   ├── etl/extract/vietnambooking/  # Bộ trích xuất dữ liệu
│   │   ├── extract_locations.py
│   │   ├── enhanced_hotel_extractor.py
│   │   └── hotel_details_extractor.py
│   └── services/               # Logic nghiệp vụ
├── 📁 data/                    # Lưu trữ dữ liệu
│   ├── raw/vietnambooking/     # Dữ liệu thô
│   └── processed/              # Dữ liệu đã xử lý
├── 📁 utils/                   # Scripts tiện ích
├── 📁 config/                  # Files cấu hình
└── 📁 tests/                   # Bộ test
```

## 🚀 Hướng dẫn nhanh

### Yêu cầu hệ thống

- Python 3.12+
- Docker & Docker Compose
- 8GB+ RAM (khuyến nghị cho Airflow)

### 1. Thiết lập môi trường

```bash
# Clone repository
git clone https://github.com/SeikoP/tourism-etl-dashboard.git
cd tourism-etl-dashboard

# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Windows CMD:
.venv\Scripts\activate.bat

# Linux/macOS:
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình

```bash
# Tạo file environment
cp .env.example .env

# Chỉnh sửa cấu hình
nano .env
```

### 3. Khởi động dịch vụ

```bash
# Khởi tạo Airflow
docker-compose up airflow-init

# Khởi động tất cả dịch vụ
docker-compose up -d

# Kiểm tra trạng thái dịch vụ
docker-compose ps
```

### 4. Truy cập ứng dụng

- **Giao diện Airflow**: http://localhost:8080 (admin/admin)  
- **Tài liệu API**: http://localhost:8000/docs
- **Kiểm tra sức khỏe API**: http://localhost:8000/health

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

## 🔧 Technical Stack

| Component | Technology | Purpose |
|-----------|------------|----------|
| **Orchestration** | Apache Airflow 2.7+ | Workflow management & scheduling |
| **Web Framework** | FastAPI 0.104+ | REST API endpoints |
| **Async Processing** | AsyncIO + aiohttp | Concurrent web scraping |
| **Data Storage** | JSON + File System | Raw & processed data storage |
| **Containerization** | Docker + Docker Compose | Service deployment |
| **Language** | Python 3.12+ | Core development language |

## 📈 Current Status & Metrics

### ✅ Giai đoạn 1 - Hotel Booking Data (Completed)
- **📊 Data Volume**: 3,540+ khách sạn từ 59 địa điểm Việt Nam
- **⚡ Extraction Speed**: ~500 hotels/minute (với rate limiting)  
- **🎯 Data Accuracy**: >95% field completion rate
- **🔄 Update Frequency**: Daily automated refresh
- **📈 Coverage**: 69.1% của tổng số hotels trên VietnamBooking.com

### 🚧 Planned Metrics (Full System)
- **🌐 Multi-Source Integration**: 5+ data sources (TripAdvisor, Google Places, Government APIs)
- **📊 Dashboard Users**: Target 1000+ monthly active users
- **⚡ Real-time Updates**: <5 minute data latency
- **🎯 Prediction Accuracy**: >85% cho seasonal trends
- **📱 API Performance**: <200ms response time

## �️ Nguồn Dữ liệu Kế hoạch

### ✅ Đã triển khai
- **🏨 VietnamBooking.com**: Hotel booking data, pricing, ratings

### 🚧 Đang phát triển
- **🌟 TripAdvisor API**: Reviews, ratings, tourist attractions
- **📍 Google Places API**: POI data, business info, photos
- **🌤️ OpenWeather API**: Weather data cho travel planning
- **🏛️ Vietnam Tourism Authority**: Official tourism statistics
- **📊 General Statistics Office**: Population, economic indicators

### 🎯 Kế hoạch tương lai
- **✈️ Flight Data APIs**: Airline pricing, schedules
- **🚌 Transportation APIs**: Bus, train schedules and pricing
- **🎪 Event APIs**: Festivals, cultural events
- **📱 Social Media APIs**: Travel sentiment analysis
- **💰 Economic APIs**: Exchange rates, inflation data

## �🛠️ Development

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **🏨 VietnamBooking.com** - Dữ liệu khách sạn toàn diện cho giai đoạn đầu
- **🔄 Apache Airflow Community** - Workflow orchestration platform tuyệt vời
- **⚡ FastAPI Team** - High-performance web framework
- **🐍 Python AsyncIO** - Concurrent processing capabilities
- **🎯 Future Data Partners** - TripAdvisor, Google, Vietnam Tourism Authority

## 🚀 Contributing to the Vision

**Tourism ETL Dashboard** đang tìm kiếm những đóng góp viên passionate về:
- **📊 Data Engineering**: ETL pipelines, data integration
- **🎨 Data Visualization**: Interactive dashboards, storytelling
- **🤖 Machine Learning**: Predictive analytics, recommendations  
- **🌐 API Development**: Multi-source data aggregation
- **📱 Frontend Development**: User experience, mobile-first design

---

<div align="center">

**⭐ Star repository này để support vision về Tourism Data Intelligence!**

Made with ❤️ by SeikoP

</div>

