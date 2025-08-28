#!/bin/bash

# BioNewsBot Master Setup Script
# This script initializes and deploys the entire BioNewsBot platform

set -e  # Exit on error

# Colors for output
RED='[0;31m'
GREEN='[0;32m'
YELLOW='[1;33m'
BLUE='[0;34m'
NC='[0m' # No Color

# Configuration
PROJECT_NAME="BioNewsBot"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then 
        log_warning "Running as root is not recommended. Consider using a regular user with docker permissions."
    fi

    log_success "All requirements met"
}

setup_environment() {
    log_info "Setting up environment configuration..."

    # Check if .env exists
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            log_info "Creating .env from .env.example..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_warning "Please edit .env file and update with your actual values"
            log_warning "Press Enter to continue after updating .env file..."
            read -r
        else
            log_error ".env.example file not found!"
            exit 1
        fi
    else
        log_info "Using existing .env file"
    fi

    # Source environment variables
    set -a
    source "$ENV_FILE"
    set +a

    log_success "Environment configured"
}

create_directories() {
    log_info "Creating necessary directories..."

    # Create log directories
    mkdir -p backend/logs
    mkdir -p scheduler/logs
    mkdir -p notifications/logs
    mkdir -p nginx/logs

    # Create data directories
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/uploads

    # Create monitoring directories
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources

    log_success "Directories created"
}

build_services() {
    log_info "Building Docker images..."

    # Build all services
    docker-compose build --parallel

    if [ $? -eq 0 ]; then
        log_success "All services built successfully"
    else
        log_error "Failed to build services"
        exit 1
    fi
}

start_infrastructure() {
    log_info "Starting infrastructure services..."

    # Start database and redis first
    docker-compose up -d postgres redis

    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    until docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER:-bionewsbot} > /dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo ""

    log_success "Infrastructure services started"
}

run_migrations() {
    log_info "Running database migrations..."

    # Check if migrations have already been run
    MIGRATION_CHECK=$(docker-compose exec -T postgres psql -U ${POSTGRES_USER:-bionewsbot} -d ${POSTGRES_DB:-bionewsbot} -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='schema_migrations'" 2>/dev/null || echo "0")

    if [ "$MIGRATION_CHECK" = "0" ]; then
        log_info "Running initial database setup..."
        # The init.sql is automatically run by PostgreSQL on first start
        sleep 5  # Give it time to complete
    else
        log_info "Database already initialized"
    fi

    # Run any pending migrations from backend
    log_info "Checking for pending migrations..."
    docker-compose run --rm backend python -m app.database.migrate

    log_success "Database migrations completed"
}

seed_database() {
    log_info "Seeding database with initial data..."

    # Check if data already exists
    USER_COUNT=$(docker-compose exec -T postgres psql -U ${POSTGRES_USER:-bionewsbot} -d ${POSTGRES_DB:-bionewsbot} -tAc "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")

    if [ "$USER_COUNT" = "0" ]; then
        log_info "Loading seed data..."
        docker-compose exec -T postgres psql -U ${POSTGRES_USER:-bionewsbot} -d ${POSTGRES_DB:-bionewsbot} < database/seeds/001_initial_data.sql
        log_success "Database seeded"
    else
        log_info "Database already contains data, skipping seed"
    fi
}

start_all_services() {
    log_info "Starting all services..."

    # Start remaining services
    docker-compose up -d

    if [ $? -eq 0 ]; then
        log_success "All services started"
    else
        log_error "Failed to start services"
        exit 1
    fi
}

verify_health() {
    log_info "Verifying service health..."

    # Wait a bit for services to fully start
    sleep 10

    # Check each service
    services=("postgres" "redis" "backend" "scheduler" "notifications" "frontend")
    all_healthy=true

    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "${service}.*Up.*healthy"; then
            log_success "${service} is healthy"
        else
            log_warning "${service} is not healthy yet"
            all_healthy=false
        fi
    done

    if [ "$all_healthy" = true ]; then
        log_success "All services are healthy"
    else
        log_warning "Some services are still starting. Run 'docker-compose ps' to check status"
    fi
}

show_urls() {
    log_info "
${GREEN}BioNewsBot is ready!${NC}"
    echo ""
    echo "Access the services at:"
    echo "  - Frontend:      http://localhost:${FRONTEND_PORT:-3000}"
    echo "  - Backend API:   http://localhost:${BACKEND_PORT:-8000}/docs"
    echo "  - Notifications: http://localhost:${NOTIFICATIONS_PORT:-8001}/docs"

    if [ "${ENVIRONMENT}" = "development" ]; then
        echo "  - PostgreSQL:    localhost:${POSTGRES_PORT:-5432}"
        echo "  - Redis:         localhost:${REDIS_PORT:-6379}"
    fi

    echo ""
    echo "Useful commands:"
    echo "  - View logs:     docker-compose logs -f [service]"
    echo "  - Stop all:      docker-compose down"
    echo "  - Restart:       docker-compose restart [service]"
    echo "  - Run tests:     ./run-tests.sh"
    echo ""
}

# Main execution
main() {
    echo "====================================="
    echo "   BioNewsBot Platform Setup"
    echo "====================================="
    echo ""

    check_requirements
    setup_environment
    create_directories
    build_services
    start_infrastructure
    run_migrations
    seed_database
    start_all_services
    verify_health
    show_urls

    log_success "
Setup completed successfully!"
}

# Handle different commands
case "${1:-}" in
    "")
        # Default: full setup
        main
        ;;
    "start")
        # Just start services
        docker-compose up -d
        verify_health
        show_urls
        ;;
    "stop")
        # Stop all services
        docker-compose down
        log_success "All services stopped"
        ;;
    "restart")
        # Restart all services
        docker-compose restart
        verify_health
        ;;
    "rebuild")
        # Rebuild and restart
        docker-compose down
        build_services
        start_all_services
        verify_health
        show_urls
        ;;
    "logs")
        # Show logs
        docker-compose logs -f ${2:-}
        ;;
    "status")
        # Show status
        docker-compose ps
        ;;
    "clean")
        # Clean everything (WARNING: destroys data)
        log_warning "This will remove all containers, volumes, and data!"
        echo -n "Are you sure? (yes/no): "
        read -r response
        if [ "$response" = "yes" ]; then
            docker-compose down -v
            rm -rf data/
            log_success "Cleanup completed"
        else
            log_info "Cleanup cancelled"
        fi
        ;;
    "help")
        # Show help
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (empty)   - Run full setup"
        echo "  start     - Start all services"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  rebuild   - Rebuild and restart all services"
        echo "  logs      - Show logs (optionally specify service)"
        echo "  status    - Show service status"
        echo "  clean     - Remove all data and containers (WARNING: destructive)"
        echo "  help      - Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
