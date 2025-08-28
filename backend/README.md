# BioNewsBot Backend API

A comprehensive FastAPI backend service for the BioNewsBot life sciences company intelligence platform.

## Features

- **Company Management**: CRUD operations for life sciences companies
- **Automated Analysis**: LLM-powered analysis of company news and developments
- **Insight Generation**: Automatic extraction of high-priority insights
- **User Authentication**: JWT-based authentication with role-based access control
- **Real-time Monitoring**: Track regulatory approvals, clinical trials, M&A, funding, and partnerships
- **RESTful API**: Clean, well-documented API endpoints
- **Async Support**: Built with async/await for high performance

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with python-jose
- **LLM Integration**: OpenAI GPT-4
- **Validation**: Pydantic
- **Testing**: Pytest with async support
- **Logging**: Structlog

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- OpenAI API key

### Setup

1. Clone the repository:
```bash
cd /root/bionewsbot/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```env
# Application
PROJECT_NAME="BioNewsBot"
VERSION="1.0.0"
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Security
SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL="postgresql://user:password@localhost/bionewsbot"

# OpenAI
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4"

# First User (Admin)
FIRST_SUPERUSER_EMAIL="admin@bionewsbot.com"
FIRST_SUPERUSER_PASSWORD="changeme"
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

### Main Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get access token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/refresh` - Refresh access token

#### Companies
- `GET /api/v1/companies/` - List companies with filtering
- `POST /api/v1/companies/` - Create new company
- `GET /api/v1/companies/{id}` - Get company details
- `PUT /api/v1/companies/{id}` - Update company
- `DELETE /api/v1/companies/{id}` - Delete company (admin only)
- `POST /api/v1/companies/{id}/toggle-monitoring` - Toggle monitoring status

#### Analysis
- `POST /api/v1/analysis/run` - Trigger analysis for a company
- `GET /api/v1/analysis/runs` - List analysis runs
- `GET /api/v1/analysis/runs/{id}` - Get analysis run details
- `GET /api/v1/analysis/runs/{id}/results` - Get analysis results

#### Insights
- `GET /api/v1/insights/` - List insights with filtering
- `GET /api/v1/insights/{id}` - Get insight details
- `PATCH /api/v1/insights/{id}` - Update insight status/notes
- `GET /api/v1/insights/high-priority` - Get high-priority insights
- `GET /api/v1/insights/export/csv` - Export insights to CSV

#### System
- `GET /api/v1/system/health` - Health check
- `GET /api/v1/system/metrics` - System metrics
- `GET /api/v1/system/config` - Get system configuration (admin)
- `PUT /api/v1/system/config` - Update system configuration (admin)

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/            # API route handlers
│   ├── core/           # Core functionality (config, security, logging)
│   ├── db/             # Database configuration and session
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic services
│   └── utils/          # Utility functions
├── tests/              # Unit and integration tests
├── alembic/            # Database migrations
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── .env                # Environment variables
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run tests in parallel
pytest -n auto
```

### Code Quality

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Lint code
flake8 app tests

# Type checking
mypy app
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Configuration

### Environment Variables

All configuration is done through environment variables. See `.env.example` for a complete list.

### LLM Configuration

The system uses OpenAI GPT-4 by default. You can configure:
- Model selection
- Temperature settings
- Token limits
- Retry policies

### Security

- JWT tokens for authentication
- Password hashing with bcrypt
- Role-based access control (viewer, analyst, admin)
- CORS configuration
- Rate limiting on API endpoints

## Deployment

### Docker

```bash
# Build image
docker build -t bionewsbot-backend .

# Run container
docker run -p 8000:8000 --env-file .env bionewsbot-backend
```

### Production Considerations

1. Use a production ASGI server (Gunicorn with Uvicorn workers)
2. Set up a reverse proxy (Nginx)
3. Enable HTTPS with SSL certificates
4. Configure proper logging and monitoring
5. Set up database backups
6. Use environment-specific configurations
7. Implement rate limiting and DDoS protection

## API Usage Examples

### Authentication

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
```

### Create Company

```python
company_data = {
    "name": "Example Pharma Inc",
    "ticker_symbol": "EXPH",
    "description": "A pharmaceutical company focused on rare diseases",
    "industry": "Pharmaceuticals",
    "therapeutic_areas": ["Rare Diseases", "Oncology"],
    "monitoring_enabled": True
}

response = requests.post(
    "http://localhost:8000/api/v1/companies/",
    json=company_data,
    headers=headers
)
```

### Trigger Analysis

```python
analysis_request = {
    "company_id": "company-uuid-here",
    "analysis_type": "comprehensive",
    "include_competitors": True
}

response = requests.post(
    "http://localhost:8000/api/v1/analysis/run",
    json=analysis_request,
    headers=headers
)
```

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check DATABASE_URL and ensure PostgreSQL is running
2. **OpenAI API errors**: Verify your API key and check rate limits
3. **Import errors**: Ensure all dependencies are installed and virtual environment is activated
4. **CORS errors**: Add your frontend URL to BACKEND_CORS_ORIGINS

### Logging

The application uses structured logging. Check logs for detailed error information:

```python
# Logs are structured JSON by default
{"timestamp": "2024-01-15T10:30:00Z", "level": "ERROR", "message": "...", "context": {...}}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation at `/docs`
