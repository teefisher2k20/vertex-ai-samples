from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    NOT_VALIDATED = "not_validated"


class Dependency(BaseModel):
    name: str
    version: Optional[str] = None
    is_pinned: bool = False


class Notebook(BaseModel):
    id: str
    path: str
    title: str
    description: str
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    vertex_ai_services: List[str] = Field(default_factory=list)
    python_version: Optional[str] = None
    dependencies: List[Dependency] = Field(default_factory=list)
    estimated_runtime: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    colab_link: Optional[str] = None
    workbench_link: Optional[str] = None
    github_link: str
    validation_status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    view_count: int = 0


class SearchResult(BaseModel):
    notebooks: List[Notebook]
    total_count: int
    facets: Dict[str, Dict[str, int]]
