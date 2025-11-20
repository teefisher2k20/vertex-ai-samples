"""Data models for notebook validation and metadata."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict


class ValidationSeverity(Enum):
    """Severity levels for validation results."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DifficultyLevel(Enum):
    """Difficulty levels for notebooks."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ValidationStatus(Enum):
    """Overall validation status."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    NOT_VALIDATED = "not_validated"


@dataclass
class ValidationResult:
    """Represents a single validation check result."""
    rule_id: str
    severity: ValidationSeverity
    message: str
    cell_index: Optional[int] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "cell_index": self.cell_index,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
        }


@dataclass
class Dependency:
    """Represents a Python dependency."""
    name: str
    version: Optional[str] = None
    is_pinned: bool = False
    constraint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "is_pinned": self.is_pinned,
            "constraint": self.constraint,
        }


@dataclass
class NotebookMetadata:
    """Extracted metadata from a notebook."""
    title: str
    description: str = ""
    author: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    vertex_ai_services: List[str] = field(default_factory=list)
    python_version: Optional[str] = None
    dependencies: List[Dependency] = field(default_factory=list)
    estimated_runtime: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    colab_link: Optional[str] = None
    workbench_link: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
            "tags": self.tags,
            "vertex_ai_services": self.vertex_ai_services,
            "python_version": self.python_version,
            "dependencies": [dep.to_dict() for dep in self.dependencies],
            "estimated_runtime": self.estimated_runtime,
            "difficulty_level": self.difficulty_level.value if self.difficulty_level else None,
            "colab_link": self.colab_link,
            "workbench_link": self.workbench_link,
        }


@dataclass
class NotebookValidationReport:
    """Complete validation report for a notebook."""
    notebook_path: str
    is_valid: bool
    validation_results: List[ValidationResult] = field(default_factory=list)
    metadata: Optional[NotebookMetadata] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def error_count(self) -> int:
        """Count of error-level validation results."""
        return sum(1 for r in self.validation_results if r.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level validation results."""
        return sum(1 for r in self.validation_results if r.severity == ValidationSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of info-level validation results."""
        return sum(1 for r in self.validation_results if r.severity == ValidationSeverity.INFO)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "notebook_path": self.notebook_path,
            "is_valid": self.is_valid,
            "validation_results": [r.to_dict() for r in self.validation_results],
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "summary": {
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
            },
        }
