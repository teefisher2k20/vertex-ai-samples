"""Data models for dependency management."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class UpdateType(Enum):
    SECURITY = "security"
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass
class Dependency:
    name: str
    version: Optional[str]
    file_path: str
    line_number: int
    cell_index: int
    raw_line: str

    def __hash__(self):
        return hash((self.name, self.version, self.file_path))


@dataclass
class Vulnerability:
    package_name: str
    current_version: str
    vuln_id: str
    description: str
    severity: str
    fixed_in: List[str]
    advisory_url: Optional[str] = None


@dataclass
class UpdatePlan:
    dependency: Dependency
    target_version: str
    update_type: UpdateType
    reason: str
    vulnerability: Optional[Vulnerability] = None

    @property
    def priority(self) -> int:
        if self.update_type == UpdateType.SECURITY:
            return 0
        if self.update_type == UpdateType.PATCH:
            return 1
        if self.update_type == UpdateType.MINOR:
            return 2
        return 3
