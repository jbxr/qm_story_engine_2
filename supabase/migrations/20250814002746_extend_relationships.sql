alter table "public"."relationships" add column "ends_at" integer;

alter table "public"."relationships" add column "starts_at" integer;

CREATE INDEX idx_relationships_temporal_lookup ON public.relationships USING btree (source_id, target_id, relation_type, starts_at, ends_at);

alter table "public"."relationships" add constraint "relationships_time_valid" CHECK (((ends_at IS NULL) OR (starts_at IS NULL) OR (starts_at <= ends_at))) not valid;

alter table "public"."relationships" validate constraint "relationships_time_valid";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.relationships_active_at(as_of integer)
 RETURNS TABLE(id uuid, source_id uuid, target_id uuid, relation_type text, weight double precision, starts_at integer, ends_at integer, metadata jsonb, created_at timestamp without time zone)
 LANGUAGE sql
 STABLE
AS $function$
  SELECT
    r.id, r.source_id, r.target_id, r.relation_type, r.weight,
    r.starts_at, r.ends_at, r.metadata, r.created_at
  FROM relationships r
  WHERE (r.starts_at IS NULL OR r.starts_at <= as_of)
    AND (r.ends_at IS NULL OR r.ends_at > as_of);
$function$
;

CREATE OR REPLACE FUNCTION public.relationships_overlapping(from_t integer, to_t integer)
 RETURNS TABLE(id uuid, source_id uuid, target_id uuid, relation_type text, weight double precision, starts_at integer, ends_at integer, metadata jsonb, created_at timestamp without time zone)
 LANGUAGE sql
 STABLE
AS $function$
  SELECT
    r.id, r.source_id, r.target_id, r.relation_type, r.weight,
    r.starts_at, r.ends_at, r.metadata, r.created_at
  FROM relationships r
  WHERE
    COALESCE(r.ends_at, 2147483647) > from_t
    AND COALESCE(r.starts_at, -2147483648) < to_t;
$function$
;


