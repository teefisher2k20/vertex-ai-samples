"""Notebook Validator - Automated validation and metadata extraction for Jupyter notebooks."""

__version__ = "1.0.0"
__author__ = "Vertex AI Samples Team"

from .core.validator import NotebookValidator
from .core.metadata_extractor import MetadataExtractor
from .core.models import (
    ValidationResult,
    ValidationSeverity,
    NotebookMetadata,
    NotebookValidationReport,
)

__all__ = [
    "NotebookValidator",
    "MetadataExtractor",
    "ValidationResult",
    "ValidationSeverity",
    "NotebookMetadata",
    "NotebookValidationReport",
]
