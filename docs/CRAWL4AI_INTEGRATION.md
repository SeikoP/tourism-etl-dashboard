# Crawl4AI Integration Setup

## 🚀 Quick Start

### 1. Start the integrated stack:
```bash
# Start Airflow + Crawl4AI stack
docker-compose up -d

# Check all services
docker-compose ps
```

### 2. Access services:
- **Airflow UI**: http://localhost:8080 (admin/admin)
- **Crawl4AI API**: http://localhost:11235
- **Flower (Celery monitoring)**: http://localhost:5555

### 3. Test Crawl4AI integration:
```bash
# Test Crawl4AI health
curl http://localhost:11235/health

# Run integration test DAG in Airflow UI
# Navigate to: DAGs > crawl4ai_integration_test > Trigger DAG
```

## 🏗️ Architecture

```
Tourism ETL Stack:
├── 🔄 Airflow (9 containers)
│   ├── Scheduler, Workers, API Server
│   ├── Database (PostgreSQL)
│   └── Message Queue (Redis)
└── 🤖 Crawl4AI (1 container)
    ├── Advanced web scraping
    ├── LLM-powered extraction
    └── API server on port 11235
```

## 🔧 Integration Features

### Traditional Scraping vs Crawl4AI

| Feature | Traditional | Crawl4AI |
|---------|-------------|----------|
| **JavaScript Support** | ❌ Limited | ✅ Full support |
| **Anti-bot Bypass** | ⚙️ Manual setup | ✅ Automatic |
| **LLM Extraction** | ❌ None | ✅ GPT-4/Claude support |
| **Parallel Processing** | ✅ AsyncIO | ✅ Built-in |
| **Content Analysis** | ❌ Basic | ✅ Semantic understanding |

### Usage in Airflow DAGs

```python
from services.crawl4ai_integration import VietnamBookingCrawl4AI

def extract_with_crawl4ai():
    crawler = VietnamBookingCrawl4AI()
    hotels = await crawler.extract_hotels_with_crawl4ai(url)
    return hotels
```

## 📊 Performance Comparison

Run the comparison DAG to see:
- Extraction accuracy
- Speed comparison  
- Data quality metrics
- Success rates

## 🛠️ Customization

### Add new extraction strategies:
```python
# CSS-based extraction
result = client.crawl_url(
    url=url,
    extraction_strategy="CSSExtractionStrategy",
    extraction_strategy_args={
        "schema": your_schema
    }
)

# LLM-powered extraction
result = client.extract_with_llm(
    url=url,
    prompt="Extract hotel data as JSON",
    model="gpt-4o-mini"
)
```

### Environment Variables:
```env
# Add to .env file
CRAWL4AI_BASE_DIRECTORY=/app/crawl4ai
CRAWL4AI_LOG_LEVEL=INFO
OPENAI_API_KEY=your_key_here  # For LLM extraction
```

## 🔍 Monitoring

- **Crawl4AI Logs**: `docker-compose logs crawl4ai`
- **Health Check**: Built-in endpoint `/health`
- **Airflow Integration**: Test DAG for validation
- **Performance Metrics**: Available in Airflow task logs

## ⚡ Benefits

1. **🤖 Intelligent Extraction**: LLM-powered data parsing
2. **🛡️ Better Anti-bot**: Advanced detection evasion
3. **📱 JS Support**: Full SPA/dynamic content handling
4. **🔄 Unified Stack**: One docker-compose for everything
5. **📊 A/B Testing**: Compare methods in same pipeline