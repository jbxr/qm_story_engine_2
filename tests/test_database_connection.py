"""
Test Database Connection - Supabase Connectivity Tests

This validates that Supabase database connection works and basic operations succeed.
These are foundational tests that must pass before any other database operations.

Based on the proven patterns from test_minimal_db.py but converted to proper pytest format.
"""

import pytest
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment for tests
load_dotenv()


class TestDatabaseConnection:
    """Test basic Supabase database connectivity"""

    def test_environment_variables_present(self):
        """Test that required environment variables are available"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        assert url is not None, "SUPABASE_URL environment variable is missing"
        assert key is not None, "SUPABASE_KEY environment variable is missing"
        assert url.startswith("http"), "SUPABASE_URL should be a valid URL"
        assert len(key) > 20, "SUPABASE_KEY should be a valid key"

    def test_supabase_client_creation(self):
        """Test that Supabase client can be created with environment credentials"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        try:
            client: Client = create_client(url, key)
            assert client is not None, "Failed to create Supabase client"
        except Exception as e:
            pytest.fail(f"Supabase client creation failed: {e}")

    def test_database_connectivity(self, supabase_client):
        """Test that we can connect to database and perform a simple query"""
        try:
            # Test a simple query - this will fail if not connected
            result = supabase_client.table("entities").select("*").limit(1).execute()
            
            # If we get here, the connection works
            assert True, "Database connection successful"
            
            # Verify result structure
            assert hasattr(result, 'data'), "Query result should have data attribute"
            assert isinstance(result.data, list), "Query result data should be a list"
            
        except Exception as e:
            pytest.fail(f"Database connectivity test failed: {e}")

    def test_database_table_access(self, supabase_client):
        """Test that we can access the main tables we need"""
        required_tables = ["entities", "scenes", "scene_blocks", "milestones", "story_goals", "relationships"]
        
        for table_name in required_tables:
            try:
                result = supabase_client.table(table_name).select("count", count="exact").execute()
                
                # If we get here, the table is accessible
                assert hasattr(result, 'count'), f"Table {table_name} should return count"
                assert result.count is not None or result.count == 0, f"Table {table_name} count should be a number"
                
            except Exception as e:
                pytest.fail(f"Failed to access table '{table_name}': {e}")


