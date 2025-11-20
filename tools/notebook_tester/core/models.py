"""Data models for notebook testing."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class CellResult:
    index: int
    status: TestStatus
    execution_count: Optional[int] = None
    output: Optional[str] = None
    error_name: Optional[str] = None
    error_value: Optional[str] = None
    duration: float = 0.0


@dataclass
class ExecutionResult:
    notebook_path: str
    status: TestStatus
    cell_results: List[CellResult] = field(default_factory=list)
    total_duration: float = 0.0
    error_message: Optional[str] = None
    
    @property
    def failed_cells(self) -> List[CellResult]:
        return [c for c in self.cell_results if c.status == TestStatus.FAILED]
