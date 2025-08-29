# BioNewsBot API Documentation

## Overview

The BioNewsBot API provides programmatic access to life sciences intelligence data, including company information, news analysis, sentiment tracking, and real-time alerts. This RESTful API uses JSON for data exchange and requires authentication via API keys.

## Base URL

```
https://api.bionewsbot.com/api/v1
```

For local development:
```
http://localhost:8000/api/v1
```

## Authentication

All API requests require authentication using an API key. Include your API key in the request header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Obtaining an API Key

1. Register at https://bionewsbot.com/register
2. Navigate to Settings > API Keys
3. Click "Generate New Key"
4. Store your key securely - it won't be shown again

## Rate Limiting

- **Free tier**: 100 requests per hour
- **Pro tier**: 1,000 requests per hour
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Error Response Format

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The 'company_id' parameter is required",
    "details": {
      "field": "company_id",
      "provided": null
    }
  },
  "request_id": "req_abc123"
}
```

## Endpoints

### Companies

#### List Companies

Get a paginated list of monitored companies.

```http
GET /companies
```

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `limit` (integer, default: 20, max: 100): Items per page
- `search` (string): Search by company name
- `category` (string): Filter by category (biotech, pharma, medtech)
- `market_cap` (string): Filter by market cap (micro, small, mid, large)
- `sort` (string): Sort field (name, market_cap, founded, -name for descending)

**Response:**
```json
{
  "data": [
    {
      "id": "comp_123abc",
      "name": "Moderna Inc",
      "ticker": "MRNA",
      "category": "biotech",
      "market_cap": 45000000000,
      "founded": 2010,
      "headquarters": "Cambridge, MA",
      "description": "Biotechnology company pioneering mRNA therapeutics",
      "website": "https://www.modernatx.com",
      "employee_count": 3900,
      "tags": ["mRNA", "vaccines", "therapeutics"]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### Get Company Details

Retrieve detailed information about a specific company.

```http
GET /companies/{company_id}
```

**Response:**
```json
{
  "id": "comp_123abc",
  "name": "Moderna Inc",
  "ticker": "MRNA",
  "category": "biotech",
  "market_cap": 45000000000,
  "founded": 2010,
  "headquarters": "Cambridge, MA",
  "description": "Biotechnology company pioneering mRNA therapeutics",
  "website": "https://www.modernatx.com",
  "employee_count": 3900,
  "tags": ["mRNA", "vaccines", "therapeutics"],
  "leadership": [
    {
      "name": "Stéphane Bancel",
      "position": "CEO",
      "tenure_start": "2011-01-01"
    }
  ],
  "pipeline": [
    {
      "drug_name": "mRNA-1273",
      "indication": "COVID-19",
      "phase": "Approved",
      "last_update": "2023-12-01"
    }
  ],
  "financials": {
    "revenue_ttm": 6800000000,
    "net_income_ttm": -4700000000,
    "cash_on_hand": 8200000000,
    "last_updated": "2023-12-31"
  }
}
```

#### Get Company Intelligence

Retrieve AI-generated insights and analysis for a company.

```http
GET /companies/{company_id}/intelligence
```

**Query Parameters:**
- `period` (string, default: "7d"): Time period (1d, 7d, 30d, 90d, 1y)
- `include_sentiment` (boolean, default: true): Include sentiment analysis
- `include_trends` (boolean, default: true): Include trend analysis

**Response:**
```json
{
  "company_id": "comp_123abc",
  "period": "7d",
  "generated_at": "2024-01-15T10:30:00Z",
  "insights": {
    "summary": "Moderna shows strong momentum with positive Phase 3 results...",
    "key_developments": [
      {
        "date": "2024-01-14",
        "type": "clinical_trial",
        "title": "Positive Phase 3 Results for mRNA-4157",
        "impact": "high",
        "description": "Moderna announced positive topline results..."
      }
    ],
    "sentiment": {
      "overall": 0.72,
      "trend": "improving",
      "breakdown": {
        "news": 0.68,
        "social": 0.75,
        "analyst": 0.73
      }
    },
    "trends": [
      {
        "topic": "personalized cancer vaccines",
        "relevance": 0.89,
        "momentum": "accelerating"
      }
    ],
    "risks": [
      {
        "type": "competitive",
        "description": "Increased competition in mRNA space",
        "severity": "medium"
      }
    ],
    "opportunities": [
      {
        "type": "market_expansion",
        "description": "Potential for platform expansion into rare diseases",
        "probability": "high"
      }
    ]
  }
}
```

### News & Articles

#### Search News

Search and filter news articles related to life sciences companies.

```http
GET /news
```

**Query Parameters:**
- `q` (string): Search query
- `company_id` (string): Filter by company
- `category` (string): Filter by category (news, publication, clinical_trial, regulatory)
- `date_from` (string): Start date (YYYY-MM-DD)
- `date_to` (string): End date (YYYY-MM-DD)
- `sentiment` (string): Filter by sentiment (positive, neutral, negative)
- `page` (integer): Page number
- `limit` (integer): Items per page

**Response:**
```json
{
  "data": [
    {
      "id": "news_456def",
      "title": "Moderna Announces Positive Phase 3 Results",
      "source": "Reuters",
      "url": "https://reuters.com/...",
      "published_at": "2024-01-14T08:00:00Z",
      "category": "news",
      "companies": [
        {
          "id": "comp_123abc",
          "name": "Moderna Inc",
          "relevance": 0.95
        }
      ],
      "summary": "Moderna announced positive topline results from Phase 3 study...",
      "sentiment": {
        "score": 0.82,
        "label": "positive"
      },
      "entities": [
        {
          "type": "drug",
          "name": "mRNA-4157",
          "context": "melanoma treatment"
        }
      ],
      "tags": ["clinical trials", "oncology", "mRNA"]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 342
  }
}
```

### Alerts & Notifications

#### Create Alert

Create a custom alert for specific events or conditions.

```http
POST /alerts
```

**Request Body:**
```json
{
  "name": "Moderna Clinical Trial Updates",
  "type": "company_event",
  "conditions": {
    "company_ids": ["comp_123abc"],
    "event_types": ["clinical_trial", "regulatory"],
    "sentiment_threshold": 0.7
  },
  "channels": [
    {
      "type": "slack",
      "webhook_url": "https://hooks.slack.com/...",
      "channel": "#biotech-alerts"
    },
    {
      "type": "email",
      "recipients": ["team@company.com"]
    }
  ],
  "frequency": "immediate",
  "active": true
}
```

**Response:**
```json
{
  "id": "alert_789ghi",
  "name": "Moderna Clinical Trial Updates",
  "created_at": "2024-01-15T10:00:00Z",
  "status": "active"
}
```

#### List Alerts

Get all configured alerts for the authenticated user.

```http
GET /alerts
```

#### Get Alert History

Retrieve the trigger history for a specific alert.

```http
GET /alerts/{alert_id}/history
```

### Analytics

#### Market Trends

Get aggregated market trends and insights.

```http
GET /analytics/trends
```

**Query Parameters:**
- `category` (string): Filter by category
- `period` (string): Time period (7d, 30d, 90d)
- `metrics` (array): Specific metrics to include

**Response:**
```json
{
  "period": "30d",
  "generated_at": "2024-01-15T12:00:00Z",
  "trends": [
    {
      "name": "AI Drug Discovery",
      "momentum": 0.85,
      "change": "+23%",
      "top_companies": [
        "Recursion Pharmaceuticals",
        "Atomwise",
        "BenevolentAI"
      ],
      "key_developments": [
        "$200M funding round for Insitro",
        "FDA approval for AI-discovered drug candidate"
      ]
    }
  ],
  "sentiment_overview": {
    "biotech": 0.68,
    "pharma": 0.71,
    "medtech": 0.74
  },
  "funding_metrics": {
    "total_raised": 4500000000,
    "deal_count": 127,
    "average_round": 35400000
  }
}
```

#### Company Comparison

Compare multiple companies across various metrics.

```http
POST /analytics/compare
```

**Request Body:**
```json
{
  "company_ids": ["comp_123abc", "comp_456def", "comp_789ghi"],
  "metrics": [
    "market_cap",
    "pipeline_count",
    "sentiment_score",
    "news_volume",
    "patent_count"
  ],
  "period": "90d"
}
```

### Webhooks

#### Webhook Events

BioNewsBot can send real-time notifications to your endpoints for various events:

- `company.update`: Company information updated
- `news.published`: New article published
- `alert.triggered`: Custom alert triggered
- `sentiment.change`: Significant sentiment change detected
- `trial.update`: Clinical trial status change

#### Webhook Payload

```json
{
  "event": "news.published",
  "timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "article_id": "news_456def",
    "title": "Breaking: FDA Approves Novel Gene Therapy",
    "companies": ["comp_123abc"],
    "impact": "high"
  },
  "signature": "sha256=abcdef123456..."
}

# Search news
news = client.news.search(
    q="gene therapy FDA approval",
    sentiment="positive",
    limit=10
)

# Create alert
alert = client.alerts.create(
    name="Biotech M&A Activity",
    conditions={
        "keywords": ["acquisition", "merger", "buyout"],
        "categories": ["biotech"]
    },
    channels=[{"type": "slack", "webhook_url": "..."}]
)
```

### JavaScript/TypeScript SDK

```typescript
import { BioNewsBot } from '@bionewsbot/sdk';

const client = new BioNewsBot({ apiKey: 'YOUR_API_KEY' });

// Get company details
const company = await client.companies.get('comp_123abc');

// Subscribe to real-time updates
client.subscribe('company.update', (event) => {
  console.log('Company updated:', event.data);
});
```

### cURL Examples

```bash
# Get company intelligence
curl -X GET "https://api.bionewsbot.com/api/v1/companies/comp_123abc/intelligence" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Create alert
curl -X POST "https://api.bionewsbot.com/api/v1/alerts" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FDA Approvals",
    "type": "keyword_match",
    "conditions": {
      "keywords": ["FDA approval", "FDA clearance"]
    }
  }'
```

## Best Practices

### Pagination

Always use pagination for list endpoints to ensure optimal performance:

```python
all_companies = []
page = 1

while True:
    response = client.companies.list(page=page, limit=100)
    all_companies.extend(response['data'])
    
    if page >= response['pagination']['pages']:
        break
    page += 1
```

### Error Handling

Implement proper error handling for all API calls:

```python
try:
    company = client.companies.get(company_id)
except BioNewsBotAPIError as e:
    if e.status_code == 404:
        print(f"Company {company_id} not found")
    elif e.status_code == 429:
        print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
    else:
        print(f"API error: {e.message}")
```

### Caching

Implement caching for frequently accessed data:

```python
import time
from functools import lru_cache

@lru_cache(maxsize=100)
def get_company_cached(company_id):
    return client.companies.get(company_id)

# Cache expires after 1 hour
get_company_cached.cache_clear()
```

### Rate Limit Management

Respect rate limits and implement exponential backoff:

```python
import time
import random

def api_call_with_retry(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

## API Changelog

### Version 1.2.0 (2024-01-15)
- Added company comparison endpoint
- Enhanced sentiment analysis with confidence scores
- New webhook event types for clinical trial updates
- Improved search relevance algorithm

### Version 1.1.0 (2023-12-01)
- Introduced real-time WebSocket support
- Added batch operations for alerts
- New analytics endpoints
- Performance improvements for large datasets

### Version 1.0.0 (2023-10-15)
- Initial public API release
- Core endpoints for companies, news, and alerts
- Basic authentication and rate limiting

## Support

For API support and questions:

- **Documentation**: https://docs.bionewsbot.com
- **API Status**: https://status.bionewsbot.com
- **Support Email**: api-support@bionewsbot.com
- **Developer Forum**: https://forum.bionewsbot.com
- **GitHub Issues**: https://github.com/romwil/bionewsbot/issues

## Terms of Service

By using the BioNewsBot API, you agree to our [Terms of Service](https://bionewsbot.com/terms) and [Privacy Policy](https://bionewsbot.com/privacy).

