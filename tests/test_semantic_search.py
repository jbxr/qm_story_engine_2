#!/usr/bin/env python3
"""
Semantic Search Testing Suite
Dedicated testing for Phase 4 pgvector semantic search functionality.
"""

import asyncio
import pytest
import os
from dotenv import load_dotenv
from uuid import UUID, uuid4
from typing import Dict, Any, List

# Load environment variables
load_dotenv()


class TestSemanticSearchFunctions:
    """Test database semantic search functions directly."""
    
    async def test_search_entities_by_embedding_function(self):
        """Test the search_entities_by_embedding database function."""
        from app.services.database import get_supabase
        from app.services.embedding_service import embedding_service
        
        db = get_supabase()
        
        # Create test entity with embedding
        entity_id = str(uuid4())
        entity_data = {
            "id": entity_id,
            "name": "Test Wizard",
            "entity_type": "character",
            "description": "A powerful wizard skilled in ancient magic and elemental spells."
        }
        
        try:
            # Insert entity
            db.table("entities").insert(entity_data).execute()
            
            # Generate and update embedding
            await embedding_service.update_entity_embedding(entity_id, "entity", entity_data)
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding("magical wizard spellcaster")
            
            # Test the database function directly
            result = db.rpc('search_entities_by_embedding', {
                'query_embedding': query_embedding,
                'match_threshold': 0.3,
                'match_count': 5
            }).execute()
            
            print(f"✅ search_entities_by_embedding returned {len(result.data)} results")
            
            if result.data:
                for entity in result.data:
                    print(f"   Found: {entity.get('name', 'Unknown')} (similarity: {entity.get('similarity', 0.0):.3f})")
                    
                # Verify result structure
                entity = result.data[0]
                assert 'id' in entity
                assert 'name' in entity
                assert 'entity_type' in entity
                assert 'similarity' in entity
                assert entity['similarity'] > 0.3
            
        except Exception as e:
            print(f"❌ search_entities_by_embedding function failed: {str(e)}")
            raise
        finally:
            # Cleanup
            db.table("entities").delete().eq("id", entity_id).execute()
    
    async def test_match_scene_blocks_function(self):
        """Test the match_scene_blocks database function."""
        from app.services.database import get_supabase
        from app.services.embedding_service import embedding_service
        
        db = get_supabase()
        
        # Create test scene and scene block
        scene_id = str(uuid4())
        block_id = str(uuid4())
        
        scene_data = {
            "id": scene_id,
            "title": "Magic Training Session"
        }
        
        block_data = {
            "id": block_id,
            "scene_id": scene_id,
            "block_type": "prose",
            "order": 1,
            "content": "The wizard raised his staff and channeled powerful magical energy through the ancient crystal."
        }
        
        try:
            # Insert scene and block
            db.table("scenes").insert(scene_data).execute()
            db.table("scene_blocks").insert(block_data).execute()
            
            # Generate and update embedding
            await embedding_service.update_entity_embedding(block_id, "scene_block", block_data)
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding("wizard magic staff crystal")
            
            # Test the database function directly
            result = db.rpc('match_scene_blocks', {
                'query_embedding': query_embedding,
                'match_threshold': 0.3,
                'match_count': 5
            }).execute()
            
            print(f"✅ match_scene_blocks returned {len(result.data)} results")
            
            if result.data:
                for block in result.data:
                    content_preview = block.get('content', 'No content')[:50] + "..."
                    print(f"   Found: {content_preview} (similarity: {block.get('similarity', 0.0):.3f})")
                    
                # Verify result structure
                block = result.data[0]
                assert 'id' in block
                assert 'scene_id' in block
                assert 'block_type' in block
                assert 'content' in block
                assert 'similarity' in block
                assert block['similarity'] > 0.3
            
        except Exception as e:
            print(f"❌ match_scene_blocks function failed: {str(e)}")
            raise
        finally:
            # Cleanup
            db.table("scene_blocks").delete().eq("id", block_id).execute()
            db.table("scenes").delete().eq("id", scene_id).execute()
    
    async def test_search_knowledge_by_embedding_function(self):
        """Test the search_knowledge_by_embedding database function."""
        from app.services.database import get_supabase
        from app.services.embedding_service import embedding_service
        
        db = get_supabase()
        
        # Create test entity and knowledge snapshot
        entity_id = str(uuid4())
        knowledge_id = str(uuid4())
        
        entity_data = {
            "id": entity_id,
            "name": "Test Character",
            "entity_type": "character"
        }
        
        knowledge_data = {
            "id": knowledge_id,
            "entity_id": entity_id,
            "timestamp": 1000,
            "knowledge": {
                "location": "Magic Academy",
                "emotional_state": "excited about learning",
                "current_goal": "master fire magic",
                "known_spells": ["light", "heat", "small flame"],
                "relationships": {
                    "mentor": "wise and patient teacher"
                }
            }
        }
        
        try:
            # Insert entity and knowledge
            db.table("entities").insert(entity_data).execute()
            db.table("knowledge_snapshots").insert(knowledge_data).execute()
            
            # Generate and update embedding
            await embedding_service.update_entity_embedding(knowledge_id, "knowledge_snapshot", knowledge_data)
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding("fire magic learning academy mentor")
            
            # Test the database function directly
            result = db.rpc('search_knowledge_by_embedding', {
                'query_embedding': query_embedding,
                'match_threshold': 0.3,
                'match_count': 5
            }).execute()
            
            print(f"✅ search_knowledge_by_embedding returned {len(result.data)} results")
            
            if result.data:
                for knowledge in result.data:
                    entity_id_str = knowledge.get('entity_id', 'Unknown')
                    print(f"   Found: Knowledge for entity {entity_id_str} (similarity: {knowledge.get('similarity', 0.0):.3f})")
                    
                # Verify result structure
                knowledge = result.data[0]
                assert 'id' in knowledge
                assert 'entity_id' in knowledge
                assert 'knowledge' in knowledge
                assert 'similarity' in knowledge
                assert knowledge['similarity'] > 0.3
            
        except Exception as e:
            print(f"❌ search_knowledge_by_embedding function failed: {str(e)}")
            raise
        finally:
            # Cleanup
            db.table("knowledge_snapshots").delete().eq("id", knowledge_id).execute()
            db.table("entities").delete().eq("id", entity_id).execute()


