"""LLM integration service for company analysis."""
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib

import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel, ValidationError

from ..core.config import settings
from ..core.logging import get_logger
from ..schemas.insight import InsightCreate
from ..schemas.analysis import AnalysisResultUpdate

logger = get_logger(__name__)


class LLMError(Exception):
    """LLM service error."""
    pass


class CompanyAnalysisOutput(BaseModel):
    """Structured output from LLM company analysis."""

    insights: List[Dict[str, Any]]
    summary: str
    confidence_score: float

    class Config:
        schema_extra = {
            "example": {
                "insights": [
                    {
                        "title": "FDA Approval for Novel Cancer Drug",
                        "summary": "Company received FDA approval for...",
                        "category": "regulatory_approval",
                        "priority": "high",
                        "confidence": 0.95,
                        "impact": 0.9,
                        "entities": {
                            "drugs": ["Drug-X"],
                            "organizations": ["FDA"],
                            "indications": ["lung cancer"]
                        },
                        "metrics": {
                            "market_size": "$5B",
                            "patient_population": "50000"
                        },
                        "source_urls": ["https://..."],
                        "event_date": "2024-01-15"
                    }
                ],
                "summary": "Company shows strong momentum with recent FDA approval...",
                "confidence_score": 0.92
            }
        }


class LLMService:
    """Service for LLM interactions."""

    def __init__(self):
        """Initialize LLM service."""
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS

        # Load prompt templates
        self.prompts = self._load_prompt_templates()

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates for different analysis types."""
        return {
            "company_analysis": """You are a life sciences industry analyst specializing in biotechnology and pharmaceutical companies.

Analyze the following company and recent information to identify key insights:

Company: {company_name}
Ticker: {ticker_symbol}
Description: {company_description}
Therapeutic Areas: {therapeutic_areas}

Recent Information:
{recent_data}

Identify and extract insights in these categories:
1. Regulatory Approvals (FDA, EMA, etc.)
2. Clinical Trial Results (Phase 1/2/3)
3. Mergers & Acquisitions
4. Funding Rounds
5. Strategic Partnerships
6. Product Launches
7. Executive Changes
8. Financial Results

For each insight, provide:
- Title (clear, concise headline)
- Summary (2-3 sentences)
- Category (from list above)
- Priority (high/medium/low based on impact)
- Confidence score (0-1)
- Impact score (0-1)
- Key entities (drugs, organizations, people)
- Key metrics (financial amounts, percentages, dates)
- Source URLs
- Event date

Focus on HIGH-PRIORITY events that significantly impact the company's value or trajectory.

Return a JSON object with:
{{
    "insights": [...],
    "summary": "Overall company status summary",
    "confidence_score": 0.0-1.0
}}""",

            "insight_validation": """Review and validate this extracted insight:

Insight: {insight_title}
Summary: {insight_summary}
Category: {category}

Validate:
1. Is this genuinely newsworthy for life sciences investors?
2. Is the information specific and actionable?
3. Are the entities and metrics accurately extracted?
4. Is the priority assessment correct?

Return validation result as JSON:
{{
    "is_valid": true/false,
    "corrections": {{}},
    "validation_notes": ""
}}""",

            "deduplication_check": """Compare these two insights and determine if they are duplicates:

Insight 1:
Title: {title1}
Summary: {summary1}
Date: {date1}

Insight 2:
Title: {title2}
Summary: {summary2}
Date: {date2}

Return JSON:
{{
    "are_duplicates": true/false,
    "similarity_score": 0.0-1.0,
    "reason": "explanation"
}}"""
        }

    @retry(
        stop=stop_after_attempt(settings.ANALYSIS_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((openai.APIError, openai.APITimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"LLM request failed, retrying... (attempt {retry_state.attempt_number})"
        )
    )
    def _make_llm_request(self, prompt: str, system_prompt: str = None) -> str:
        """Make a request to the LLM with retry logic."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            start_time = time.time()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Force JSON response
            )

            elapsed_time = time.time() - start_time

            logger.info(
                "LLM request completed",
                model=self.model,
                elapsed_time=elapsed_time,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )

            return response.choices[0].message.content

        except openai.APIError as e:
            logger.error("OpenAI API error", error=str(e))
            raise LLMError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in LLM request", error=str(e))
            raise LLMError(f"Unexpected error: {str(e)}")

    def analyze_company(
        self,
        company_data: Dict[str, Any],
        recent_data: str
    ) -> Tuple[CompanyAnalysisOutput, Dict[str, Any]]:
        """Analyze a company using LLM."""
        logger.info("Starting company analysis", company_id=company_data.get("id"))

        # Prepare prompt
        prompt = self.prompts["company_analysis"].format(
            company_name=company_data.get("name", ""),
            ticker_symbol=company_data.get("ticker_symbol", "N/A"),
            company_description=company_data.get("description", "N/A"),
            therapeutic_areas=", ".join(company_data.get("therapeutic_areas", [])),
            recent_data=recent_data
        )

        # Make LLM request
        raw_response = self._make_llm_request(prompt)

        # Parse and validate response
        try:
            parsed_data = json.loads(raw_response)
            analysis_output = CompanyAnalysisOutput(**parsed_data)

            # Calculate token usage (approximate)
            token_usage = {
                "prompt_tokens": len(prompt.split()) * 1.3,  # Rough estimate
                "completion_tokens": len(raw_response.split()) * 1.3,
                "total_tokens": (len(prompt.split()) + len(raw_response.split())) * 1.3
            }

            return analysis_output, token_usage

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error("Failed to parse LLM response", error=str(e))
            raise LLMError(f"Invalid LLM response format: {str(e)}")

    def validate_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an insight using LLM."""
        prompt = self.prompts["insight_validation"].format(
            insight_title=insight.get("title"),
            insight_summary=insight.get("summary"),
            category=insight.get("category")
        )

        response = self._make_llm_request(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"is_valid": False, "validation_notes": "Failed to parse validation response"}

    def check_duplicate_insights(
        self,
        insight1: Dict[str, Any],
        insight2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if two insights are duplicates."""
        prompt = self.prompts["deduplication_check"].format(
            title1=insight1.get("title"),
            summary1=insight1.get("summary"),
            date1=insight1.get("event_date"),
            title2=insight2.get("title"),
            summary2=insight2.get("summary"),
            date2=insight2.get("event_date")
        )

        response = self._make_llm_request(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"are_duplicates": False, "similarity_score": 0.0, "reason": "Parse error"}

    def generate_content_hash(self, content: str) -> str:
        """Generate a hash for content deduplication."""
        # Normalize content
        normalized = " ".join(content.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def extract_priority_keywords(self, text: str) -> List[str]:
        """Extract high-priority keywords from text."""
        found_keywords = []
        text_lower = text.lower()

        for keyword in settings.HIGH_PRIORITY_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        return found_keywords


# Singleton instance
llm_service = LLMService()
