"""
Phase 3 Performance Testing - Load and Performance Tests
Ensuring all Phase 3 systems perform well under load and stress conditions.

Target: 20+ performance tests covering scalability, response times, and resource usage
"""

import pytest
import time
import asyncio
import concurrent.futures
import psutil
import threading
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPhase3Performance:
    """Performance testing base class for Phase 3 systems"""
    
    def setup_method(self):
        """Setup performance test environment"""
        self.test_entities = {}
        self.test_relationships = {}
        self.test_knowledge = {}
        self.performance_metrics = {}
        
    def create_bulk_characters(self, count: int, prefix: str = "PerfTest") -> List[dict]:
        """Create multiple characters for performance testing"""
        characters = []
        start_time = time.time()
        
        for i in range(count):
            data = {
                "name": f"{prefix}_Character_{i:05d}",
                "entity_type": "character",
                "description": f"Performance test character {i}",
                "metadata": {"test": True, "performance_test": True, "batch": prefix}
            }
            response = client.post("/api/v1/entities/", json=data)
            assert response.status_code == 200
            characters.append(response.json()["data"]["entity"])
            
        creation_time = time.time() - start_time
        self.performance_metrics[f"create_{count}_characters"] = {
            "time": creation_time,
            "rate": count / creation_time if creation_time > 0 else float('inf')
        }
        
        return characters
        
    def create_bulk_relationships(self, characters: List[dict], 
                                relationship_count: int) -> List[dict]:
        """Create multiple relationships for performance testing"""
        relationships = []
        start_time = time.time()
        
        for i in range(relationship_count):
            char1 = characters[i % len(characters)]
            char2 = characters[(i + 1) % len(characters)]
            
            data = {
                "entity1_id": char1["id"],
                "entity2_id": char2["id"],
                "relationship_type": f"connection_{i % 5}",
                "timestamp_start": 1000 + i,
                "metadata": {"test": True, "performance_test": True}
            }
            response = client.post("/api/v1/relationships/", json=data)
            assert response.status_code == 200
            relationships.append(response.json()["data"]["relationship"])
            
        creation_time = time.time() - start_time
        self.performance_metrics[f"create_{relationship_count}_relationships"] = {
            "time": creation_time,
            "rate": relationship_count / creation_time if creation_time > 0 else float('inf')
        }
        
        return relationships
        
    def create_bulk_knowledge_snapshots(self, characters: List[dict], 
                                      snapshots_per_character: int) -> List[dict]:
        """Create multiple knowledge snapshots for performance testing"""
        snapshots = []
        start_time = time.time()
        
        for char in characters:
            for i in range(snapshots_per_character):
                data = {
                    "entity_id": char["id"],
                    "timestamp": 1000 + (i * 100),
                    "knowledge": {
                        "snapshot_number": i,
                        "character_name": char["name"],
                        "performance_test": True,
                        "complexity_level": i % 10,
                        "connections": list(range(min(i, 20)))  # Increasing complexity
                    },
                    "metadata": {"test": True, "performance_test": True}
                }
                response = client.post("/api/v1/knowledge/snapshots", json=data)
                assert response.status_code == 200
                snapshots.append(response.json()["data"]["snapshot"])
                
        creation_time = time.time() - start_time
        total_snapshots = len(characters) * snapshots_per_character
        self.performance_metrics[f"create_{total_snapshots}_knowledge_snapshots"] = {
            "time": creation_time,
            "rate": total_snapshots / creation_time if creation_time > 0 else float('inf')
        }
        
        return snapshots
        
    def measure_query_performance(self, query_func, query_name: str, 
                                iterations: int = 10) -> Dict[str, float]:
        """Measure query performance over multiple iterations"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            result = query_func()
            query_time = time.time() - start_time
            times.append(query_time)
            
            # Ensure we got a valid response
            if hasattr(result, 'status_code'):
                assert result.status_code == 200
                
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        metrics = {
            "average": avg_time,
            "minimum": min_time,
            "maximum": max_time,
            "iterations": iterations
        }
        
        self.performance_metrics[f"query_{query_name}"] = metrics
        return metrics


class TestEntityPerformance(TestPhase3Performance):
    """Performance tests for entity operations"""
    
    def test_bulk_entity_creation_performance(self):
        """Test: Performance of creating many entities"""
        test_sizes = [50, 100, 200]
        
        for size in test_sizes:
            characters = self.create_bulk_characters(size, f"Bulk_{size}")
            
            metrics = self.performance_metrics[f"create_{size}_characters"]
            print(f"Created {size} characters in {metrics['time']:.2f}s (rate: {metrics['rate']:.1f}/s)")
            
            # Performance assertions
            assert metrics["time"] < 60.0  # Should create even 200 characters in under 1 minute
            assert metrics["rate"] > 1.0   # Should create at least 1 character per second
            
    def test_entity_query_performance(self):
        """Test: Performance of entity queries with large datasets"""
        # Create test dataset
        characters = self.create_bulk_characters(100, "QueryTest")
        
        # Test different query types
        def list_all_entities():
            return client.get("/api/v1/entities/")
            
        def get_specific_entity():
            return client.get(f"/api/v1/entities/{characters[0]['id']}")
            
        def search_entities():
            return client.get("/api/v1/entities/?name=QueryTest")
            
        # Measure performance
        list_metrics = self.measure_query_performance(list_all_entities, "list_all_entities")
        get_metrics = self.measure_query_performance(get_specific_entity, "get_specific_entity")
        search_metrics = self.measure_query_performance(search_entities, "search_entities")
        
        print(f"List all entities: {list_metrics['average']:.3f}s avg")
        print(f"Get specific entity: {get_metrics['average']:.3f}s avg")
        print(f"Search entities: {search_metrics['average']:.3f}s avg")
        
        # Performance assertions
        assert list_metrics["average"] < 2.0  # List all under 2 seconds
        assert get_metrics["average"] < 0.1   # Get specific under 100ms
        assert search_metrics["average"] < 1.0  # Search under 1 second
        
    def test_concurrent_entity_operations(self):
        """Test: Performance under concurrent entity operations"""
        import threading
        
        def create_entities_batch(batch_id: int, count: int):
            """Create entities in a separate thread"""
            for i in range(count):
                data = {
                    "name": f"Concurrent_Batch_{batch_id}_Entity_{i}",
                    "entity_type": "character",
                    "description": f"Concurrent test entity {batch_id}-{i}",
                    "metadata": {"test": True, "concurrent_test": True, "batch": batch_id}
                }
                response = client.post("/api/v1/entities/", json=data)
                assert response.status_code == 200
                
        # Test concurrent creation
        start_time = time.time()
        threads = []
        
        for batch_id in range(5):  # 5 concurrent threads
            thread = threading.Thread(target=create_entities_batch, args=(batch_id, 20))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        concurrent_time = time.time() - start_time
        total_entities = 5 * 20  # 100 entities total
        
        print(f"Created {total_entities} entities concurrently in {concurrent_time:.2f}s")
        
        # Performance assertion
        assert concurrent_time < 120.0  # Should complete in under 2 minutes
        
        # Verify all entities were created
        response = client.get("/api/v1/entities/")
        assert response.status_code == 200
        entities = response.json()["data"]["entities"]
        concurrent_entities = [e for e in entities 
                             if e.get("metadata", {}).get("concurrent_test")]
        assert len(concurrent_entities) == total_entities


class TestRelationshipPerformance(TestPhase3Performance):
    """Performance tests for relationship operations"""
    
    def test_bulk_relationship_creation_performance(self):
        """Test: Performance of creating many relationships"""
        # Create characters first
        characters = self.create_bulk_characters(50, "RelTest")
        
        # Test different relationship counts
        test_sizes = [100, 250, 500]
        
        for size in test_sizes:
            relationships = self.create_bulk_relationships(characters, size)
            
            metrics = self.performance_metrics[f"create_{size}_relationships"]
            print(f"Created {size} relationships in {metrics['time']:.2f}s (rate: {metrics['rate']:.1f}/s)")
            
            # Performance assertions
            assert metrics["time"] < 120.0  # Should create even 500 relationships in under 2 minutes
            assert metrics["rate"] > 0.5    # Should create at least 0.5 relationships per second
            
    def test_relationship_query_performance(self):
        """Test: Performance of relationship queries with large datasets"""
        # Create test dataset
        characters = self.create_bulk_characters(30, "RelQueryTest")
        relationships = self.create_bulk_relationships(characters, 200)
        
        # Test different query types
        def list_all_relationships():
            return client.get("/api/v1/relationships/")
            
        def get_entity_relationships():
            return client.get(f"/api/v1/relationships/entity/{characters[0]['id']}")
            
        def get_active_relationships():
            return client.get("/api/v1/relationships/active?timestamp=1100")
            
        def get_relationship_graph():
            return client.get(f"/api/v1/relationships/graph/{characters[0]['id']}")
            
        # Measure performance
        list_metrics = self.measure_query_performance(list_all_relationships, "list_all_relationships")
        entity_metrics = self.measure_query_performance(get_entity_relationships, "get_entity_relationships")
        active_metrics = self.measure_query_performance(get_active_relationships, "get_active_relationships")
        graph_metrics = self.measure_query_performance(get_relationship_graph, "get_relationship_graph")
        
        print(f"List all relationships: {list_metrics['average']:.3f}s avg")
        print(f"Get entity relationships: {entity_metrics['average']:.3f}s avg")
        print(f"Get active relationships: {active_metrics['average']:.3f}s avg")
        print(f"Get relationship graph: {graph_metrics['average']:.3f}s avg")
        
        # Performance assertions
        assert list_metrics["average"] < 3.0   # List all under 3 seconds
        assert entity_metrics["average"] < 0.5  # Entity relationships under 500ms
        assert active_metrics["average"] < 1.0  # Active relationships under 1 second
        assert graph_metrics["average"] < 2.0   # Relationship graph under 2 seconds
        
    def test_temporal_relationship_query_performance(self):
        """Test: Performance of temporal relationship queries"""
        # Create test data with temporal relationships
        characters = self.create_bulk_characters(20, "TemporalTest")
        
        # Create relationships across different time periods
        relationships = []
        for i in range(100):
            char1 = characters[i % len(characters)]
            char2 = characters[(i + 1) % len(characters)]
            
            start_time = 1000 + (i * 10)
            end_time = start_time + 50 if i % 3 == 0 else None  # Some relationships end
            
            data = {
                "entity1_id": char1["id"],
                "entity2_id": char2["id"],
                "relationship_type": "temporal_connection",
                "timestamp_start": start_time,
                "metadata": {"test": True, "temporal_test": True}
            }
            if end_time:
                data["timestamp_end"] = end_time
                
            response = client.post("/api/v1/relationships/", json=data)
            assert response.status_code == 200
            relationships.append(response.json()["data"]["relationship"])
            
        # Test temporal queries at different timestamps
        test_timestamps = [1100, 1500, 2000, 2500]
        
        for timestamp in test_timestamps:
            def query_at_timestamp():
                return client.get(f"/api/v1/relationships/active?timestamp={timestamp}")
                
            metrics = self.measure_query_performance(
                query_at_timestamp, f"temporal_query_{timestamp}", iterations=5
            )
            
            print(f"Temporal query at {timestamp}: {metrics['average']:.3f}s avg")
            
            # Performance assertion
            assert metrics["average"] < 1.0  # Temporal queries under 1 second


class TestKnowledgePerformance(TestPhase3Performance):
    """Performance tests for knowledge operations"""
    
    def test_bulk_knowledge_creation_performance(self):
        """Test: Performance of creating many knowledge snapshots"""
        # Create characters first
        characters = self.create_bulk_characters(25, "KnowledgeTest")
        
        # Test different knowledge snapshot densities
        test_configs = [
            (10, "Low density"),     # 10 snapshots per character
            (25, "Medium density"),  # 25 snapshots per character
            (50, "High density")     # 50 snapshots per character
        ]
        
        for snapshots_per_char, description in test_configs:
            snapshots = self.create_bulk_knowledge_snapshots(characters, snapshots_per_char)
            
            total_snapshots = len(characters) * snapshots_per_char
            metrics = self.performance_metrics[f"create_{total_snapshots}_knowledge_snapshots"]
            
            print(f"{description}: Created {total_snapshots} snapshots in {metrics['time']:.2f}s (rate: {metrics['rate']:.1f}/s)")
            
            # Performance assertions
            assert metrics["time"] < 180.0  # Should create even high density in under 3 minutes
            assert metrics["rate"] > 1.0    # Should create at least 1 snapshot per second
            
    def test_knowledge_query_performance(self):
        """Test: Performance of knowledge queries with large datasets"""
        # Create test dataset
        characters = self.create_bulk_characters(20, "KnowledgeQueryTest")
        snapshots = self.create_bulk_knowledge_snapshots(characters, 30)
        
        # Test different query types
        def get_character_knowledge():
            return client.get(f"/api/v1/knowledge/snapshots/character/{characters[0]['id']}")
            
        def get_knowledge_with_timestamp():
            return client.get(f"/api/v1/knowledge/snapshots/character/{characters[0]['id']}?timestamp=1500")
            
        def get_specific_snapshot():
            return client.get(f"/api/v1/knowledge/snapshots/{snapshots[0]['id']}")
            
        # Measure performance
        char_metrics = self.measure_query_performance(get_character_knowledge, "get_character_knowledge")
        timestamp_metrics = self.measure_query_performance(get_knowledge_with_timestamp, "get_knowledge_with_timestamp")
        specific_metrics = self.measure_query_performance(get_specific_snapshot, "get_specific_snapshot")
        
        print(f"Get character knowledge: {char_metrics['average']:.3f}s avg")
        print(f"Get knowledge with timestamp: {timestamp_metrics['average']:.3f}s avg")
        print(f"Get specific snapshot: {specific_metrics['average']:.3f}s avg")
        
        # Performance assertions
        assert char_metrics["average"] < 1.0      # Character knowledge under 1 second
        assert timestamp_metrics["average"] < 0.5  # Timestamp query under 500ms
        assert specific_metrics["average"] < 0.1   # Specific snapshot under 100ms
        
    def test_knowledge_temporal_performance(self):
        """Test: Performance of temporal knowledge queries"""
        # Create character with many temporal snapshots
        character = self.create_bulk_characters(1, "TemporalKnowledge")[0]
        
        # Create snapshots across a wide time range
        snapshots = []
        for i in range(200):  # 200 snapshots across time
            timestamp = 1000 + (i * 100)  # Every 100 time units
            
            data = {
                "entity_id": character["id"],
                "timestamp": timestamp,
                "knowledge": {
                    "timeline_position": i,
                    "era": f"era_{i // 50}",
                    "accumulated_knowledge": list(range(i)),  # Growing knowledge base
                    "complexity": min(i, 100)
                },
                "metadata": {"test": True, "temporal_performance_test": True}
            }
            response = client.post("/api/v1/knowledge/snapshots", json=data)
            assert response.status_code == 200
            snapshots.append(response.json()["data"]["snapshot"])
            
        # Test temporal queries at various points
        test_timestamps = [2000, 5000, 10000, 15000, 20000]
        
        for timestamp in test_timestamps:
            def query_knowledge_at_timestamp():
                return client.get(f"/api/v1/knowledge/snapshots/character/{character['id']}?timestamp={timestamp}")
                
            metrics = self.measure_query_performance(
                query_knowledge_at_timestamp, f"temporal_knowledge_{timestamp}", iterations=5
            )
            
            print(f"Knowledge temporal query at {timestamp}: {metrics['average']:.3f}s avg")
            
            # Performance assertion
            assert metrics["average"] < 0.5  # Temporal knowledge queries under 500ms


class TestIntegratedSystemPerformance(TestPhase3Performance):
    """Performance tests for integrated Phase 3 systems"""
    
    def test_full_story_world_creation_performance(self):
        """Test: Performance of creating a complete story world"""
        start_time = time.time()
        
        # Create characters (50)
        characters = self.create_bulk_characters(50, "StoryWorld")
        characters_time = time.time() - start_time
        
        # Create relationships (200)
        start_time = time.time()
        relationships = self.create_bulk_relationships(characters, 200)
        relationships_time = time.time() - start_time
        
        # Create knowledge snapshots (500 total - 10 per character)
        start_time = time.time()
        snapshots = self.create_bulk_knowledge_snapshots(characters, 10)
        knowledge_time = time.time() - start_time
        
        # Create scenes
        start_time = time.time()
        scenes = []
        for i in range(25):  # 25 scenes
            data = {
                "title": f"StoryWorld_Scene_{i:03d}",
                "description": f"Performance test scene {i}",
                "timestamp": 1000 + (i * 200),
                "metadata": {"test": True, "story_world_test": True}
            }
            response = client.post("/api/v1/scenes/", json=data)
            assert response.status_code == 200
            scenes.append(response.json()["data"]["scene"])
        scenes_time = time.time() - start_time
        
        total_time = characters_time + relationships_time + knowledge_time + scenes_time
        
        print(f"Complete story world creation:")
        print(f"  Characters (50): {characters_time:.2f}s")
        print(f"  Relationships (200): {relationships_time:.2f}s")
        print(f"  Knowledge (500): {knowledge_time:.2f}s")
        print(f"  Scenes (25): {scenes_time:.2f}s")
        print(f"  Total: {total_time:.2f}s")
        
        # Performance assertions
        assert total_time < 300.0  # Complete story world in under 5 minutes
        assert len(characters) == 50
        assert len(relationships) == 200
        assert len(snapshots) == 500
        assert len(scenes) == 25
        
    def test_story_world_query_performance(self):
        """Test: Performance of querying a complete story world"""
        # Create story world (smaller for query testing)
        characters = self.create_bulk_characters(20, "QueryWorld")
        relationships = self.create_bulk_relationships(characters, 80)
        snapshots = self.create_bulk_knowledge_snapshots(characters, 5)
        
        # Test comprehensive story world queries
        def query_all_entities():
            return client.get("/api/v1/entities/")
            
        def query_all_relationships():
            return client.get("/api/v1/relationships/")
            
        def query_character_full_profile():
            char_id = characters[0]["id"]
            # Get character, their relationships, and knowledge
            char_response = client.get(f"/api/v1/entities/{char_id}")
            rel_response = client.get(f"/api/v1/relationships/entity/{char_id}")
            knowledge_response = client.get(f"/api/v1/knowledge/snapshots/character/{char_id}")
            return char_response  # Just return one for timing
            
        def query_story_at_timestamp():
            timestamp = 1500
            return client.get(f"/api/v1/relationships/active?timestamp={timestamp}")
            
        # Measure performance
        entities_metrics = self.measure_query_performance(query_all_entities, "query_all_entities")
        relationships_metrics = self.measure_query_performance(query_all_relationships, "query_all_relationships")
        profile_metrics = self.measure_query_performance(query_character_full_profile, "query_character_profile")
        story_metrics = self.measure_query_performance(query_story_at_timestamp, "query_story_at_timestamp")
        
        print(f"Story world query performance:")
        print(f"  All entities: {entities_metrics['average']:.3f}s avg")
        print(f"  All relationships: {relationships_metrics['average']:.3f}s avg")
        print(f"  Character profile: {profile_metrics['average']:.3f}s avg")
        print(f"  Story at timestamp: {story_metrics['average']:.3f}s avg")
        
        # Performance assertions
        assert entities_metrics["average"] < 1.0     # All entities under 1 second
        assert relationships_metrics["average"] < 2.0  # All relationships under 2 seconds
        assert profile_metrics["average"] < 0.5      # Character profile under 500ms
        assert story_metrics["average"] < 1.0        # Story query under 1 second
        
    def test_concurrent_mixed_operations_performance(self):
        """Test: Performance under concurrent mixed operations (read/write)"""
        import threading
        import random
        
        # Create initial dataset
        characters = self.create_bulk_characters(30, "ConcurrentTest")
        
        # Results tracking
        results = {"reads": 0, "writes": 0, "errors": 0}
        results_lock = threading.Lock()
        
        def mixed_operations_worker(worker_id: int, duration: int):
            """Worker that performs mixed read/write operations"""
            end_time = time.time() + duration
            
            while time.time() < end_time:
                try:
                    operation = random.choice(["read_entity", "read_relationships", "write_relationship", "write_knowledge"])
                    
                    if operation == "read_entity":
                        char = random.choice(characters)
                        response = client.get(f"/api/v1/entities/{char['id']}")
                        with results_lock:
                            results["reads"] += 1
                            
                    elif operation == "read_relationships":
                        char = random.choice(characters)
                        response = client.get(f"/api/v1/relationships/entity/{char['id']}")
                        with results_lock:
                            results["reads"] += 1
                            
                    elif operation == "write_relationship":
                        char1 = random.choice(characters)
                        char2 = random.choice(characters)
                        if char1["id"] != char2["id"]:
                            data = {
                                "entity1_id": char1["id"],
                                "entity2_id": char2["id"],
                                "relationship_type": f"concurrent_{worker_id}",
                                "timestamp_start": int(time.time() * 1000),
                                "metadata": {"concurrent_test": True, "worker": worker_id}
                            }
                            response = client.post("/api/v1/relationships/", json=data)
                            with results_lock:
                                results["writes"] += 1
                                
                    elif operation == "write_knowledge":
                        char = random.choice(characters)
                        data = {
                            "entity_id": char["id"],
                            "timestamp": int(time.time() * 1000),
                            "knowledge": {
                                "worker_id": worker_id,
                                "operation_time": time.time(),
                                "concurrent_test": True
                            },
                            "metadata": {"concurrent_test": True, "worker": worker_id}
                        }
                        response = client.post("/api/v1/knowledge/snapshots", json=data)
                        with results_lock:
                            results["writes"] += 1
                            
                    # Small delay to avoid overwhelming the system
                    time.sleep(0.01)
                    
                except Exception as e:
                    with results_lock:
                        results["errors"] += 1
                        
        # Run concurrent workers
        start_time = time.time()
        workers = []
        num_workers = 8
        duration = 30  # 30 seconds of concurrent operations
        
        for worker_id in range(num_workers):
            worker = threading.Thread(target=mixed_operations_worker, args=(worker_id, duration))
            workers.append(worker)
            worker.start()
            
        for worker in workers:
            worker.join()
            
        actual_duration = time.time() - start_time
        
        print(f"Concurrent mixed operations ({duration}s with {num_workers} workers):")
        print(f"  Total reads: {results['reads']}")
        print(f"  Total writes: {results['writes']}")
        print(f"  Total errors: {results['errors']}")
        print(f"  Read rate: {results['reads'] / actual_duration:.1f} ops/sec")
        print(f"  Write rate: {results['writes'] / actual_duration:.1f} ops/sec")
        print(f"  Error rate: {results['errors'] / (results['reads'] + results['writes']) * 100:.1f}%")
        
        # Performance assertions
        assert results["errors"] < (results["reads"] + results["writes"]) * 0.05  # Less than 5% error rate
        assert (results["reads"] + results["writes"]) > 100  # Should complete at least 100 operations
        assert results["reads"] > 0 and results["writes"] > 0  # Both read and write operations should occur


class TestMemoryAndResourcePerformance(TestPhase3Performance):
    """Performance tests for memory usage and resource consumption"""
    
    def test_memory_usage_under_load(self):
        """Test: Memory usage during bulk operations"""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Initial memory usage: {initial_memory:.1f} MB")
        
        # Create large dataset and monitor memory
        memory_measurements = []
        
        # Phase 1: Create characters
        characters = self.create_bulk_characters(100, "MemoryTest")
        memory_after_entities = process.memory_info().rss / 1024 / 1024
        memory_measurements.append(("After 100 entities", memory_after_entities))
        
        # Phase 2: Create relationships
        relationships = self.create_bulk_relationships(characters, 500)
        memory_after_relationships = process.memory_info().rss / 1024 / 1024
        memory_measurements.append(("After 500 relationships", memory_after_relationships))
        
        # Phase 3: Create knowledge snapshots
        snapshots = self.create_bulk_knowledge_snapshots(characters, 20)  # 2000 total
        memory_after_knowledge = process.memory_info().rss / 1024 / 1024
        memory_measurements.append(("After 2000 knowledge snapshots", memory_after_knowledge))
        
        print("Memory usage progression:")
        for phase, memory in memory_measurements:
            print(f"  {phase}: {memory:.1f} MB (delta: +{memory - initial_memory:.1f} MB)")
            
        # Memory usage assertions (adjust based on acceptable thresholds)
        memory_increase = memory_after_knowledge - initial_memory
        assert memory_increase < 500.0  # Should not use more than 500MB additional memory
        
    def test_database_connection_performance(self):
        """Test: Database connection efficiency under load"""
        # Test rapid consecutive database operations
        start_time = time.time()
        
        operations_count = 100
        for i in range(operations_count):
            # Alternate between different types of operations
            if i % 3 == 0:
                response = client.get("/api/v1/entities/")
            elif i % 3 == 1:
                response = client.get("/api/v1/relationships/")
            else:
                response = client.get("/health")
                
            assert response.status_code == 200
            
        total_time = time.time() - start_time
        operations_per_second = operations_count / total_time
        
        print(f"Database connection performance:")
        print(f"  {operations_count} operations in {total_time:.2f}s")
        print(f"  Rate: {operations_per_second:.1f} operations/second")
        
        # Performance assertion
        assert operations_per_second > 10.0  # Should handle at least 10 operations per second
        
    def test_api_response_size_performance(self):
        """Test: Performance with large API responses"""
        # Create large dataset
        characters = self.create_bulk_characters(200, "LargeResponse")
        relationships = self.create_bulk_relationships(characters, 1000)
        
        # Test large response handling
        start_time = time.time()
        response = client.get("/api/v1/entities/")
        entity_response_time = time.time() - start_time
        
        start_time = time.time()
        response = client.get("/api/v1/relationships/")
        relationship_response_time = time.time() - start_time
        
        # Measure response sizes
        entities_data = response.json() if response.status_code == 200 else {}
        entity_count = len(entities_data.get("data", {}).get("entities", []))
        
        print(f"Large response performance:")
        print(f"  Entities response ({entity_count} items): {entity_response_time:.3f}s")
        print(f"  Relationships response: {relationship_response_time:.3f}s")
        
        # Performance assertions
        assert entity_response_time < 5.0     # Large entity response under 5 seconds
        assert relationship_response_time < 10.0  # Large relationship response under 10 seconds


class TestScalabilityLimits(TestPhase3Performance):
    """Test system behavior at scale limits"""
    
    def test_maximum_entities_handling(self):
        """Test: System behavior with maximum reasonable entity count"""
        # Test with large but reasonable entity count
        large_count = 500  # Adjust based on system capabilities
        
        print(f"Testing scalability with {large_count} entities...")
        
        start_time = time.time()
        characters = self.create_bulk_characters(large_count, "ScaleTest")
        creation_time = time.time() - start_time
        
        # Test system responsiveness after bulk creation
        start_time = time.time()
        response = client.get("/api/v1/entities/")
        query_time = time.time() - start_time
        
        print(f"Scalability test results:")
        print(f"  Created {large_count} entities in {creation_time:.2f}s")
        print(f"  Queried all entities in {query_time:.2f}s")
        
        # Verify system is still responsive
        assert response.status_code == 200
        entities = response.json()["data"]["entities"]
        scale_test_entities = [e for e in entities 
                             if e.get("metadata", {}).get("batch") == "ScaleTest"]
        assert len(scale_test_entities) == large_count
        
        # Performance assertions
        assert creation_time < 600.0  # Should create 500 entities in under 10 minutes
        assert query_time < 10.0      # Should query all entities in under 10 seconds
        
    def test_complex_relationship_networks(self):
        """Test: Performance with complex relationship networks"""
        # Create a dense relationship network
        characters = self.create_bulk_characters(50, "NetworkTest")
        
        # Create a more complex network (each character connected to multiple others)
        relationships = []
        for i, char1 in enumerate(characters):
            # Each character connects to next 5 characters (wrapping around)
            for j in range(1, 6):
                char2_idx = (i + j) % len(characters)
                char2 = characters[char2_idx]
                
                rel = self.create_bulk_relationships([char1, char2], 1)[0]
                relationships.append(rel)
                
        # Test complex graph queries
        def test_graph_query():
            # Query relationship graph for a central node
            central_char = characters[0]
            return client.get(f"/api/v1/relationships/graph/{central_char['id']}")
            
        graph_metrics = self.measure_query_performance(test_graph_query, "complex_graph_query")
        
        print(f"Complex network performance:")
        print(f"  Network: {len(characters)} nodes, {len(relationships)} edges")
        print(f"  Graph query: {graph_metrics['average']:.3f}s avg")
        
        # Performance assertion
        assert graph_metrics["average"] < 3.0  # Complex graph query under 3 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements