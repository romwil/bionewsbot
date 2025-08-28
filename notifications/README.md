# BioNewsBot Notification Service

Real-time Slack notifications for life sciences intelligence with rich formatting, interactive features, and comprehensive monitoring.

## Features

- **Real-time Slack Integration**: WebSocket connection for instant notifications
- **Rich Message Formatting**: Beautiful Slack blocks with company info, metrics, and actions
- **Priority-based Routing**: High-priority alerts to #alerts, normal updates to #updates
- **Interactive Actions**: Mark as reviewed, view details, access source links
- **Rate Limiting**: Intelligent rate limiting per channel to prevent spam
- **Comprehensive Monitoring**: Prometheus metrics for delivery tracking and performance
- **Webhook Support**: Receive insights from backend via secure webhooks
- **OAuth Flow**: Easy workspace installation with pre-configured permissions

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Redis server
- PostgreSQL database
- Slack workspace with admin access

### 2. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From an app manifest"
3. Select your workspace
4. Copy the contents of `slack_app_manifest.yaml`
5. Review and create the app
6. Install the app to your workspace

### 3. Configure Tokens

After creating the app, get these tokens from the Slack app settings:

- **Bot User OAuth Token**: Found in OAuth & Permissions (starts with `xoxb-`)
- **App-Level Token**: Create in Basic Information → App-Level Tokens (starts with `xapp-`)
- **Signing Secret**: Found in Basic Information

### 4. Environment Setup

```bash
# Clone the repository
cd /root/bionewsbot/notifications

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### 5. Configure Environment

Edit `.env` with your credentials:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# Optional: OAuth for distribution
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret

# Channel Configuration
SLACK_HIGH_PRIORITY_CHANNEL=#alerts
SLACK_NORMAL_PRIORITY_CHANNEL=#updates

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bionewsbot
DB_USER=postgres
DB_PASSWORD=your-db-password

# API Configuration
API_BASE_URL=http://localhost:8000
API_KEY=your-api-key
WEBHOOK_SECRET=your-webhook-secret
```

### 6. Database Setup

```sql
-- Create notification_history table
CREATE TABLE notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id UUID NOT NULL,
    channel VARCHAR(255) NOT NULL,
    message_ts VARCHAR(255),
    thread_ts VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    read_by TEXT[],
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    INDEX idx_insight_id (insight_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### 7. Start the Service

```bash
# Development mode
python -m uvicorn main:app --reload --port 8001

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

## Architecture

### Components

1. **Slack Service** (`services/slack_service.py`)
   - Manages Slack Bolt app and WebSocket connection
   - Handles message sending and interactive components
   - Implements retry logic and error handling

2. **Notification Manager** (`services/notification_manager.py`)
   - Orchestrates the notification lifecycle
   - Manages priority queues (high/normal)
   - Polls backend API for new insights
   - Tracks notification history

3. **Message Templates** (`templates/slack_messages.py`)
   - Generates rich Slack blocks for each insight type
   - Formats regulatory approvals, clinical trials, M&A, funding, partnerships
   - Adds interactive buttons and metadata

4. **Rate Limiter** (`utils/rate_limiter.py`)
   - Token bucket algorithm with Redis backend
   - Different limits for high-priority vs normal channels
   - Prevents API rate limit errors

5. **Metrics Collector** (`utils/metrics.py`)
   - Prometheus metrics for monitoring
   - Tracks delivery success, response times, user interactions
   - Exposes /metrics endpoint

### Message Flow

1. Backend generates insight → Sends webhook to notification service
2. Notification manager validates and queues the notification
3. Priority-based processing (high priority first)
4. Rate limiter checks if sending is allowed
5. Slack service formats and sends the message
6. User interactions tracked and processed
7. Metrics updated throughout the flow

## API Endpoints

### Webhooks

- `POST /webhooks/insights` - Receive new insight notifications
- `POST /webhooks/slack/interactions` - Handle Slack interactions

### Health & Monitoring

- `GET /` - Service info
- `GET /status` - Detailed service status
- `GET /webhooks/health` - Health check
- `GET /webhooks/metrics` - Prometheus metrics

## Message Types

### Regulatory Approval
```
🟠 FDA Approves Keytruda for Advanced Melanoma
Merck (MRK) • Pharmaceuticals

The FDA has granted accelerated approval for Keytruda (pembrolizumab) 
for the treatment of advanced melanoma patients.

Regulatory Body: FDA
Drug: Keytruda (pembrolizumab)
Indication: Advanced Melanoma
Approval Type: Accelerated Approval

[✅ Mark as Reviewed] [📊 View Details] [🔗 Source]
```

### Clinical Trial Update
```
🔵 Phase 3 Trial Shows Positive Results
BioNTech (BNTX) • Biotechnology

Phase 3 trial of BNT162b2 meets primary efficacy endpoint with 95% efficacy.

Phase: Phase 3
Status: Completed
Patients: 43,548
Primary Endpoint: Prevention of COVID-19

[✅ Mark as Reviewed] [📊 View Details] [🔗 Source]
```

## Monitoring

### Key Metrics

- `bionewsbot_notifications_sent_total` - Total notifications sent
- `bionewsbot_notifications_failed_total` - Failed notifications
- `bionewsbot_notification_send_duration_seconds` - Send duration
- `bionewsbot_user_actions_total` - User interactions
- `bionewsbot_rate_limit_hits_total` - Rate limit hits
- `bionewsbot_notification_queue_size` - Current queue size

### Grafana Dashboard

Import the included `grafana_dashboard.json` for pre-configured monitoring.

## Troubleshooting

### Common Issues

1. **"Invalid auth" error**
   - Verify SLACK_BOT_TOKEN starts with `xoxb-`
   - Ensure bot is installed to workspace

2. **Messages not sending**
   - Check channel exists and bot is invited
   - Verify rate limits aren't exceeded
   - Check Redis connection

3. **Webhooks failing**
   - Verify WEBHOOK_SECRET matches backend
   - Check request signatures
   - Ensure proper JSON format

### Debug Mode

Enable debug logging:
```bash
export NOTIFICATION_LOG_LEVEL=DEBUG
```

## Development

### Running Tests

```bash
pytest tests/ -v --cov=notifications
```

### Code Quality

```bash
# Linting
flake8 .

# Type checking
mypy .

# Format code
black .
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Kubernetes

See `k8s/` directory for Kubernetes manifests.

### Environment Variables

All configuration is done via environment variables. See `.env.example` for full list.

## Security

- Webhook signatures verified with HMAC-SHA256
- Slack signatures verified on all requests
- API key authentication for backend calls
- No sensitive data logged
- Rate limiting prevents abuse

## License

MIT License - See LICENSE file for details.
