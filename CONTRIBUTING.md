# 🤝 Hướng dẫn Đóng góp cho TourismFlow

Cảm ơn bạn đã quan tâm đến việc đóng góp cho TourismFlow! Tài liệu này cung cấp hướng dẫn và thông tin dành cho các nhà đóng góp.

## 🤝 Quy tắc Ứng xử

Bằng việc tham gia dự án này, bạn đồng ý tuân thủ Quy tắc Ứng xử của chúng tôi:

- **Tôn trọng**: Đối xử với mọi người bằng sự tôn trọng và tử tế
- **Bao dung**: Chào đón người mới và giúp họ bắt đầu
- **Hợp tác**: Cùng nhau làm việc hướng tới mục tiêu chung
- **Xây dựng**: Đưa ra phản hồi và gợi ý hữu ích

## 🚀 Bắt đầu

### Thiết lập Môi trường Phát triển

1. **Fork và Clone**
   ```bash
   git clone https://github.com/SeikoP/tourism-etl-dashboard.git
   cd tourism-etl-dashboard
   ```

2. **Tạo Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. **Cài đặt Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Thiết lập Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## 📝 Cách Đóng góp

### Báo cáo Vấn đề

Trước khi tạo issue, vui lòng:

1. **Tìm kiếm issue hiện có** để tránh trùng lặp
2. **Sử dụng template issue** được cung cấp
3. **Cung cấp thông tin chi tiết**:
   - Các bước tái hiện lỗi
   - Hành vi mong đợi so với thực tế
   - Chi tiết môi trường
   - Screenshots nếu có

### Đề xuất Tính năng

Đối với yêu cầu tính năng:

1. **Sử dụng template feature request**
2. **Giải thích use case** và lợi ích
3. **Cung cấp ví dụ** về cách hoạt động
4. **Xem xét độ phức tạp triển khai**

### Đóng góp Code

#### Quy ước Đặt tên Branch

- `feature/mo-ta` - Tính năng mới
- `fix/mo-ta` - Sửa lỗi
- `docs/mo-ta` - Cập nhật tài liệu
- `refactor/mo-ta` - Tái cấu trúc code
- `test/mo-ta` - Cải thiện test

#### Định dạng Commit Message

Tuân theo đặc tả [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): mô tả

[nội dung tùy chọn]

[footer tùy chọn]
```

**Các loại:**
- `feat`: Tính năng mới
- `fix`: Sửa lỗi
- `docs`: Thay đổi tài liệu
- `style`: Thay đổi style code (formatting, v.v.)
- `refactor`: Tái cấu trúc code
- `test`: Thêm hoặc cập nhật tests
- `chore`: Các tác vụ bảo trì

**Ví dụ:**
```
feat(extractor): thêm trích xuất tiện ích khách sạn
fix(api): giải quyết vấn đề timeout trong API chi tiết khách sạn
docs(readme): cập nhật hướng dẫn cài đặt
```

#### Quy trình Pull Request

1. **Tạo feature branch** từ `main`
2. **Thực hiện thay đổi** theo tiêu chuẩn coding của chúng tôi
3. **Thêm/cập nhật tests** cho chức năng mới
4. **Cập nhật tài liệu** nếu cần
5. **Chạy test suite** và đảm bảo tất cả tests pass
6. **Submit pull request** với:
   - Tiêu đề và mô tả rõ ràng
   - Tham chiếu tới issues liên quan
   - Screenshots cho thay đổi UI
   - Kết quả test

#### Template Pull Request

```markdown
## Mô tả
Mô tả ngắn gọn về các thay đổi

## Loại Thay đổi
- [ ] Sửa lỗi
- [ ] Tính năng mới
- [ ] Thay đổi breaking
- [ ] Cập nhật tài liệu

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing hoàn thành

## Checklist
- [ ] Code theo đúng style guidelines
- [ ] Self-review hoàn thành
- [ ] Tài liệu đã cập nhật
- [ ] Tests đã thêm/cập nhật
```

## 🧪 Hướng dẫn Testing

### Chạy Tests

```bash
# Chạy tất cả tests
pytest

# Chạy với coverage
pytest --cov=src --cov-report=html

# Chạy test file cụ thể
pytest tests/test_extractor.py

# Chạy tests với marker cụ thể
pytest -m "not slow"
```

### Viết Tests

- **Unit tests**: Test các function/method riêng lẻ
- **Integration tests**: Test tương tác giữa các component
- **End-to-end tests**: Test toàn bộ workflow

Ví dụ cấu trúc test:
```python
def test_hotel_extraction():
    # Arrange
    extractor = HotelExtractor()
    test_data = {...}
    
    # Act
    result = extractor.extract(test_data)
    
    # Assert
    assert result is not None
    assert len(result) > 0
    assert 'name' in result[0]
