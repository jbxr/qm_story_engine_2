create extension if not exists "vector" with schema "public" version '0.8.0';

create table "public"."dag_edges" (
    "id" uuid not null default gen_random_uuid(),
    "from_id" uuid not null,
    "to_id" uuid not null,
    "label" text,
    "metadata" jsonb,
    "created_at" timestamp without time zone default now()
);


create table "public"."entities" (
    "id" uuid not null default gen_random_uuid(),
    "name" text not null,
    "entity_type" text not null,
    "description" text,
    "metadata" jsonb,
    "created_at" timestamp without time zone default now(),
    "updated_at" timestamp without time zone default now()
);


create table "public"."knowledge_snapshots" (
    "id" uuid not null default gen_random_uuid(),
    "entity_id" uuid,
    "timestamp" integer,
    "knowledge" jsonb,
    "metadata" jsonb,
    "created_at" timestamp without time zone default now()
);


create table "public"."knowledge_snapshots_history" (
    "id" uuid not null,
    "entity_id" uuid,
    "timestamp" integer,
    "knowledge" jsonb,
    "metadata" jsonb,
    "valid_from" timestamp with time zone not null,
    "valid_to" timestamp with time zone,
    "sys_from" timestamp with time zone not null default now(),
    "sys_to" timestamp with time zone,
    "operation" text not null
);


create table "public"."milestones" (
    "id" uuid not null default gen_random_uuid(),
    "scene_id" uuid,
    "subject_id" uuid,
    "verb" text not null,
    "object_id" uuid,
    "description" text,
    "weight" double precision default 1.0,
    "metadata" jsonb,
    "created_at" timestamp without time zone default now()
);


create table "public"."relationships" (
    "id" uuid not null default gen_random_uuid(),
    "source_id" uuid,
    "target_id" uuid,
    "relation_type" text,
    "weight" double precision,
    "metadata" jsonb,
    "created_at" timestamp without time zone default now()
);


create table "public"."scene_blocks" (
    "id" uuid not null default gen_random_uuid(),
    "scene_id" uuid,
    "block_type" text not null,
    "order" integer not null,
    "content" text,
    "summary" text,
    "lines" jsonb,
    "subject_id" uuid,
    "verb" text,
    "object_id" uuid,
    "embedding" vector(1536),
    "weight" double precision,
    "metadata" jsonb,
    "created_at" timestamp without time zone default now(),
    "updated_at" timestamp without time zone default now()
);


create table "public"."scene_blocks_history" (
    "id" uuid not null,
    "scene_id" uuid,
    "block_type" text,
    "order" integer,
    "content" text,
    "summary" text,
    "lines" jsonb,
    "subject_id" uuid,
    "verb" text,
    "object_id" uuid,
    "embedding" vector(1536),
    "weight" double precision,
    "metadata" jsonb,
    "valid_from" timestamp with time zone not null,
    "valid_to" timestamp with time zone,
    "sys_from" timestamp with time zone not null default now(),
    "sys_to" timestamp with time zone,
    "operation" text not null
);


create table "public"."scenes" (
    "id" uuid not null default gen_random_uuid(),
    "title" text not null,
    "location_id" uuid,
    "timestamp" integer,
    "created_at" timestamp without time zone default now()
);


create table "public"."story_goals" (
    "id" uuid not null default gen_random_uuid(),
    "description" text,
    "subject_id" uuid,
    "verb" text,
    "object_id" uuid,
    "milestone_id" uuid,
    "created_at" timestamp without time zone default now()
);


create table "public"."timeline_events" (
    "id" uuid not null default gen_random_uuid(),
    "scene_id" uuid,
    "entity_id" uuid,
    "timestamp" integer,
    "summary" text,
    "metadata" jsonb,
    "created_at" timestamp without time zone default now()
);


CREATE UNIQUE INDEX dag_edges_pkey ON public.dag_edges USING btree (id);

CREATE UNIQUE INDEX entities_pkey ON public.entities USING btree (id);

CREATE INDEX idx_dag_edges_from_to ON public.dag_edges USING btree (from_id, to_id);

CREATE INDEX idx_entities_entity_type ON public.entities USING btree (entity_type);

CREATE INDEX idx_knowledge_snapshots_entity_time ON public.knowledge_snapshots USING btree (entity_id, "timestamp");

CREATE INDEX idx_milestones_scene ON public.milestones USING btree (scene_id);

