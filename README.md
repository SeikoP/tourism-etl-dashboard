# 🏛️ Hệ thống ETL & Trực quan hóa Dữ liệu Du lịch
> **Nền tảng Thu thập, Xử lý và Phân tích Dữ liệu Du lịch & Văn hóa Thông minh**

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.7+-green.svg)](https://airflow.apache.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com)
[![Crawl4AI](https://img.shields.io/badge/Crawl4AI-Latest-purple.svg)](https://crawl4ai.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Đang%20Phát%20triển-yellow.svg)]()
[![GitHub](https://img.shields.io/badge/GitHub-SeikoP-blue.svg)](https://github.com/SeikoP/tourism-etl-dashboard)

## 🎯 Tầm nhìn và Mục tiêu

Xây dựng **hệ thống thu thập – xử lý – trực quan hóa dữ liệu** từ nhiều nguồn mở (API, dữ liệu công khai, file CSV/Excel), nhằm phân tích xu hướng du lịch, điểm đến nổi bật và hành vi của du khách.

### 👥 Đối tượng Thụ hưởng

- **🏢 Doanh nghiệp Du lịch** → Tối ưu hóa chiến dịch marketing và định giá
- **🏛️ Chính quyền Địa phương** → Theo dõi lượng khách và xu hướng phát triển du lịch
- **👥 Du khách** → Tham khảo điểm đến thịnh hành và xu hướng du lịch mới

## 📊 Tình trạng Hiện tại

**Hệ thống ETL Du lịch** hiện đang trong **Giai đoạn 1** phát triển với trọng tâm xây dựng nền tảng ETL pipeline vững chắc. Đã hoàn thành việc thu thập dữ liệu đặt phòng từ VietnamBooking.com với khả năng crawling bất đồng bộ tiên tiến.

### ✅ Các Tính năng Đã hoàn thành (Giai đoạn 1)

- **🔄 Nền tảng ETL Pipeline**: Quy trình ETL được điều phối bởi Apache Airflow
- **🚀 Thu thập Dữ liệu Khách sạn**: Web scraping bất đồng bộ từ VietnamBooking.com
- **📊 Phủ sóng Toàn diện**: 3.540+ khách sạn trên 59 địa điểm Việt Nam
- **🛡️ Bảo vệ Chống Bot**: Điều tiết yêu cầu và xoay vòng user-agent thông minh
- **📈 Kiểm định Chất lượng Dữ liệu**: Kiểm tra tính toàn vẹn và đầy đủ
- **🔧 Sẵn sàng Sản xuất**: Container hóa Docker với monitoring
- **📱 API REST Cơ bản**: Endpoints FastAPI cho truy cập dữ liệu khách sạn
- **🤖 Tích hợp Crawl4AI**: Web scraping nâng cao với hỗ trợ LLM

### 🚧 Lộ trình Phát triển

#### 📊 **Giai đoạn 2: Tích hợp Đa nguồn Dữ liệu**
- **🌐 Tích hợp API**: TripAdvisor, Google Places, OpenWeather
- **📂 Xử lý File**: CSV/Excel từ Tổng cục Du lịch, Tổng cục Thống kê
- **🗄️ Tích hợp Cơ sở dữ liệu**: PostgreSQL/MongoDB cho data lake
- **🔍 Làm giàu Dữ liệu**: Định vị địa lý, phân tích cảm xúc

#### 📈 **Giai đoạn 3: Phân tích & Trực quan hóa**
- **📊 Dashboard Tương tác**: Streamlit/Dash cho trực quan hóa dữ liệu
- **📈 Phân tích Xu hướng**: Phân tích xu hướng du lịch theo mùa và địa điểm
- **🎯 Công cụ Gợi ý**: Gợi ý điểm đến được hỗ trợ bởi AI
- **📱 Giao diện Thân thiện**: Dashboard web responsive

#### 🤖 **Giai đoạn 4: Trí tuệ & Tự động hóa**
- **🧠 Mô hình Học máy**: Dự đoán xu hướng du lịch
- **🔔 Hệ thống Cảnh báo**: Cảnh báo thay đổi thị trường
- **📧 Báo cáo Tự động**: Báo cáo tự động cho các bên liên quan
- **🔌 Thị trường API**: Open API cho các nhà phát triển bên thứ ba

## 🏗️ Kiến trúc Hệ thống

### 🔧 Kiến trúc Hiện tại (Giai đoạn 1)

```
tourism-etl-dashboard/
├── 📁 dags/                    # Apache Airflow DAGs
│   ├── vietnambooking_pipeline.py    # Pipeline chính
│   └── crawl4ai_test_dag.py          # Test tích hợp Crawl4AI
├── 📁 src/                     # Mã nguồn
│   ├── api/                    # FastAPI endpoints (cơ bản)
│   ├── etl/extract/vietnambooking/   # Trích xuất dữ liệu khách sạn
│   │   ├── extract_locations.py
│   │   ├── enhanced_hotel_extractor.py
│   │   └── hotel_details_extractor.py
│   └── services/               # Logic nghiệp vụ
│       ├── collector.py
│       └── crawl4ai_integration.py   # Tích hợp Crawl4AI
├── 📁 data/                    # Lưu trữ dữ liệu
│   ├── raw/vietnambooking/     # Dữ liệu thô khách sạn
│   └── processed/              # Tập dữ liệu đã xử lý
├── 📁 utils/                   # Scripts tiện ích
├── 📁 config/                  # Files cấu hình
├── 📁 docs/                    # Tài liệu
└── 📁 tests/                   # Bộ test
```

### 🎯 Kiến trúc Mục tiêu (Hệ thống Hoàn chỉnh)

```
tourism-etl-dashboard/
├── 📊 dashboards/              # Dashboard trực quan hóa
│   ├── streamlit_app.py        # Dashboard chính
│   ├── components/             # Thành phần dashboard
│   └── assets/                 # Tài nguyên tĩnh
├── 📁 dags/                    # ETL DAGs đa nguồn
│   ├── vietnambooking_pipeline.py
│   ├── tripadvisor_pipeline.py
│   ├── government_data_pipeline.py
│   └── weather_data_pipeline.py
├── 📁 src/
│   ├── api/                    # REST API hoàn chỉnh
│   ├── etl/                    # Trích xuất đa nguồn
│   │   ├── extract/            # Trích xuất dữ liệu
│   │   ├── transform/          # Biến đổi dữ liệu
│   │   └── load/               # Tải dữ liệu
│   ├── ml/                     # Mô hình học máy
│   ├── analytics/              # Công cụ phân tích
│   └── services/               # Dịch vụ nghiệp vụ
├── 📁 data/                    # Data lake
│   ├── raw/                    # Dữ liệu thô từ tất cả nguồn
│   ├── processed/              # Dữ liệu đã biến đổi
│   ├── analytics/              # Kết quả phân tích
│   └── models/                 # Artifacts mô hình ML
└── 📁 infrastructure/          # Infrastructure as code
    ├── docker/                 # Cấu hình Docker
    ├── kubernetes/             # Manifests K8s
    └── terraform/              # Hạ tầng cloud
```

## 🚀 Hướng dẫn Khởi động Nhanh

### Yêu cầu Hệ thống

- Python 3.12+
- Docker & Docker Compose
- 8GB+ RAM (khuyến nghị cho Airflow)
- 10GB+ dung lượng đĩa trống

### 1. Thiết lập Môi trường

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

# Chỉnh sửa cấu hình (tùy chọn)
nano .env
```

### 3. Khởi động Dịch vụ

```bash
# Khởi tạo Airflow và Crawl4AI
docker-compose up airflow-init

# Khởi động tất cả dịch vụ
docker-compose up -d

# Kiểm tra trạng thái dịch vụ
docker-compose ps
```

### 4. Truy cập Ứng dụng

- **🌐 Giao diện Airflow**: http://localhost:8080 (admin/admin)
- **📚 Tài liệu API**: http://localhost:8000/docs
- **💊 Kiểm tra Sức khỏe API**: http://localhost:8000/health
- **🤖 Crawl4AI API**: http://localhost:11235
- **🌺 Flower (Celery monitoring)**: http://localhost:5555

## 📈 Thông số Hiệu suất Hiện tại

### ✅ Giai đoạn 1 - Dữ liệu Đặt phòng Khách sạn (Hoàn thành)

- **📊 Khối lượng Dữ liệu**: 3.540+ khách sạn từ 59 địa điểm Việt Nam
- **⚡ Tốc độ Trích xuất**: ~500 khách sạn/phút (với rate limiting)
- **🎯 Độ chính xác Dữ liệu**: >95% tỷ lệ hoàn thiện trường dữ liệu
- **🔄 Tần suất Cập nhật**: Làm mới tự động hằng ngày
- **📈 Phủ sóng**: 69.1% tổng số khách sạn trên VietnamBooking.com

### 🚧 Chỉ số Kế hoạch (Hệ thống Hoàn chỉnh)

- **🌐 Tích hợp Đa nguồn**: 5+ nguồn dữ liệu (TripAdvisor, Google Places, API Chính phủ)
- **📊 Người dùng Dashboard**: Mục tiêu 1.000+ người dùng hoạt động hàng tháng
- **⚡ Cập nhật Thời gian thực**: Độ trễ dữ liệu <5 phút
- **🎯 Độ chính xác Dự đoán**: >85% cho xu hướng theo mùa
- **📱 Hiệu suất API**: Thời gian phản hồi <200ms

## 🗂️ Nguồn Dữ liệu Kế hoạch

### ✅ Đã Triển khai
- **🏨 VietnamBooking.com**: Dữ liệu đặt phòng, giá cả, đánh giá khách sạn

### 🚧 Đang Phát triển
- **🌟 TripAdvisor API**: Đánh giá, xếp hạng, điểm tham quan du lịch
- **📍 Google Places API**: Dữ liệu POI, thông tin doanh nghiệp, hình ảnh
- **🌤️ OpenWeather API**: Dữ liệu thời tiết cho lập kế hoạch du lịch
- **🏛️ Tổng cục Du lịch Việt Nam**: Thống kê du lịch chính thức
- **📊 Tổng cục Thống kê**: Dân số, chỉ số kinh tế

### 🎯 Kế hoạch Tương lai
- **✈️ APIs Dữ liệu Hàng không**: Giá vé, lịch trình hàng không
- **🚌 APIs Giao thông**: Lịch trình và giá vé xe bus, tàu hỏa
- **🎪 APIs Sự kiện**: Lễ hội, sự kiện văn hóa
- **📱 APIs Mạng xã hội**: Phân tích cảm xúc du lịch
- **💰 APIs Kinh tế**: Tỷ giá hối đoái, dữ liệu lạm phát

## 🔧 Technical Stack

| Thành phần | Công nghệ | Mục đích sử dụng |
|-----------|-----------|------------------|
| **Điều phối** | Apache Airflow 2.7+ | Quản lý workflow & lập lịch |
| **Web Framework** | FastAPI 0.104+ | REST API endpoints |
| **Xử lý Bất đồng bộ** | AsyncIO + aiohttp | Web scraping đồng thời |
| **AI Web Scraping** | Crawl4AI Latest | Trích xuất thông minh với LLM |
| **Lưu trữ Dữ liệu** | JSON + File System | Lưu trữ dữ liệu thô & đã xử lý |
| **Container hóa** | Docker + Docker Compose | Triển khai dịch vụ |
| **Ngôn ngữ** | Python 3.12+ | Ngôn ngữ phát triển chính |

## 🛠️ Phát triển

### 🔧 Trạng thái Phát triển Hiện tại
- **✅ Hoàn thành**: Hotel booking ETL pipeline, Crawl4AI integration
- **🚧 Đang tiến hành**: Mở rộng API, cải thiện chất lượng dữ liệu
- **📋 Tiếp theo**: Tích hợp đa nguồn, phát triển dashboard

### Phát triển Cục bộ

```bash
# Cài đặt development dependencies
pip install -r requirements-dev.txt

# Chạy tests
pytest tests/

# Định dạng code
black src/
isort src/

# Kiểm tra kiểu dữ liệu
mypy src/

### 🧪 Tests Pipeline Crawl4AI + Gemini (Mock)

Để kiểm thử luồng: Crawl trang → Trích lọc khách sạn → Giả lập LLM (Gemini) trả JSON cấu trúc, dùng file `tests/test_crawl4ai_pipeline.py`.

Không cần chạy container `crawl4ai` vì mọi HTTP call đã được mock bằng `monkeypatch`.

Chạy riêng:

```bash
pytest -q tests/test_crawl4ai_pipeline.py
```

Hiển thị log chi tiết:

```bash
pytest -q tests/test_crawl4ai_pipeline.py -o log_cli=true --log-cli-level=INFO
```

Các kiểm thử gồm:
1. `test_extract_hotels_pipeline`: xác nhận crawl danh sách (mock)
2. `test_hotel_detail_extraction_mock`: chi tiết khách sạn (mock)
3. `test_end_to_end_flow`: full flow + mock LLM trả về structured JSON

Có thể mở rộng trong tương lai để:
* Kết nối thật tới container Crawl4AI (integration test)
* Thêm validation schema (pydantic) cho output
* So sánh số lượng hotels với threshold tối thiểu
```

### Chạy các Thành phần Riêng lẻ

```bash
# Chỉ trích xuất địa điểm
python src/etl/extract/vietnambooking/extract_locations.py

# Trích xuất khách sạn cho địa điểm cụ thể
python src/etl/extract/vietnambooking/enhanced_hotel_extractor.py

# Trích xuất chi tiết khách sạn
python src/etl/extract/vietnambooking/hotel_details_extractor.py

# Kiểm tra trạng thái pipeline
python utils/check_airflow_readiness.py

# Test tích hợp Crawl4AI
python src/services/crawl4ai_integration.py
```

### 🤝 Đóng góp Phát triển

Chúng tôi đặc biệt hoan nghênh đóng góp cho các lĩnh vực sau:
- **🌐 Tích hợp Nguồn Dữ liệu**: APIs mới, data connectors
- **📊 Phân tích & Trực quan hóa**: Thành phần dashboard, biểu đồ
- **🤖 Học máy**: Mô hình dự đoán, công cụ gợi ý
- **📱 Phát triển Frontend**: Giao diện người dùng, tối ưu mobile
- **🧪 Testing**: Unit tests, integration tests, kiểm định dữ liệu

## 📚 Tài liệu API

### Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
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

## 📊 Schema Dữ liệu

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

## 📄 Giấy phép

Dự án này được cấp phép theo MIT License - xem file [LICENSE](LICENSE) để biết chi tiết.

## 🏆 Lời cảm ơn

- **🏨 VietnamBooking.com** - Dữ liệu khách sạn toàn diện cho giai đoạn đầu
- **🔄 Apache Airflow Community** - Platform điều phối workflow tuyệt vời
- **⚡ FastAPI Team** - High-performance web framework
- **🐍 Python AsyncIO** - Khả năng xử lý đồng thời
- **🤖 Crawl4AI** - Advanced AI-powered web scraping
- **🎯 Các Đối tác Dữ liệu Tương lai** - TripAdvisor, Google, Tổng cục Du lịch Việt Nam

## 🚀 Đóng góp cho Tầm nhìn

**Hệ thống ETL Du lịch** đang tìm kiếm những đóng góp viên passionate về:
- **📊 Kỹ thuật Dữ liệu**: ETL pipelines, tích hợp dữ liệu
- **🎨 Trực quan hóa Dữ liệu**: Dashboard tương tác, storytelling
- **🤖 Học máy**: Phân tích dự đoán, gợi ý thông minh
- **🌐 Phát triển API**: Tổng hợp dữ liệu đa nguồn
- **📱 Phát triển Frontend**: Trải nghiệm người dùng, thiết kế mobile-first

---

<div align="center">

**⭐ Star repository này để ủng hộ tầm nhìn về Tourism Data Intelligence!**

Made with ❤️ by [SeikoP](https://github.com/SeikoP)

</div>