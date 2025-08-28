#!/bin/bash

# BioNewsBot Test Runner
# Runs all test suites across services

set -e

# Colors
GREEN='[0;32m'
RED='[0;31m'
YELLOW='[1;33m'
NC='[0m'

echo "====================================="
echo "   BioNewsBot Test Suite Runner"
echo "====================================="
echo ""

# Function to run tests for a service
run_service_tests() {
    local service=$1
    local test_command=$2

    echo -e "
${YELLOW}Running tests for: ${service}${NC}"
    echo "-------------------------------------"

    if docker-compose exec -T ${service} ${test_command}; then
        echo -e "${GREEN}✅ ${service} tests passed${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service} tests failed${NC}"
        return 1
    fi
}

# Track overall status
all_passed=true

# Backend tests
if ! run_service_tests "backend" "pytest -v --cov=app tests/"; then
    all_passed=false
fi

# Frontend tests
if ! run_service_tests "frontend" "npm test -- --watchAll=false"; then
    all_passed=false
fi

# Scheduler tests
if ! run_service_tests "scheduler" "pytest -v tests/"; then
    all_passed=false
fi

# Notification service tests
if ! run_service_tests "notifications" "pytest -v tests/"; then
    all_passed=false
fi

# Integration tests
echo -e "
${YELLOW}Running integration tests${NC}"
echo "-------------------------------------"

if python tests/integration/test_integration.py; then
    echo -e "${GREEN}✅ Integration tests passed${NC}"
else
    echo -e "${RED}❌ Integration tests failed${NC}"
    all_passed=false
fi

# Summary
echo -e "
====================================="
if [ "$all_passed" = true ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