CREATE INDEX idx_milestones_subject_object ON public.milestones USING btree (subject_id, object_id);

CREATE INDEX idx_relationships_source_target_type ON public.relationships USING btree (source_id, target_id, relation_type);

CREATE INDEX idx_scene_blocks_block_type ON public.scene_blocks USING btree (block_type);

CREATE INDEX idx_scene_blocks_embedding ON public.scene_blocks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_scene_blocks_scene_order ON public.scene_blocks USING btree (scene_id, "order");

CREATE INDEX idx_timeline_events_entity_time ON public.timeline_events USING btree (entity_id, "timestamp");

CREATE INDEX idx_timeline_events_scene ON public.timeline_events USING btree (scene_id);

CREATE UNIQUE INDEX knowledge_snapshots_history_pkey ON public.knowledge_snapshots_history USING btree (id, sys_from);

CREATE UNIQUE INDEX knowledge_snapshots_pkey ON public.knowledge_snapshots USING btree (id);

CREATE UNIQUE INDEX milestones_pkey ON public.milestones USING btree (id);

CREATE UNIQUE INDEX relationships_pkey ON public.relationships USING btree (id);

CREATE UNIQUE INDEX scene_blocks_history_pkey ON public.scene_blocks_history USING btree (id, sys_from);

CREATE UNIQUE INDEX scene_blocks_pkey ON public.scene_blocks USING btree (id);

CREATE UNIQUE INDEX scenes_pkey ON public.scenes USING btree (id);

CREATE UNIQUE INDEX story_goals_pkey ON public.story_goals USING btree (id);

CREATE UNIQUE INDEX timeline_events_pkey ON public.timeline_events USING btree (id);

alter table "public"."dag_edges" add constraint "dag_edges_pkey" PRIMARY KEY using index "dag_edges_pkey";

alter table "public"."entities" add constraint "entities_pkey" PRIMARY KEY using index "entities_pkey";

alter table "public"."knowledge_snapshots" add constraint "knowledge_snapshots_pkey" PRIMARY KEY using index "knowledge_snapshots_pkey";

alter table "public"."knowledge_snapshots_history" add constraint "knowledge_snapshots_history_pkey" PRIMARY KEY using index "knowledge_snapshots_history_pkey";

alter table "public"."milestones" add constraint "milestones_pkey" PRIMARY KEY using index "milestones_pkey";

alter table "public"."relationships" add constraint "relationships_pkey" PRIMARY KEY using index "relationships_pkey";

alter table "public"."scene_blocks" add constraint "scene_blocks_pkey" PRIMARY KEY using index "scene_blocks_pkey";

alter table "public"."scene_blocks_history" add constraint "scene_blocks_history_pkey" PRIMARY KEY using index "scene_blocks_history_pkey";

alter table "public"."scenes" add constraint "scenes_pkey" PRIMARY KEY using index "scenes_pkey";

alter table "public"."story_goals" add constraint "story_goals_pkey" PRIMARY KEY using index "story_goals_pkey";

alter table "public"."timeline_events" add constraint "timeline_events_pkey" PRIMARY KEY using index "timeline_events_pkey";

alter table "public"."knowledge_snapshots" add constraint "knowledge_snapshots_entity_id_fkey" FOREIGN KEY (entity_id) REFERENCES entities(id) not valid;

alter table "public"."knowledge_snapshots" validate constraint "knowledge_snapshots_entity_id_fkey";

alter table "public"."milestones" add constraint "milestones_object_id_fkey" FOREIGN KEY (object_id) REFERENCES entities(id) not valid;

alter table "public"."milestones" validate constraint "milestones_object_id_fkey";

alter table "public"."milestones" add constraint "milestones_scene_id_fkey" FOREIGN KEY (scene_id) REFERENCES scenes(id) not valid;

alter table "public"."milestones" validate constraint "milestones_scene_id_fkey";

alter table "public"."milestones" add constraint "milestones_subject_id_fkey" FOREIGN KEY (subject_id) REFERENCES entities(id) not valid;

alter table "public"."milestones" validate constraint "milestones_subject_id_fkey";

alter table "public"."relationships" add constraint "relationships_source_id_fkey" FOREIGN KEY (source_id) REFERENCES entities(id) not valid;

alter table "public"."relationships" validate constraint "relationships_source_id_fkey";

alter table "public"."relationships" add constraint "relationships_target_id_fkey" FOREIGN KEY (target_id) REFERENCES entities(id) not valid;

