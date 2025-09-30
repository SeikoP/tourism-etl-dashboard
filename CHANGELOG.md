# 📋 Nhật ký Thay đổi TourismFlow

Tất cả các thay đổi đáng chú ý cho dự án này sẽ được ghi lại trong file này.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
và dự án này tuân thủ [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Chưa Phát hành]

### Đã Thêm
- Cấu trúc dự án ban đầu và tài liệu
- README toàn diện sẵn sàng cho GitHub
- Việt hóa CONTRIBUTING.md với hướng dẫn chi tiết

## [1.0.0] - 2025-10-01

### Đã Thêm
- **Pipeline Dữ liệu VietnamBooking**: Pipeline ETL hoàn chỉnh cho trích xuất dữ liệu khách sạn
- **Tích hợp Apache Airflow**: Điều phối workflow tự động với 6-stage DAG
- **Web Scraping Bất đồng bộ**: Trích xuất dữ liệu đồng thời hiệu suất cao sử dụng AsyncIO
- **Bảo vệ Chống Bot**: Điều tiết yêu cầu nâng cao và xoay vòng user-agent
- **Phủ sóng Dữ liệu**: 3.540+ khách sạn trên 59 địa điểm Việt Nam (69.1% phủ sóng)
- **Tích hợp FastAPI**: REST API endpoints cho truy cập dữ liệu
- **Hỗ trợ Docker**: Container hóa hoàn chỉnh với docker-compose
- **Xác thực Dữ liệu**: Kiểm tra tính toàn vẹn và đầy đủ của dữ liệu tích hợp sẵn
- **Sẵn sàng Production**: Cấu hình monitoring, alerting và triển khai

### Tính năng Kỹ thuật
- **Location Extractor**: Khám phá tự động 59 điểm đến Việt Nam
- **Enhanced Hotel Extractor**: Trích xuất đồng thời với tăng cường metadata
- **Hotel Details Extractor**: Trích xuất chi tiết sâu cho hồ sơ toàn diện
- **Airflow DAG**: Pipeline 6-task với dependencies và xử lý lỗi
- **Utility Scripts**: Kiểm tra trạng thái dự án và xác thực sẵn sàng
- **Kiến trúc Sạch**: Codebase có tổ chức với tách biệt rõ ràng các concerns

### Schema Dữ liệu
- **Khách sạn**: Tên, vị trí, giá cả, đánh giá, tiện ích, hình ảnh
- **Địa điểm**: Tên thành phố, URLs, vùng địa lý
- **Metadata**: Timestamps trích xuất, chỉ số chất lượng dữ liệu

### Chỉ số Hiệu suất
- **Tốc độ Trích xuất**: ~500 khách sạn/phút với rate limiting tôn trọng
- **Độ chính xác Dữ liệu**: >95% tỷ lệ hoàn thiện trường
- **Độ tin cậy Hệ thống**: Mục tiêu availability 99.5%

### Hạ tầng
- **Docker Compose**: Điều phối đa dịch vụ
- **Cấu hình Environment**: Quản lý settings linh hoạt
- **Logging**: Logging toàn diện với tích hợp Airflow
- **Xử lý Lỗi**: Cơ chế khôi phục lỗi và retry mạnh mẽ

## [1.1.0] - 2025-10-01

### Đã Thêm
- **Tích hợp Crawl4AI**: Web scraping nâng cao với hỗ trợ LLM
- **Việt hóa Documentation**: CONTRIBUTING.md và CHANGELOG.md tiếng Việt
- **Development Tools**: requirements-dev.txt với đầy đủ development dependencies
- **Cải thiện Configuration**: .env.example với production-ready settings

### Cải thiện
- **Code Quality**: Thêm type hints cho Airflow imports
- **Project Cleanup**: Loại bỏ các file README duplicate
- **Performance Tuning**: Tối ưu cấu hình CeleryExecutor + PostgreSQL + Redis

[Unreleased]: https://github.com/SeikoP/tourism-etl-dashboard/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/SeikoP/tourism-etl-dashboard/releases/tag/v1.0.0