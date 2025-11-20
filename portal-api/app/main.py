from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import search

app = FastAPI(
    title="Vertex AI Notebook Portal API",
    description="API for searching and managing Vertex AI notebooks",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api/v1", tags=["search"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
