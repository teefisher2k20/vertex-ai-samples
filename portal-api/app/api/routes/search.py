from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from ..models.notebook import SearchResult, Notebook
from ..services.search_service import SearchService

router = APIRouter()
search_service = SearchService()

@router.get("/search", response_model=SearchResult)
async def search_notebooks(
    q: Optional[str] = None,
    tags: List[str] = Query(default=[]),
    services: List[str] = Query(default=[]),
    difficulty: List[str] = Query(default=[]),
    page: int = 1,
    limit: int = 20,
):
    """
    Search for notebooks with filters.
    """
    try:
        results = search_service.search(
            query_str=q,
            tags=tags,
            services=services,
            difficulty=difficulty,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notebooks/{notebook_id}", response_model=Notebook)
async def get_notebook(notebook_id: str):
    """
    Get details for a single notebook.
    """
    # In a real app, fetch from DB/Index
    # For now, returning mock
    raise HTTPException(status_code=404, detail="Notebook not found")
