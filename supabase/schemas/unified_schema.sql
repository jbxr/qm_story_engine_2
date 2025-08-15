-- Unified QuantumMateria Story Engine Schema (Declarative)
-- Place this file in supabase/schemas/unified_schema.sql

-- =============================
-- EXTENSIONS
-- =============================
-- Required for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Required for VECTOR type and HNSW index
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================
-- ENTITIES
-- =============================
CREATE TABLE IF NOT EXISTS entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  entity_type TEXT NOT NULL, -- 'character', 'location', 'artifact', 'event', 'knowledge_fact'
  description TEXT,
  metadata JSONB,
  embedding VECTOR(1536), -- for semantic search
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_entities_entity_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_embedding ON entities USING hnsw (embedding vector_cosine_ops);

-- Semantic search function for entities
CREATE OR REPLACE FUNCTION search_entities_by_embedding(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10
) RETURNS TABLE (
  id UUID,
  name TEXT,
  entity_type TEXT,
  description TEXT,
  metadata JSONB,
  similarity FLOAT
) LANGUAGE sql STABLE AS $$
  SELECT
    e.id, e.name, e.entity_type, e.description, e.metadata,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM entities e
  WHERE e.embedding IS NOT NULL
    AND (1 - (e.embedding <=> query_embedding)) > match_threshold
  ORDER BY (e.embedding <=> query_embedding) ASC
  LIMIT match_count;
$$;

-- =============================
-- SCENES
-- =============================
CREATE TABLE IF NOT EXISTS scenes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  location_id UUID REFERENCES entities(id),
  "timestamp" INT,
  created_at TIMESTAMP DEFAULT now()
);

-- =============================
-- SCENE BLOCKS
-- =============================
CREATE TABLE IF NOT EXISTS scene_blocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id UUID REFERENCES scenes(id),
  block_type TEXT NOT NULL, -- 'prose', 'dialogue', 'milestone', etc.
  "order" INT NOT NULL,
  content TEXT,            -- prose
  summary TEXT,            -- dialogue
  lines JSONB,             -- dialogue lines
  subject_id UUID,         -- milestone
  verb TEXT,               -- milestone
  object_id UUID,          -- milestone
  embedding VECTOR(1536),  -- for semantic search
  weight FLOAT,            -- for causal/event significance
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_scene_blocks_scene_order ON scene_blocks(scene_id, "order");
CREATE INDEX IF NOT EXISTS idx_scene_blocks_embedding ON scene_blocks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_scene_blocks_block_type ON scene_blocks(block_type);

-- Semantic search function for scene_blocks
CREATE OR REPLACE FUNCTION match_scene_blocks(
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT
) RETURNS TABLE (
  id UUID,
  scene_id UUID,
  block_type TEXT,
  "order" INT,
  content TEXT,
  summary TEXT,
  lines JSONB,
  subject_id UUID,
  verb TEXT,
  object_id UUID,
  embedding VECTOR(1536),
  weight FLOAT,
  metadata JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  similarity FLOAT
) LANGUAGE sql STABLE AS $$
  SELECT
    id, scene_id, block_type, "order", content, summary, lines,
    subject_id, verb, object_id, embedding, weight, metadata, created_at, updated_at,
    1 - (embedding <=> query_embedding) AS similarity
  FROM scene_blocks
  WHERE embedding IS NOT NULL
    AND (1 - (embedding <=> query_embedding)) > match_threshold
  ORDER BY (embedding <=> query_embedding) ASC
  LIMIT match_count;
$$;

-- =============================
-- MILESTONES (EXPLICIT)
-- =============================
CREATE TABLE IF NOT EXISTS milestones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id UUID REFERENCES scenes(id),
  subject_id UUID REFERENCES entities(id),
  verb TEXT NOT NULL,
  object_id UUID REFERENCES entities(id),
  description TEXT,
  weight FLOAT DEFAULT 1.0,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_milestones_scene ON milestones(scene_id);
CREATE INDEX IF NOT EXISTS idx_milestones_subject_object ON milestones(subject_id, object_id);

-- =============================
-- DAG EDGES (EVENT GRAPH)
-- =============================
CREATE TABLE IF NOT EXISTS dag_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_id UUID NOT NULL,
  to_id UUID NOT NULL,
  label TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dag_edges_from_to ON dag_edges(from_id, to_id);

