"""Test LLM service functionality."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

from app.services.llm_service import LLMService
from app.schemas.analysis import (
    CompanyAnalysisRequest,
    InsightExtraction,
    InsightValidation
)


class TestLLMService:
    """Test LLM service functionality."""

    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance."""
        return LLMService()

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "insights": [
                            {
                                "title": "FDA Approval for New Drug",
                                "summary": "Company received FDA approval for their novel cancer treatment.",
                                "category": "regulatory_approval",
                                "confidence_score": 0.95,
                                "impact_score": 0.9,
                                "event_date": "2024-01-15",
                                "source_urls": ["https://example.com/news/fda-approval"],
                                "key_entities": ["FDA", "cancer treatment"],
                                "supporting_evidence": ["FDA announcement", "Company press release"]
                            }
                        ],
                        "company_summary": {
                            "recent_developments": "Major FDA approval received",
                            "market_position": "Strong growth potential",
                            "key_risks": ["Competition from established players"],
                            "opportunities": ["Market expansion with new drug"]
                        }
                    })
                }
            }]
        }

    @pytest.mark.asyncio
    async def test_analyze_company_success(self, llm_service, mock_openai_response):
        """Test successful company analysis."""
        with patch.object(llm_service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response["choices"][0]["message"]["content"]

            request = CompanyAnalysisRequest(
                company_name="Test Pharma Inc",
                company_description="A pharmaceutical company focused on oncology",
                data_points=[
                    {
                        "source": "press_release",
                        "title": "FDA Approval Announcement",
                        "content": "Test Pharma receives FDA approval for new cancer drug",
                        "published_date": "2024-01-15",
                        "url": "https://example.com/news/fda-approval"
                    }
                ]
            )

            result = await llm_service.analyze_company(request)

            assert result is not None
            assert len(result["insights"]) == 1
            assert result["insights"][0]["title"] == "FDA Approval for New Drug"
            assert result["insights"][0]["confidence_score"] == 0.95
            assert "company_summary" in result

    @pytest.mark.asyncio
    async def test_analyze_company_invalid_response(self, llm_service):
        """Test handling of invalid LLM response."""
        with patch.object(llm_service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Invalid JSON response"

            request = CompanyAnalysisRequest(
                company_name="Test Pharma Inc",
                company_description="A pharmaceutical company",
                data_points=[]
            )

            with pytest.raises(Exception):
                await llm_service.analyze_company(request)

    @pytest.mark.asyncio
    async def test_validate_insight_high_priority(self, llm_service):
        """Test insight validation for high priority."""
        with patch.object(llm_service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps({
                "is_valid": True,
                "priority": "high",
                "reasoning": "FDA approval is a major regulatory milestone",
                "suggested_actions": ["Update company profile", "Alert portfolio managers"]
            })

            insight = InsightExtraction(
                title="FDA Approval for New Drug",
                summary="Company received FDA approval",
                category="regulatory_approval",
                confidence_score=0.95,
                impact_score=0.9,
                event_date="2024-01-15",
                source_urls=["https://example.com"],
                key_entities=["FDA"],
                supporting_evidence=["FDA announcement"]
            )

            validation = await llm_service.validate_insight(insight, "Test Pharma Inc")

            assert validation.is_valid is True
            assert validation.priority == "high"
            assert "FDA approval" in validation.reasoning
            assert len(validation.suggested_actions) == 2

    @pytest.mark.asyncio
    async def test_extract_key_insights(self, llm_service):
        """Test key insights extraction."""
        with patch.object(llm_service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps({
                "insights": [
                    {
                        "type": "regulatory",
                        "description": "FDA approval received",
                        "importance": "high"
                    },
                    {
                        "type": "financial",
                        "description": "Revenue growth of 25%",
                        "importance": "medium"
                    }
                ]
            })

            text = """Test Pharma announced FDA approval for their new drug.
            The company also reported 25% revenue growth in Q4."""

            insights = await llm_service.extract_key_insights(text)

            assert len(insights) == 2
            assert insights[0]["type"] == "regulatory"
            assert insights[1]["type"] == "financial"

    def test_build_analysis_prompt(self, llm_service):
        """Test analysis prompt building."""
        request = CompanyAnalysisRequest(
            company_name="Test Pharma Inc",
            company_description="A pharmaceutical company",
            data_points=[
                {
                    "source": "news",
                    "title": "Test News",
                    "content": "News content",
                    "published_date": "2024-01-15",
                    "url": "https://example.com"
                }
            ]
        )

        prompt = llm_service._build_analysis_prompt(request)

        assert "Test Pharma Inc" in prompt
        assert "pharmaceutical company" in prompt
        assert "Test News" in prompt
        assert "regulatory_approval" in prompt  # From categories

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, llm_service):
        """Test retry mechanism on API failure."""
        with patch.object(llm_service, "_call_openai", new_callable=AsyncMock) as mock_call:
            # First two calls fail, third succeeds
            mock_call.side_effect = [
                Exception("API Error"),
                Exception("API Error"),
                json.dumps({"insights": [], "company_summary": {}})
            ]

            request = CompanyAnalysisRequest(
                company_name="Test Pharma Inc",
                company_description="A pharmaceutical company",
                data_points=[]
            )

            result = await llm_service.analyze_company(request)

            assert result is not None
            assert mock_call.call_count == 3
