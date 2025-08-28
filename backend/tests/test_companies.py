"""Test company management endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.company import Company


class TestCompanies:
    """Test company management functionality."""

    def test_create_company(self, client: TestClient, auth_headers: dict):
        """Test creating a new company."""
        response = client.post(
            "/api/v1/companies/",
            headers=auth_headers,
            json={
                "name": "New Biotech Corp",
                "ticker_symbol": "NBIO",
                "description": "A new biotechnology company",
                "industry": "Biotechnology",
                "therapeutic_areas": ["Oncology", "Immunology"],
                "website": "https://newbiotech.com",
                "headquarters_location": "San Francisco, CA",
                "founded_year": 2020,
                "employee_count": "50-100",
                "monitoring_enabled": True,
                "monitoring_keywords": ["NBIO news", "New Biotech"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Biotech Corp"
        assert data["ticker_symbol"] == "NBIO"
        assert data["monitoring_enabled"] is True
        assert "id" in data

    def test_create_company_unauthorized(self, client: TestClient):
        """Test creating company without auth."""
        response = client.post(
            "/api/v1/companies/",
            json={"name": "Test Corp"}
        )
        assert response.status_code == 401

    def test_get_company(self, client: TestClient, test_company: Company, auth_headers: dict):
        """Test getting company details."""
        response = client.get(
            f"/api/v1/companies/{test_company.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_company.id)
        assert data["name"] == test_company.name

    def test_get_company_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent company."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/companies/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_list_companies(self, client: TestClient, test_company: Company, auth_headers: dict):
        """Test listing companies."""
        response = client.get(
            "/api/v1/companies/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "companies" in data
        assert "total" in data
        assert data["total"] >= 1
        assert any(c["id"] == str(test_company.id) for c in data["companies"])

    def test_list_companies_with_filters(self, client: TestClient, test_company: Company, auth_headers: dict):
        """Test listing companies with filters."""
        response = client.get(
            "/api/v1/companies/",
            headers=auth_headers,
            params={
                "industry": "Pharmaceuticals",
                "monitoring_enabled": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert all(c["industry"] == "Pharmaceuticals" for c in data["companies"])
        assert all(c["monitoring_enabled"] is True for c in data["companies"])

    def test_search_companies(self, client: TestClient, test_company: Company, auth_headers: dict):
        """Test searching companies."""
        response = client.get(
            "/api/v1/companies/",
            headers=auth_headers,
            params={"search": "Test Pharma"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Test Pharma" in c["name"] for c in data["companies"])

    def test_update_company(self, client: TestClient, test_company: Company, auth_headers: dict):
        """Test updating company."""
        response = client.put(
            f"/api/v1/companies/{test_company.id}",
            headers=auth_headers,
            json={
                "description": "Updated description",
                "monitoring_enabled": False,
                "monitoring_keywords": ["new keyword"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["monitoring_enabled"] is False
        assert "new keyword" in data["monitoring_keywords"]

    def test_delete_company(self, client: TestClient, test_company: Company, admin_headers: dict):
        """Test deleting company (admin only)."""
        response = client.delete(
            f"/api/v1/companies/{test_company.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify company is deleted
        response = client.get(
            f"/api/v1/companies/{test_company.id}",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_delete_company_non_admin(self, client: TestClient, test_company: Company, auth_headers: dict):
        """Test deleting company without admin rights."""
        response = client.delete(
            f"/api/v1/companies/{test_company.id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_toggle_monitoring(self, client: TestClient, test_company: Company, auth_headers: dict):
        """Test toggling company monitoring."""
        # Get initial state
        initial_state = test_company.monitoring_enabled

        response = client.post(
            f"/api/v1/companies/{test_company.id}/toggle-monitoring",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["monitoring_enabled"] != initial_state

        # Toggle back
        response = client.post(
            f"/api/v1/companies/{test_company.id}/toggle-monitoring",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["monitoring_enabled"] == initial_state
