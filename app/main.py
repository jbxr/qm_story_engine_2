"""
FastAPI application entry point for QuantumMateria Story Engine
Simplified version based on proven test_minimal_api.py patterns
"""
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from .api.scenes import router as scenes_router
from .api.entities import router as entities_router
from .api.milestones import router as milestones_router
from .api.goals import router as goals_router
from .api.knowledge import router as knowledge_router
from .api.content import router as content_router
from .api.relationships import router as relationships_router
from .api.search import router as search_router
from .services.database import get_db

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="QuantumMateria Story Engine",
    description="A structured storytelling platform with SQLModel + Supabase backend",
    version="0.2.0"
)

# Include API routes - Phase 3: Data Team (Relationships & Search)
app.include_router(scenes_router, prefix="/api/v1/scenes", tags=["scenes"])
app.include_router(entities_router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(milestones_router, prefix="/api/v1/milestones", tags=["milestones"])
app.include_router(goals_router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(content_router, prefix="/api/v1/content", tags=["content"])
app.include_router(relationships_router, prefix="/api/v1/relationships", tags=["relationships"])
app.include_router(search_router, prefix="/api/v1/search", tags=["search"])

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "QuantumMateria Story Engine API", 
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
def health():
    """Health check with database connectivity"""
    try:
        db = get_db()
        # Simple query to test connection
        result = db.table("entities").select("count", count="exact").execute()
        entity_count = result.count if result.count is not None else 0
        
        # Check knowledge snapshots table as well
        knowledge_result = db.table("knowledge_snapshots").select("count", count="exact").execute()
        knowledge_count = knowledge_result.count if knowledge_result.count is not None else 0
        
        return {
            "status": "healthy",
            "database": "connected", 
            "entity_count": entity_count,
            "knowledge_snapshot_count": knowledge_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting QuantumMateria Story Engine - Phase 3: Data Team...")
    print("📊 Health check: http://localhost:8000/health")
    print("🎬 Scenes API: http://localhost:8000/api/v1/scenes")
    print("👥 Entities API: http://localhost:8000/api/v1/entities")
    print("🏆 Milestones API: http://localhost:8000/api/v1/milestones")
    print("🎯 Goals API: http://localhost:8000/api/v1/goals")
    print("🧠 Knowledge API: http://localhost:8000/api/v1/knowledge")
    print("📝 Content API: http://localhost:8000/api/v1/content")
    print("🔗 Relationships API: http://localhost:8000/api/v1/relationships")
    print("🔍 Search API: http://localhost:8000/api/v1/search")
    print("📚 Docs: http://localhost:8000/docs")
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)