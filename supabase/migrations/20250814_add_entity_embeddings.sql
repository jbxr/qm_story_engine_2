-- Add embedding support to entities table for semantic search
-- This enables vector similarity search across characters, locations, artifacts, etc.

-- Add embedding column to entities table
ALTER TABLE entities ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- Create HNSW index for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_entities_embedding ON entities USING hnsw (embedding vector_cosine_ops);

-- Add embedding column to knowledge_snapshots table if not exists
ALTER TABLE knowledge_snapshots ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- Create HNSW index for knowledge_snapshots
CREATE INDEX IF NOT EXISTS idx_knowledge_snapshots_embedding ON knowledge_snapshots USING hnsw (embedding vector_cosine_ops);

-- Function to search entities by semantic similarity
CREATE OR REPLACE FUNCTION search_entities_by_embedding(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  name TEXT,
  entity_type TEXT,
  description TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    e.id,
    e.name,
    e.entity_type,
    e.description,
    e.metadata,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM entities e
  WHERE e.embedding IS NOT NULL
    AND (1 - (e.embedding <=> query_embedding)) > match_threshold
  ORDER BY (e.embedding <=> query_embedding) ASC
  LIMIT match_count;
END;
$$;

-- Function to search knowledge snapshots by semantic similarity
CREATE OR REPLACE FUNCTION search_knowledge_by_embedding(
  query_embedding VECTOR(1536),
  character_id UUID DEFAULT NULL,
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  character_id UUID,
  timeline_timestamp INT,
  knowledge_state JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    k.id,
    k.character_id,
    k.timeline_timestamp,
    k.knowledge_state,
    1 - (k.embedding <=> query_embedding) AS similarity
  FROM knowledge_snapshots k
  WHERE k.embedding IS NOT NULL
    AND (character_id IS NULL OR k.character_id = character_id)
    AND (1 - (k.embedding <=> query_embedding)) > match_threshold
  ORDER BY (k.embedding <=> query_embedding) ASC
  LIMIT match_count;
END;
$$;