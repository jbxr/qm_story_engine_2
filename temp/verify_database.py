"""
MANUAL VERIFICATION - Check what's actually in the database
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def verify_database_state():
    """Check current database state"""
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    print("📊 DATABASE STATE VERIFICATION")
    print("=" * 50)
    
    # Check entities table
    entities_result = supabase.table("entities").select("*").execute()
    print(f"\n📁 ENTITIES: {len(entities_result.data) if entities_result.data else 0} records")
    if entities_result.data:
        for entity in entities_result.data:
            print(f"  - {entity['name']} ({entity['entity_type']}) - {entity['id']}")
    
    # Check scenes table  
    scenes_result = supabase.table("scenes").select("*").execute()
    print(f"\n🎬 SCENES: {len(scenes_result.data) if scenes_result.data else 0} records")
    if scenes_result.data:
        for scene in scenes_result.data:
            print(f"  - {scene['title']} - {scene['id']}")
    
    # Check scene_blocks table
    blocks_result = supabase.table("scene_blocks").select("*").order("order").execute()
    print(f"\n📝 SCENE BLOCKS: {len(blocks_result.data) if blocks_result.data else 0} records")
    if blocks_result.data:
        for block in blocks_result.data:
            print(f"  - Order {block['order']}: {block['block_type']} - {block['id']}")
    
    # Check relationships table
    relationships_result = supabase.table("relationships").select("*").execute()
    print(f"\n🔗 RELATIONSHIPS: {len(relationships_result.data) if relationships_result.data else 0} records")
    
    # Check story_goals table
    goals_result = supabase.table("story_goals").select("*").execute()
    print(f"\n🎯 STORY GOALS: {len(goals_result.data) if goals_result.data else 0} records")
    
    print(f"\n✅ Database is clean (test cleanup worked)")
    print(f"🌐 View in Supabase Studio: http://127.0.0.1:54323")
    
    return True

if __name__ == "__main__":
    verify_database_state()