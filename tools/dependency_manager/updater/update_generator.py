"""Generate update plans for dependencies."""

from typing import List
from ..core.models import Dependency, Vulnerability, UpdatePlan, UpdateType


class UpdateGenerator:
    """Generates update plans based on vulnerabilities and policies."""

    def generate_security_updates(
        self, 
        dependencies: List[Dependency], 
        vulnerabilities: List[Vulnerability]
    ) -> List[UpdatePlan]:
        """Generate updates to fix vulnerabilities."""
        plans = []
        
        # Map vulns to deps
        vuln_map = {v.package_name: v for v in vulnerabilities}
        
        for dep in dependencies:
            if dep.name in vuln_map:
                vuln = vuln_map[dep.name]
                # Assume first fixed version is best
                target_version = vuln.fixed_in[0]
                
                plans.append(
                    UpdatePlan(
                        dependency=dep,
                        target_version=target_version,
                        update_type=UpdateType.SECURITY,
                        reason=f"Fixes {vuln.vuln_id}: {vuln.description}",
                        vulnerability=vuln
                    )
                )
                
        return plans

    def generate_maintenance_updates(
        self,
        dependencies: List[Dependency]
    ) -> List[UpdatePlan]:
        """Generate routine maintenance updates (mock)."""
        # In reality, this would query PyPI for latest versions
        plans = []
        return plans