alter table "public"."relationships" validate constraint "relationships_target_id_fkey";

alter table "public"."scene_blocks" add constraint "scene_blocks_scene_id_fkey" FOREIGN KEY (scene_id) REFERENCES scenes(id) not valid;

alter table "public"."scene_blocks" validate constraint "scene_blocks_scene_id_fkey";

alter table "public"."scenes" add constraint "scenes_location_id_fkey" FOREIGN KEY (location_id) REFERENCES entities(id) not valid;

alter table "public"."scenes" validate constraint "scenes_location_id_fkey";

alter table "public"."story_goals" add constraint "story_goals_milestone_id_fkey" FOREIGN KEY (milestone_id) REFERENCES milestones(id) not valid;

alter table "public"."story_goals" validate constraint "story_goals_milestone_id_fkey";

alter table "public"."story_goals" add constraint "story_goals_object_id_fkey" FOREIGN KEY (object_id) REFERENCES entities(id) not valid;

alter table "public"."story_goals" validate constraint "story_goals_object_id_fkey";

alter table "public"."story_goals" add constraint "story_goals_subject_id_fkey" FOREIGN KEY (subject_id) REFERENCES entities(id) not valid;

alter table "public"."story_goals" validate constraint "story_goals_subject_id_fkey";

alter table "public"."timeline_events" add constraint "timeline_events_entity_id_fkey" FOREIGN KEY (entity_id) REFERENCES entities(id) not valid;

alter table "public"."timeline_events" validate constraint "timeline_events_entity_id_fkey";

alter table "public"."timeline_events" add constraint "timeline_events_scene_id_fkey" FOREIGN KEY (scene_id) REFERENCES scenes(id) not valid;

alter table "public"."timeline_events" validate constraint "timeline_events_scene_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.knowledge_snapshots_as_of(as_of timestamp with time zone)
 RETURNS TABLE(id uuid, entity_id uuid, "timestamp" integer, knowledge jsonb, metadata jsonb, created_at timestamp without time zone)
 LANGUAGE sql
 STABLE
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.match_scene_blocks(query_embedding vector, match_threshold double precision, match_count integer)
 RETURNS TABLE(id uuid, scene_id uuid, block_type text, "order" integer, content text, summary text, lines jsonb, subject_id uuid, verb text, object_id uuid, embedding vector, weight double precision, metadata jsonb, created_at timestamp without time zone, updated_at timestamp without time zone, similarity double precision)
 LANGUAGE sql
 STABLE
AS $function$
  SELECT
    id, scene_id, block_type, "order", content, summary, lines,
    subject_id, verb, object_id, embedding, weight, metadata, created_at, updated_at,
    1 - (embedding <=> query_embedding) AS similarity
  FROM scene_blocks
  WHERE embedding IS NOT NULL
    AND (1 - (embedding <=> query_embedding)) > match_threshold
  ORDER BY (embedding <=> query_embedding) ASC
  LIMIT match_count;
$function$
;

CREATE OR REPLACE FUNCTION public.scene_blocks_as_of(as_of timestamp with time zone)
 RETURNS TABLE(id uuid, scene_id uuid, block_type text, "order" integer, content text, summary text, lines jsonb, subject_id uuid, verb text, object_id uuid, embedding vector, weight double precision, metadata jsonb, created_at timestamp without time zone, updated_at timestamp without time zone)
 LANGUAGE sql
 STABLE
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.trg_knowledge_snapshots_history()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
END$function$
;

CREATE OR REPLACE FUNCTION public.trg_scene_blocks_history()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
END$function$
;

grant delete on table "public"."dag_edges" to "anon";

grant insert on table "public"."dag_edges" to "anon";

grant references on table "public"."dag_edges" to "anon";

grant select on table "public"."dag_edges" to "anon";

grant trigger on table "public"."dag_edges" to "anon";

grant truncate on table "public"."dag_edges" to "anon";

grant update on table "public"."dag_edges" to "anon";

grant delete on table "public"."dag_edges" to "authenticated";

grant insert on table "public"."dag_edges" to "authenticated";

grant references on table "public"."dag_edges" to "authenticated";

grant select on table "public"."dag_edges" to "authenticated";

grant trigger on table "public"."dag_edges" to "authenticated";

grant truncate on table "public"."dag_edges" to "authenticated";

grant update on table "public"."dag_edges" to "authenticated";

