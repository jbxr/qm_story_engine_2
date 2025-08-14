-- QuantumMateria Story Engine - Seed Data Validation Script
-- This script validates all relationships and data integrity after loading seed.sql

-- =============================
-- DATA COUNT VALIDATION
-- =============================

SELECT 'ENTITIES' as table_name, count(*) as record_count FROM entities
UNION ALL
SELECT 'SCENES', count(*) FROM scenes  
UNION ALL
SELECT 'SCENE_BLOCKS', count(*) FROM scene_blocks
UNION ALL
SELECT 'MILESTONES', count(*) FROM milestones
UNION ALL
SELECT 'RELATIONSHIPS', count(*) FROM relationships
UNION ALL
SELECT 'KNOWLEDGE_SNAPSHOTS', count(*) FROM knowledge_snapshots
UNION ALL
SELECT 'TIMELINE_EVENTS', count(*) FROM timeline_events
UNION ALL
SELECT 'STORY_GOALS', count(*) FROM story_goals
UNION ALL
SELECT 'DAG_EDGES', count(*) FROM dag_edges
ORDER BY table_name;

-- =============================
-- ENTITY TYPE BREAKDOWN
-- =============================

SELECT 
    'Entity Types' as validation_category,
    entity_type,
    count(*) as count
FROM entities 
GROUP BY entity_type
ORDER BY entity_type;

-- =============================
-- FOREIGN KEY RELATIONSHIP VALIDATION
-- =============================

-- Validate scene_blocks reference valid scenes
SELECT 
    'Scene Block Relationships' as validation_category,
    'scene_blocks → scenes' as relationship_type,
    count(*) as valid_references,
    0 as invalid_references
FROM scene_blocks sb
JOIN scenes s ON sb.scene_id = s.id

UNION ALL

-- Check for orphaned scene_blocks (should be 0)
SELECT 
    'Scene Block Relationships',
    'orphaned scene_blocks',
    0,
    count(*)
FROM scene_blocks sb
LEFT JOIN scenes s ON sb.scene_id = s.id
WHERE s.id IS NULL

UNION ALL

-- Validate milestones reference valid scenes and entities
SELECT 
    'Milestone Relationships',
    'milestones → scenes',
    count(*),
    0
FROM milestones m
JOIN scenes s ON m.scene_id = s.id

UNION ALL

SELECT 
    'Milestone Relationships',
    'milestones → entities (subject)',
    count(*),
    0
FROM milestones m
JOIN entities e ON m.subject_id = e.id

UNION ALL

SELECT 
    'Milestone Relationships',
    'milestones → entities (object)',
    count(*),
    0
FROM milestones m
JOIN entities e ON m.object_id = e.id
WHERE m.object_id IS NOT NULL

UNION ALL

-- Validate relationships reference valid entities
SELECT 
    'Entity Relationships',
    'relationships → entities (source)',
    count(*),
    0
FROM relationships r
JOIN entities e ON r.source_id = e.id

UNION ALL

SELECT 
    'Entity Relationships',
    'relationships → entities (target)',
    count(*),
    0
FROM relationships r
JOIN entities e ON r.target_id = e.id

UNION ALL

-- Validate knowledge_snapshots reference valid entities
SELECT 
    'Knowledge Snapshots',
    'knowledge_snapshots → entities',
    count(*),
    0
FROM knowledge_snapshots ks
JOIN entities e ON ks.entity_id = e.id

UNION ALL

-- Validate timeline_events reference valid scenes and entities
SELECT 
    'Timeline Events',
    'timeline_events → scenes',
    count(*),
    0
FROM timeline_events te
JOIN scenes s ON te.scene_id = s.id
WHERE te.scene_id IS NOT NULL

UNION ALL

SELECT 
    'Timeline Events',
    'timeline_events → entities',
    count(*),
    0
FROM timeline_events te
JOIN entities e ON te.entity_id = e.id

UNION ALL

-- Validate story_goals reference valid entities
SELECT 
    'Story Goals',
    'story_goals → entities (subject)',
    count(*),
    0
FROM story_goals sg
JOIN entities e ON sg.subject_id = e.id
WHERE sg.subject_id IS NOT NULL

UNION ALL

SELECT 
    'Story Goals',
    'story_goals → entities (object)',
    count(*),
    0
FROM story_goals sg
JOIN entities e ON sg.object_id = e.id
WHERE sg.object_id IS NOT NULL

UNION ALL

-- Validate DAG edges reference valid entities
SELECT 
    'DAG Edges',
    'dag_edges → entities (from)',
    count(*),
    0
FROM dag_edges de
JOIN entities e ON de.from_id = e.id

UNION ALL

SELECT 
    'DAG Edges',
    'dag_edges → entities (to)',
    count(*),
    0
FROM dag_edges de
JOIN entities e ON de.to_id = e.id

ORDER BY validation_category, relationship_type;

-- =============================
-- STORY COHERENCE VALIDATION
-- =============================

-- Main characters in the story
SELECT 
    'Main Characters' as story_element,
    name,
    entity_type,
    (metadata->>'alignment') as alignment,
    (metadata->>'age')::int as age
FROM entities 
WHERE entity_type = 'character'
ORDER BY name;