-- =============================
-- TIMELINE EVENTS
-- =============================
CREATE TABLE IF NOT EXISTS timeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id UUID REFERENCES scenes(id),
  entity_id UUID REFERENCES entities(id),
  "timestamp" INT,
  summary TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_timeline_events_scene ON timeline_events(scene_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_entity_time ON timeline_events(entity_id, "timestamp");

-- =============================
-- KNOWLEDGE SNAPSHOTS
-- =============================
CREATE TABLE IF NOT EXISTS knowledge_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id UUID REFERENCES entities(id),
  "timestamp" INT,
  knowledge JSONB, -- key-value store of what this entity knows at a given point
  metadata JSONB,
  embedding VECTOR(1536), -- for semantic search
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_snapshots_entity_time ON knowledge_snapshots(entity_id, "timestamp");
CREATE INDEX IF NOT EXISTS idx_knowledge_snapshots_embedding ON knowledge_snapshots USING hnsw (embedding vector_cosine_ops);

-- Semantic search function for knowledge snapshots
CREATE OR REPLACE FUNCTION search_knowledge_by_embedding(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10,
  filter_entity_id UUID DEFAULT NULL
) RETURNS TABLE (
  id UUID,
  entity_id UUID,
  "timestamp" INT,
  knowledge JSONB,
  metadata JSONB,
  similarity FLOAT
) LANGUAGE sql STABLE AS $$
  SELECT
    k.id, k.entity_id, k."timestamp", k.knowledge, k.metadata,
    1 - (k.embedding <=> query_embedding) AS similarity
  FROM knowledge_snapshots k
  WHERE k.embedding IS NOT NULL
    AND (filter_entity_id IS NULL OR k.entity_id = filter_entity_id)
    AND (1 - (k.embedding <=> query_embedding)) > match_threshold
  ORDER BY (k.embedding <=> query_embedding) ASC
  LIMIT match_count;
$$;

-- =============================
-- RELATIONSHIPS
-- =============================
CREATE TABLE IF NOT EXISTS relationships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID REFERENCES entities(id),
  target_id UUID REFERENCES entities(id),
  relation_type TEXT,
  weight FLOAT,
  starts_at INT,   -- inclusive story timeline start
  ends_at INT,     -- exclusive story timeline end (NULL = open-ended)
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now(),
  CONSTRAINT relationships_time_valid CHECK (ends_at IS NULL OR starts_at IS NULL OR starts_at <= ends_at)
);
CREATE INDEX IF NOT EXISTS idx_relationships_source_target_type ON relationships(source_id, target_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_relationships_temporal_lookup ON relationships(source_id, target_id, relation_type, starts_at, ends_at);

-- Temporal relationship query functions
CREATE OR REPLACE FUNCTION relationships_active_at(as_of INT)
RETURNS TABLE (
  id UUID,
  source_id UUID,
  target_id UUID,
  relation_type TEXT,
  weight FLOAT,
  starts_at INT,
  ends_at INT,
  metadata JSONB,
  created_at TIMESTAMP
) LANGUAGE sql STABLE AS $$
  SELECT
    r.id, r.source_id, r.target_id, r.relation_type, r.weight,
    r.starts_at, r.ends_at, r.metadata, r.created_at
  FROM relationships r
  WHERE (r.starts_at IS NULL OR r.starts_at <= as_of)
    AND (r.ends_at IS NULL OR r.ends_at > as_of);
$$;

CREATE OR REPLACE FUNCTION relationships_overlapping(from_t INT, to_t INT)
RETURNS TABLE (
  id UUID,
  source_id UUID,
  target_id UUID,
  relation_type TEXT,
  weight FLOAT,
  starts_at INT,
  ends_at INT,
  metadata JSONB,
  created_at TIMESTAMP
) LANGUAGE sql STABLE AS $$
  SELECT
    r.id, r.source_id, r.target_id, r.relation_type, r.weight,
    r.starts_at, r.ends_at, r.metadata, r.created_at
  FROM relationships r
  WHERE
    COALESCE(r.ends_at, 2147483647) > from_t
    AND COALESCE(r.starts_at, -2147483648) < to_t;
$$;

-- =============================
-- STORY GOALS
-- =============================
CREATE TABLE IF NOT EXISTS story_goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  description TEXT,
  subject_id UUID REFERENCES entities(id),
  verb TEXT,
  object_id UUID REFERENCES entities(id),
  milestone_id UUID REFERENCES milestones(id),
  created_at TIMESTAMP DEFAULT now()
);

-- =============================
-- NOTES
-- =============================
-- All extensible/optional/LLM-related fields should use metadata jsonb
-- Embedding and weight fields are present for semantic and causal analytics
-- Schema is designed for temporal queries, LLM workflows, and future expansion