grant delete on table "public"."dag_edges" to "service_role";

grant insert on table "public"."dag_edges" to "service_role";

grant references on table "public"."dag_edges" to "service_role";

grant select on table "public"."dag_edges" to "service_role";

grant trigger on table "public"."dag_edges" to "service_role";

grant truncate on table "public"."dag_edges" to "service_role";

grant update on table "public"."dag_edges" to "service_role";

grant delete on table "public"."entities" to "anon";

grant insert on table "public"."entities" to "anon";

grant references on table "public"."entities" to "anon";

grant select on table "public"."entities" to "anon";

grant trigger on table "public"."entities" to "anon";

grant truncate on table "public"."entities" to "anon";

grant update on table "public"."entities" to "anon";

grant delete on table "public"."entities" to "authenticated";

grant insert on table "public"."entities" to "authenticated";

grant references on table "public"."entities" to "authenticated";

grant select on table "public"."entities" to "authenticated";

grant trigger on table "public"."entities" to "authenticated";

grant truncate on table "public"."entities" to "authenticated";

grant update on table "public"."entities" to "authenticated";

grant delete on table "public"."entities" to "service_role";

grant insert on table "public"."entities" to "service_role";

grant references on table "public"."entities" to "service_role";

grant select on table "public"."entities" to "service_role";

grant trigger on table "public"."entities" to "service_role";

grant truncate on table "public"."entities" to "service_role";

grant update on table "public"."entities" to "service_role";

grant delete on table "public"."knowledge_snapshots" to "anon";

grant insert on table "public"."knowledge_snapshots" to "anon";

grant references on table "public"."knowledge_snapshots" to "anon";

grant select on table "public"."knowledge_snapshots" to "anon";

grant trigger on table "public"."knowledge_snapshots" to "anon";

grant truncate on table "public"."knowledge_snapshots" to "anon";

grant update on table "public"."knowledge_snapshots" to "anon";

grant delete on table "public"."knowledge_snapshots" to "authenticated";

grant insert on table "public"."knowledge_snapshots" to "authenticated";

grant references on table "public"."knowledge_snapshots" to "authenticated";

grant select on table "public"."knowledge_snapshots" to "authenticated";

grant trigger on table "public"."knowledge_snapshots" to "authenticated";

grant truncate on table "public"."knowledge_snapshots" to "authenticated";

grant update on table "public"."knowledge_snapshots" to "authenticated";

grant delete on table "public"."knowledge_snapshots" to "service_role";

grant insert on table "public"."knowledge_snapshots" to "service_role";

grant references on table "public"."knowledge_snapshots" to "service_role";

grant select on table "public"."knowledge_snapshots" to "service_role";

grant trigger on table "public"."knowledge_snapshots" to "service_role";

grant truncate on table "public"."knowledge_snapshots" to "service_role";

grant update on table "public"."knowledge_snapshots" to "service_role";

grant delete on table "public"."knowledge_snapshots_history" to "anon";

grant insert on table "public"."knowledge_snapshots_history" to "anon";

grant references on table "public"."knowledge_snapshots_history" to "anon";

grant select on table "public"."knowledge_snapshots_history" to "anon";

grant trigger on table "public"."knowledge_snapshots_history" to "anon";

grant truncate on table "public"."knowledge_snapshots_history" to "anon";

grant update on table "public"."knowledge_snapshots_history" to "anon";

grant delete on table "public"."knowledge_snapshots_history" to "authenticated";

grant insert on table "public"."knowledge_snapshots_history" to "authenticated";

grant references on table "public"."knowledge_snapshots_history" to "authenticated";

grant select on table "public"."knowledge_snapshots_history" to "authenticated";

grant trigger on table "public"."knowledge_snapshots_history" to "authenticated";

grant truncate on table "public"."knowledge_snapshots_history" to "authenticated";

grant update on table "public"."knowledge_snapshots_history" to "authenticated";

grant delete on table "public"."knowledge_snapshots_history" to "service_role";

grant insert on table "public"."knowledge_snapshots_history" to "service_role";

grant references on table "public"."knowledge_snapshots_history" to "service_role";

grant select on table "public"."knowledge_snapshots_history" to "service_role";

grant trigger on table "public"."knowledge_snapshots_history" to "service_role";

grant truncate on table "public"."knowledge_snapshots_history" to "service_role";

grant update on table "public"."knowledge_snapshots_history" to "service_role";

