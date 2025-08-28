#!/usr/bin/env python3
"""Test script for BioNewsBot Scheduler Service."""
import sys
import time
from datetime import datetime
import requests
from celery import Celery
from redis import Redis
import structlog

logger = structlog.get_logger(__name__)


def test_redis_connection():
    """Test Redis connectivity."""
    print("Testing Redis connection...")
    try:
        redis_client = Redis(host='localhost', port=6379, db=0)
        redis_client.ping()
        print("✓ Redis connection successful")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False


def test_celery_connection():
    """Test Celery broker connectivity."""
    print("\nTesting Celery connection...")
    try:
        app = Celery('test', broker='redis://localhost:6379/2')
        # Try to inspect active workers
        inspector = app.control.inspect()
        stats = inspector.stats()
        if stats:
            print(f"✓ Celery connection successful, {len(stats)} worker(s) found")
        else:
            print("⚠ Celery connection successful, but no workers found")
        return True
    except Exception as e:
        print(f"✗ Celery connection failed: {e}")
        return False


def test_health_endpoint():
    """Test health check endpoint."""
    print("\nTesting health check endpoint...")
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        if response.status_code == 200:
            print("✓ Health check endpoint responding")
            print(f"  Status: {response.json()}")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check endpoint not available: {e}")
        return False


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    print("\nTesting metrics endpoint...")
    try:
        response = requests.get('http://localhost:9090/metrics', timeout=5)
        if response.status_code == 200:
            metrics_text = response.text
            if 'bionewsbot' in metrics_text:
                print("✓ Metrics endpoint responding with BioNewsBot metrics")
                return True
            else:
                print("⚠ Metrics endpoint responding but no BioNewsBot metrics found")
                return True
        else:
            print(f"✗ Metrics endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Metrics endpoint not available: {e}")
        return False


def test_task_execution():
    """Test basic task execution."""
    print("\nTesting task execution...")
    try:
        from celery_app import app
        from tasks.analysis import analyze_single_company
        
        # Send a test task
        result = analyze_single_company.delay('TEST', force=True)
        print(f"✓ Task submitted with ID: {result.id}")
        
        # Wait for result (with timeout)
        print("  Waiting for task completion...")
        try:
            task_result = result.get(timeout=30)
            print(f"✓ Task completed successfully: {task_result}")
            return True
        except Exception as e:
            print(f"✗ Task execution failed: {e}")
            return False
    except ImportError:
        print("⚠ Cannot test task execution - modules not available")
        return None
    except Exception as e:
        print(f"✗ Task submission failed: {e}")
        return False


def test_scheduled_jobs():
    """Test scheduled jobs configuration."""
    print("\nTesting scheduled jobs...")
    try:
        response = requests.get('http://localhost:8001/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            jobs = stats.get('scheduled_jobs', [])
            print(f"✓ Found {len(jobs)} scheduled jobs:")
            for job in jobs:
                print(f"  - {job['name']} (ID: {job['id']})")
                print(f"    Next run: {job['next_run']}")
            return True
        else:
            print("✗ Could not retrieve scheduled jobs")
            return False
    except Exception as e:
        print(f"✗ Stats endpoint not available: {e}")
        return False


def main():
    """Run all tests."""
    print("BioNewsBot Scheduler Service Test Suite")
    print("=" * 40)
    print(f"Test started at: {datetime.now()}")
    print()
    
    tests = [
        test_redis_connection,
        test_celery_connection,
        test_health_endpoint,
        test_metrics_endpoint,
        test_scheduled_jobs,
        test_task_execution,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"⚠ Skipped: {skipped}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The scheduler service is ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
