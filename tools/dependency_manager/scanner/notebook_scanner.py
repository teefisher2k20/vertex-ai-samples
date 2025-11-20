"""Scanner for extracting dependencies from notebooks."""

import re
import nbformat
from pathlib import Path
from typing import List, Set

from ..core.models import Dependency


class NotebookScanner:
    """Scans notebooks for pip install commands."""

    def scan_directory(self, directory: Path) -> List[Dependency]:
        """Scan all notebooks in a directory."""
        dependencies = []
        for notebook_path in directory.rglob("*.ipynb"):
            if ".ipynb_checkpoints" in str(notebook_path):
                continue
            dependencies.extend(self.scan_notebook(notebook_path))
        return dependencies

    def scan_notebook(self, notebook_path: Path) -> List[Dependency]:
        """Scan a single notebook for dependencies."""
        dependencies = []
        
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)
        except Exception:
            return []

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue

            # Look for pip install commands
            # Matches: !pip install package==1.0.0
            # Matches: %pip install package>=1.0.0
            pip_pattern = r"(?:!|%)pip\s+install\s+(.+)"
            
            lines = cell.source.split("\n")
            for line_idx, line in enumerate(lines):
                match = re.search(pip_pattern, line)
                if match:
                    packages_str = match.group(1)
                    parsed_deps = self._parse_pip_args(packages_str)
                    
                    for name, version in parsed_deps:
                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version,
                                file_path=str(notebook_path),
                                line_number=line_idx + 1,
                                cell_index=i,
                                raw_line=line.strip(),
                            )
                        )
        
        return dependencies

    def _parse_pip_args(self, args_str: str) -> List[tuple]:
        """Parse pip install arguments into (name, version) tuples."""
        results = []
        
        # Split by space but respect quotes (simplified)
        parts = args_str.split()
        
        for part in parts:
            part = part.strip()
            if part.startswith("-"):  # Skip flags
                continue
            if part.startswith("git+"): # Skip git urls
                continue
                
            # Parse version specifiers
            # This is a simplified parser. For robust parsing, use 'packaging' library
            if "==" in part:
                name, version = part.split("==", 1)
            elif ">=" in part:
                name, version = part.split(">=", 1)
            elif "<=" in part:
                name, version = part.split("<=", 1)
            elif "~=" in part:
                name, version = part.split("~=", 1)
            else:
                name = part
                version = None
                
            # Clean up
            name = re.split(r"[\[\]]", name)[0]  # Remove extras like package[extra]
            
            if name:
                results.append((name, version))
                
        return results
