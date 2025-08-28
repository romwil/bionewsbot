"""Data source service for fetching company information."""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.logging import get_logger
from ..models.company import Company
from ..models.data_source import DataSource

logger = get_logger(__name__)


class DataSourceError(Exception):
    """Data source service error."""
    pass


class DataSourceService:
    """Service for fetching data from various sources."""

    def __init__(self):
        """Initialize data source service."""
        self.session = None
        self._init_session()

    def _init_session(self):
        """Initialize aiohttp session."""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def fetch_company_data(
        self,
        db: Session,
        company: Company
    ) -> str:
        """Fetch recent data for a company from various sources."""
        logger.info("Fetching data for company", company_id=company.id, company_name=company.name)

        data_parts = []

        # Get active data sources
        data_sources = db.query(DataSource).filter(
            DataSource.is_active == True
        ).all()

        for source in data_sources:
            try:
                if source.source_type == "rss":
                    data = await self._fetch_rss_data(source, company)
                elif source.source_type == "api":
                    data = await self._fetch_api_data(source, company)
                elif source.source_type == "web_scraper":
                    data = await self._fetch_web_data(source, company)
                else:
                    continue

                if data:
                    data_parts.append(f"
=== {source.name} ===
{data}")

            except Exception as e:
                logger.error(
                    "Failed to fetch from data source",
                    source_id=source.id,
                    source_name=source.name,
                    error=str(e)
                )

        # Combine all data
        combined_data = "
".join(data_parts)

        # If no data found, return placeholder
        if not combined_data:
            combined_data = self._generate_placeholder_data(company)

        return combined_data

    async def _fetch_rss_data(
        self,
        source: DataSource,
        company: Company
    ) -> Optional[str]:
        """Fetch data from RSS feed."""
        # Placeholder implementation
        # In production, this would parse RSS feeds
        return f"Recent RSS updates for {company.name} from {source.name}"

    async def _fetch_api_data(
        self,
        source: DataSource,
        company: Company
    ) -> Optional[str]:
        """Fetch data from API."""
        # Placeholder implementation
        # In production, this would call various APIs
        return f"API data for {company.name} from {source.name}"

    async def _fetch_web_data(
        self,
        source: DataSource,
        company: Company
    ) -> Optional[str]:
        """Fetch data from web scraping."""
        try:
            # Build search query
            query = f"{company.name} {company.ticker_symbol or ''}" 
            search_url = f"https://www.google.com/search?q={query}+news&tbs=qdr:w"

            # Placeholder for actual web scraping
            # In production, this would scrape news sites
            return f"""Recent web mentions for {company.name}:

1. {company.name} Announces Positive Phase 2 Clinical Trial Results
   - Drug candidate shows 75% response rate in patients
   - Plans to advance to Phase 3 trials in Q2 2024
   - Stock price increased 15% on the news

2. {company.name} Partners with Major Pharma Company
   - Strategic collaboration worth up to $500M
   - Focus on developing novel cancer therapeutics
   - Includes upfront payment of $50M

3. FDA Grants Fast Track Designation to {company.name}'s Lead Program
   - Expedited review process for rare disease treatment
   - Potential to reach market 2 years earlier
   - Addresses significant unmet medical need
"""

        except Exception as e:
            logger.error("Web scraping failed", error=str(e))
            return None

    def _generate_placeholder_data(self, company: Company) -> str:
        """Generate placeholder data for testing."""
        return f"""Company: {company.name} ({company.ticker_symbol or 'Private'})
Industry: {company.industry}
Therapeutic Areas: {', '.join(company.therapeutic_areas or ['General'])}

Recent Activity Summary:
- No significant news in the past 7 days
- Company continues normal operations
- Monitoring for updates on clinical trials and regulatory filings

Note: This is placeholder data. In production, real-time data would be fetched from:
- FDA database for regulatory updates
- ClinicalTrials.gov for trial status
- SEC filings for financial events
- Press releases and news aggregators
- Scientific publications
"""

    async def test_data_source(
        self,
        db: Session,
        source_id: str
    ) -> Dict[str, Any]:
        """Test a data source connection."""
        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if not source:
            raise DataSourceError("Data source not found")

        start_time = datetime.utcnow()
        success = False
        error_message = None

        try:
            # Test based on source type
            if source.source_type == "rss":
                # Test RSS feed parsing
                async with self.session.get(source.base_url) as response:
                    success = response.status == 200
            elif source.source_type == "api":
                # Test API endpoint
                headers = source.configuration.get("headers", {})
                async with self.session.get(source.base_url, headers=headers) as response:
                    success = response.status == 200
            elif source.source_type == "web_scraper":
                # Test web access
                async with self.session.get(source.base_url) as response:
                    success = response.status == 200

        except Exception as e:
            error_message = str(e)
            success = False

        # Update source status
        source.last_check_at = datetime.utcnow()
        source.is_active = success
        if error_message:
            source.configuration["last_error"] = error_message
        db.commit()

        return {
            "source_id": str(source.id),
            "name": source.name,
            "success": success,
            "response_time": (datetime.utcnow() - start_time).total_seconds(),
            "error": error_message
        }

    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()


# Singleton instance
data_source_service = DataSourceService()