/* ======================================================================
   LIGHTWEIGHT HISTORY (BITEMPORAL-LITE) FOR KEY TABLES
   - We capture previous versions on UPDATE/DELETE.
   - Columns:
       valid_from / valid_to : business/application time window
       sys_from   / sys_to   : system (transaction) time window
       operation             : 'I' | 'U' | 'D' (we emit on U/D by default)
   ====================================================================== */

-- =============================
-- HISTORY TABLES
-- =============================
CREATE TABLE IF NOT EXISTS scene_blocks_history (
  id UUID NOT NULL,
  scene_id UUID,
  block_type TEXT,
  "order" INT,
  content TEXT,
  summary TEXT,
  lines JSONB,
  subject_id UUID,
  verb TEXT,
  object_id UUID,
  embedding VECTOR(1536),
  weight FLOAT,
  metadata JSONB,
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to   TIMESTAMPTZ,
  sys_from   TIMESTAMPTZ NOT NULL DEFAULT now(),
  sys_to     TIMESTAMPTZ,
  operation  TEXT NOT NULL, -- 'I','U','D'
  PRIMARY KEY (id, sys_from)
);

CREATE TABLE IF NOT EXISTS knowledge_snapshots_history (
  id UUID NOT NULL,
  entity_id UUID,
  "timestamp" INT,
  knowledge JSONB,
  metadata JSONB,
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to   TIMESTAMPTZ,
  sys_from   TIMESTAMPTZ NOT NULL DEFAULT now(),
  sys_to     TIMESTAMPTZ,
  operation  TEXT NOT NULL,
  PRIMARY KEY (id, sys_from)
);

-- =============================
-- TRIGGER FUNCTIONS
-- =============================
CREATE OR REPLACE FUNCTION trg_scene_blocks_history()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    -- Write the OLD row as a closed history version up to now()
    INSERT INTO scene_blocks_history
      (id, scene_id, block_type, "order", content, summary, lines, subject_id, verb, object_id,
       embedding, weight, metadata, valid_from, valid_to, operation)
    VALUES
      (OLD.id, OLD.scene_id, OLD.block_type, OLD."order", OLD.content, OLD.summary, OLD.lines,
       OLD.subject_id, OLD.verb, OLD.object_id, OLD.embedding, OLD.weight, OLD.metadata,
       COALESCE(OLD.updated_at, OLD.created_at)::timestamptz, now(), 'U');

    NEW.updated_at := now();
    RETURN NEW;

  ELSIF TG_OP = 'DELETE' THEN
    -- Write the OLD row as a closed history version at deletion time
    INSERT INTO scene_blocks_history
      (id, scene_id, block_type, "order", content, summary, lines, subject_id, verb, object_id,
       embedding, weight, metadata, valid_from, valid_to, operation)
    VALUES
      (OLD.id, OLD.scene_id, OLD.block_type, OLD."order", OLD.content, OLD.summary, OLD.lines,
       OLD.subject_id, OLD.verb, OLD.object_id, OLD.embedding, OLD.weight, OLD.metadata,
       COALESCE(OLD.updated_at, OLD.created_at)::timestamptz, now(), 'D');

    RETURN OLD;

  ELSIF TG_OP = 'INSERT' THEN
    -- Keep base row; optionally emit 'I' history if you want full provenance
    NEW.created_at := now();
    RETURN NEW;
  END IF;
END$$;

CREATE OR REPLACE FUNCTION trg_knowledge_snapshots_history()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    INSERT INTO knowledge_snapshots_history
      (id, entity_id, "timestamp", knowledge, metadata,
       valid_from, valid_to, operation)
    VALUES
      (OLD.id, OLD.entity_id, OLD."timestamp", OLD.knowledge, OLD.metadata,
       COALESCE(OLD.created_at, now())::timestamptz, now(), 'U');

    RETURN NEW;

  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO knowledge_snapshots_history
      (id, entity_id, "timestamp", knowledge, metadata,
       valid_from, valid_to, operation)
    VALUES
      (OLD.id, OLD.entity_id, OLD."timestamp", OLD.knowledge, OLD.metadata,
       COALESCE(OLD.created_at, now())::timestamptz, now(), 'D');

    RETURN OLD;

  ELSIF TG_OP = 'INSERT' THEN
    NEW.created_at := now();
    RETURN NEW;
  END IF;
END$$;

