# BioNewsBot Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "External Services"
        SLACK[Slack API]
        OPENAI[OpenAI API]
        PUBMED[PubMed API]
        NEWS[News API]
    end

    subgraph "Client Layer"
        BROWSER[Web Browser]
        SLACKAPP[Slack App]
    end

    subgraph "Load Balancer / Proxy"
        NGINX[Nginx<br/>- Reverse Proxy<br/>- SSL Termination<br/>- Static Files]
    end

    subgraph "Application Layer"
        FRONTEND[Frontend<br/>Next.js 14<br/>- Dashboard UI<br/>- Real-time Updates]
        BACKEND[Backend API<br/>FastAPI<br/>- REST API<br/>- WebSocket]
        NOTIFICATIONS[Notifications<br/>- Slack Bot<br/>- Webhooks]
        SCHEDULER[Scheduler<br/>- Celery Workers<br/>- Periodic Tasks]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL<br/>- Companies<br/>- Analyses<br/>- Insights)]
        REDIS[(Redis<br/>- Cache<br/>- Sessions<br/>- Rate Limiting)]
    end

    subgraph "Monitoring"
        PROMETHEUS[Prometheus<br/>Metrics]
        GRAFANA[Grafana<br/>Dashboards]
    end

    %% Client connections
    BROWSER --> NGINX
    SLACKAPP --> NGINX

    %% Nginx routing
    NGINX --> FRONTEND
    NGINX --> BACKEND
    NGINX --> NOTIFICATIONS

    %% Internal connections
    FRONTEND --> BACKEND
    SCHEDULER --> BACKEND
    NOTIFICATIONS --> BACKEND

    %% Database connections
    BACKEND --> POSTGRES
    BACKEND --> REDIS
    SCHEDULER --> POSTGRES
    SCHEDULER --> REDIS
    NOTIFICATIONS --> REDIS

    %% External API connections
    BACKEND --> OPENAI
    BACKEND --> PUBMED
    BACKEND --> NEWS
    NOTIFICATIONS --> SLACK

    %% Monitoring connections
    BACKEND -.-> PROMETHEUS
    SCHEDULER -.-> PROMETHEUS
    NOTIFICATIONS -.-> PROMETHEUS
    PROMETHEUS --> GRAFANA

    classDef external fill:#f9f,stroke:#333,stroke-width:2px
    classDef client fill:#bbf,stroke:#333,stroke-width:2px
    classDef app fill:#bfb,stroke:#333,stroke-width:2px
    classDef data fill:#fbb,stroke:#333,stroke-width:2px
    classDef monitor fill:#fbf,stroke:#333,stroke-width:2px

    class SLACK,OPENAI,PUBMED,NEWS external
    class BROWSER,SLACKAPP client
    class FRONTEND,BACKEND,NOTIFICATIONS,SCHEDULER,NGINX app
    class POSTGRES,REDIS data
    class PROMETHEUS,GRAFANA monitor
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant S as Scheduler
    participant N as Notifications
    participant DB as PostgreSQL
    participant R as Redis
    participant AI as OpenAI
    participant SL as Slack

    Note over U,SL: Company Analysis Flow

    U->>F: Add new company
    F->>B: POST /api/v1/companies
    B->>DB: Insert company
    B->>F: Company created

    U->>F: Trigger analysis
    F->>B: POST /api/v1/analyses
    B->>DB: Create analysis job
    B->>R: Queue analysis task
    B->>F: Analysis started

    S->>R: Poll for tasks
    R->>S: Analysis task
    S->>B: Get company data
    B->>DB: Fetch company
    B->>S: Company details

    S->>AI: Generate analysis
    AI->>S: AI insights
    S->>DB: Save analysis
    S->>B: Analysis complete

    B->>N: Trigger notification
    N->>SL: Send Slack message
    SL->>U: Notification received

    U->>F: View insights
    F->>B: GET /api/v1/insights
    B->>DB: Fetch insights
    B->>F: Insights data
    F->>U: Display dashboard
```

## Component Details

### Frontend (Next.js)
- **Purpose**: User interface for monitoring and management
- **Features**:
  - Real-time dashboard
  - Company management
  - Analysis visualization
  - Insight reports
- **Technologies**: Next.js 14, TypeScript, Tailwind CSS, Chart.js

### Backend API (FastAPI)
- **Purpose**: Core business logic and API endpoints
- **Features**:
  - RESTful API
  - WebSocket support
  - Authentication/Authorization
  - Data validation
- **Technologies**: FastAPI, Python 3.11, SQLAlchemy, Pydantic

### Scheduler (Celery)
- **Purpose**: Asynchronous task processing
- **Features**:
  - Periodic analysis runs
  - Background processing
  - Task retry logic
  - Schedule management
- **Technologies**: Celery, APScheduler, Python 3.11

### Notifications (Slack Bot)
- **Purpose**: Alert delivery and user notifications
- **Features**:
  - Slack integration
  - Webhook handling
  - Rate limiting
  - Message formatting
- **Technologies**: FastAPI, Slack SDK, Python 3.11

### Database (PostgreSQL)
- **Purpose**: Primary data storage
- **Schema**:
  - Companies
  - Analyses
  - Insights
  - Users
  - Audit logs
- **Features**: JSONB storage, UUID keys, Triggers

### Cache (Redis)
- **Purpose**: Performance optimization
- **Usage**:
  - API response caching
  - Session storage
  - Rate limiting
  - Task queue
- **Features**: Persistence, Pub/Sub

## Security Architecture

```mermaid
graph LR
    subgraph "Internet"
        USER[User]
        ATTACKER[Potential Attacker]
    end

    subgraph "Security Layers"
        FW[Firewall<br/>- Port filtering<br/>- DDoS protection]
        SSL[SSL/TLS<br/>- Encryption<br/>- Certificate validation]
        AUTH[Authentication<br/>- JWT tokens<br/>- API keys]
        RATE[Rate Limiting<br/>- Request throttling<br/>- IP blocking]
    end

    subgraph "Application"
        APP[BioNewsBot<br/>Services]
    end

    USER --> FW
    ATTACKER -.-> FW
    FW --> SSL
    SSL --> AUTH
    AUTH --> RATE
    RATE --> APP

    style ATTACKER fill:#f99,stroke:#333,stroke-width:2px
    style FW fill:#9f9,stroke:#333,stroke-width:2px
    style SSL fill:#9f9,stroke:#333,stroke-width:2px
    style AUTH fill:#9f9,stroke:#333,stroke-width:2px
    style RATE fill:#9f9,stroke:#333,stroke-width:2px
```
