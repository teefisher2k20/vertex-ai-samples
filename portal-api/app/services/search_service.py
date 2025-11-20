import os
from pathlib import Path
from typing import List, Dict, Any
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.analysis import StemmingAnalyzer

from ..models.notebook import Notebook, DifficultyLevel, ValidationStatus, Dependency

class SearchService:
    def __init__(self, index_dir: str = "index"):
        self.index_dir = index_dir
        self.schema = Schema(
            id=ID(stored=True, unique=True),
            path=STORED,
            title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            description=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            content=TEXT(analyzer=StemmingAnalyzer()),  # Full notebook content
            tags=KEYWORD(stored=True, lowercase=True, commas=True, scorable=True),
            services=KEYWORD(stored=True, lowercase=True, commas=True, scorable=True),
            difficulty=KEYWORD(stored=True),
            author=STORED,
            github_link=STORED,
        )
        self._ensure_index()

    def _ensure_index(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            create_in(self.index_dir, self.schema)

    def index_notebooks(self, notebooks: List[Dict]):
        """Index a list of notebook dictionaries."""
        ix = open_dir(self.index_dir)
        writer = ix.writer()
        
        for nb in notebooks:
            writer.update_document(
                id=nb["id"],
                path=nb["path"],
                title=nb["title"],
                description=nb["description"],
                content=nb.get("content", ""),
                tags=",".join(nb["tags"]),
                services=",".join(nb["vertex_ai_services"]),
                difficulty=nb.get("difficulty_level"),
                author=nb.get("author"),
                github_link=nb["github_link"],
            )
        
        writer.commit()

    def search(
        self, 
        query_str: str, 
        tags: List[str] = None, 
        services: List[str] = None,
        difficulty: List[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search notebooks with filtering and faceting.
        """
        ix = open_dir(self.index_dir)
        
        with ix.searcher() as searcher:
            # Build query
            if query_str:
                parser = MultifieldParser(
                    ["title", "description", "content", "tags", "services"], 
                    ix.schema
                )
                query = parser.parse(query_str)
            else:
                # Match all if no query
                from whoosh.query import Every
                query = Every()

            # Apply filters (simplified for this implementation)
            # In a real implementation, we'd combine queries
            
            results = searcher.search(query, limit=limit)
            
            # Convert results to Notebook models (mocking some data for now)
            notebooks = []
            for r in results:
                notebooks.append(Notebook(
                    id=r["id"],
                    path=r["path"],
                    title=r["title"],
                    description=r["description"],
                    author=r.get("author"),
                    tags=r["tags"].split(",") if r.get("tags") else [],
                    vertex_ai_services=r["services"].split(",") if r.get("services") else [],
                    difficulty_level=r.get("difficulty"),
                    github_link=r["github_link"],
                    # Defaults for fields not in search index
                    dependencies=[],
                    validation_status=ValidationStatus.NOT_VALIDATED
                ))

            # Calculate facets (simplified)
            facets = {
                "tags": {},
                "services": {},
                "difficulty": {}
            }

            return {
                "notebooks": notebooks,
                "total_count": len(results),
                "facets": facets
            }