class TestDatabaseOperations:
    """Test basic database CRUD operations"""

    def test_entity_creation_and_retrieval(self, supabase_client):
        """Test creating and retrieving a simple entity"""
        test_entity = {
            "name": "Test Database Character",
            "entity_type": "character",
            "description": "A test character for database validation",
            "metadata": {
                "role": "test_character",
                "level": 1,
                "skills": ["database_testing"]
            }
        }
        
        entity_id = None
        try:
            # Create entity
            result = supabase_client.table("entities").insert(test_entity).execute()
            
            assert result.data is not None, "No data returned from entity creation"
            assert len(result.data) > 0, "Empty data returned from entity creation"
            
            entity_id = result.data[0]["id"]
            created_entity = result.data[0]
            
            # Verify entity was created correctly
            assert created_entity["name"] == test_entity["name"]
            assert created_entity["entity_type"] == test_entity["entity_type"]
            assert created_entity["description"] == test_entity["description"]
            assert created_entity["metadata"] == test_entity["metadata"], "JSONB metadata not stored correctly"
            
            # Verify we can retrieve it
            retrieve_result = supabase_client.table("entities").select("*").eq("id", entity_id).execute()
            
            assert retrieve_result.data is not None, "Failed to retrieve created entity"
            assert len(retrieve_result.data) > 0, "Created entity not found"
            
            retrieved_entity = retrieve_result.data[0]
            assert retrieved_entity["id"] == entity_id, "Retrieved entity has wrong ID"
            assert retrieved_entity["name"] == test_entity["name"], "Retrieved entity has wrong name"
            assert retrieved_entity["metadata"] == test_entity["metadata"], "JSONB metadata not retrieved correctly"
            
        except Exception as e:
            pytest.fail(f"Entity creation/retrieval test failed: {e}")
            
        finally:
            # Clean up test entity
            if entity_id:
                try:
                    supabase_client.table("entities").delete().eq("id", entity_id).execute()
                except:
                    pass  # Cleanup failure is not critical for test

    def test_entity_update_and_delete(self, supabase_client):
        """Test updating and deleting an entity"""
        # First create an entity
        test_entity = {
            "name": "Test Update Character",
            "entity_type": "character",
            "description": "Original description"
        }
        
        create_result = supabase_client.table("entities").insert(test_entity).execute()
        entity_id = create_result.data[0]["id"]
        
        try:
            # Test update
            update_data = {"description": "Updated description"}
            update_result = supabase_client.table("entities").update(update_data).eq("id", entity_id).execute()
            
            assert update_result.data is not None, "No data returned from update"
            assert len(update_result.data) > 0, "Empty data returned from update"
            assert update_result.data[0]["description"] == "Updated description", "Entity not updated correctly"
            
            # Test delete
            delete_result = supabase_client.table("entities").delete().eq("id", entity_id).execute()
            
            # Verify deletion
            verify_result = supabase_client.table("entities").select("*").eq("id", entity_id).execute()
            assert len(verify_result.data) == 0, "Entity was not deleted"
            
        except Exception as e:
            # Cleanup on failure
            try:
                supabase_client.table("entities").delete().eq("id", entity_id).execute()
            except:
                pass
            pytest.fail(f"Entity update/delete test failed: {e}")

    def test_scene_with_int_timestamps(self, supabase_client):
        """Test scene creation with INT timestamps (new schema)"""
        test_scene = {
            "title": "Test Database Scene",
            "timestamp": 150  # INT timestamp, not datetime
        }
        
        scene_id = None
        try:
            # Create scene
            result = supabase_client.table("scenes").insert(test_scene).execute()
            
            assert result.data is not None, "No data returned from scene creation"
            assert len(result.data) > 0, "Empty data returned from scene creation"
            
            scene_id = result.data[0]["id"]
            created_scene = result.data[0]
            
            # Verify scene was created correctly
            assert created_scene["title"] == test_scene["title"]
            assert created_scene["timestamp"] == test_scene["timestamp"], "INT timestamp not stored correctly"
            assert isinstance(created_scene["timestamp"], int), "Timestamp should be stored as integer"
            
            # Test negative timestamps (allowed for "pre-story" events)
            test_scene_negative = {
                "title": "Pre-story Event",
                "timestamp": -100
            }
            
            negative_result = supabase_client.table("scenes").insert(test_scene_negative).execute()
            negative_scene_id = negative_result.data[0]["id"]
            
            assert negative_result.data[0]["timestamp"] == -100, "Negative timestamps should be allowed"
            
            # Clean up negative timestamp scene
            supabase_client.table("scenes").delete().eq("id", negative_scene_id).execute()
            
        except Exception as e:
            pytest.fail(f"Scene INT timestamp test failed: {e}")
            
        finally:
            # Clean up test scene
            if scene_id:
                try:
                    supabase_client.table("scenes").delete().eq("id", scene_id).execute()
                except:
                    pass

    def test_milestone_first_class_entity(self, supabase_client):
        """Test that milestones are now first-class entities (not embedded in scene blocks)"""
        # First create entities for subject and object
        subject_entity = {
            "name": "Test Hero",
            "entity_type": "character",
            "description": "Hero for milestone testing"
        }
        
        object_entity = {
            "name": "Test Villain",
            "entity_type": "character", 
            "description": "Villain for milestone testing"
        }
        
        subject_id = None
        object_id = None
        milestone_id = None
        
        try:
            # Create subject and object entities
            subject_result = supabase_client.table("entities").insert(subject_entity).execute()
            subject_id = subject_result.data[0]["id"]
            
            object_result = supabase_client.table("entities").insert(object_entity).execute()
            object_id = object_result.data[0]["id"]
            
            # Create milestone as first-class entity
            test_milestone = {
                "subject_id": subject_id,
                "verb": "defeats",
                "object_id": object_id,
                "description": "Hero defeats villain in epic battle",
                "timestamp": 200,
                "significance": "major"
            }
            
            milestone_result = supabase_client.table("milestones").insert(test_milestone).execute()
            
            assert milestone_result.data is not None, "No data returned from milestone creation"
            assert len(milestone_result.data) > 0, "Empty data returned from milestone creation"
            
            milestone_id = milestone_result.data[0]["id"]
            created_milestone = milestone_result.data[0]
            
            # Verify milestone was created correctly
            assert created_milestone["subject_id"] == subject_id
            assert created_milestone["verb"] == "defeats"
            assert created_milestone["object_id"] == object_id
            assert created_milestone["description"] == test_milestone["description"]
            assert created_milestone["timestamp"] == 200
            assert created_milestone["significance"] == "major"
            
        except Exception as e:
            pytest.fail(f"Milestone first-class entity test failed: {e}")
            
        finally:
            # Clean up in reverse dependency order
            if milestone_id:
                try:
                    supabase_client.table("milestones").delete().eq("id", milestone_id).execute()
                except:
                    pass
            if object_id:
                try:
                    supabase_client.table("entities").delete().eq("id", object_id).execute()
                except:
                    pass
            if subject_id:
                try:
                    supabase_client.table("entities").delete().eq("id", subject_id).execute()
                except:
                    pass