grant delete on table "public"."milestones" to "anon";

grant insert on table "public"."milestones" to "anon";

grant references on table "public"."milestones" to "anon";

grant select on table "public"."milestones" to "anon";

grant trigger on table "public"."milestones" to "anon";

grant truncate on table "public"."milestones" to "anon";

grant update on table "public"."milestones" to "anon";

grant delete on table "public"."milestones" to "authenticated";

grant insert on table "public"."milestones" to "authenticated";

grant references on table "public"."milestones" to "authenticated";

grant select on table "public"."milestones" to "authenticated";

grant trigger on table "public"."milestones" to "authenticated";

grant truncate on table "public"."milestones" to "authenticated";

grant update on table "public"."milestones" to "authenticated";

grant delete on table "public"."milestones" to "service_role";

grant insert on table "public"."milestones" to "service_role";

grant references on table "public"."milestones" to "service_role";

grant select on table "public"."milestones" to "service_role";

grant trigger on table "public"."milestones" to "service_role";

grant truncate on table "public"."milestones" to "service_role";

grant update on table "public"."milestones" to "service_role";

grant delete on table "public"."relationships" to "anon";

grant insert on table "public"."relationships" to "anon";

grant references on table "public"."relationships" to "anon";

grant select on table "public"."relationships" to "anon";

grant trigger on table "public"."relationships" to "anon";

grant truncate on table "public"."relationships" to "anon";

grant update on table "public"."relationships" to "anon";

grant delete on table "public"."relationships" to "authenticated";

grant insert on table "public"."relationships" to "authenticated";

grant references on table "public"."relationships" to "authenticated";

grant select on table "public"."relationships" to "authenticated";

grant trigger on table "public"."relationships" to "authenticated";

grant truncate on table "public"."relationships" to "authenticated";

grant update on table "public"."relationships" to "authenticated";

grant delete on table "public"."relationships" to "service_role";

grant insert on table "public"."relationships" to "service_role";

grant references on table "public"."relationships" to "service_role";

grant select on table "public"."relationships" to "service_role";

grant trigger on table "public"."relationships" to "service_role";

grant truncate on table "public"."relationships" to "service_role";

grant update on table "public"."relationships" to "service_role";

grant delete on table "public"."scene_blocks" to "anon";

grant insert on table "public"."scene_blocks" to "anon";

grant references on table "public"."scene_blocks" to "anon";

grant select on table "public"."scene_blocks" to "anon";

grant trigger on table "public"."scene_blocks" to "anon";

grant truncate on table "public"."scene_blocks" to "anon";

grant update on table "public"."scene_blocks" to "anon";

grant delete on table "public"."scene_blocks" to "authenticated";

grant insert on table "public"."scene_blocks" to "authenticated";

grant references on table "public"."scene_blocks" to "authenticated";

grant select on table "public"."scene_blocks" to "authenticated";

grant trigger on table "public"."scene_blocks" to "authenticated";

grant truncate on table "public"."scene_blocks" to "authenticated";

grant update on table "public"."scene_blocks" to "authenticated";

grant delete on table "public"."scene_blocks" to "service_role";

grant insert on table "public"."scene_blocks" to "service_role";

grant references on table "public"."scene_blocks" to "service_role";

grant select on table "public"."scene_blocks" to "service_role";

grant trigger on table "public"."scene_blocks" to "service_role";

grant truncate on table "public"."scene_blocks" to "service_role";

grant update on table "public"."scene_blocks" to "service_role";

grant delete on table "public"."scene_blocks_history" to "anon";

grant insert on table "public"."scene_blocks_history" to "anon";

grant references on table "public"."scene_blocks_history" to "anon";

grant select on table "public"."scene_blocks_history" to "anon";

grant trigger on table "public"."scene_blocks_history" to "anon";

grant truncate on table "public"."scene_blocks_history" to "anon";

grant update on table "public"."scene_blocks_history" to "anon";

grant delete on table "public"."scene_blocks_history" to "authenticated";

grant insert on table "public"."scene_blocks_history" to "authenticated";

grant references on table "public"."scene_blocks_history" to "authenticated";

grant select on table "public"."scene_blocks_history" to "authenticated";

grant trigger on table "public"."scene_blocks_history" to "authenticated";

grant truncate on table "public"."scene_blocks_history" to "authenticated";

grant update on table "public"."scene_blocks_history" to "authenticated";