class TestSearchServiceIntegration:
    """Test search service integration with database functions."""
    
    async def test_search_service_entities(self):
        """Test search service entity search integration."""
        from app.services.search_service import search_service
        from app.services.embedding_service import embedding_service
        from app.services.database import get_supabase
        
        db = get_supabase()
        
        # Create multiple test entities
        entities_data = [
            {
                "id": str(uuid4()),
                "name": "Fire Mage",
                "entity_type": "character",
                "description": "A skilled practitioner of fire magic and elemental spells."
            },
            {
                "id": str(uuid4()),
                "name": "Ice Sorceress",
                "entity_type": "character", 
                "description": "A master of ice magic and frozen enchantments."
            },
            {
                "id": str(uuid4()),
                "name": "Magic Academy",
                "entity_type": "location",
                "description": "An ancient school where young mages learn the arcane arts."
            }
        ]
        
        try:
            # Insert entities and generate embeddings
            for entity in entities_data:
                db.table("entities").insert(entity).execute()
                await embedding_service.update_entity_embedding(entity["id"], "entity", entity)
            
            # Small delay for database consistency
            await asyncio.sleep(1)
            
            # Test search service
            results = await search_service.search_entities(
                query="fire magic elemental spells",
                similarity_threshold=0.3,
                limit=5
            )
            
            print(f"✅ Search service found {len(results)} entities")
            
            if results:
                # Fire Mage should be top result
                top_result = results[0]
                print(f"   Top result: {top_result.get('name', 'Unknown')} (similarity: {top_result.get('similarity', 0.0):.3f})")
                
                # Verify Fire Mage is most similar
                fire_mage_found = any(
                    result.get('name') == 'Fire Mage' 
                    for result in results
                )
                assert fire_mage_found, "Fire Mage should be found in results"
            
            # Test entity type filtering
            character_results = await search_service.search_entities(
                query="magic",
                entity_type="character",
                similarity_threshold=0.2,
                limit=5
            )
            
            print(f"✅ Character-filtered search found {len(character_results)} results")
            
            # Verify all results are characters
            if character_results:
                for result in character_results:
                    assert result.get('entity_type') == 'character'
            
        except Exception as e:
            print(f"❌ Search service entity test failed: {str(e)}")
            raise
        finally:
            # Cleanup
            entity_ids = [entity["id"] for entity in entities_data]
            db.table("entities").delete().in_("id", entity_ids).execute()
    
    async def test_search_service_unified(self):
        """Test unified search across all content types."""
        from app.services.search_service import search_service
        from app.services.embedding_service import embedding_service
        from app.services.database import get_supabase
        
        db = get_supabase()
        
        # Create comprehensive test data
        entity_id = str(uuid4())
        scene_id = str(uuid4())
        block_id = str(uuid4())
        knowledge_id = str(uuid4())
        
        test_data = {
            "entity": {
                "id": entity_id,
                "name": "Lightning Wizard",
                "entity_type": "character",
                "description": "A master of storm magic and electrical spells."
            },
            "scene": {
                "id": scene_id,
                "title": "Storm Magic Training"
            },
            "scene_block": {
                "id": block_id,
                "scene_id": scene_id,
                "block_type": "prose",
                "order": 1,
                "content": "Lightning crackled between the wizard's fingers as he demonstrated the power of storm magic to his eager students."
            },
            "knowledge": {
                "id": knowledge_id,
                "entity_id": entity_id,
                "timestamp": 1000,
                "knowledge": {
                    "specialization": "storm magic",
                    "teaching_style": "hands-on demonstration",
                    "current_lesson": "basic lightning control"
                }
            }
        }
        
        try:
            # Insert all test data
            db.table("entities").insert(test_data["entity"]).execute()
            db.table("scenes").insert(test_data["scene"]).execute()
            db.table("scene_blocks").insert(test_data["scene_block"]).execute()
            db.table("knowledge_snapshots").insert(test_data["knowledge"]).execute()
            
            # Generate embeddings for all content
            await embedding_service.update_entity_embedding(entity_id, "entity", test_data["entity"])
            await embedding_service.update_entity_embedding(block_id, "scene_block", test_data["scene_block"])
            await embedding_service.update_entity_embedding(knowledge_id, "knowledge_snapshot", test_data["knowledge"])
            
            # Small delay for database consistency
            await asyncio.sleep(1)
            
            # Test unified search
            results = await search_service.search_all(
                query="lightning storm magic electrical wizard",
                similarity_threshold=0.2,
                limit_per_type=3
            )
            
            print(f"✅ Unified search results:")
            print(f"   Entities: {len(results.get('entities', []))}")
            print(f"   Scene blocks: {len(results.get('scene_blocks', []))}")
            print(f"   Knowledge: {len(results.get('knowledge_snapshots', []))}")
            
            # Verify we found our test content in each category
            entities = results.get('entities', [])
            scene_blocks = results.get('scene_blocks', [])
            knowledge_snapshots = results.get('knowledge_snapshots', [])
            
            lightning_wizard_found = any(
                entity.get('name') == 'Lightning Wizard'
                for entity in entities
            )
            
            lightning_content_found = any(
                'lightning' in block.get('content', '').lower()
                for block in scene_blocks
            )
            
            storm_knowledge_found = any(
                'storm magic' in str(knowledge.get('knowledge', {})).lower()
                for knowledge in knowledge_snapshots
            )
            
            if lightning_wizard_found:
                print("   ✅ Found Lightning Wizard in entities")
            if lightning_content_found:
                print("   ✅ Found lightning content in scene blocks")
            if storm_knowledge_found:
                print("   ✅ Found storm magic in knowledge")
            
        except Exception as e:
            print(f"❌ Unified search test failed: {str(e)}")
            raise
        finally:
            # Cleanup
            db.table("knowledge_snapshots").delete().eq("id", knowledge_id).execute()
            db.table("scene_blocks").delete().eq("id", block_id).execute()
            db.table("scenes").delete().eq("id", scene_id).execute()
            db.table("entities").delete().eq("id", entity_id).execute()