```

### Test Coverage

- Duy trì **>90% test coverage**
- Tập trung vào **critical paths** và **edge cases**
- Bao gồm tests cho **error handling**

## 📚 Tiêu chuẩn Tài liệu

### Tài liệu Code

- **Docstrings**: Tất cả functions, classes, và modules public
- **Type hints**: Sử dụng cho tất cả tham số và giá trị trả về
- **Inline comments**: Chỉ cho logic phức tạp

Ví dụ:
```python
async def extract_hotels(
    location_url: str, 
    max_pages: int = 10
) -> List[Dict[str, Any]]:
    """Trích xuất dữ liệu khách sạn từ một địa điểm cụ thể.
    
    Args:
        location_url: URL của trang địa điểm
        max_pages: Số trang tối đa để crawl
        
    Returns:
        Danh sách các dictionary khách sạn với dữ liệu đã trích xuất
        
    Raises:
        ExtractionError: Nếu trích xuất thất bại
    """
```

### Cập nhật Tài liệu

- Cập nhật **README.md** cho các thay đổi user-facing
- Cập nhật **API documentation** cho thay đổi endpoint
- Thêm **ví dụ** cho tính năng mới
- Cập nhật **changelog** cho releases

## 🎨 Hướng dẫn Code Style

### Python Style

Chúng tôi tuân theo **PEP 8** với các bổ sung sau:

- **Độ dài dòng**: 88 ký tự (Black default)
- **Sắp xếp import**: Sử dụng `isort`
- **Định dạng code**: Sử dụng `black`
- **Kiểm tra kiểu**: Sử dụng `mypy`

### Pre-commit Hooks

Cấu hình pre-commit của chúng tôi bao gồm:
- `black` - Định dạng code
- `isort` - Sắp xếp import
- `flake8` - Linting
- `mypy` - Kiểm tra kiểu
- `pytest` - Chạy test

### Công cụ Chất lượng Code

```bash
# Định dạng code
black src/

# Sắp xếp imports
isort src/

# Lint code
flake8 src/

# Kiểm tra kiểu
mypy src/

# Kiểm tra bảo mật
bandit -r src/
```

## 🏷️ Versioning và Releases

Chúng tôi sử dụng [Semantic Versioning](https://semver.org/):

- **MAJOR**: Thay đổi breaking
- **MINOR**: Tính năng mới (tương thích ngược)
- **PATCH**: Sửa lỗi (tương thích ngược)

### Quy trình Release

1. **Cập nhật version** trong `pyproject.toml`
2. **Cập nhật CHANGELOG.md**
3. **Tạo release PR**
4. **Tag release** sau khi merge
5. **Publish release** trên GitHub

## 🆘 Nhận Trợ giúp

Nếu bạn cần trợ giúp:

1. **Kiểm tra tài liệu** trước
2. **Tìm kiếm issues và discussions** hiện có
3. **Hỏi trong GitHub Discussions**
4. **Tham gia community** chat
5. **Liên hệ maintainers** trực tiếp

## 🏆 Ghi nhận

Contributors sẽ được ghi nhận:

- **AUTHORS.md**: Danh sách tất cả contributors
- **Release notes**: Ghi công cho những đóng góp quan trọng
- **GitHub contributors**: Ghi nhận tự động
- **Community highlights**: Đặc biệt nổi bật các đóng góp

## 📋 Checklist Phát triển

Trước khi submit một đóng góp:

- [ ] Code tuân theo style guidelines
- [ ] Tests pass locally
- [ ] Tài liệu đã cập nhật
- [ ] Commit messages theo convention
- [ ] PR template đã hoàn thành
- [ ] Không có merge conflicts
- [ ] Thay đổi tương thích ngược

## 🎯 Lĩnh vực Đóng góp Ưu tiên

Chúng tôi đặc biệt hoan nghênh đóng góp trong các lĩnh vực:

### 🌐 **Tích hợp Nguồn Dữ liệu**
- APIs mới (TripAdvisor, Google Places, OpenWeather)
- Data connectors cho các platform du lịch
- Extractors cho dữ liệu chính phủ (CSV, Excel)
- Webhooks và real-time data streams

### 📊 **Phân tích & Trực quan hóa**
- Dashboard components cho Streamlit/Dash
- Biểu đồ và visualizations mới
- Interactive data exploration tools
- Mobile-responsive dashboard components

### 🤖 **Học máy & AI**
- Mô hình dự đoán xu hướng du lịch
- Recommendation engines
- Sentiment analysis cho reviews
- Computer vision cho image processing

### 📱 **Frontend & UX**
- Dashboard UI improvements
- Mobile app development
- Progressive Web App features
- Accessibility enhancements

### 🧪 **Testing & Quality Assurance**
- Unit tests cho các modules mới
- Integration tests cho workflows
- Performance testing và benchmarking
- Security testing và vulnerability assessment

### 📚 **Documentation & Tutorials**
- User guides và tutorials
- API documentation improvements
- Video tutorials và demos
- Multilingual documentation

### 🛠️ **Infrastructure & DevOps**
- CI/CD pipeline improvements
- Docker và Kubernetes configurations
- Monitoring và logging enhancements
- Performance optimization

## 📞 Liên hệ

- **GitHub Issues**: [Tạo issue mới](https://github.com/SeikoP/tourism-etl-dashboard/issues/new)
- **GitHub Discussions**: [Thảo luận](https://github.com/SeikoP/tourism-etl-dashboard/discussions)
- **Email**: Contact maintainers qua GitHub profile

---

Cảm ơn bạn đã đóng góp cho TourismFlow! 🚀

**Cùng nhau xây dựng tương lai của Tourism Data Intelligence!** 🏛️✨