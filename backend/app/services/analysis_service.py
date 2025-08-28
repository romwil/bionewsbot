"""Analysis service for orchestrating company analysis."""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.config import settings
from ..core.logging import get_logger
from ..models.company import Company
from ..models.analysis import AnalysisRun, AnalysisResult
from ..models.insight import Insight, InsightCategory
from ..schemas.analysis import AnalysisRunCreate, AnalysisResultUpdate
from ..schemas.insight import InsightCreate
from .llm_service import llm_service, LLMError

logger = get_logger(__name__)


class AnalysisError(Exception):
    """Analysis service error."""
    pass


class AnalysisService:
    """Service for managing company analysis."""

    async def create_analysis_run(
        self,
        db: Session,
        run_data: AnalysisRunCreate,
        user_id: Optional[UUID] = None
    ) -> AnalysisRun:
        """Create a new analysis run."""
        logger.info("Creating new analysis run", run_type=run_data.run_type)

        # Create analysis run
        analysis_run = AnalysisRun(
            run_type=run_data.run_type,
            configuration=run_data.configuration or {},
            triggered_by_id=user_id,
            status="pending"
        )

        db.add(analysis_run)
        db.commit()
        db.refresh(analysis_run)

        # Start analysis in background
        asyncio.create_task(self._execute_analysis_run(analysis_run.id))

        return analysis_run

    async def _execute_analysis_run(self, run_id: UUID) -> None:
        """Execute an analysis run asynchronously."""
        from ..db.session import SessionLocal

        db = SessionLocal()
        try:
            # Get analysis run
            analysis_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
            if not analysis_run:
                logger.error("Analysis run not found", run_id=run_id)
                return

            # Update status to running
            analysis_run.status = "running"
            analysis_run.started_at = datetime.utcnow()
            db.commit()

            # Get companies to analyze
            companies = self._get_companies_for_analysis(db, analysis_run)
            analysis_run.total_companies = len(companies)
            db.commit()

            logger.info(
                "Starting analysis for companies",
                run_id=run_id,
                company_count=len(companies)
            )

            # Process companies in batches
            batch_size = settings.ANALYSIS_BATCH_SIZE
            for i in range(0, len(companies), batch_size):
                batch = companies[i:i + batch_size]
                await self._process_company_batch(db, analysis_run, batch)

                # Update progress
                analysis_run.processed_companies = min(i + batch_size, len(companies))
                db.commit()

            # Complete analysis run
            analysis_run.status = "completed"
            analysis_run.completed_at = datetime.utcnow()
            analysis_run.duration_seconds = int(
                (analysis_run.completed_at - analysis_run.started_at).total_seconds()
            )
            db.commit()

            logger.info(
                "Analysis run completed",
                run_id=run_id,
                duration=analysis_run.duration_seconds,
                insights_generated=analysis_run.insights_generated
            )

        except Exception as e:
            logger.error("Analysis run failed", run_id=run_id, error=str(e))
            if analysis_run:
                analysis_run.status = "failed"
                analysis_run.error_count += 1
                analysis_run.error_details = {"error": str(e)}
                db.commit()
        finally:
            db.close()


    def _get_companies_for_analysis(
        self,
        db: Session,
        analysis_run: AnalysisRun
    ) -> List[Company]:
        """Get companies that need analysis."""
        query = db.query(Company).filter(
            Company.is_active == True,
            Company.monitoring_enabled == True
        )

        # Filter by specific company IDs if provided
        config = analysis_run.configuration or {}
        if "company_ids" in config:
            query = query.filter(Company.id.in_(config["company_ids"]))

        # Filter by companies that need analysis
        if not config.get("force_rerun", False):
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            query = query.filter(
                or_(
                    Company.last_analysis_at == None,
                    Company.last_analysis_at < cutoff_time
                )
            )

        # Order by priority
        query = query.order_by(
            Company.priority_level.desc(),
            Company.last_analysis_at.asc().nullsfirst()
        )

        return query.all()

    async def _process_company_batch(
        self,
        db: Session,
        analysis_run: AnalysisRun,
        companies: List[Company]
    ) -> None:
        """Process a batch of companies."""
        tasks = []
        for company in companies:
            task = self._analyze_company(db, analysis_run, company)
            tasks.append(task)

        # Process companies concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results
        for company, result in zip(companies, results):
            if isinstance(result, Exception):
                logger.error(
                    "Company analysis failed",
                    company_id=company.id,
                    error=str(result)
                )
                analysis_run.failed_companies += 1
            else:
                logger.info(
                    "Company analysis completed",
                    company_id=company.id,
                    insights_count=result
                )

    async def _analyze_company(
        self,
        db: Session,
        analysis_run: AnalysisRun,
        company: Company
    ) -> int:
        """Analyze a single company."""
        logger.info("Analyzing company", company_id=company.id, company_name=company.name)

        # Create analysis result
        analysis_result = AnalysisResult(
            analysis_run_id=analysis_run.id,
            company_id=company.id,
            status="processing",
            model_used=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
        db.add(analysis_result)
        db.commit()

        try:
            # Fetch recent data for the company (placeholder for now)
            recent_data = f"Recent news and updates for {company.name}..."

            # Prepare company data
            company_data = {
                "id": str(company.id),
                "name": company.name,
                "ticker_symbol": company.ticker_symbol,
                "description": company.description,
                "therapeutic_areas": company.therapeutic_areas or []
            }

            # Analyze with LLM
            analysis_output, token_usage = llm_service.analyze_company(
                company_data,
                recent_data
            )

            # Update analysis result
            analysis_result.status = "completed"
            analysis_result.raw_response = json.dumps(analysis_output.dict())
            analysis_result.parsed_data = analysis_output.dict()
            analysis_result.prompt_tokens = token_usage.get("prompt_tokens", 0)
            analysis_result.completion_tokens = token_usage.get("completion_tokens", 0)
            analysis_result.total_tokens = token_usage.get("total_tokens", 0)
            analysis_result.validation_status = "valid"
            db.commit()

            # Process insights
            insights_created = await self._process_insights(
                db,
                company,
                analysis_result,
                analysis_output.insights
            )

            # Update company last analysis time
            company.last_analysis_at = datetime.utcnow()
            company.total_insights_count += insights_created
            db.commit()

            # Update analysis run stats
            analysis_run.insights_generated += insights_created
            analysis_run.processed_companies += 1
            db.commit()

            return insights_created

        except Exception as e:
            logger.error(
                "Failed to analyze company",
                company_id=company.id,
                error=str(e)
            )

            # Update analysis result with error
            analysis_result.status = "failed"
            analysis_result.error_message = str(e)
            analysis_result.error_type = type(e).__name__
            db.commit()

            # Update analysis run error count
            analysis_run.error_count += 1
            db.commit()

            raise AnalysisError(f"Company analysis failed: {str(e)}")


    async def _process_insights(
        self,
        db: Session,
        company: Company,
        analysis_result: AnalysisResult,
        insights_data: List[Dict[str, Any]]
    ) -> int:
        """Process and store insights from analysis."""
        insights_created = 0
        high_priority_count = 0

        for insight_data in insights_data:
            try:
                # Get or create category
                category = self._get_or_create_category(
                    db,
                    insight_data.get("category", "general")
                )

                # Generate content hash for deduplication
                content = f"{insight_data.get('title', '')} {insight_data.get('summary', '')}"
                content_hash = llm_service.generate_content_hash(content)

                # Check for duplicates
                existing_insight = db.query(Insight).filter(
                    Insight.company_id == company.id,
                    Insight.content_hash == content_hash
                ).first()

                if existing_insight:
                    logger.info(
                        "Duplicate insight detected",
                        company_id=company.id,
                        insight_id=existing_insight.id
                    )
                    continue

                # Create insight
                insight = Insight(
                    company_id=company.id,
                    analysis_result_id=analysis_result.id,
                    category_id=category.id,
                    title=insight_data.get("title", "Untitled"),
                    summary=insight_data.get("summary", ""),
                    full_content=insight_data.get("full_content"),
                    priority=insight_data.get("priority", "medium"),
                    confidence_score=insight_data.get("confidence", 0.5),
                    impact_score=insight_data.get("impact", 0.5),
                    source_urls=insight_data.get("source_urls", []),
                    extracted_entities=insight_data.get("entities", {}),
                    key_metrics=insight_data.get("metrics", {}),
                    event_date=self._parse_date(insight_data.get("event_date")),
                    published_date=datetime.utcnow(),
                    content_hash=content_hash,
                    status="new"
                )

                db.add(insight)
                insights_created += 1

                if insight.priority == "high":
                    high_priority_count += 1

            except Exception as e:
                logger.error(
                    "Failed to create insight",
                    company_id=company.id,
                    error=str(e)
                )

        # Update company high priority insights count
        company.high_priority_insights_count += high_priority_count

        # Update category counts
        db.commit()

        return insights_created

    def _get_or_create_category(
        self,
        db: Session,
        category_name: str
    ) -> InsightCategory:
        """Get or create an insight category."""
        # Normalize category name
        normalized_name = category_name.lower().replace(" ", "_")

        # Check if category exists
        category = db.query(InsightCategory).filter(
            InsightCategory.name == normalized_name
        ).first()

        if not category:
            # Create new category
            category = InsightCategory(
                name=normalized_name,
                description=f"Insights related to {category_name}",
                is_high_priority=normalized_name in [
                    "regulatory_approval",
                    "clinical_trial_results",
                    "mergers_acquisitions",
                    "funding_rounds"
                ],
                priority_score=80 if normalized_name in [
                    "regulatory_approval",
                    "clinical_trial_results"
                ] else 60
            )
            db.add(category)
            db.commit()
            db.refresh(category)

        return category

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, return None
            return None
        except Exception:
            return None

    async def get_analysis_stats(
        self,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analysis statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get run statistics
        total_runs = db.query(AnalysisRun).count()
        successful_runs = db.query(AnalysisRun).filter(
            AnalysisRun.status == "completed"
        ).count()
        failed_runs = db.query(AnalysisRun).filter(
            AnalysisRun.status == "failed"
        ).count()

        # Get recent runs
        recent_runs = db.query(AnalysisRun).filter(
            AnalysisRun.created_at >= cutoff_date
        ).order_by(AnalysisRun.created_at.desc()).limit(10).all()

        # Calculate average duration
        completed_runs = db.query(AnalysisRun).filter(
            AnalysisRun.status == "completed",
            AnalysisRun.duration_seconds != None
        ).all()

        avg_duration = 0
        if completed_runs:
            avg_duration = sum(r.duration_seconds for r in completed_runs) / len(completed_runs)

        # Get insights statistics
        total_insights = db.query(Insight).filter(
            Insight.created_at >= cutoff_date
        ).count()

        # Get insights by category
        insights_by_category = {}
        categories = db.query(InsightCategory).all()
        for category in categories:
            count = db.query(Insight).filter(
                Insight.category_id == category.id,
                Insight.created_at >= cutoff_date
            ).count()
            if count > 0:
                insights_by_category[category.name] = count

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "average_duration_seconds": avg_duration,
            "total_insights_generated": total_insights,
            "insights_by_category": insights_by_category,
            "recent_runs": [
                {
                    "id": str(run.id),
                    "run_type": run.run_type,
                    "status": run.status,
                    "created_at": run.created_at.isoformat(),
                    "insights_generated": run.insights_generated
                }
                for run in recent_runs
            ]
        }


# Singleton instance
analysis_service = AnalysisService()