-- Key artifacts and their owners/locations
SELECT 
    'Artifacts' as story_element,
    e.name as artifact_name,
    COALESCE(owner.name, 'Unknown') as current_owner,
    (e.metadata->>'status') as status
FROM entities e
LEFT JOIN relationships r ON e.id = r.target_id AND r.relation_type = 'possesses'
LEFT JOIN entities owner ON r.source_id = owner.id
WHERE e.entity_type = 'artifact'
ORDER BY e.name;

-- Scene progression timeline
SELECT 
    'Scene Timeline' as story_element,
    s.title,
    s.timestamp as story_time,
    l.name as location,
    count(sb.id) as scene_blocks
FROM scenes s
LEFT JOIN entities l ON s.location_id = l.id
LEFT JOIN scene_blocks sb ON s.id = sb.scene_id
GROUP BY s.id, s.title, s.timestamp, l.name
ORDER BY s.timestamp;

-- Character relationships at different time points
SELECT 
    'Relationship Evolution' as story_element,
    source.name as character1,
    target.name as character2,
    r.relation_type,
    r.weight,
    r.starts_at,
    r.ends_at
FROM relationships r
JOIN entities source ON r.source_id = source.id
JOIN entities target ON r.target_id = target.id
WHERE source.entity_type = 'character' 
  AND target.entity_type = 'character'
ORDER BY r.starts_at, source.name;

-- Knowledge evolution for main character
SELECT 
    'Knowledge Evolution' as story_element,
    e.name as character_name,
    ks.timestamp as time_point,
    (ks.knowledge->>'heritage') as heritage_knowledge,
    (ks.knowledge->>'mission') as mission_understanding,
    (ks.metadata->>'knowledge_level') as knowledge_level
FROM knowledge_snapshots ks
JOIN entities e ON ks.entity_id = e.id
WHERE e.name = 'Lyra Dawnweaver'
ORDER BY ks.timestamp;

-- =============================
-- ADVANCED RELATIONSHIP QUERIES
-- =============================

-- Test temporal relationship functions
SELECT 
    'Temporal Functions' as test_category,
    'relationships_active_at(2500)' as test_name,
    count(*) as result_count
FROM relationships_active_at(2500);

-- Test overlapping relationships
SELECT 
    'Temporal Functions' as test_category,
    'relationships_overlapping(1000,3000)' as test_name,
    count(*) as result_count
FROM relationships_overlapping(1000, 3000);

-- =============================
-- DATA QUALITY CHECKS
-- =============================

-- Check for duplicate UUIDs across all tables
WITH all_uuids AS (
    SELECT id, 'entities' as table_name FROM entities
    UNION ALL
    SELECT id, 'scenes' FROM scenes
    UNION ALL
    SELECT id, 'scene_blocks' FROM scene_blocks
    UNION ALL
    SELECT id, 'milestones' FROM milestones
    UNION ALL
    SELECT id, 'relationships' FROM relationships
    UNION ALL
    SELECT id, 'knowledge_snapshots' FROM knowledge_snapshots
    UNION ALL
    SELECT id, 'timeline_events' FROM timeline_events
    UNION ALL
    SELECT id, 'story_goals' FROM story_goals
    UNION ALL
    SELECT id, 'dag_edges' FROM dag_edges
),
uuid_counts AS (
    SELECT id, count(*) as usage_count
    FROM all_uuids
    GROUP BY id
    HAVING count(*) > 1
)
SELECT 
    'Data Quality' as check_category,
    'Duplicate UUIDs Found' as check_name,
    count(*) as issues_found
FROM uuid_counts;

-- Check for NULL values in required fields
SELECT 
    'Data Quality' as check_category,
    'Entities with NULL names' as check_name,
    count(*) as issues_found
FROM entities 
WHERE name IS NULL OR name = '';

-- Check scene blocks order consistency
WITH scene_order_gaps AS (
    SELECT 
        scene_id,
        "order",
        LAG("order") OVER (PARTITION BY scene_id ORDER BY "order") as prev_order
    FROM scene_blocks
),
order_issues AS (
    SELECT scene_id
    FROM scene_order_gaps
    WHERE prev_order IS NOT NULL AND "order" != prev_order + 1
)
SELECT 
    'Data Quality' as check_category,
    'Scene blocks order gaps' as check_name,
    count(DISTINCT scene_id) as issues_found
FROM order_issues;

-- =============================
-- JSONB METADATA VALIDATION
-- =============================

-- Validate character metadata structure
SELECT 
    'Metadata Validation' as check_category,
    'Characters missing age' as check_name,
    count(*) as issues_found
FROM entities 
WHERE entity_type = 'character' 
  AND (metadata->>'age') IS NULL;

-- Validate artifact metadata
SELECT 
    'Metadata Validation' as check_category,
    'Artifacts missing type' as check_name,
    count(*) as issues_found
FROM entities 
WHERE entity_type = 'artifact' 
  AND (metadata->>'type') IS NULL;

-- =============================
-- SUMMARY REPORT
-- =============================

SELECT 
    '=== SEED DATA VALIDATION COMPLETE ===' as status,
    'Total entities: ' || (SELECT count(*) FROM entities) as summary1,
    'Total scenes: ' || (SELECT count(*) FROM scenes) as summary2,
    'Total relationships: ' || (SELECT count(*) FROM relationships) as summary3,
    'Fantasy story: The Crown of Starlight' as summary4;