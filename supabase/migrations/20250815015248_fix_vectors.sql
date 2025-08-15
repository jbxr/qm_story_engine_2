drop function if exists "public"."search_knowledge_by_embedding"(query_embedding vector, character_id uuid, match_threshold double precision, match_count integer);

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.search_knowledge_by_embedding(query_embedding vector, match_threshold double precision DEFAULT 0.5, match_count integer DEFAULT 10, filter_entity_id uuid DEFAULT NULL::uuid)
 RETURNS TABLE(id uuid, entity_id uuid, "timestamp" integer, knowledge jsonb, metadata jsonb, similarity double precision)
 LANGUAGE sql
 STABLE
AS $function$
  SELECT
    k.id, k.entity_id, k."timestamp", k.knowledge, k.metadata,
    1 - (k.embedding <=> query_embedding) AS similarity
  FROM knowledge_snapshots k
  WHERE k.embedding IS NOT NULL
    AND (filter_entity_id IS NULL OR k.entity_id = filter_entity_id)
    AND (1 - (k.embedding <=> query_embedding)) > match_threshold
  ORDER BY (k.embedding <=> query_embedding) ASC
  LIMIT match_count;
$function$
;

CREATE OR REPLACE FUNCTION public.search_entities_by_embedding(query_embedding vector, match_threshold double precision DEFAULT 0.5, match_count integer DEFAULT 10)
 RETURNS TABLE(id uuid, name text, entity_type text, description text, metadata jsonb, similarity double precision)
 LANGUAGE sql
 STABLE
AS $function$
  SELECT
    e.id, e.name, e.entity_type, e.description, e.metadata,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM entities e
  WHERE e.embedding IS NOT NULL
    AND (1 - (e.embedding <=> query_embedding)) > match_threshold
  ORDER BY (e.embedding <=> query_embedding) ASC
  LIMIT match_count;
$function$
;


