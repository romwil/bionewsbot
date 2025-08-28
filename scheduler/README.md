# BioNewsBot Scheduler Service

Automated scheduling and task processing service for BioNewsBot company analysis system.

## Overview

The Scheduler Service orchestrates automated analysis tasks, report generation, and system maintenance for BioNewsBot. It uses APScheduler for cron-based scheduling and Celery for distributed task processing.

## Features

- **Automated Analysis**: Daily company analysis and hourly quick scans
- **Report Generation**: Weekly comprehensive reports with insights
- **Data Maintenance**: Automatic cleanup of old data and optimization
- **Distributed Processing**: Scalable task execution with Celery workers
- **Monitoring**: Prometheus metrics and health check endpoints
- **Fault Tolerance**: Retry logic with exponential backoff
- **Priority Queues**: High, default, and low priority task queues

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   APScheduler   │────▶│     Redis       │
│   (Cron Jobs)   │     │  (Job Store)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Celery Beat    │────▶│ Celery Workers  │
│  (Scheduler)    │     │ (Task Execution)│
└─────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Backend API    │     │   PostgreSQL    │
│   (Analysis)    │     │   (Storage)     │
└─────────────────┘     └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- Redis server
- PostgreSQL (via Backend API)
- Docker (optional)

### Local Setup

1. Clone the repository:
```bash
cd /root/bionewsbot/scheduler
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_SCHEDULER_DB=1
REDIS_CELERY_DB=2

# API Configuration
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# Scheduling Configuration
DAILY_ANALYSIS_HOUR=6  # 6 AM UTC
WEEKLY_REPORT_DAY=mon  # Monday
WEEKLY_REPORT_HOUR=8   # 8 AM UTC

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3
CELERY_WORKER_CONCURRENCY=4

# Monitoring
PROMETHEUS_PORT=9090
HEALTH_CHECK_PORT=8001

# Archive Storage
ARCHIVE_LOCATION=/var/bionewsbot/archive

# Company Configuration
PRIORITY_COMPANIES=GILD,MRNA,PFE,JNJ
```

### Company Configuration (config/companies.yaml)

```yaml
companies:
  - id: GILD
    name: Gilead Sciences
    priority: high
    analysis_frequency: daily
  - id: MRNA
    name: Moderna
    priority: high
    analysis_frequency: daily
  - id: PFE
    name: Pfizer
    priority: medium
    analysis_frequency: daily
```

## Usage

### Starting the Scheduler

```bash
# Start the main scheduler service
python scheduler_service.py
```

### Starting Celery Workers

```bash
# Start a Celery worker
python celery_worker.py

# Or use Celery directly with more options
celery -A celery_app worker --loglevel=info --concurrency=4

# Start multiple workers
celery -A celery_app worker --loglevel=info --concurrency=2 -n worker1@%h
celery -A celery_app worker --loglevel=info --concurrency=2 -n worker2@%h
```

### Running with Docker

```bash
# Build and start all services
docker-compose up -d

# Scale workers
docker-compose up -d --scale worker=3

# View logs
docker-compose logs -f scheduler
docker-compose logs -f worker
```

## Scheduled Jobs

### Daily Jobs

- **Daily Company Analysis** (6 AM UTC)
  - Analyzes all active companies
  - Generates insights and alerts
  - Updates risk scores

- **Data Cleanup** (3 AM UTC)
  - Archives data older than 90 days
  - Cleans temporary files
  - Removes orphaned records

### Hourly Jobs

- **Quick Scan** (Every hour)
  - Scans priority companies
  - Checks for breaking news
  - Triggers alerts for significant events

### Weekly Jobs

- **Comprehensive Report** (Monday 8 AM UTC)
  - Generates portfolio-wide analysis
  - Creates executive summaries
  - Sends notifications

- **Database Optimization** (Sunday 2 AM UTC)
  - Analyzes tables
  - Rebuilds indexes
  - Updates statistics

### Monthly Jobs

- **Report Archival** (1st of month, 1 AM UTC)
  - Archives reports older than 30 days
  - Compresses and stores in cold storage

## Monitoring

### Health Check Endpoints

- `http://localhost:8001/health` - Basic health check
- `http://localhost:8001/ready` - Readiness check
- `http://localhost:8001/metrics` - Prometheus metrics
- `http://localhost:8001/stats` - Detailed statistics

### Prometheus Metrics

- `bionewsbot_jobs_total` - Total jobs executed
- `bionewsbot_job_duration_seconds` - Job execution duration
- `bionewsbot_tasks_total` - Total Celery tasks
- `bionewsbot_task_duration_seconds` - Task execution duration
- `bionewsbot_active_workers` - Number of active workers
- `bionewsbot_companies_analyzed_total` - Companies analyzed
- `bionewsbot_insights_generated_total` - Insights generated
- `bionewsbot_errors_total` - Error count by type

### Logging

Logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "logger": "scheduler.tasks.analysis",
  "event": "company_analysis_complete",
  "company_id": "GILD",
  "duration": 45.2,
  "insights_count": 5
}
```

## API Integration

The scheduler integrates with the Backend API for:

- Triggering company analysis
- Storing insights and reports
- Fetching company configurations
- Database maintenance operations

## Error Handling

- **Retry Logic**: Failed tasks retry with exponential backoff
- **Dead Letter Queue**: Permanently failed tasks are moved to DLQ
- **Circuit Breaker**: Prevents cascading failures
- **Graceful Shutdown**: Completes running tasks before stopping

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_analysis_tasks.py
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Type checking
mypy .
```

### Adding New Tasks

1. Create task function in appropriate module:
```python
@app.task(bind=True, name='scheduler.tasks.custom.my_task')
def my_custom_task(self, param1: str) -> Dict[str, Any]:
    """My custom task description."""
    logger.info("executing_custom_task", param1=param1)
    # Task implementation
    return {"status": "success"}
```

2. Schedule in `scheduler_service.py`:
```python
self.scheduler.add_job(
    lambda: my_custom_task.delay("value"),
    'cron',
    hour=12,
    minute=0,
    id='my_custom_task',
    name='My Custom Task'
)
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Check Redis is running: `redis-cli ping`
   - Verify connection settings in `.env`

2. **Task Not Executing**
   - Check worker logs: `docker-compose logs worker`
   - Verify task is registered: `celery -A celery_app inspect registered`

3. **Memory Issues**
   - Adjust worker concurrency
   - Set `--max-tasks-per-child` to prevent memory leaks

4. **Scheduling Issues**
   - Check timezone settings (default: UTC)
   - Verify cron expressions
   - Check APScheduler job store

## Performance Tuning

- **Worker Concurrency**: Set based on CPU cores and task types
- **Task Time Limits**: Prevent long-running tasks from blocking
- **Connection Pooling**: Configure Redis connection pool size
- **Batch Processing**: Group related tasks for efficiency

## Security

- Use strong Redis passwords
- Enable SSL/TLS for Redis connections
- Restrict network access to services
- Rotate API keys regularly
- Monitor for suspicious activity

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Check logs in `/var/log/bionewsbot/`
- Review metrics at `http://localhost:9090/metrics`
- Contact the development team
