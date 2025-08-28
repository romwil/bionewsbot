#!/usr/bin/env python3
"""
BioNewsBot Integration Tests
Tests the complete flow: Company → Analysis → Insight → Notification
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
import subprocess

# Configuration
BASE_URL = os.getenv('API_URL', 'http://localhost:8000')
API_KEY = os.getenv('API_KEY', 'test-api-key')
NOTIFICATION_URL = os.getenv('NOTIFICATION_URL', 'http://localhost:8001')

# Test data
TEST_COMPANY = {
    "name": "Test Biotech Inc",
    "description": "A test biotechnology company for integration testing",
    "website": "https://example.com",
    "focus_areas": ["oncology", "immunology"]
}

class IntegrationTests:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.company_id = None
        self.analysis_id = None
        self.insight_id = None

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def check_service_health(self, service_name, url):
        """Check if a service is healthy"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                self.log(f"✅ {service_name} is healthy")
                return True
            else:
                self.log(f"❌ {service_name} returned status {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ {service_name} is not reachable: {str(e)}", "ERROR")
            return False

    def test_health_checks(self):
        """Test 1: Verify all services are healthy"""
        self.log("
=== Test 1: Health Checks ===")

        services = [
            ("Backend API", BASE_URL),
            ("Notification Service", NOTIFICATION_URL),
            ("Frontend", "http://localhost:3000")
        ]

        all_healthy = True
        for service_name, url in services:
            if not self.check_service_health(service_name, url):
                all_healthy = False

        return all_healthy

    def test_create_company(self):
        """Test 2: Create a new company"""
        self.log("
=== Test 2: Create Company ===")

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/companies",
                headers=self.headers,
                json=TEST_COMPANY
            )

            if response.status_code == 201:
                data = response.json()
                self.company_id = data.get("id")
                self.log(f"✅ Company created with ID: {self.company_id}")
                return True
            else:
                self.log(f"❌ Failed to create company: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error creating company: {str(e)}", "ERROR")
            return False

    def test_trigger_analysis(self):
        """Test 3: Trigger analysis for the company"""
        self.log("
=== Test 3: Trigger Analysis ===")

        if not self.company_id:
            self.log("❌ No company ID available", "ERROR")
            return False

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/analyses",
                headers=self.headers,
                json={
                    "company_id": self.company_id,
                    "analysis_type": "comprehensive",
                    "sources": ["pubmed", "news"]
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.analysis_id = data.get("id")
                self.log(f"✅ Analysis triggered with ID: {self.analysis_id}")
                return True
            else:
                self.log(f"❌ Failed to trigger analysis: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error triggering analysis: {str(e)}", "ERROR")
            return False

    def test_wait_for_analysis(self):
        """Test 4: Wait for analysis to complete"""
        self.log("
=== Test 4: Wait for Analysis Completion ===")

        if not self.analysis_id:
            self.log("❌ No analysis ID available", "ERROR")
            return False

        max_attempts = 30  # 5 minutes max wait
        attempt = 0

        while attempt < max_attempts:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/v1/analyses/{self.analysis_id}",
                    headers=self.headers
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")

                    if status == "completed":
                        self.log("✅ Analysis completed successfully")
                        return True
                    elif status == "failed":
                        self.log("❌ Analysis failed", "ERROR")
                        return False
                    else:
                        self.log(f"⏳ Analysis status: {status} (attempt {attempt + 1}/{max_attempts})")

            except Exception as e:
                self.log(f"❌ Error checking analysis status: {str(e)}", "ERROR")

            time.sleep(10)  # Wait 10 seconds between checks
            attempt += 1

        self.log("❌ Analysis timed out", "ERROR")
        return False

    def test_generate_insight(self):
        """Test 5: Generate insight from analysis"""
        self.log("
=== Test 5: Generate Insight ===")

        if not self.analysis_id:
            self.log("❌ No analysis ID available", "ERROR")
            return False

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/insights",
                headers=self.headers,
                json={
                    "analysis_id": self.analysis_id,
                    "insight_type": "strategic",
                    "focus": "market_opportunities"
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.insight_id = data.get("id")
                self.log(f"✅ Insight generated with ID: {self.insight_id}")
                return True
            else:
                self.log(f"❌ Failed to generate insight: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error generating insight: {str(e)}", "ERROR")
            return False

    def test_send_notification(self):
        """Test 6: Send notification about the insight"""
        self.log("
=== Test 6: Send Notification ===")

        if not self.insight_id:
            self.log("❌ No insight ID available", "ERROR")
            return False

        try:
            # First, get the insight details
            response = requests.get(
                f"{BASE_URL}/api/v1/insights/{self.insight_id}",
                headers=self.headers
            )

            if response.status_code != 200:
                self.log("❌ Failed to retrieve insight details", "ERROR")
                return False

            insight_data = response.json()

            # Send notification
            notification_payload = {
                "type": "insight_generated",
                "channel": "#bionewsbot-alerts",
                "data": {
                    "company_name": TEST_COMPANY["name"],
                    "insight_type": "strategic",
                    "summary": insight_data.get("summary", "New strategic insight generated"),
                    "insight_id": self.insight_id
                }
            }

            response = requests.post(
                f"{NOTIFICATION_URL}/api/v1/notifications",
                headers=self.headers,
                json=notification_payload
            )

            if response.status_code in [200, 201]:
                self.log("✅ Notification sent successfully")
                return True
            else:
                self.log(f"❌ Failed to send notification: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error sending notification: {str(e)}", "ERROR")
            return False

    def test_verify_data_flow(self):
        """Test 7: Verify complete data flow"""
        self.log("
=== Test 7: Verify Data Flow ===")

        checks = [
            ("Company exists in database", self.company_id is not None),
            ("Analysis was created", self.analysis_id is not None),
            ("Insight was generated", self.insight_id is not None)
        ]

        all_passed = True
        for check_name, passed in checks:
            if passed:
                self.log(f"✅ {check_name}")
            else:
                self.log(f"❌ {check_name}", "ERROR")
                all_passed = False

        return all_passed

    def cleanup(self):
        """Clean up test data"""
        self.log("
=== Cleanup ===")

        if self.company_id:
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/v1/companies/{self.company_id}",
                    headers=self.headers
                )
                if response.status_code in [200, 204]:
                    self.log("✅ Test data cleaned up")
                else:
                    self.log("⚠️  Failed to clean up test data", "WARNING")
            except Exception as e:
                self.log(f"⚠️  Error during cleanup: {str(e)}", "WARNING")

    def run_all_tests(self):
        """Run all integration tests"""
        self.log("
" + "=" * 50)
        self.log("BioNewsBot Integration Tests")
        self.log("=" * 50)

        tests = [
            ("Health Checks", self.test_health_checks),
            ("Create Company", self.test_create_company),
            ("Trigger Analysis", self.test_trigger_analysis),
            ("Wait for Analysis", self.test_wait_for_analysis),
            ("Generate Insight", self.test_generate_insight),
            ("Send Notification", self.test_send_notification),
            ("Verify Data Flow", self.test_verify_data_flow)
        ]

        results = []
        for test_name, test_func in tests:
            try:
                passed = test_func()
                results.append((test_name, passed))
                if not passed:
                    self.log(f"
⚠️  Stopping tests due to failure in: {test_name}", "WARNING")
                    break
            except Exception as e:
                self.log(f"
❌ Unexpected error in {test_name}: {str(e)}", "ERROR")
                results.append((test_name, False))
                break

        # Cleanup
        self.cleanup()

        # Summary
        self.log("
" + "=" * 50)
        self.log("Test Summary")
        self.log("=" * 50)

        total_tests = len(results)
        passed_tests = sum(1 for _, passed in results if passed)

        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            self.log(f"{test_name}: {status}")

        self.log(f"
Total: {passed_tests}/{total_tests} tests passed")

        return passed_tests == total_tests


if __name__ == "__main__":
    tester = IntegrationTests()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
