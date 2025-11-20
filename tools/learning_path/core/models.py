"""Data models for learning paths."""

from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum


class Difficulty(Enum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


@dataclass
class Topic:
    name: str
    keywords: List[str]
    weight: float = 1.0


@dataclass
class NotebookNode:
    path: str
    title: str
    difficulty: Difficulty
    topics: List[str]
    prerequisites: List[str] = field(default_factory=list)
    estimated_time_mins: int = 30


@dataclass
class LearningPath:
    title: str
    description: str
    nodes: List[NotebookNode]
    total_time_mins: int
    difficulty: Difficulty
    
    @property
    def steps(self) -> int:
        return len(self.nodes)
