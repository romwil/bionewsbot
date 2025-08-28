"""Database base configuration."""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from typing import Generator

# Base class for all models
Base = declarative_base()

# Import all models here to ensure they are registered
from ..models.user import User
from ..models.company import Company
from ..models.analysis import AnalysisRun, AnalysisResult
from ..models.insight import Insight, InsightCategory
from ..models.data_source import DataSource, CompanyDataSource
from ..models.configuration import SystemConfiguration
from ..models.audit import AuditLog