grant delete on table "public"."scene_blocks_history" to "service_role";

grant insert on table "public"."scene_blocks_history" to "service_role";

grant references on table "public"."scene_blocks_history" to "service_role";

grant select on table "public"."scene_blocks_history" to "service_role";

grant trigger on table "public"."scene_blocks_history" to "service_role";

grant truncate on table "public"."scene_blocks_history" to "service_role";

grant update on table "public"."scene_blocks_history" to "service_role";

grant delete on table "public"."scenes" to "anon";

grant insert on table "public"."scenes" to "anon";

grant references on table "public"."scenes" to "anon";

grant select on table "public"."scenes" to "anon";

grant trigger on table "public"."scenes" to "anon";

grant truncate on table "public"."scenes" to "anon";

grant update on table "public"."scenes" to "anon";

grant delete on table "public"."scenes" to "authenticated";

grant insert on table "public"."scenes" to "authenticated";

grant references on table "public"."scenes" to "authenticated";

grant select on table "public"."scenes" to "authenticated";

grant trigger on table "public"."scenes" to "authenticated";

grant truncate on table "public"."scenes" to "authenticated";

grant update on table "public"."scenes" to "authenticated";

grant delete on table "public"."scenes" to "service_role";

grant insert on table "public"."scenes" to "service_role";

grant references on table "public"."scenes" to "service_role";

grant select on table "public"."scenes" to "service_role";

grant trigger on table "public"."scenes" to "service_role";

grant truncate on table "public"."scenes" to "service_role";

grant update on table "public"."scenes" to "service_role";

grant delete on table "public"."story_goals" to "anon";

grant insert on table "public"."story_goals" to "anon";

grant references on table "public"."story_goals" to "anon";

grant select on table "public"."story_goals" to "anon";

grant trigger on table "public"."story_goals" to "anon";

grant truncate on table "public"."story_goals" to "anon";

grant update on table "public"."story_goals" to "anon";

grant delete on table "public"."story_goals" to "authenticated";

grant insert on table "public"."story_goals" to "authenticated";

grant references on table "public"."story_goals" to "authenticated";

grant select on table "public"."story_goals" to "authenticated";

grant trigger on table "public"."story_goals" to "authenticated";

grant truncate on table "public"."story_goals" to "authenticated";

grant update on table "public"."story_goals" to "authenticated";

grant delete on table "public"."story_goals" to "service_role";

grant insert on table "public"."story_goals" to "service_role";

grant references on table "public"."story_goals" to "service_role";

grant select on table "public"."story_goals" to "service_role";

grant trigger on table "public"."story_goals" to "service_role";

grant truncate on table "public"."story_goals" to "service_role";

grant update on table "public"."story_goals" to "service_role";

grant delete on table "public"."timeline_events" to "anon";

grant insert on table "public"."timeline_events" to "anon";

grant references on table "public"."timeline_events" to "anon";

grant select on table "public"."timeline_events" to "anon";

grant trigger on table "public"."timeline_events" to "anon";

grant truncate on table "public"."timeline_events" to "anon";

grant update on table "public"."timeline_events" to "anon";

grant delete on table "public"."timeline_events" to "authenticated";

grant insert on table "public"."timeline_events" to "authenticated";

grant references on table "public"."timeline_events" to "authenticated";

grant select on table "public"."timeline_events" to "authenticated";

grant trigger on table "public"."timeline_events" to "authenticated";

grant truncate on table "public"."timeline_events" to "authenticated";

grant update on table "public"."timeline_events" to "authenticated";

grant delete on table "public"."timeline_events" to "service_role";

grant insert on table "public"."timeline_events" to "service_role";

grant references on table "public"."timeline_events" to "service_role";

grant select on table "public"."timeline_events" to "service_role";

grant trigger on table "public"."timeline_events" to "service_role";

grant truncate on table "public"."timeline_events" to "service_role";

grant update on table "public"."timeline_events" to "service_role";

CREATE TRIGGER knowledge_snapshots_history_trg BEFORE INSERT OR DELETE OR UPDATE ON public.knowledge_snapshots FOR EACH ROW EXECUTE FUNCTION trg_knowledge_snapshots_history();

CREATE TRIGGER scene_blocks_history_trg BEFORE INSERT OR DELETE OR UPDATE ON public.scene_blocks FOR EACH ROW EXECUTE FUNCTION trg_scene_blocks_history();


