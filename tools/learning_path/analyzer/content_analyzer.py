"""Analyze notebook content to extract topics and difficulty."""

import nbformat
from pathlib import Path
from typing import List, Dict
from .models import NotebookNode, Difficulty, Topic


class ContentAnalyzer:
    """Analyzes notebooks for learning path generation."""

    def __init__(self):
        self.topics = {
            "automl": Topic("AutoML", ["automl", "tabular", "image classification"]),
            "custom_training": Topic("Custom Training", ["custom training", "training job", "container"]),
            "pipelines": Topic("Pipelines", ["pipeline", "kfp", "component"]),
            "generative_ai": Topic("Generative AI", ["llm", "generative", "palm", "gemini"]),
        }

    def analyze_notebook(self, notebook_path: Path) -> NotebookNode:
        """Analyze a notebook to create a node."""
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
        except Exception:
            return self._create_empty_node(notebook_path)

        # Extract text content
        content = ""
        code_content = ""
        for cell in nb.cells:
            if cell.cell_type == "markdown":
                content += cell.source + "\n"
            elif cell.cell_type == "code":
                code_content += cell.source + "\n"

        full_text = (content + code_content).lower()

        # Identify topics
        found_topics = []
        for topic_id, topic in self.topics.items():
            if any(k in full_text for k in topic.keywords):
                found_topics.append(topic.name)

        # Estimate difficulty
        difficulty = self._estimate_difficulty(code_content)
        
        # Extract title
        title = notebook_path.stem.replace("_", " ").title()
        
        return NotebookNode(
            path=str(notebook_path),
            title=title,
            difficulty=difficulty,
            topics=found_topics,
            estimated_time_mins=30 + (len(nb.cells) // 2)  # Rough estimate
        )

    def _estimate_difficulty(self, code: str) -> Difficulty:
        """Estimate difficulty based on code complexity."""
        score = 0
        
        # Check for advanced concepts
        if "class " in code: score += 2
        if "async " in code: score += 2
        if "@" in code: score += 1
        if "lambda" in code: score += 1
        
        if score < 2:
            return Difficulty.BEGINNER
        elif score < 5:
            return Difficulty.INTERMEDIATE
        else:
            return Difficulty.ADVANCED

    def _create_empty_node(self, path: Path) -> NotebookNode:
        return NotebookNode(
            path=str(path),
            title=path.stem,
            difficulty=Difficulty.BEGINNER,
            topics=[]
        )