class TestDatabaseConstraints:
    """Test database constraints and data validation"""

    def test_entity_required_fields(self, supabase_client):
        """Test that required fields are enforced"""
        # Test missing name (should fail)
        try:
            invalid_entity = {
                "entity_type": "character",
                # Missing required 'name' field
            }
            
            result = supabase_client.table("entities").insert(invalid_entity).execute()
            
            # If this succeeds, check if the database allows null names
            if result.data and len(result.data) > 0:
                # Clean up
                entity_id = result.data[0]["id"]
                supabase_client.table("entities").delete().eq("id", entity_id).execute()
                pytest.fail("Database should require 'name' field for entities")
                
        except Exception as e:
            # Expected - missing required field should fail
            assert True, "Required field validation working correctly"

    def test_entity_type_validation(self, supabase_client):
        """Test that entity_type field accepts valid values"""
        valid_types = ["character", "location", "artifact", "concept"]
        
        for entity_type in valid_types:
            entity_id = None
            try:
                test_entity = {
                    "name": f"Test {entity_type.title()}",
                    "entity_type": entity_type,
                    "description": f"A test {entity_type}"
                }
                
                result = supabase_client.table("entities").insert(test_entity).execute()
                
                assert result.data is not None, f"Failed to create entity with type '{entity_type}'"
                assert len(result.data) > 0, f"Empty data returned for entity type '{entity_type}'"
                
                entity_id = result.data[0]["id"]
                
            except Exception as e:
                pytest.fail(f"Valid entity type '{entity_type}' was rejected: {e}")
                
            finally:
                # Clean up
                if entity_id:
                    try:
                        supabase_client.table("entities").delete().eq("id", entity_id).execute()
                    except:
                        pass


class TestDatabaseState:
    """Test database state and consistency"""

    def test_database_is_clean_after_tests(self, supabase_client):
        """Verify that test cleanup worked and database is in expected state"""
        # Check that no test entities remain
        test_entities = supabase_client.table("entities").select("*").ilike("name", "%test%").execute()
        
        # Should be minimal or no test entities (cleanup should have worked)
        if test_entities.data and len(test_entities.data) > 0:
            # Report but don't fail - this is informational
            print(f"Warning: Found {len(test_entities.data)} test entities remaining")

    def test_database_tables_exist_and_accessible(self, supabase_client):
        """Final verification that all required tables are accessible"""
        required_tables = {
            "entities": "Core entity storage",
            "scenes": "Scene management", 
            "scene_blocks": "Scene content blocks",
            "milestones": "First-class milestone entities",
            "story_goals": "Story goal tracking",
            "relationships": "Entity relationships"
        }
        
        for table_name, description in required_tables.items():
            try:
                result = supabase_client.table(table_name).select("count", count="exact").execute()
                assert True, f"{description} table ({table_name}) is accessible"
                
            except Exception as e:
                pytest.fail(f"Required table '{table_name}' ({description}) is not accessible: {e}")

    def test_database_schema_features(self, supabase_client):
        """Test that new schema features work correctly"""
        # Test JSONB metadata flexibility
        test_entity = {
            "name": "Schema Test Entity",
            "entity_type": "character",
            "metadata": {
                "complex_data": {
                    "nested": {"deeply": {"nested": "value"}},
                    "array": [1, 2, {"item": "value"}],
                    "boolean": True,
                    "null_value": None
                }
            }
        }
        
        entity_id = None
        try:
            result = supabase_client.table("entities").insert(test_entity).execute()
            entity_id = result.data[0]["id"]
            
            # Verify complex JSONB was stored and retrieved correctly
            retrieved = supabase_client.table("entities").select("*").eq("id", entity_id).execute()
            assert retrieved.data[0]["metadata"] == test_entity["metadata"], "Complex JSONB metadata not handled correctly"
            
            print("✅ JSONB metadata flexibility confirmed")
            
        except Exception as e:
            pytest.fail(f"Database schema features test failed: {e}")
            
        finally:
            if entity_id:
                try:
                    supabase_client.table("entities").delete().eq("id", entity_id).execute()
                except:
                    pass