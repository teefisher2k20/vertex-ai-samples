"""Execute notebooks and capture results."""

import time
import nbformat
from pathlib import Path
from typing import Optional
from nbconvert.preprocessors import ExecutePreprocessor
from nbclient.exceptions import CellExecutionError

from ..core.models import ExecutionResult, CellResult, TestStatus


class NotebookExecutor:
    """Executes notebooks using nbconvert."""

    def __init__(self, timeout: int = 600, kernel_name: str = "python3"):
        self.timeout = timeout
        self.kernel_name = kernel_name
        self.preprocessor = ExecutePreprocessor(
            timeout=timeout,
            kernel_name=kernel_name,
            allow_errors=True  # We want to capture errors, not crash
        )

    def execute(self, notebook_path: Path) -> ExecutionResult:
        """Execute a notebook and return results."""
        start_time = time.time()
        
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)
        except Exception as e:
            return ExecutionResult(
                notebook_path=str(notebook_path),
                status=TestStatus.ERROR,
                error_message=f"Failed to read notebook: {str(e)}"
            )

        try:
            # Execute the notebook
            self.preprocessor.preprocess(notebook, {'metadata': {'path': str(notebook_path.parent)}})
            status = TestStatus.PASSED
            error_msg = None
        except Exception as e:
            status = TestStatus.ERROR
            error_msg = str(e)

        # Analyze results
        cell_results = []
        has_failures = False
        
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
                
            cell_status = TestStatus.PASSED
            error_name = None
            error_value = None
            
            # Check for errors in output
            for output in cell.outputs:
                if output.output_type == "error":
                    cell_status = TestStatus.FAILED
                    error_name = output.ename
                    error_value = output.evalue
                    has_failures = True
            
            cell_results.append(
                CellResult(
                    index=i,
                    status=cell_status,
                    execution_count=cell.execution_count,
                    error_name=error_name,
                    error_value=error_value
                )
            )

        if has_failures:
            status = TestStatus.FAILED

        return ExecutionResult(
            notebook_path=str(notebook_path),
            status=status,
            cell_results=cell_results,
            total_duration=time.time() - start_time,
            error_message=error_msg
        )
