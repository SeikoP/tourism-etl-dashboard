# Contributing to TourismFlow

Thank you for your interest in contributing to TourismFlow! This document provides guidelines and information for contributors.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful**: Treat everyone with respect and kindness
- **Be inclusive**: Welcome newcomers and help them get started
- **Be collaborative**: Work together towards common goals
- **Be constructive**: Provide helpful feedback and suggestions

## 🚀 Getting Started

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/SeikoP/tourism-etl-dashboard.git
   cd tourism-etl-dashboard
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set Up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## 📝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue templates** provided
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Screenshots if applicable

### Suggesting Features

For feature requests:

1. **Use the feature request template**
2. **Explain the use case** and benefits
3. **Provide examples** of how it would work
4. **Consider implementation complexity**

### Code Contributions

#### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

#### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(extractor): add hotel amenities extraction
fix(api): resolve timeout issue in hotel details endpoint
docs(readme): update installation instructions
```

#### Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following our coding standards
3. **Add/update tests** for new functionality
4. **Update documentation** if needed
5. **Run the test suite** and ensure all tests pass
6. **Submit a pull request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots for UI changes
   - Test results

#### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_extractor.py

# Run tests with specific marker
pytest -m "not slow"
```

### Writing Tests

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

Example test structure:
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

- Maintain **>90% test coverage**
- Focus on **critical paths** and **edge cases**
- Include **error handling** tests

## 📚 Documentation Standards

### Code Documentation

- **Docstrings**: All public functions, classes, and modules
- **Type hints**: Use for all function parameters and returns
- **Inline comments**: For complex logic only

Example:
```python
async def extract_hotels(
    location_url: str, 
    max_pages: int = 10
) -> List[Dict[str, Any]]:
    """Extract hotel data from a specific location.
    
    Args:
        location_url: URL of the location page
        max_pages: Maximum number of pages to crawl
        
    Returns:
        List of hotel dictionaries with extracted data
        
    Raises:
        ExtractionError: If extraction fails
    """
```

### Documentation Updates

- Update **README.md** for user-facing changes
- Update **API documentation** for endpoint changes
- Add **examples** for new features
- Update **changelog** for releases

## 🎨 Code Style Guidelines

### Python Style

We follow **PEP 8** with these additions:

- **Line length**: 88 characters (Black default)
- **Import sorting**: Use `isort`
- **Code formatting**: Use `black`
- **Type checking**: Use `mypy`

### Pre-commit Hooks

Our pre-commit configuration includes:
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking
- `pytest` - Test running

### Code Quality Tools

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
flake8 src/

# Type check
mypy src/

# Security check
bandit -r src/
```

## 🏷️ Versioning and Releases

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Process

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md**
3. **Create release PR**
4. **Tag release** after merge
5. **Publish release** on GitHub

## 🆘 Getting Help

If you need help:

1. **Check the documentation** first
2. **Search existing issues** and discussions
3. **Ask in GitHub Discussions**
4. **Join our community** chat
5. **Contact maintainers** directly

## 🏆 Recognition

Contributors will be recognized:

- **AUTHORS.md**: List of all contributors
- **Release notes**: Credit for significant contributions
- **GitHub contributors**: Automatic recognition
- **Community highlights**: Featured contributions

## 📋 Development Checklist

Before submitting a contribution:

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] PR template completed
- [ ] No merge conflicts
- [ ] Changes are backwards compatible

Thank you for contributing to TourismFlow! 🚀