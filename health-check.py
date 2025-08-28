#!/usr/bin/env python3
"""
BioNewsBot Health Check Script
Checks the health of all services and provides a unified status report
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple

# Service endpoints
SERVICES = {
    "backend": {
        "url": "http://localhost:8000/health",
        "name": "Backend API",
        "critical": True
    },
    "frontend": {
        "url": "http://localhost:3000/api/health",
        "name": "Frontend Dashboard",
        "critical": True
    },
    "notifications": {
        "url": "http://localhost:8001/webhooks/health",
        "name": "Notification Service",
        "critical": False
    },
    "postgres": {
        "url": "http://localhost:8000/health/database",
        "name": "PostgreSQL Database",
        "critical": True
    },
    "redis": {
        "url": "http://localhost:8000/health/cache",
        "name": "Redis Cache",
        "critical": True
    }
}

def check_service(service_id: str, service_info: Dict) -> Tuple[bool, str, float]:
    """Check a single service health"""
    start_time = datetime.now()

    try:
        response = requests.get(service_info["url"], timeout=5)
        response_time = (datetime.now() - start_time).total_seconds()

        if response.status_code == 200:
            return True, "Healthy", response_time
        else:
            return False, f"HTTP {response.status_code}", response_time
    except requests.exceptions.Timeout:
        return False, "Timeout", 5.0
    except requests.exceptions.ConnectionError:
        return False, "Connection Error", 0.0
    except Exception as e:
        return False, str(e), 0.0

def main():
    """Run health checks for all services"""
    print("
" + "=" * 60)
    print("BioNewsBot Health Check Report")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("
")

    results = {}
    all_healthy = True
    critical_healthy = True

    # Check each service
    for service_id, service_info in SERVICES.items():
        is_healthy, status, response_time = check_service(service_id, service_info)
        results[service_id] = {
            "name": service_info["name"],
            "healthy": is_healthy,
            "status": status,
            "response_time": response_time,
            "critical": service_info["critical"]
        }

        # Update overall status
        if not is_healthy:
            all_healthy = False
            if service_info["critical"]:
                critical_healthy = False

        # Print status
        status_icon = "✅" if is_healthy else "❌"
        critical_marker = "*" if service_info["critical"] else " "
        print(f"{status_icon} {service_info['name']:<25} {status:<20} ({response_time:.2f}s){critical_marker}")

    # Summary
    print("
" + "-" * 60)
    print("Summary:")
    print(f"  Total Services: {len(SERVICES)}")
    print(f"  Healthy: {sum(1 for r in results.values() if r['healthy'])}")
    print(f"  Unhealthy: {sum(1 for r in results.values() if not r['healthy'])}")

    if all_healthy:
        print("
✅ All services are healthy!")
        exit_code = 0
    elif critical_healthy:
        print("
⚠️  Some non-critical services are unhealthy")
        exit_code = 1
    else:
        print("
❌ Critical services are unhealthy!")
        exit_code = 2

    print("
* Critical services
")

    # Output JSON if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        output = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "critical_status": "healthy" if critical_healthy else "unhealthy",
            "services": results
        }
        print(json.dumps(output, indent=2))

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
