"""Metadata extraction from Jupyter notebooks."""

import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import nbformat

from .models import NotebookMetadata, Dependency, DifficultyLevel


class MetadataExtractor:
    """Extract structured metadata from notebooks."""

    # Vertex AI service patterns
    VERTEX_SERVICES = {
        "AutoML": [
            r"from google\.cloud import automl",
            r"automl\.AutoMlClient",
            r"AutoMLTabularTrainingJob",
            r"AutoMLImageTrainingJob",
        ],
        "Pipelines": [
            r"from google\.cloud import aiplatform",
            r"@kfp\.dsl\.pipeline",
            r"aiplatform\.PipelineJob",
        ],
        "Custom Training": [
            r"CustomTrainingJob",
            r"CustomContainerTrainingJob",
        ],
        "Prediction": [
            r"\.predict\(",
            r"Endpoint\.deploy",
            r"Model\.deploy",
        ],
        "Feature Store": [
            r"aiplatform\.Featurestore",
            r"aiplatform\.EntityType",
        ],
        "Model Registry": [
            r"aiplatform\.Model\.upload",
            r"model_registry",
        ],
    }

    def extract_metadata(
        self,
        notebook: nbformat.NotebookNode,
        notebook_path: Path,
    ) -> NotebookMetadata:
        """
        Extract metadata from notebook.

        Args:
            notebook: Parsed notebook object
            notebook_path: Path to notebook file

        Returns:
            NotebookMetadata object
        """
        title = self._extract_title(notebook)
        description = self._extract_description(notebook)
        author = self._extract_author(notebook)
        tags = self._extract_tags(notebook)
        vertex_services = self._extract_vertex_services(notebook)
        dependencies = self._extract_dependencies(notebook)
        python_version = self._extract_python_version(notebook)
        estimated_runtime = self._estimate_runtime(notebook)
        difficulty = self._estimate_difficulty(notebook)
        colab_link = self._extract_colab_link(notebook)
        workbench_link = self._extract_workbench_link(notebook)

        # Get file timestamps
        created_date = None
        modified_date = None
        if notebook_path.exists():
            stat = notebook_path.stat()
            modified_date = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return NotebookMetadata(
            title=title,
            description=description,
            author=author,
            created_date=created_date,
            modified_date=modified_date,
            tags=tags,
            vertex_ai_services=vertex_services,
            python_version=python_version,
            dependencies=dependencies,
            estimated_runtime=estimated_runtime,
            difficulty_level=difficulty,
            colab_link=colab_link,
            workbench_link=workbench_link,
        )

    def _extract_title(self, notebook: nbformat.NotebookNode) -> str:
        """Extract title from first markdown cell or metadata."""
        # Check notebook metadata first
        if "title" in notebook.metadata:
            return notebook.metadata["title"]

        # Look for first H1 heading
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                lines = cell.source.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        return line[2:].strip()

        return "Untitled Notebook"

    def _extract_description(self, notebook: nbformat.NotebookNode) -> str:
        """Extract description from notebook."""
        # Look for description in metadata
        if "description" in notebook.metadata:
            return notebook.metadata["description"]

        # Look for first paragraph after title
        found_title = False
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                lines = cell.source.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        found_title = True
                        continue
                    if found_title and line.strip() and not line.startswith("#"):
                        return line.strip()

        return ""

    def _extract_author(self, notebook: nbformat.NotebookNode) -> Optional[str]:
        """Extract author from metadata."""
        if "author" in notebook.metadata:
            return notebook.metadata["author"]
        
        # Look for author in first few markdown cells
        for cell in notebook.cells[:5]:
            if cell.cell_type == "markdown":
                match = re.search(r"(?:Author|By):\s*(.+)", cell.source, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        return None

    def _extract_tags(self, notebook: nbformat.NotebookNode) -> List[str]:
        """Extract tags from metadata."""
        tags = []
        
        if "tags" in notebook.metadata:
            tags.extend(notebook.metadata["tags"])
        
        # Infer tags from content
        content = self._get_all_text(notebook).lower()
        
        tag_keywords = {
            "automl": ["automl"],
            "custom-training": ["custom training", "customtrainingjob"],
            "pipelines": ["pipeline", "kfp"],
            "prediction": ["prediction", "endpoint"],
            "image-classification": ["image classification"],
            "text-classification": ["text classification"],
            "tabular": ["tabular", "structured data"],
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in content for keyword in keywords):
                tags.append(tag)
        
        return list(set(tags))

    def _extract_vertex_services(self, notebook: nbformat.NotebookNode) -> List[str]:
        """Identify Vertex AI services used based on imports and API calls."""
        services = []
        code_content = self._get_all_code(notebook)

        for service, patterns in self.VERTEX_SERVICES.items():
            for pattern in patterns:
                if re.search(pattern, code_content):
                    services.append(service)
                    break

        return list(set(services))

    def _extract_dependencies(self, notebook: nbformat.NotebookNode) -> List[Dependency]:
        """Extract pip/conda dependencies from install cells."""
        dependencies = []
        seen = set()

        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue

            # Look for pip install commands
            pip_pattern = r"!pip\s+install\s+(.+)"
            matches = re.finditer(pip_pattern, cell.source)
            
            for match in matches:
                packages = match.group(1).strip()
                # Split by space, handle multiple packages
                for pkg in packages.split():
                    pkg = pkg.strip()
                    if pkg.startswith("-"):  # Skip flags
                        continue
                    
                    # Parse package name and version
                    if "==" in pkg:
                        name, version = pkg.split("==", 1)
                        is_pinned = True
                    elif ">=" in pkg or "<=" in pkg or "~=" in pkg:
                        parts = re.split(r"[><=~]+", pkg, 1)
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else None
                        is_pinned = False
                    else:
                        name = pkg
                        version = None
                        is_pinned = False
                    
                    if name and name not in seen:
                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version,
                                is_pinned=is_pinned,
                            )
                        )
                        seen.add(name)

        return dependencies

    def _extract_python_version(self, notebook: nbformat.NotebookNode) -> Optional[str]:
        """Extract Python version from metadata or kernel spec."""
        # Check kernel spec
        if "kernelspec" in notebook.metadata:
            kernel_name = notebook.metadata["kernelspec"].get("name", "")
            if "python" in kernel_name.lower():
                # Try to extract version from kernel name
                match = re.search(r"python(\d+)", kernel_name)
                if match:
                    return f"3.{match.group(1)}"
        
        return None

    def _estimate_runtime(self, notebook: nbformat.NotebookNode) -> Optional[str]:
        """Estimate runtime based on cell execution metadata."""
        total_time = 0
        count = 0

        for cell in notebook.cells:
            if cell.cell_type == "code" and "execution" in cell.metadata:
                exec_meta = cell.metadata["execution"]
                if "iopub.execute_input" in exec_meta and "iopub.status.idle" in exec_meta:
                    try:
                        start = datetime.fromisoformat(exec_meta["iopub.execute_input"])
                        end = datetime.fromisoformat(exec_meta["iopub.status.idle"])
                        total_time += (end - start).total_seconds()
                        count += 1
                    except:
                        pass

        if count > 0:
            minutes = int(total_time / 60)
            if minutes < 1:
                return "< 1 minute"
            elif minutes < 60:
                return f"~{minutes} minutes"
            else:
                hours = minutes // 60
                return f"~{hours} hours"

        return None

    def _estimate_difficulty(self, notebook: nbformat.NotebookNode) -> Optional[DifficultyLevel]:
        """Estimate difficulty based on content analysis."""
        code_content = self._get_all_code(notebook)
        
        # Simple heuristic-based difficulty estimation
        score = 0
        
        # Check for advanced patterns
        advanced_patterns = [
            r"class\s+\w+",  # Class definitions
            r"@\w+",  # Decorators
            r"async\s+def",  # Async functions
            r"yield",  # Generators
            r"lambda",  # Lambda functions
        ]
        
        for pattern in advanced_patterns:
            score += len(re.findall(pattern, code_content))
        
        # Check for complexity indicators
        if len(notebook.cells) > 30:
            score += 2
        if len(self._extract_dependencies(notebook)) > 10:
            score += 2
        
        # Classify based on score
        if score < 5:
            return DifficultyLevel.BEGINNER
        elif score < 15:
            return DifficultyLevel.INTERMEDIATE
        else:
            return DifficultyLevel.ADVANCED

    def _extract_colab_link(self, notebook: nbformat.NotebookNode) -> Optional[str]:
        """Extract Colab link from notebook."""
        markdown_content = self._get_all_markdown(notebook)
        
        # Look for Colab badge/link
        colab_pattern = r"https://colab\.research\.google\.com/[^\s\)\"']+"
        match = re.search(colab_pattern, markdown_content)
        
        return match.group(0) if match else None

    def _extract_workbench_link(self, notebook: nbformat.NotebookNode) -> Optional[str]:
        """Extract Workbench link from notebook."""
        markdown_content = self._get_all_markdown(notebook)
        
        # Look for Workbench link
        workbench_pattern = r"https://console\.cloud\.google\.com/vertex-ai/workbench/[^\s\)\"']+"
        match = re.search(workbench_pattern, markdown_content)
        
        return match.group(0) if match else None

    def _get_all_code(self, notebook: nbformat.NotebookNode) -> str:
        """Get all code from notebook as single string."""
        return "\n".join(
            cell.source for cell in notebook.cells if cell.cell_type == "code"
        )

    def _get_all_markdown(self, notebook: nbformat.NotebookNode) -> str:
        """Get all markdown from notebook as single string."""
        return "\n".join(
            cell.source for cell in notebook.cells if cell.cell_type == "markdown"
        )

    def _get_all_text(self, notebook: nbformat.NotebookNode) -> str:
        """Get all text from notebook."""
        return "\n".join(cell.source for cell in notebook.cells)
