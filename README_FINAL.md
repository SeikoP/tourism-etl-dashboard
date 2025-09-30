# 🏨 Tourism ETL Dashboard
> **Nền tảng Thu thập và Xử lý Dữ liệu Du lịch Thông minh**

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.7+-green.svg)](https://airflow.apache.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Sẵn%20sàng%20Production-brightgreen.svg)]()
[![GitHub](https://img.shields.io/badge/GitHub-SeikoP-blue.svg)](https://github.com/SeikoP/tourism-etl-dashboard)

## 📋 Tổng quan

**Tourism ETL Dashboard** là một nền tảng kỹ thuật dữ liệu toàn diện được thiết kế để thu thập, xử lý và phân tích dữ liệu du lịch tự động. Hệ thống chuyên về việc trích xuất dữ liệu đặt phòng khách sạn từ VietnamBooking.com với khả năng crawling bất đồng bộ tiên tiến, pipeline dữ liệu tự động và kiến trúc sẵn sàng production.

### 🎯 Tính năng chính

- **🔄 Pipeline Dữ liệu Tự động**: Quy trình ETL được điều phối bởi Apache Airflow
- **🚀 Web Scraping Bất đồng bộ**: Trích xuất dữ liệu đồng thời hiệu suất cao  
- **📊 Phủ sóng Toàn diện**: 3,540+ khách sạn trên 59 địa điểm Việt Nam
- **🛡️ Chống Bot Nâng cao**: Điều tiết request và xoay user-agent thông minh
- **📈 Kiểm tra Chất lượng Dữ liệu**: Tích hợp sẵn kiểm tra tính toàn vẹn và đầy đủ
- **🔧 Sẵn sàng Production**: Docker container hóa với monitoring và alerting
- **📱 REST API**: Endpoints được hỗ trợ bởi FastAPI để truy cập dữ liệu

## 🏗️ Kiến trúc

```
tourism-etl-dashboard/
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

### Quy trình Trích xuất

Tourism ETL Dashboard thu thập dữ liệu du lịch toàn diện thông qua quy trình tinh vi 3 giai đoạn:

#### Giai đoạn 1: Khám phá Địa điểm
- **Nguồn**: Trang địa điểm VietnamBooking.com
- **Đầu ra**: 59 điểm đến Việt Nam với metadata
- **Dữ liệu**: Tên thành phố, URLs, khu vực địa lý

#### Giai đoạn 2: Trích xuất Khách sạn  
- **Quy trình**: Trích xuất bất đồng bộ đồng thời trên tất cả địa điểm
- **Đầu ra**: 3,540+ khách sạn với metadata nâng cao
- **Phủ sóng**: 69.1% tổng số khách sạn có sẵn
- **Tính năng**: Tên, vị trí, giá cả, đánh giá, tiện nghi

#### Giai đoạn 3: Thông tin Chi tiết
- **Quy trình**: Trích xuất sâu dữ liệu cụ thể của khách sạn
- **Đầu ra**: Hồ sơ khách sạn toàn diện
- **Tính năng**: Mô tả, cơ sở vật chất, chính sách, hình ảnh

## 🔧 Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | Apache Airflow 2.7+ | Quản lý workflow & lập lịch |
| **Web Framework** | FastAPI 0.104+ | REST API endpoints |
| **Async Processing** | AsyncIO + aiohttp | Web scraping đồng thời |
| **Data Storage** | JSON + File System | Lưu trữ dữ liệu thô & đã xử lý |
| **Containerization** | Docker + Docker Compose | Triển khai dịch vụ |
| **Language** | Python 3.12+ | Ngôn ngữ phát triển chính |

## 📈 Performance Metrics

- **Khối lượng Dữ liệu**: 3,540+ khách sạn trên 59 điểm đến
- **Tốc độ Trích xuất**: ~500 khách sạn/phút (với rate limiting)
- **Độ chính xác Dữ liệu**: >95% tỷ lệ hoàn thiện trường
- **Tần suất Cập nhật**: Làm mới tự động hằng ngày
- **Thời gian Hoạt động**: Mục tiêu 99.5% availability

## 🛠️ Development

### Local Development

```bash
# Cài đặt development dependencies
pip install -r requirements-dev.txt

# Chạy tests
pytest tests/

# Format code
black src/
isort src/

# Type checking
mypy src/
```

### Chạy các Component riêng lẻ

```bash
# Chỉ trích xuất địa điểm
python src/etl/extract/vietnambooking/extract_locations.py

# Trích xuất khách sạn cho địa điểm cụ thể
python src/etl/extract/vietnambooking/enhanced_hotel_extractor.py

# Trích xuất chi tiết khách sạn
python src/etl/extract/vietnambooking/hotel_details_extractor.py

# Kiểm tra trạng thái pipeline
python utils/check_airflow_readiness.py
```

## 📚 API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|  
| `/health` | GET | Kiểm tra sức khỏe hệ thống |
| `/hotels` | GET | Liệt kê tất cả khách sạn |
| `/hotels/{id}` | GET | Lấy thông tin chi tiết khách sạn |
| `/locations` | GET | Liệt kê tất cả địa điểm |
| `/stats` | GET | Thống kê pipeline |

### Ví dụ Sử dụng

```python
import requests

# Lấy tất cả khách sạn
response = requests.get("http://localhost:8000/hotels")
hotels = response.json()

# Lấy khách sạn cụ thể
hotel_id = "hotel_123"
response = requests.get(f"http://localhost:8000/hotels/{hotel_id}")
hotel_details = response.json()

# Lấy thống kê pipeline
response = requests.get("http://localhost:8000/stats")
stats = response.json()
```

## 🤝 Đóng góp

Chúng tôi hoan nghênh sự đóng góp! Vui lòng làm theo các hướng dẫn sau:

### Quy trình Phát triển

1. **Fork** repository
2. **Tạo** feature branch (`git checkout -b feature/tinh-nang-tuyet-voi`)
3. **Commit** thay đổi (`git commit -m 'Thêm tính năng tuyệt vời'`)
4. **Push** lên branch (`git push origin feature/tinh-nang-tuyet-voi`)
5. **Mở** Pull Request

### Tiêu chuẩn Code

- Tuân theo hướng dẫn style **PEP 8**
- Thêm **type hints** cho tất cả functions
- Bao gồm **docstrings** cho classes và methods
- Viết **unit tests** cho tính năng mới
- Đảm bảo **>90% test coverage**

## 📊 Data Schema

### Cấu trúc Dữ liệu Khách sạn

```json
{
  "id": "hotel_unique_id",
  "name": "Tên Khách sạn",
  "location": {
    "city": "Thành phố Hồ Chí Minh",
    "district": "Quận 1",
    "address": "Địa chỉ đầy đủ"
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
  "amenities": ["WiFi", "Hồ bơi", "Phòng gym", "Nhà hàng"],
  "images": ["url1", "url2", "url3"],
  "extracted_at": "2025-01-01T00:00:00Z"
}
```

## 📄 License

Dự án này được cấp phép theo MIT License - xem file [LICENSE](LICENSE) để biết chi tiết.

## 🏆 Acknowledgments

- **VietnamBooking.com** vì cung cấp dữ liệu khách sạn toàn diện
- **Apache Airflow** community vì workflow orchestration xuất sắc
- **FastAPI** team vì web framework hiệu suất cao
- **Python AsyncIO** vì cho phép xử lý đồng thời hiệu quả

---

<div align="center">

**⭐ Star repository này nếu bạn thấy hữu ích!**

Made with ❤️ by SeikoP

</div>