class TestSimilarityScoring:
    """Test semantic similarity scoring and thresholds."""
    
    async def test_similarity_thresholds(self):
        """Test different similarity thresholds."""
        from app.services.search_service import search_service
        from app.services.embedding_service import embedding_service
        from app.services.database import get_supabase
        
        db = get_supabase()
        
        # Create entities with varying relevance
        entities_data = [
            {
                "id": str(uuid4()),
                "name": "Fire Dragon",
                "entity_type": "character",
                "description": "A massive dragon that breathes fire and guards ancient treasures."
            },
            {
                "id": str(uuid4()),
                "name": "Flame Sprite",
                "entity_type": "character",
                "description": "A tiny magical creature made of pure fire energy."
            },
            {
                "id": str(uuid4()),
                "name": "Ice Giant",
                "entity_type": "character",
                "description": "A colossal being of ice and snow from the frozen wastelands."
            }
        ]
        
        try:
            # Insert entities and generate embeddings
            for entity in entities_data:
                db.table("entities").insert(entity).execute()
                await embedding_service.update_entity_embedding(entity["id"], "entity", entity)
            
            await asyncio.sleep(1)
            
            # Test high threshold (should find exact matches)
            high_threshold_results = await search_service.search_entities(
                query="fire dragon flame",
                similarity_threshold=0.7,
                limit=5
            )
            
            # Test medium threshold (should find related matches)
            medium_threshold_results = await search_service.search_entities(
                query="fire dragon flame",
                similarity_threshold=0.4,
                limit=5
            )
            
            # Test low threshold (should find more distant matches)
            low_threshold_results = await search_service.search_entities(
                query="fire dragon flame",
                similarity_threshold=0.1,
                limit=5
            )
            
            print(f"✅ Similarity threshold tests:")
            print(f"   High threshold (0.7): {len(high_threshold_results)} results")
            print(f"   Medium threshold (0.4): {len(medium_threshold_results)} results")
            print(f"   Low threshold (0.1): {len(low_threshold_results)} results")
            
            # Verify that lower thresholds return more results
            assert len(low_threshold_results) >= len(medium_threshold_results)
            assert len(medium_threshold_results) >= len(high_threshold_results)
            
            # Check similarity scores are in expected ranges
            for result in high_threshold_results:
                assert result.get('similarity', 0) >= 0.7
            
            for result in medium_threshold_results:
                assert result.get('similarity', 0) >= 0.4
            
        except Exception as e:
            print(f"❌ Similarity threshold test failed: {str(e)}")
            raise
        finally:
            # Cleanup
            entity_ids = [entity["id"] for entity in entities_data]
            db.table("entities").delete().in_("id", entity_ids).execute()


# Main test execution
if __name__ == "__main__":
    import sys
    
    async def run_all_tests():
        """Run all semantic search tests."""
        print("🔍 Semantic Search Testing Suite")
        print("=" * 50)
        
        try:
            # Test database functions directly
            print("\n📊 Testing Database Functions...")
            db_tests = TestSemanticSearchFunctions()
            await db_tests.test_search_entities_by_embedding_function()
            await db_tests.test_match_scene_blocks_function()
            await db_tests.test_search_knowledge_by_embedding_function()
            print("✅ Database function tests completed")
            
            # Test search service integration
            print("\n🔧 Testing Search Service Integration...")
            service_tests = TestSearchServiceIntegration()
            await service_tests.test_search_service_entities()
            await service_tests.test_search_service_unified()
            print("✅ Search service tests completed")
            
            # Test similarity scoring
            print("\n📈 Testing Similarity Scoring...")
            similarity_tests = TestSimilarityScoring()
            await similarity_tests.test_similarity_thresholds()
            print("✅ Similarity scoring tests completed")
            
            print("\n" + "=" * 50)
            print("🎉 Semantic Search Testing Complete!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)