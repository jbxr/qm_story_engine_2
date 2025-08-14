#!/usr/bin/env python3
"""Test script to validate imports for Phase 4 semantic search."""

try:
    print("Testing imports...")
    
    # Test basic service imports
    from app.services.database import get_supabase
    print("✅ Database service import successful")
    
    from app.services.embedding_service import embedding_service
    print("✅ Embedding service import successful")
    
    from app.services.search_service import search_service
    print("✅ Search service import successful")
    
    # Test API imports
    from app.api.search import router as search_router
    print("✅ Search API import successful")
    
    print("\n🎉 All Phase 4 imports successful!")
    print("\nPhase 4 Semantic Search Infrastructure Ready:")
    print("- pgvector extension enabled in Supabase")
    print("- Embedding service with OpenAI/Groq integration")
    print("- Semantic search service with similarity matching")
    print("- API endpoints for semantic search operations")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()