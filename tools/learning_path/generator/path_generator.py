"""Generate learning paths from analyzed notebooks."""

from typing import List, Dict
from .models import LearningPath, NotebookNode, Difficulty


class PathGenerator:
    """Generates structured learning paths."""

    def generate_path(
        self, 
        nodes: List[NotebookNode], 
        topic: str, 
        max_difficulty: Difficulty = Difficulty.ADVANCED
    ) -> LearningPath:
        """Generate a learning path for a specific topic."""
        
        # Filter relevant nodes
        relevant_nodes = [
            n for n in nodes 
            if topic in n.topics and n.difficulty.value <= max_difficulty.value
        ]
        
        # Sort by difficulty then estimated time
        sorted_nodes = sorted(
            relevant_nodes, 
            key=lambda n: (n.difficulty.value, n.estimated_time_mins)
        )
        
        total_time = sum(n.estimated_time_mins for n in sorted_nodes)
        
        return LearningPath(
            title=f"Mastering {topic}",
            description=f"A comprehensive guide to {topic} using Vertex AI.",
            nodes=sorted_nodes,
            total_time_mins=total_time,
            difficulty=max_difficulty
        )

    def generate_all_paths(self, nodes: List[NotebookNode]) -> List[LearningPath]:
        """Generate paths for all discovered topics."""
        # Collect all unique topics
        all_topics = set()
        for node in nodes:
            all_topics.update(node.topics)
            
        paths = []
        for topic in all_topics:
            paths.append(self.generate_path(nodes, topic))
            
        return paths
