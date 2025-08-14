"""Embedding generation service for semantic search.

Provides text-to-vector conversion using OpenAI/Groq APIs for semantic search
across scenes, entities, and knowledge snapshots.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
import os
# Config will be imported lazily to avoid circular imports

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenAI/Groq APIs."""

    def __init__(self):
        """Initialize the embedding service with API clients."""
        self.openai_client = None
        self.groq_client = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of API clients to avoid circular imports."""
        if self._initialized:
            return
            
        try:
            from app.config import get_settings
            settings = get_settings()
            
            # Initialize OpenAI client if API key is available
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Initialize Groq client if API key is available
            if hasattr(settings, 'groq_api_key') and settings.groq_api_key:
                try:
                    # Groq uses OpenAI-compatible client with custom base URL
                    self.groq_client = AsyncOpenAI(
                        api_key=settings.groq_api_key,
                        base_url="https://api.groq.com/openai/v1"
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize Groq client: {e}")
                    
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            # Fallback: try environment variables directly
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = AsyncOpenAI(api_key=openai_key)
            self._initialized = True

    async def generate_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Generate embedding vector for given text.
        
        Args:
            text: Text to generate embedding for
            model: Embedding model to use (default: text-embedding-3-small)
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If no API clients are available or text is empty
            Exception: If embedding generation fails
        """
        self._ensure_initialized()
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
            
        # Try OpenAI first (typically more reliable for embeddings)
        if self.openai_client:
            try:
                response = await self.openai_client.embeddings.create(
                    model=model,
                    input=text.strip()
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding generation failed: {e}")
                
        # Fallback to Groq if OpenAI fails
        if self.groq_client:
            try:
                # Note: Groq may not support all embedding models
                response = await self.groq_client.embeddings.create(
                    model=model,
                    input=text.strip()
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"Groq embedding generation failed: {e}")
                
        raise ValueError("No available API clients for embedding generation")

    async def generate_embeddings_batch(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to generate embeddings for
            model: Embedding model to use
            
        Returns:
            List of embedding vectors in same order as input texts
        """
        if not texts:
            return []
            
        # Filter out empty texts
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
        if not valid_texts:
            raise ValueError("No valid texts provided")
            
        try:
            # Try batch API call first (more efficient)
            if self.openai_client:
                response = await self.openai_client.embeddings.create(
                    model=model,
                    input=[text for _, text in valid_texts]
                )
                
                # Create result list with correct indexing
                result = [None] * len(texts)
                for i, (original_index, _) in enumerate(valid_texts):
                    result[original_index] = response.data[i].embedding
                    
                return [emb for emb in result if emb is not None]
                
        except Exception as e:
            logger.warning(f"Batch embedding generation failed: {e}")
            
        # Fallback to individual calls
        embeddings = []
        for _, text in valid_texts:
            try:
                embedding = await self.generate_embedding(text, model)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to generate embedding for text: {e}")
                # Use zero vector as placeholder
                embeddings.append([0.0] * 1536)
                
        return embeddings

    def extract_text_for_embedding(self, entity_type: str, data: Dict[str, Any]) -> str:
        """Extract relevant text from entity data for embedding generation.
        
        Args:
            entity_type: Type of entity ('scene_block', 'entity', 'knowledge_snapshot')
            data: Entity data dictionary
            
        Returns:
            Concatenated text suitable for embedding
        """
        if entity_type == "scene_block":
            parts = []
            if data.get("content"):
                parts.append(data["content"])
            if data.get("summary"):
                parts.append(data["summary"])
            if data.get("lines"):
                # Extract dialogue lines
                for line in data["lines"]:
                    if isinstance(line, dict) and line.get("text"):
                        parts.append(line["text"])
            return " ".join(parts)
            
        elif entity_type == "entity":
            parts = []
            if data.get("name"):
                parts.append(data["name"])
            if data.get("description"):
                parts.append(data["description"])
            if data.get("metadata"):
                # Extract searchable metadata
                metadata = data["metadata"]
                if isinstance(metadata, dict):
                    for key, value in metadata.items():
                        if isinstance(value, str):
                            parts.append(f"{key}: {value}")
            return " ".join(parts)
            
        elif entity_type == "knowledge_snapshot":
            parts = []
            # Try both 'knowledge' and 'knowledge_state' for compatibility
            knowledge_data = data.get("knowledge") or data.get("knowledge_state")
            if knowledge_data:
                if isinstance(knowledge_data, dict):
                    for key, value in knowledge_data.items():
                        if isinstance(value, str):
                            parts.append(f"{key}: {value}")
                        elif isinstance(value, list):
                            parts.extend([str(item) for item in value if isinstance(item, str)])
            return " ".join(parts)
            
        return ""

    async def update_entity_embedding(self, entity_id: str, entity_type: str, data: Dict[str, Any]):
        """Update embedding for a specific entity.
        
        Args:
            entity_id: UUID of the entity
            entity_type: Type of entity
            data: Entity data
        """
        text = self.extract_text_for_embedding(entity_type, data)
        if not text:
            logger.warning(f"No text extracted for {entity_type} {entity_id}")
            return
            
        try:
            embedding = await self.generate_embedding(text)
            
            # Update database based on entity type
            from app.services.database import get_supabase
            supabase = get_supabase()
            
            if entity_type == "scene_block":
                supabase.table("scene_blocks").update({
                    "embedding": embedding
                }).eq("id", entity_id).execute()
            elif entity_type == "entity":
                supabase.table("entities").update({
                    "embedding": embedding
                }).eq("id", entity_id).execute()
            elif entity_type == "knowledge_snapshot":
                supabase.table("knowledge_snapshots").update({
                    "embedding": embedding
                }).eq("id", entity_id).execute()
                
            logger.info(f"Updated embedding for {entity_type} {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to update embedding for {entity_type} {entity_id}: {e}")


# Global embedding service instance
embedding_service = EmbeddingService()