-- =============================
-- TRIGGERS
-- =============================
DROP TRIGGER IF EXISTS scene_blocks_history_trg ON scene_blocks;
CREATE TRIGGER scene_blocks_history_trg
BEFORE INSERT OR UPDATE OR DELETE ON scene_blocks
FOR EACH ROW EXECUTE FUNCTION trg_scene_blocks_history();

DROP TRIGGER IF EXISTS knowledge_snapshots_history_trg ON knowledge_snapshots;
CREATE TRIGGER knowledge_snapshots_history_trg
BEFORE INSERT OR UPDATE OR DELETE ON knowledge_snapshots
FOR EACH ROW EXECUTE FUNCTION trg_knowledge_snapshots_history();


/* ======================================================================
   AS-OF QUERY HELPERS
   Postgres views cannot accept parameters, so we expose AS-OF functions
   that return table-shaped results for a given timestamptz.
   Logic:
     - Prefer the history row overlapping the AS-OF timestamp.
     - Otherwise, include current base rows created before AS-OF and
       with no overlapping history record.
   ====================================================================== */

-- =============================
-- AS-OF for scene_blocks
-- =============================
CREATE OR REPLACE FUNCTION scene_blocks_as_of(as_of TIMESTAMPTZ)
RETURNS TABLE (
  id UUID,
  scene_id UUID,
  block_type TEXT,
  "order" INT,
  content TEXT,
  summary TEXT,
  lines JSONB,
  subject_id UUID,
  verb TEXT,
  object_id UUID,
  embedding VECTOR(1536),
  weight FLOAT,
  metadata JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
) LANGUAGE sql STABLE AS $$
  WITH hist AS (
    SELECT
      h.id, h.scene_id, h.block_type, h."order", h.content, h.summary, h.lines,
      h.subject_id, h.verb, h.object_id, h.embedding, h.weight, h.metadata,
      NULL::TIMESTAMP AS created_at,
      NULL::TIMESTAMP AS updated_at
    FROM scene_blocks_history h
    WHERE h.valid_from <= as_of AND (h.valid_to IS NULL OR h.valid_to > as_of)
  ),
  live AS (
    SELECT
      b.id, b.scene_id, b.block_type, b."order", b.content, b.summary, b.lines,
      b.subject_id, b.verb, b.object_id, b.embedding, b.weight, b.metadata,
      b.created_at, b.updated_at
    FROM scene_blocks b
    WHERE b.created_at <= as_of
      AND NOT EXISTS (
        SELECT 1
        FROM scene_blocks_history h
        WHERE h.id = b.id
          AND h.valid_from <= as_of
          AND (h.valid_to IS NULL OR h.valid_to > as_of)
      )
  )
  SELECT * FROM hist
  UNION ALL
  SELECT * FROM live;
$$;

-- =============================
-- AS-OF for knowledge_snapshots
-- =============================
CREATE OR REPLACE FUNCTION knowledge_snapshots_as_of(as_of TIMESTAMPTZ)
RETURNS TABLE (
  id UUID,
  entity_id UUID,
  "timestamp" INT,
  knowledge JSONB,
  metadata JSONB,
  created_at TIMESTAMP
) LANGUAGE sql STABLE AS $$
  WITH hist AS (
    SELECT
      h.id, h.entity_id, h."timestamp", h.knowledge, h.metadata,
      NULL::TIMESTAMP AS created_at
    FROM knowledge_snapshots_history h
    WHERE h.valid_from <= as_of AND (h.valid_to IS NULL OR h.valid_to > as_of)
  ),
  live AS (
    SELECT
      k.id, k.entity_id, k."timestamp", k.knowledge, k.metadata, k.created_at
    FROM knowledge_snapshots k
    WHERE k.created_at <= as_of
      AND NOT EXISTS (
        SELECT 1
        FROM knowledge_snapshots_history h
        WHERE h.id = k.id
          AND h.valid_from <= as_of
          AND (h.valid_to IS NULL OR h.valid_to > as_of)
      )
  )
  SELECT * FROM hist
  UNION ALL
  SELECT * FROM live;
$$;

/* ======================================================================
   OPTIONAL: Emit INSERT history rows (provenance)
   If you want a full audit trail including first-version rows, uncomment:

-- In trg_scene_blocks_history():
--   ELSIF TG_OP = 'INSERT' THEN
--     NEW.created_at := now();
--     INSERT INTO scene_blocks_history (..., valid_from, valid_to, operation)
--     VALUES (..., NEW.created_at::timestamptz, NULL, 'I');
--     RETURN NEW;

-- In trg_knowledge_snapshots_history(): add similar 'I'.
   ====================================================================== */
