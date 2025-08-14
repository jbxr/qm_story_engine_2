"""
Complete Story Authoring Workflows - End-to-End Testing
Testing complete story authoring workflows using all Phase 3 systems together.

Target: 25+ tests covering realistic story creation, editing, and management workflows
"""

import pytest
import time
import json
from typing import List, Dict, Any, Optional
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestStoryAuthoringWorkflows:
    """Base class for story authoring workflow tests"""
    
    def setup_method(self):
        """Setup for each workflow test"""
        self.story_world = {
            "characters": {},
            "locations": {},
            "artifacts": {},
            "scenes": {},
            "relationships": {},
            "knowledge": {},
            "timeline_events": []
        }
        
    def create_character(self, name: str, character_type: str = "protagonist", 
                        description: str = None, metadata: dict = None) -> dict:
        """Create a character with story context"""
        data = {
            "name": name,
            "entity_type": "character",
            "description": description or f"Story character: {name}",
            "metadata": {
                "character_type": character_type,
                "workflow_test": True,
                **(metadata or {})
            }
        }
        
        response = client.post("/api/v1/entities/", json=data)
        assert response.status_code == 200
        character = response.json()["data"]["entity"]
        self.story_world["characters"][name] = character
        return character
        
    def create_location(self, name: str, location_type: str = "setting",
                       description: str = None, metadata: dict = None) -> dict:
        """Create a location for the story"""
        data = {
            "name": name,
            "entity_type": "location",
            "description": description or f"Story location: {name}",
            "metadata": {
                "location_type": location_type,
                "workflow_test": True,
                **(metadata or {})
            }
        }
        
        response = client.post("/api/v1/entities/", json=data)
        assert response.status_code == 200
        location = response.json()["data"]["entity"]
        self.story_world["locations"][name] = location
        return location
        
    def create_artifact(self, name: str, artifact_type: str = "item",
                       description: str = None, metadata: dict = None) -> dict:
        """Create an artifact for the story"""
        data = {
            "name": name,
            "entity_type": "artifact",
            "description": description or f"Story artifact: {name}",
            "metadata": {
                "artifact_type": artifact_type,
                "workflow_test": True,
                **(metadata or {})
            }
        }
        
        response = client.post("/api/v1/entities/", json=data)
        assert response.status_code == 200
        artifact = response.json()["data"]["entity"]
        self.story_world["artifacts"][name] = artifact
        return artifact
        
    def create_scene(self, title: str, timestamp: int, description: str = None,
                    location_name: str = None, metadata: dict = None) -> dict:
        """Create a scene in the story"""
        location_id = None
        if location_name and location_name in self.story_world["locations"]:
            location_id = self.story_world["locations"][location_name]["id"]
            
        data = {
            "title": title,
            "description": description or f"Story scene: {title}",
            "timestamp": timestamp,
            "location_id": location_id,
            "metadata": {
                "workflow_test": True,
                **(metadata or {})
            }
        }
        
        response = client.post("/api/v1/scenes/", json=data)
        assert response.status_code == 200
        scene = response.json()["data"]["scene"]
        self.story_world["scenes"][title] = scene
        return scene
        
    def create_relationship(self, entity1_name: str, entity2_name: str,
                          relationship_type: str, timestamp_start: int,
                          timestamp_end: int = None, metadata: dict = None) -> dict:
        """Create a relationship between story entities"""
        # Find entities in story world
        entity1 = None
        entity2 = None
        
        for entity_type in ["characters", "locations", "artifacts"]:
            if entity1_name in self.story_world[entity_type]:
                entity1 = self.story_world[entity_type][entity1_name]
            if entity2_name in self.story_world[entity_type]:
                entity2 = self.story_world[entity_type][entity2_name]
                
        assert entity1 is not None, f"Entity {entity1_name} not found"
        assert entity2 is not None, f"Entity {entity2_name} not found"
        
        data = {
            "entity1_id": entity1["id"],
            "entity2_id": entity2["id"],
            "relationship_type": relationship_type,
            "timestamp_start": timestamp_start,
            "metadata": {
                "workflow_test": True,
                "entity1_name": entity1_name,
                "entity2_name": entity2_name,
                **(metadata or {})
            }
        }
        
        if timestamp_end:
            data["timestamp_end"] = timestamp_end
            
        response = client.post("/api/v1/relationships/", json=data)
        assert response.status_code == 200
        relationship = response.json()["data"]["relationship"]
        
        rel_key = f"{entity1_name}-{entity2_name}-{relationship_type}"
        self.story_world["relationships"][rel_key] = relationship
        return relationship
        
    def create_knowledge_snapshot(self, character_name: str, timestamp: int,
                                knowledge_content: dict, metadata: dict = None) -> dict:
        """Create knowledge snapshot for a character"""
        character = self.story_world["characters"][character_name]
        
        data = {
            "entity_id": character["id"],
            "timestamp": timestamp,
            "knowledge": knowledge_content,
            "metadata": {
                "workflow_test": True,
                "character_name": character_name,
                **(metadata or {})
            }
        }
        
        response = client.post("/api/v1/knowledge/snapshots", json=data)
        assert response.status_code == 200
        snapshot = response.json()["data"]["snapshot"]
        
        if character_name not in self.story_world["knowledge"]:
            self.story_world["knowledge"][character_name] = []
        self.story_world["knowledge"][character_name].append(snapshot)
        
        return snapshot
        
    def add_scene_content(self, scene_title: str, block_type: str, content: str,
                         sort_order: int, block_data: dict = None) -> dict:
        """Add content block to a scene"""
        scene = self.story_world["scenes"][scene_title]
        
        data = {
            "scene_id": scene["id"],
            "block_type": block_type,
            "content": content,
            "sort_order": sort_order,
            "metadata": {"workflow_test": True}
        }
        
        if block_data:
            data.update(block_data)
            
        response = client.post("/api/v1/scenes/blocks", json=data)
        assert response.status_code == 200
        return response.json()["data"]["block"]
        
    def record_timeline_event(self, timestamp: int, event: str, characters: List[str] = None):
        """Record a major timeline event"""
        self.story_world["timeline_events"].append({
            "timestamp": timestamp,
            "event": event,
            "characters": characters or []
        })
        
    def validate_story_consistency(self, timestamp: int) -> dict:
        """Validate story world consistency at a specific timestamp"""
        # Get active relationships
        response = client.get(f"/api/v1/relationships/active?timestamp={timestamp}")
        active_relationships = response.json()["data"]["relationships"] if response.status_code == 200 else []
        
        # Get character knowledge at timestamp
        character_knowledge = {}
        for char_name, char in self.story_world["characters"].items():
            response = client.get(f"/api/v1/knowledge/snapshots/character/{char['id']}?timestamp={timestamp}")
            if response.status_code == 200:
                snapshots = response.json()["data"]["snapshots"]
                valid_snapshots = [s for s in snapshots if s["timestamp"] <= timestamp]
                if valid_snapshots:
                    latest = max(valid_snapshots, key=lambda x: x["timestamp"])
                    character_knowledge[char_name] = latest
                    
        return {
            "timestamp": timestamp,
            "active_relationships": active_relationships,
            "character_knowledge": character_knowledge,
            "story_world": self.story_world
        }


class TestBasicStoryCreationWorkflows(TestStoryAuthoringWorkflows):
    """Test basic story creation workflows"""
    
    def test_simple_story_creation_workflow(self):
        """Test: Create a simple story from start to finish"""
        # Story: "The Apprentice's First Quest"
        
        # 1. Create characters
        hero = self.create_character("Lyra", "protagonist", 
                                   "A young mage apprentice eager to prove herself")
        mentor = self.create_character("Master Aldric", "mentor",
                                     "A wise and experienced wizard")
        villain = self.create_character("Shadow Wraith", "antagonist",
                                      "A dark entity threatening the realm")
        
        # 2. Create locations
        academy = self.create_location("Mystic Academy", "academy",
                                     "A prestigious school of magical arts")
        forest = self.create_location("Whispering Woods", "wilderness",
                                    "An ancient forest filled with magical creatures")
        ruins = self.create_location("Ancient Ruins", "dungeon",
                                   "Crumbling stone structures with dark secrets")
        
        # 3. Create important artifacts
        staff = self.create_artifact("Crystal Staff", "weapon",
                                   "A powerful magical staff with a glowing crystal")
        spellbook = self.create_artifact("Tome of Shadows", "book",
                                       "An ancient book containing forbidden magic")
        
        # 4. Create story timeline with relationships
        T1 = 1000  # Story begins
        T2 = 2000  # Quest starts
        T3 = 3000  # First challenge
        T4 = 4000  # Discovery
        T5 = 5000  # Final confrontation
        
        # Initial relationships
        mentor_student = self.create_relationship("Lyra", "Master Aldric", "mentor_student", T1)
        lyra_at_academy = self.create_relationship("Lyra", "Mystic Academy", "resident", T1)
        
        # 5. Create scenes with progression
        opening_scene = self.create_scene("The Assignment", T1, 
                                        "Master Aldric gives Lyra her first real quest",
                                        "Mystic Academy")
        
        forest_scene = self.create_scene("Into the Woods", T2,
                                       "Lyra enters the mysterious forest",
                                       "Whispering Woods")
        
        discovery_scene = self.create_scene("The Ancient Secret", T3,
                                          "Lyra discovers the hidden ruins",
                                          "Ancient Ruins")
        
        confrontation_scene = self.create_scene("Facing the Shadow", T4,
                                              "The final battle with the Shadow Wraith",
                                              "Ancient Ruins")
        
        # 6. Add detailed content to key scenes
        self.add_scene_content("The Assignment", "dialogue", 
                             "Lyra, you have shown great promise. It is time for your first real test.",
                             1, {
                                 "dialogue": {
                                     "speaker_id": mentor["id"],
                                     "listener_id": hero["id"],
                                     "emotion": "encouraging"
                                 }
                             })
        
        self.add_scene_content("The Assignment", "dialogue",
                             "I won't let you down, Master. I'm ready for whatever awaits.",
                             2, {
                                 "dialogue": {
                                     "speaker_id": hero["id"],
                                     "listener_id": mentor["id"],
                                     "emotion": "determined"
                                 }
                             })
        
        self.add_scene_content("The Assignment", "milestone",
                             "Lyra accepts her first quest to investigate strange happenings in the Whispering Woods.",
                             3, {
                                 "milestone": {
                                     "subject_id": hero["id"],
                                     "verb": "accepts",
                                     "object_type": "quest",
                                     "description": "First quest accepted",
                                     "impact_level": "major"
                                 }
                             })
        
        # 7. Create knowledge progression
        lyra_initial_knowledge = self.create_knowledge_snapshot("Lyra", T1 + 100, {
            "story_phase": "ordinary_world",
            "location": "Mystic Academy",
            "mentor": mentor["id"],
            "skills": ["basic_magic", "eager_to_learn"],
            "goals": ["prove_myself", "become_powerful_mage"],
            "known_locations": [academy["id"]]
        })
        
        lyra_quest_knowledge = self.create_knowledge_snapshot("Lyra", T2 + 100, {
            "story_phase": "call_to_adventure",
            "location": "Whispering Woods", 
            "mentor": mentor["id"],
            "skills": ["basic_magic", "forest_navigation"],
            "goals": ["investigate_forest", "complete_first_quest"],
            "known_locations": [academy["id"], forest["id"]],
            "current_quest": "investigate_strange_happenings"
        })
        
        # Introduce villain relationship
        lyra_vs_wraith = self.create_relationship("Lyra", "Shadow Wraith", "enemies", T3)
        
        lyra_discovery_knowledge = self.create_knowledge_snapshot("Lyra", T3 + 100, {
            "story_phase": "approaching_ordeal",
            "location": "Ancient Ruins",
            "mentor": mentor["id"],
            "skills": ["basic_magic", "forest_navigation", "ancient_lore"],
            "goals": ["stop_shadow_wraith", "protect_realm"],
            "known_locations": [academy["id"], forest["id"], ruins["id"]],
            "enemies": [villain["id"]],
            "discovered_threats": ["shadow_wraith_presence"],
            "artifacts_known": [spellbook["id"]]
        })
        
        # Final knowledge state
        lyra_final_knowledge = self.create_knowledge_snapshot("Lyra", T5 + 100, {
            "story_phase": "return_with_elixir",
            "location": "Mystic Academy",
            "mentor": mentor["id"],
            "skills": ["basic_magic", "forest_navigation", "ancient_lore", "shadow_magic_resistance"],
            "goals": ["return_to_academy", "report_success"],
            "known_locations": [academy["id"], forest["id"], ruins["id"]],
            "defeated_enemies": [villain["id"]],
            "artifacts_possessed": [staff["id"]],
            "achievements": ["first_quest_completed", "saved_realm"],
            "character_growth": "confident_young_mage"
        })
        
        # 8. Validate story consistency at key points
        consistency_checks = [
            (T1 + 500, "Story beginning"),
            (T2 + 500, "Quest begins"),
            (T3 + 500, "Discovery phase"),
            (T5 + 500, "Story conclusion")
        ]
        
        for timestamp, phase in consistency_checks:
            state = self.validate_story_consistency(timestamp)
            
            # Verify Lyra has appropriate knowledge for this phase
            lyra_knowledge = state["character_knowledge"].get("Lyra")
            if lyra_knowledge:
                knowledge_data = lyra_knowledge["knowledge"]
                assert "story_phase" in knowledge_data
                assert "location" in knowledge_data
                assert "skills" in knowledge_data
                
                # Phase-specific validations
                if phase == "Story beginning":
                    assert knowledge_data["story_phase"] == "ordinary_world"
                elif phase == "Quest begins":
                    assert knowledge_data["story_phase"] == "call_to_adventure"
                elif phase == "Discovery phase":
                    assert knowledge_data["story_phase"] == "approaching_ordeal"
                elif phase == "Story conclusion":
                    assert knowledge_data["story_phase"] == "return_with_elixir"
                    
        # 9. Verify complete story structure
        assert len(self.story_world["characters"]) == 3
        assert len(self.story_world["locations"]) == 3
        assert len(self.story_world["artifacts"]) == 2
        assert len(self.story_world["scenes"]) == 4
        assert len(self.story_world["relationships"]) >= 3
        assert len(self.story_world["knowledge"]["Lyra"]) == 4
        
        print("Simple story creation workflow completed successfully!")
        print(f"Created story with {len(self.story_world['characters'])} characters, "
              f"{len(self.story_world['scenes'])} scenes, and {len(self.story_world['relationships'])} relationships")
        
    def test_character_arc_development_workflow(self):
        """Test: Character development arc across story timeline"""
        # Story: Character growth through challenges
        
        # Create protagonist with growth potential
        hero = self.create_character("Elena", "protagonist",
                                   "A reluctant hero who must overcome her fears")
        
        supporting_char = self.create_character("Marcus", "supporting",
                                              "Elena's loyal friend and voice of reason")
        
        # Character arc timeline
        T_INTRODUCTION = 1000
        T_INCITING_INCIDENT = 2000
        T_FIRST_CHALLENGE = 3000
        T_MIDPOINT_CRISIS = 4000
        T_DARK_MOMENT = 5000
        T_CLIMAX = 6000
        T_RESOLUTION = 7000
        
        # Track character development through knowledge snapshots
        character_development = [
            (T_INTRODUCTION, {
                "personality": "fearful",
                "confidence": 2,
                "skills": ["hiding", "avoiding_conflict"],
                "fears": ["confrontation", "responsibility", "failure"],
                "relationships": {supporting_char["id"]: "protective_friend"},
                "internal_goal": "stay_safe"
            }),
            (T_INCITING_INCIDENT, {
                "personality": "reluctant",
                "confidence": 3,
                "skills": ["hiding", "avoiding_conflict", "basic_courage"],
                "fears": ["confrontation", "responsibility"],
                "relationships": {supporting_char["id"]: "trusted_friend"},
                "internal_goal": "help_others_despite_fear",
                "character_moment": "accepts_call_to_adventure"
            }),
            (T_FIRST_CHALLENGE, {
                "personality": "testing_limits",
                "confidence": 4,
                "skills": ["hiding", "basic_courage", "problem_solving"],
                "fears": ["responsibility", "making_wrong_choice"],
                "relationships": {supporting_char["id"]: "reliable_ally"},
                "internal_goal": "prove_myself",
                "achievements": ["overcame_first_fear"]
            }),
            (T_MIDPOINT_CRISIS, {
                "personality": "struggling",
                "confidence": 5,
                "skills": ["basic_courage", "problem_solving", "leadership"],
                "fears": ["making_wrong_choice", "losing_friends"],
                "relationships": {supporting_char["id"]: "equal_partner"},
                "internal_goal": "protect_those_i_care_about",
                "realizations": ["responsibility_can_be_positive"]
            }),
            (T_DARK_MOMENT, {
                "personality": "tested",
                "confidence": 3,  # Temporary setback
                "skills": ["basic_courage", "problem_solving", "leadership", "sacrifice"],
                "fears": ["losing_friends"],
                "relationships": {supporting_char["id"]: "deep_bond"},
                "internal_goal": "save_everyone_even_if_it_costs_me",
                "crisis_moment": "everything_seems_lost"
            }),
            (T_CLIMAX, {
                "personality": "heroic",
                "confidence": 8,
                "skills": ["courage", "problem_solving", "leadership", "sacrifice", "wisdom"],
                "fears": [],  # Has overcome major fears
                "relationships": {supporting_char["id"]: "lifelong_friend"},
                "internal_goal": "use_my_strength_to_help_others",
                "transformation": "from_fearful_to_courageous"
            }),
            (T_RESOLUTION, {
                "personality": "confident_hero",
                "confidence": 9,
                "skills": ["courage", "wisdom", "leadership", "inspiring_others"],
                "fears": [],
                "relationships": {supporting_char["id"]: "cherished_friend"},
                "internal_goal": "continue_growing_and_helping",
                "character_arc_complete": True,
                "new_role": "mentor_to_others"
            })
        ]
        
        # Create knowledge snapshots for character development
        for timestamp, development in character_development:
            self.create_knowledge_snapshot("Elena", timestamp, development)
            
        # Create parallel relationship evolution
        friendship_evolution = [
            (T_INTRODUCTION, "protector_protected", T_INCITING_INCIDENT),
            (T_INCITING_INCIDENT, "friends", T_MIDPOINT_CRISIS),
            (T_MIDPOINT_CRISIS, "partners", T_RESOLUTION)
        ]
        
        for start_time, rel_type, end_time in friendship_evolution:
            if end_time == T_RESOLUTION:
                end_time = None  # Ongoing relationship
            self.create_relationship("Elena", "Marcus", rel_type, start_time, end_time)
            
        # Validate character development progression
        validation_points = [T_INTRODUCTION + 100, T_FIRST_CHALLENGE + 100, 
                           T_CLIMAX + 100, T_RESOLUTION + 100]
                           
        previous_confidence = 0
        for timestamp in validation_points:
            state = self.validate_story_consistency(timestamp)
            elena_knowledge = state["character_knowledge"].get("Elena")
            
            if elena_knowledge:
                development = elena_knowledge["knowledge"]
                current_confidence = development.get("confidence", 0)
                
                # Character should generally grow in confidence (except during dark moment)
                if timestamp != T_DARK_MOMENT + 100:
                    assert current_confidence >= previous_confidence or timestamp == validation_points[0]
                
                # Specific development milestones
                if timestamp >= T_CLIMAX + 100:
                    assert "transformation" in development
                    assert len(development.get("fears", [])) == 0
                    
                if timestamp >= T_RESOLUTION + 100:
                    assert development.get("character_arc_complete") is True
                    
                previous_confidence = current_confidence
                
        print("Character arc development workflow completed successfully!")
        print(f"Tracked character development through {len(character_development)} stages")
        
    def test_multi_character_story_workflow(self):
        """Test: Complex story with multiple character perspectives"""
        # Story: Multiple POV characters with intersecting storylines
        
        # Create main characters
        alice = self.create_character("Alice", "protagonist", "A detective investigating mysterious disappearances")
        bob = self.create_character("Bob", "supporting", "A journalist uncovering a conspiracy")
        charlie = self.create_character("Charlie", "protagonist", "A victim who escaped and holds key information")
        diana = self.create_character("Diana", "antagonist", "The mastermind behind the disappearances")
        
        # Timeline with parallel storylines
        T_START = 1000
        T_ALICE_CASE = 1500
        T_BOB_INVESTIGATION = 1800
        T_CHARLIE_ESCAPE = 2000
        T_FIRST_MEETING = 2500
        T_REVELATION = 3000
        T_FINAL_CONFRONTATION = 4000
        T_RESOLUTION = 4500
        
        # Alice's storyline (Detective perspective)
        alice_timeline = [
            (T_START, {
                "role": "detective",
                "current_case": "missing_persons",
                "known_characters": [],
                "evidence": [],
                "leads": ["strange_disappearance_pattern"],
                "emotional_state": "professional_concern"
            }),
            (T_ALICE_CASE, {
                "role": "detective", 
                "current_case": "missing_persons",
                "known_characters": [],
                "evidence": ["witness_reports", "security_footage"],
                "leads": ["strange_disappearance_pattern", "possible_serial_kidnapper"],
                "emotional_state": "growing_urgency"
            }),
            (T_FIRST_MEETING, {
                "role": "detective",
                "current_case": "missing_persons",
                "known_characters": [bob["id"], charlie["id"]],
                "evidence": ["witness_reports", "security_footage", "bob_journalist_info"],
                "leads": ["conspiracy_theory", "underground_organization"],
                "emotional_state": "determined_collaboration",
                "alliances": [bob["id"], charlie["id"]]
            }),
            (T_REVELATION, {
                "role": "detective",
                "current_case": "human_trafficking_ring",
                "known_characters": [bob["id"], charlie["id"], diana["id"]],
                "evidence": ["witness_reports", "security_footage", "charlie_testimony", "organization_documents"],
                "leads": ["diana_mastermind", "operation_locations"],
                "emotional_state": "shocked_but_resolved",
                "enemies": [diana["id"]]
            })
        ]
        
        # Bob's storyline (Journalist perspective)
        bob_timeline = [
            (T_BOB_INVESTIGATION, {
                "role": "journalist",
                "current_story": "corruption_investigation",
                "sources": ["anonymous_tip"],
                "evidence": ["financial_records", "suspicious_transactions"],
                "theories": ["money_laundering", "political_corruption"],
                "emotional_state": "investigative_excitement"
            }),
            (T_FIRST_MEETING, {
                "role": "journalist",
                "current_story": "human_trafficking_expose",
                "sources": ["anonymous_tip", "police_contact"],
                "known_characters": [alice["id"], charlie["id"]],
                "evidence": ["financial_records", "police_reports", "charlie_interview"],
                "theories": ["organized_crime_network"],
                "emotional_state": "collaborative_determination"
            }),
            (T_REVELATION, {
                "role": "journalist",
                "current_story": "major_trafficking_ring_expose",
                "sources": ["anonymous_tip", "police_contact", "survivor_testimony"],
                "known_characters": [alice["id"], charlie["id"], diana["id"]],
                "evidence": ["complete_financial_trail", "victim_testimonies", "organization_structure"],
                "ready_to_publish": True,
                "emotional_state": "righteous_anger_and_purpose"
            })
        ]
        
        # Charlie's storyline (Victim/Survivor perspective)
        charlie_timeline = [
            (T_CHARLIE_ESCAPE, {
                "role": "survivor",
                "trauma_level": "high",
                "memories": ["captivity", "escape_route", "other_victims"],
                "known_characters": [],
                "fears": ["being_found", "not_being_believed"],
                "goals": ["stay_hidden", "survive"],
                "emotional_state": "terrified_but_free"
            }),
            (T_FIRST_MEETING, {
                "role": "survivor_witness",
                "trauma_level": "medium",
                "memories": ["captivity", "escape_route", "other_victims", "organization_details"],
                "known_characters": [alice["id"], bob["id"]],
                "fears": ["retaliation"],
                "goals": ["help_other_victims", "get_justice"],
                "emotional_state": "cautious_hope",
                "trusted_allies": [alice["id"], bob["id"]]
            }),
            (T_REVELATION, {
                "role": "key_witness",
                "trauma_level": "low",
                "memories": ["full_organization_knowledge", "diana_identity", "victim_locations"],
                "known_characters": [alice["id"], bob["id"], diana["id"]],
                "fears": [],
                "goals": ["testify_against_diana", "help_rescue_victims"],
                "emotional_state": "empowered_survivor",
                "character_growth": "from_victim_to_hero"
            })
        ]
        
        # Create knowledge snapshots for all characters
        for character_name, timeline in [("Alice", alice_timeline), ("Bob", bob_timeline), ("Charlie", charlie_timeline)]:
            for timestamp, knowledge in timeline:
                self.create_knowledge_snapshot(character_name, timestamp, knowledge)
                
        # Create evolving relationships between characters
        # Alice and Bob meet and collaborate
        alice_bob_professional = self.create_relationship("Alice", "Bob", "professional_collaboration", T_FIRST_MEETING)
        
        # All three form alliance
        alice_charlie_protector = self.create_relationship("Alice", "Charlie", "protector_witness", T_FIRST_MEETING)
        bob_charlie_interviewer = self.create_relationship("Bob", "Charlie", "journalist_source", T_FIRST_MEETING)
        
        # Everyone vs Diana
        alice_diana_adversary = self.create_relationship("Alice", "Diana", "law_enforcement_criminal", T_REVELATION)
        bob_diana_adversary = self.create_relationship("Bob", "Diana", "journalist_corrupt_target", T_REVELATION)
        charlie_diana_adversary = self.create_relationship("Charlie", "Diana", "victim_perpetrator", T_CHARLIE_ESCAPE)
        
        # Create scenes showing convergence
        meeting_scene = self.create_scene("Unlikely Alliance", T_FIRST_MEETING,
                                        "Three different perspectives unite for justice")
        
        revelation_scene = self.create_scene("The Truth Revealed", T_REVELATION,
                                           "All pieces come together to expose the conspiracy")
        
        # Validate multi-character consistency
        validation_timestamps = [T_ALICE_CASE, T_FIRST_MEETING, T_REVELATION]
        
        for timestamp in validation_timestamps:
            state = self.validate_story_consistency(timestamp)
            
            # Check each character has appropriate knowledge for timeline
            for char_name in ["Alice", "Bob", "Charlie"]:
                char_knowledge = state["character_knowledge"].get(char_name)
                if char_knowledge:
                    knowledge_data = char_knowledge["knowledge"]
                    
                    # All characters should have growing awareness
                    if timestamp >= T_FIRST_MEETING:
                        known_chars = knowledge_data.get("known_characters", [])
                        if char_name == "Alice":
                            assert bob["id"] in known_chars
                            assert charlie["id"] in known_chars
                        elif char_name == "Bob":
                            assert alice["id"] in known_chars
                            assert charlie["id"] in known_chars
                        elif char_name == "Charlie":
                            assert alice["id"] in known_chars
                            assert bob["id"] in known_chars
                            
                    # By revelation, all should know about Diana
                    if timestamp >= T_REVELATION:
                        known_chars = knowledge_data.get("known_characters", [])
                        assert diana["id"] in known_chars
                        
        print("Multi-character story workflow completed successfully!")
        print(f"Tracked {len([alice, bob, charlie])} character perspectives through convergent storylines")


class TestAdvancedStoryEditingWorkflows(TestStoryAuthoringWorkflows):
    """Test advanced story editing and revision workflows"""
    
    def test_story_revision_workflow(self):
        """Test: Revising and updating an existing story"""
        # Create initial story version
        hero = self.create_character("Alex", "protagonist", "A young explorer seeking treasure")
        companion = self.create_character("Robin", "supporting", "Alex's loyal companion")
        villain = self.create_character("Captain Dread", "antagonist", "A ruthless pirate captain")
        
        # Initial story setup
        T_START = 1000
        T_ADVENTURE = 2000
        T_CONFLICT = 3000
        T_RESOLUTION = 4000
        
        # Create original story relationships
        original_friendship = self.create_relationship("Alex", "Robin", "friends", T_START)
        original_rivalry = self.create_relationship("Alex", "Captain Dread", "enemies", T_CONFLICT)
        
        # Original story knowledge
        original_knowledge = self.create_knowledge_snapshot("Alex", T_START + 100, {
            "story_version": "original",
            "goal": "find_treasure",
            "motivation": "adventure_seeking",
            "companions": [companion["id"]],
            "story_tone": "light_adventure"
        })
        
        # REVISION 1: Change character motivation and add depth
        # Update Alex's knowledge to reflect character development revision
        revised_knowledge_v1 = self.create_knowledge_snapshot("Alex", T_START + 200, {
            "story_version": "revision_1",
            "goal": "find_treasure_to_save_village",
            "motivation": "helping_others",
            "companions": [companion["id"]],
            "story_tone": "heroic_journey",
            "backstory": "village_in_danger",
            "emotional_stakes": "high"
        })
        
        # Add new character for revised storyline
        mentor = self.create_character("Elder Sage", "mentor", "Wise village elder who sends Alex on quest")
        mentor_relationship = self.create_relationship("Alex", "Elder Sage", "mentor_student", T_START + 200)
        
        # REVISION 2: Add subplot and complexity
        love_interest = self.create_character("Jordan", "love_interest", "A skilled navigator with secrets")
        
        # Complex relationship evolution
        alex_jordan_initial = self.create_relationship("Alex", "Jordan", "acquaintances", T_ADVENTURE + 100)
        
        # Updated knowledge for subplot
        revised_knowledge_v2 = self.create_knowledge_snapshot("Alex", T_ADVENTURE + 200, {
            "story_version": "revision_2",
            "goal": "find_treasure_to_save_village",
            "motivation": "helping_others",
            "companions": [companion["id"], love_interest["id"]],
            "story_tone": "epic_adventure_with_romance",
            "backstory": "village_in_danger",
            "emotional_stakes": "very_high",
            "subplots": ["romantic_development", "jordan_secret_identity"],
            "character_relationships": {
                companion["id"]: "loyal_friend",
                love_interest["id"]: "growing_attraction_and_trust"
            }
        })
        
        # REVISION 3: Change ending and villain motivation
        # Update villain's relationship and motivation
        complex_villain_relationship = self.create_relationship("Captain Dread", "Jordan", "secret_siblings", T_START)
        
        # Final revision knowledge
        final_revision_knowledge = self.create_knowledge_snapshot("Alex", T_CONFLICT + 100, {
            "story_version": "final_revision",
            "goal": "save_village_and_redeem_villain",
            "motivation": "compassion_and_justice",
            "companions": [companion["id"], love_interest["id"]],
            "story_tone": "redemption_epic",
            "backstory": "village_in_danger",
            "emotional_stakes": "maximum",
            "subplots": ["romantic_development", "family_revelation", "villain_redemption"],
            "character_relationships": {
                companion["id"]: "trusted_friend",
                love_interest["id"]: "true_love",
                villain["id"]: "complex_adversary_with_hidden_pain"
            },
            "story_themes": ["redemption", "family", "love_conquers_all"]
        })
        
        # Create scenes showing story evolution
        original_scene = self.create_scene("The Treasure Hunt Begins", T_START,
                                         "Alex sets out for adventure and treasure")
        
        revised_scene = self.create_scene("A Village's Last Hope", T_START + 200,
                                        "Alex accepts the quest to save their home village")
        
        complex_scene = self.create_scene("Unlikely Allies", T_ADVENTURE + 200,
                                        "Alex's party grows and relationships deepen")
        
        final_scene = self.create_scene("Redemption and Resolution", T_CONFLICT + 100,
                                      "The final confrontation becomes a moment of healing")
        
        # Validate revision consistency
        revision_points = [
            (T_START + 150, "original_version"),
            (T_START + 250, "revision_1"),
            (T_ADVENTURE + 250, "revision_2"),
            (T_CONFLICT + 150, "final_revision")
        ]
        
        for timestamp, expected_version in revision_points:
            state = self.validate_story_consistency(timestamp)
            alex_knowledge = state["character_knowledge"].get("Alex")
            
            if alex_knowledge:
                knowledge_data = alex_knowledge["knowledge"]
                actual_version = knowledge_data.get("story_version", "unknown")
                
                # Version should match expected
                assert expected_version in actual_version or actual_version in expected_version
                
                # Complexity should increase with revisions
                subplots = knowledge_data.get("subplots", [])
                if "final_revision" in actual_version:
                    assert len(subplots) >= 2
                    assert "redemption" in knowledge_data.get("story_themes", [])
                    
        print("Story revision workflow completed successfully!")
        print(f"Evolved story through {len(revision_points)} major revisions")
        
    def test_character_relationship_editing_workflow(self):
        """Test: Editing and updating character relationships"""
        # Create characters for relationship testing
        anna = self.create_character("Anna", "protagonist", "A diplomat seeking peace")
        bruce = self.create_character("Bruce", "supporting", "A military commander")
        claire = self.create_character("Claire", "supporting", "A trade representative")
        
        # Timeline for relationship evolution
        T_INITIAL = 1000
        T_COOPERATION = 2000
        T_CONFLICT = 3000
        T_RECONCILIATION = 4000
        T_ALLIANCE = 5000
        
        # Phase 1: Initial relationships (neutral/professional)
        anna_bruce_initial = self.create_relationship("Anna", "Bruce", "diplomatic_contact", T_INITIAL, T_COOPERATION)
        anna_claire_initial = self.create_relationship("Anna", "Claire", "trade_contact", T_INITIAL, T_CONFLICT)
        bruce_claire_initial = self.create_relationship("Bruce", "Claire", "neutral", T_INITIAL, T_CONFLICT)
        
        # Phase 2: Cooperation develops
        anna_bruce_cooperation = self.create_relationship("Anna", "Bruce", "allies", T_COOPERATION, T_CONFLICT)
        anna_claire_cooperation = self.create_relationship("Anna", "Claire", "business_partners", T_COOPERATION, T_CONFLICT)
        
        # Phase 3: Conflict emerges
        anna_bruce_conflict = self.create_relationship("Anna", "Bruce", "political_rivals", T_CONFLICT, T_RECONCILIATION)
        anna_claire_conflict = self.create_relationship("Anna", "Claire", "competitors", T_CONFLICT, T_RECONCILIATION)
        bruce_claire_conflict = self.create_relationship("Bruce", "Claire", "enemies", T_CONFLICT, T_RECONCILIATION)
        
        # Phase 4: Reconciliation
        anna_bruce_reconciliation = self.create_relationship("Anna", "Bruce", "reconciling_allies", T_RECONCILIATION, T_ALLIANCE)
        anna_claire_reconciliation = self.create_relationship("Anna", "Claire", "cautious_partners", T_RECONCILIATION, T_ALLIANCE)
        bruce_claire_reconciliation = self.create_relationship("Bruce", "Claire", "grudging_respect", T_RECONCILIATION, T_ALLIANCE)
        
        # Phase 5: Strong alliance
        anna_bruce_alliance = self.create_relationship("Anna", "Bruce", "trusted_allies", T_ALLIANCE)
        anna_claire_alliance = self.create_relationship("Anna", "Claire", "close_partners", T_ALLIANCE)
        bruce_claire_alliance = self.create_relationship("Bruce", "Claire", "mutual_respect", T_ALLIANCE)
        
        # Track Anna's perspective on relationship changes
        relationship_knowledge = [
            (T_INITIAL + 100, {
                "diplomatic_status": "establishing_contacts",
                "relationship_with_bruce": "professional_military_contact",
                "relationship_with_claire": "trade_negotiation_partner",
                "overall_situation": "building_diplomatic_network"
            }),
            (T_COOPERATION + 100, {
                "diplomatic_status": "successful_cooperation",
                "relationship_with_bruce": "reliable_ally_in_security_matters",
                "relationship_with_claire": "profitable_business_relationship",
                "overall_situation": "strong_multi_party_cooperation"
            }),
            (T_CONFLICT + 100, {
                "diplomatic_status": "crisis_management",
                "relationship_with_bruce": "political_disagreement_over_policy",
                "relationship_with_claire": "competing_for_same_resources",
                "bruce_claire_tension": "they_actively_dislike_each_other",
                "overall_situation": "managing_multiple_conflicts"
            }),
            (T_RECONCILIATION + 100, {
                "diplomatic_status": "rebuilding_trust", 
                "relationship_with_bruce": "working_through_differences",
                "relationship_with_claire": "finding_common_ground",
                "bruce_claire_progress": "they_respect_each_others_abilities",
                "overall_situation": "healing_and_growing_stronger"
            }),
            (T_ALLIANCE + 100, {
                "diplomatic_status": "unified_leadership",
                "relationship_with_bruce": "deep_trust_and_strategic_partnership",
                "relationship_with_claire": "close_collaboration_and_friendship",
                "bruce_claire_bond": "they_have_learned_to_work_together_effectively",
                "overall_situation": "strong_three_way_alliance",
                "achievement": "turned_conflict_into_cooperation"
            })
        ]
        
        # Create knowledge snapshots
        for timestamp, knowledge in relationship_knowledge:
            self.create_knowledge_snapshot("Anna", timestamp, knowledge)
            
        # Create scenes showing relationship evolution
        scenes = [
            ("First Contact", T_INITIAL, "Initial diplomatic meetings"),
            ("Working Together", T_COOPERATION, "Successful joint projects"),
            ("The Falling Out", T_CONFLICT, "Disagreements lead to conflict"),
            ("Making Amends", T_RECONCILIATION, "Difficult conversations and healing"),
            ("Stronger Than Before", T_ALLIANCE, "United in purpose and trust")
        ]
        
        for title, timestamp, description in scenes:
            self.create_scene(title, timestamp, description)
            
        # Validate relationship evolution
        test_timestamps = [T_INITIAL + 200, T_COOPERATION + 200, T_CONFLICT + 200, 
                          T_RECONCILIATION + 200, T_ALLIANCE + 200]
                          
        expected_relationship_counts = [3, 5, 8, 11, 14]  # Cumulative relationships as they change
        
        for i, timestamp in enumerate(test_timestamps):
            state = self.validate_story_consistency(timestamp)
            
            # Check Anna's knowledge reflects current relationship state
            anna_knowledge = state["character_knowledge"].get("Anna")
            if anna_knowledge:
                knowledge_data = anna_knowledge["knowledge"]
                
                # Verify relationship awareness matches timeline
                if timestamp >= T_ALLIANCE + 100:
                    assert "achievement" in knowledge_data
                    assert "unified_leadership" in knowledge_data.get("diplomatic_status", "")
                elif timestamp >= T_CONFLICT + 100:
                    assert "crisis_management" in knowledge_data.get("diplomatic_status", "")
                    
        print("Character relationship editing workflow completed successfully!")
        print(f"Tracked relationship evolution through {len(relationship_knowledge)} phases")
        
    def test_timeline_restructuring_workflow(self):
        """Test: Restructuring story timeline and maintaining consistency"""
        # Create story elements
        hero = self.create_character("Sam", "protagonist", "A time-traveling historian")
        ally = self.create_character("Taylor", "supporting", "Sam's research partner")
        artifact = self.create_artifact("Temporal Key", "device", "A device that enables time travel")
        
        # Original timeline
        ORIGINAL_START = 1000
        ORIGINAL_DISCOVERY = 2000
        ORIGINAL_FIRST_JUMP = 3000
        ORIGINAL_COMPLICATIONS = 4000
        ORIGINAL_RESOLUTION = 5000
        
        # Create original story structure
        original_scenes = [
            ("Research Begins", ORIGINAL_START, "Sam starts investigating temporal anomalies"),
            ("The Discovery", ORIGINAL_DISCOVERY, "Finding the Temporal Key"),
            ("First Time Jump", ORIGINAL_FIRST_JUMP, "Sam's first trip through time"),
            ("Complications Arise", ORIGINAL_COMPLICATIONS, "Time travel has consequences"),
            ("Setting Things Right", ORIGINAL_RESOLUTION, "Resolving temporal paradoxes")
        ]
        
        for title, timestamp, description in original_scenes:
            self.create_scene(title, timestamp, description)
            
        # Original knowledge progression
        original_knowledge = [
            (ORIGINAL_START + 100, {
                "timeline_version": "original",
                "research_focus": "temporal_anomalies",
                "partner": ally["id"],
                "discoveries": [],
                "time_travel_experience": "none"
            }),
            (ORIGINAL_DISCOVERY + 100, {
                "timeline_version": "original",
                "research_focus": "temporal_device_analysis",
                "partner": ally["id"],
                "discoveries": [artifact["id"]],
                "time_travel_experience": "theoretical_only"
            }),
            (ORIGINAL_FIRST_JUMP + 100, {
                "timeline_version": "original",
                "research_focus": "practical_time_travel",
                "partner": ally["id"],
                "discoveries": [artifact["id"]],
                "time_travel_experience": "first_successful_jump",
                "temporal_destinations": ["ancient_rome"]
            })
        ]
        
        for timestamp, knowledge in original_knowledge:
            self.create_knowledge_snapshot("Sam", timestamp, knowledge)
            
        # RESTRUCTURING: Move discovery earlier and add flashback structure
        RESTRUCTURED_FLASHBACK = 500   # New opening flashback
        RESTRUCTURED_PRESENT = 1200    # Story starts in media res
        RESTRUCTURED_PAST_1 = 800      # Flashback to earlier discovery
        RESTRUCTURED_PAST_2 = 1500     # Another past sequence
        RESTRUCTURED_CLIMAX = 2000     # Final sequence
        
        # Create restructured scenes
        restructured_scenes = [
            ("The Consequence", RESTRUCTURED_PRESENT, "Sam deals with aftermath of time travel"),
            ("How It Started", RESTRUCTURED_FLASHBACK, "Flashback to original discovery"),
            ("The First Clue", RESTRUCTURED_PAST_1, "Earlier investigation scene"),
            ("The Revelation", RESTRUCTURED_PAST_2, "Understanding the true nature of time"),
            ("Breaking the Cycle", RESTRUCTURED_CLIMAX, "Final resolution with full context")
        ]
        
        for title, timestamp, description in restructured_scenes:
            scene = self.create_scene(f"Restructured_{title}", timestamp, description)
            
        # Restructured knowledge (non-linear storytelling)
        restructured_knowledge = [
            (RESTRUCTURED_PRESENT + 100, {
                "timeline_version": "restructured",
                "narrative_structure": "in_media_res",
                "current_situation": "dealing_with_consequences",
                "knowledge_state": "experienced_but_confused",
                "story_position": "middle_of_crisis"
            }),
            (RESTRUCTURED_FLASHBACK + 100, {
                "timeline_version": "restructured", 
                "narrative_structure": "flashback",
                "current_situation": "initial_discovery",
                "knowledge_state": "naive_and_hopeful",
                "story_position": "origin_story"
            }),
            (RESTRUCTURED_CLIMAX + 100, {
                "timeline_version": "restructured",
                "narrative_structure": "climax_with_full_context",
                "current_situation": "resolution_with_wisdom",
                "knowledge_state": "complete_understanding",
                "story_position": "enlightened_conclusion",
                "narrative_technique": "circular_structure"
            })
        ]
        
        for timestamp, knowledge in restructured_knowledge:
            self.create_knowledge_snapshot("Sam", timestamp, knowledge)
            
        # Create relationships that work with restructured timeline
        sam_taylor_original = self.create_relationship("Sam", "Taylor", "research_partners", ORIGINAL_START)
        sam_artifact_discovery = self.create_relationship("Sam", "Temporal Key", "discoverer", RESTRUCTURED_FLASHBACK)
        
        # Validate timeline restructuring
        original_validation_points = [ORIGINAL_START + 200, ORIGINAL_DISCOVERY + 200, ORIGINAL_FIRST_JUMP + 200]
        restructured_validation_points = [RESTRUCTURED_PRESENT + 200, RESTRUCTURED_FLASHBACK + 200, RESTRUCTURED_CLIMAX + 200]
        
        # Verify both timeline versions maintain internal consistency
        for timestamp in original_validation_points:
            state = self.validate_story_consistency(timestamp)
            sam_knowledge = state["character_knowledge"].get("Sam")
            if sam_knowledge and "original" in sam_knowledge["knowledge"].get("timeline_version", ""):
                knowledge_data = sam_knowledge["knowledge"]
                assert "research_focus" in knowledge_data
                
        for timestamp in restructured_validation_points:
            state = self.validate_story_consistency(timestamp)
            sam_knowledge = state["character_knowledge"].get("Sam")
            if sam_knowledge and "restructured" in sam_knowledge["knowledge"].get("timeline_version", ""):
                knowledge_data = sam_knowledge["knowledge"]
                assert "narrative_structure" in knowledge_data
                assert "story_position" in knowledge_data
                
        # Verify we have both timeline versions represented
        all_sam_knowledge = self.story_world["knowledge"]["Sam"]
        original_count = sum(1 for k in all_sam_knowledge if "original" in k["knowledge"].get("timeline_version", ""))
        restructured_count = sum(1 for k in all_sam_knowledge if "restructured" in k["knowledge"].get("timeline_version", ""))
        
        assert original_count >= 3
        assert restructured_count >= 3
        
        print("Timeline restructuring workflow completed successfully!")
        print(f"Maintained consistency across {original_count} original and {restructured_count} restructured timeline points")


class TestComplexStoryManagementWorkflows(TestStoryAuthoringWorkflows):
    """Test complex story management and organization workflows"""
    
    def test_story_world_expansion_workflow(self):
        """Test: Expanding an existing story world with new elements"""
        # Start with a simple story world
        main_hero = self.create_character("Kira", "protagonist", "A young warrior defending her homeland")
        homeland = self.create_location("Valdris", "kingdom", "A peaceful mountain kingdom")
        
        # Initial simple story (Phase 1)
        T_PHASE1_START = 1000
        T_PHASE1_END = 2000
        
        initial_knowledge = self.create_knowledge_snapshot("Kira", T_PHASE1_START + 100, {
            "story_scope": "local_conflict",
            "known_world": ["Valdris"],
            "threats": ["bandit_raids"],
            "story_scale": "village_level"
        })
        
        # EXPANSION 1: Add neighboring regions and larger conflict
        neighboring_kingdom = self.create_location("Astoria", "kingdom", "A rival kingdom to the east")
        neutral_territory = self.create_location("The Borderlands", "wilderness", "Contested territory between kingdoms")
        
        # New characters for expanded world
        rival_prince = self.create_character("Prince Daven", "antagonist", "Ambitious prince of Astoria")
        diplomat = self.create_character("Ambassador Lydia", "supporting", "A peace-seeking diplomat")
        
        # Phase 2: Regional conflict
        T_PHASE2_START = 2500
        T_PHASE2_END = 4000
        
        # Create relationships for expanded scope
        kira_daven_rivalry = self.create_relationship("Kira", "Prince Daven", "enemies", T_PHASE2_START)
        valdris_astoria_tension = self.create_relationship("Valdris", "Astoria", "political_rivals", T_PHASE2_START)
        
        expanded_knowledge_1 = self.create_knowledge_snapshot("Kira", T_PHASE2_START + 100, {
            "story_scope": "regional_conflict",
            "known_world": ["Valdris", "Astoria", "The Borderlands"],
            "threats": ["inter_kingdom_war", "prince_daven"],
            "story_scale": "kingdom_level",
            "political_awareness": "growing",
            "allies": [diplomat["id"]]
        })
        
        # EXPANSION 2: Add international scope and ancient threats
        distant_empire = self.create_location("The Crimson Empire", "empire", "A distant but powerful empire")
        ancient_ruins = self.create_location("Sunken City of Thalassos", "ruins", "Ancient underwater city with dark secrets")
        
        # New characters for global scope
        emperor = self.create_character("Emperor Maximus", "antagonist", "Ruler of the Crimson Empire")
        ancient_guardian = self.create_character("Thalassos Guardian", "neutral", "Ancient protector of forbidden knowledge")
        foreign_ally = self.create_character("Captain Zara", "supporting", "Sea captain from distant lands")
        
        # Powerful artifacts for expanded story
        ancient_weapon = self.create_artifact("Trident of Storms", "weapon", "Legendary weapon from the sunken city")
        prophecy_scroll = self.create_artifact("The Ocean Prophecy", "document", "Ancient prophecy about rising waters")
        
        # Phase 3: Global stakes
        T_PHASE3_START = 4500
        T_PHASE3_END = 6000
        
        # Complex international relationships
        empire_expansion = self.create_relationship("The Crimson Empire", "Valdris", "expansionist_threat", T_PHASE3_START)
        ancient_awakening = self.create_relationship("Thalassos Guardian", "Emperor Maximus", "ancient_enemy", T_PHASE3_START)
        
        expanded_knowledge_2 = self.create_knowledge_snapshot("Kira", T_PHASE3_START + 100, {
            "story_scope": "global_crisis",
            "known_world": ["Valdris", "Astoria", "The Borderlands", "The Crimson Empire", "Sunken City of Thalassos"],
            "threats": ["empire_invasion", "ancient_prophecy_fulfillment", "rising_sea_levels"],
            "story_scale": "world_level",
            "political_awareness": "sophisticated",
            "allies": [diplomat["id"], foreign_ally["id"], ancient_guardian["id"]],
            "artifacts_known": [ancient_weapon["id"], prophecy_scroll["id"]],
            "character_evolution": "from_village_defender_to_world_protector"
        })
        
        # EXPANSION 3: Add time travel/multiverse elements
        alternate_reality = self.create_location("Mirror Valdris", "alternate_dimension", "A parallel version of Kira's homeland")
        time_nexus = self.create_location("The Temporal Nexus", "mystical_realm", "Where all timelines converge")
        
        # Characters from expanded reality
        alternate_kira = self.create_character("Kira the Conqueror", "alternate_self", "Evil version of Kira from another timeline")
        time_guardian = self.create_character("Chronos Keeper", "mystical", "Guardian of the timeline")
        
        # Phase 4: Multiverse scope
        T_PHASE4_START = 6500
        
        multiverse_knowledge = self.create_knowledge_snapshot("Kira", T_PHASE4_START + 100, {
            "story_scope": "multiverse_crisis",
            "known_world": ["multiple_realities", "all_timelines"],
            "threats": ["timeline_collapse", "evil_alternate_selves", "reality_war"],
            "story_scale": "cosmic_level",
            "character_growth": "cosmic_awareness",
            "philosophical_understanding": "nature_of_reality_and_choice",
            "ultimate_responsibility": "protecting_all_possible_worlds"
        })
        
        # Create scenes showing expansion
        expansion_scenes = [
            ("The Village Defender", T_PHASE1_START, "Kira's humble beginnings", "Valdris"),
            ("Kingdoms in Conflict", T_PHASE2_START, "Regional war begins", "The Borderlands"),
            ("The Empire Rises", T_PHASE3_START, "Global threat emerges", "The Crimson Empire"),
            ("Reality's Edge", T_PHASE4_START, "Multiverse crisis unfolds", "The Temporal Nexus")
        ]
        
        for title, timestamp, description, location in expansion_scenes:
            self.create_scene(title, timestamp, description, location)
            
        # Validate expansion consistency
        expansion_phases = [
            (T_PHASE1_START + 500, "local_conflict", 1),
            (T_PHASE2_START + 500, "regional_conflict", 3),
            (T_PHASE3_START + 500, "global_crisis", 5),
            (T_PHASE4_START + 500, "multiverse_crisis", 7)
        ]
        
        for timestamp, expected_scope, min_known_locations in expansion_phases:
            state = self.validate_story_consistency(timestamp)
            kira_knowledge = state["character_knowledge"].get("Kira")
            
            if kira_knowledge:
                knowledge_data = kira_knowledge["knowledge"]
                actual_scope = knowledge_data.get("story_scope", "")
                known_world = knowledge_data.get("known_world", [])
                
                assert expected_scope in actual_scope
                assert len(known_world) >= min_known_locations
                
        # Verify world expansion metrics
        total_characters = len(self.story_world["characters"])
        total_locations = len(self.story_world["locations"])
        total_artifacts = len(self.story_world["artifacts"])
        total_scenes = len(self.story_world["scenes"])
        
        print("Story world expansion workflow completed successfully!")
        print(f"Expanded world: {total_characters} characters, {total_locations} locations, "
              f"{total_artifacts} artifacts, {total_scenes} scenes")
        print(f"Scope evolution: Village → Kingdom → World → Multiverse")
        
        # Assertions for expansion success
        assert total_characters >= 8  # Should have created many characters across expansions
        assert total_locations >= 7   # Multiple locations across different scopes
        assert total_artifacts >= 2   # Important story artifacts
        assert total_scenes >= 4      # Scenes showing expansion
        
    def test_story_consistency_maintenance_workflow(self):
        """Test: Maintaining consistency while making complex story changes"""
        # Create complex initial story state
        characters = {}
        for name, role, desc in [
            ("Elena", "protagonist", "A detective with psychic abilities"),
            ("Marcus", "partner", "Elena's rational police partner"),
            ("Dr. Kane", "mentor", "A researcher studying psychic phenomena"),
            ("The Shadow", "antagonist", "A serial killer who targets psychics"),
            ("Vera", "witness", "A psychic who survived the killer's attack")
        ]:
            characters[name] = self.create_character(name, role, desc)
            
        # Complex initial relationships
        T_INITIAL = 1000
        relationships = [
            ("Elena", "Marcus", "police_partners", T_INITIAL),
            ("Elena", "Dr. Kane", "mentor_student", T_INITIAL),
            ("Elena", "The Shadow", "hunter_hunted", T_INITIAL + 500),
            ("Dr. Kane", "Vera", "researcher_subject", T_INITIAL - 200),
            ("Marcus", "Dr. Kane", "skeptical_of", T_INITIAL + 300)
        ]
        
        for entity1, entity2, rel_type, timestamp in relationships:
            self.create_relationship(entity1, entity2, rel_type, timestamp)
            
        # Initial complex knowledge state
        initial_knowledge_states = {
            "Elena": {
                "psychic_abilities": ["empathy", "precognition"],
                "known_characters": [characters["Marcus"]["id"], characters["Dr. Kane"]["id"]],
                "case_status": "investigating_psychic_murders",
                "emotional_state": "determined_but_struggling",
                "secrets": ["hiding_full_extent_of_abilities"]
            },
            "Marcus": {
                "partner_relationship": characters["Elena"]["id"],
                "skepticism_level": "high",
                "known_about_psychics": "minimal",
                "case_focus": "traditional_detective_work",
                "concerns": ["elena_acting_strange"]
            },
            "Dr. Kane": {
                "research_focus": "psychic_phenomena",
                "subjects": [characters["Vera"]["id"], characters["Elena"]["id"]],
                "theories": ["psychics_targeted_for_abilities"],
                "protective_instincts": ["must_keep_subjects_safe"]
            }
        }
        
        for char_name, knowledge in initial_knowledge_states.items():
            self.create_knowledge_snapshot(char_name, T_INITIAL + 100, knowledge)
            
        # CONSISTENCY CHALLENGE 1: Change Elena's abilities
        T_CHANGE1 = 2000
        
        # Update Elena's knowledge to reflect new abilities
        elena_enhanced = self.create_knowledge_snapshot("Elena", T_CHANGE1, {
            "psychic_abilities": ["empathy", "precognition", "telekinesis", "mind_reading"],
            "ability_development": "rapid_enhancement_under_stress",
            "known_characters": [characters["Marcus"]["id"], characters["Dr. Kane"]["id"], characters["Vera"]["id"]],
            "case_status": "getting_closer_to_killer",
            "emotional_state": "powerful_but_overwhelmed",
            "secrets": ["new_abilities_emerging", "can_read_marcus_thoughts"]
        })
        
        # Marcus must notice changes
        marcus_awareness = self.create_knowledge_snapshot("Marcus", T_CHANGE1, {
            "partner_relationship": characters["Elena"]["id"],
            "skepticism_level": "decreasing",
            "known_about_psychics": "growing_awareness",
            "observations": ["elena_knows_things_she_shouldnt", "unexplained_evidence"],
            "case_focus": "following_elena_lead",
            "emotional_state": "confused_but_trusting"
        })
        
        # Dr. Kane should have theories
        kane_research_update = self.create_knowledge_snapshot("Dr. Kane", T_CHANGE1, {
            "research_focus": "accelerated_psychic_development",
            "subjects": [characters["Vera"]["id"], characters["Elena"]["id"]],
            "theories": ["stress_triggers_ability_growth", "killer_seeking_powerful_psychics"],
            "observations": ["elena_abilities_strengthening_rapidly"],
            "concerns": ["elena_becoming_primary_target"]
        })
        
        # CONSISTENCY CHALLENGE 2: Reveal Dr. Kane as the killer
        T_REVEAL = 3000
        
        # This requires updating all character knowledge and relationships
        
        # Elena discovers the truth
        elena_revelation = self.create_knowledge_snapshot("Elena", T_REVEAL, {
            "psychic_abilities": ["empathy", "precognition", "telekinesis", "mind_reading"],
            "shocking_discovery": "dr_kane_is_the_shadow",
            "known_characters": [characters["Marcus"]["id"], characters["Dr. Kane"]["id"], characters["Vera"]["id"]],
            "case_status": "confronting_the_killer",
            "emotional_state": "betrayed_and_determined",
            "realization": "he_was_studying_us_to_hunt_us",
            "danger_level": "extreme"
        })
        
        # Update relationship: Kane becomes Elena's enemy
        kane_elena_enemy = self.create_relationship("Elena", "Dr. Kane", "victim_killer", T_REVEAL)
        
        # Marcus must be brought up to speed
        marcus_revelation = self.create_knowledge_snapshot("Marcus", T_REVEAL, {
            "partner_relationship": characters["Elena"]["id"],
            "skepticism_level": "converted_to_believer",
            "known_about_psychics": "full_acceptance",
            "case_breakthrough": "kane_is_the_killer",
            "emotional_state": "protective_of_elena",
            "new_mission": "help_elena_stop_kane"
        })
        
        # Vera's perspective (she was being studied by her attacker)
        vera_horror = self.create_knowledge_snapshot("Vera", T_REVEAL, {
            "survivor_status": "was_being_studied_by_killer",
            "betrayal_trauma": "trusted_researcher_was_hunter",
            "alliance": [characters["Elena"]["id"], characters["Marcus"]["id"]],
            "emotional_state": "traumatized_but_determined_to_help"
        })
        
        # CONSISTENCY CHALLENGE 3: Kane escapes and Elena loses abilities
        T_SETBACK = 3500
        
        # Elena's abilities are damaged in confrontation
        elena_setback = self.create_knowledge_snapshot("Elena", T_SETBACK, {
            "psychic_abilities": ["empathy_damaged", "precognition_unreliable"],
            "ability_status": "severely_weakened_after_psychic_attack",
            "known_characters": [characters["Marcus"]["id"], characters["Dr. Kane"]["id"], characters["Vera"]["id"]],
            "case_status": "kane_escaped_must_hunt_traditionally",
            "emotional_state": "vulnerable_but_not_giving_up",
            "adaptation": "learning_to_work_without_full_abilities",
            "partner_dependency": "relying_more_on_marcus"
        })
        
        # Marcus steps up as lead
        marcus_leadership = self.create_knowledge_snapshot("Marcus", T_SETBACK, {
            "partner_relationship": characters["Elena"]["id"],
            "role_reversal": "now_protecting_weakened_elena",
            "case_leadership": "taking_point_on_investigation",
            "emotional_state": "determined_protector",
            "new_skills": ["understanding_psychic_crimes", "protecting_psychics"]
        })
        
        # Create scenes showing consistency maintenance
        consistency_scenes = [
            ("The Enhancement", T_CHANGE1, "Elena's abilities grow stronger"),
            ("The Betrayal", T_REVEAL, "Dr. Kane's true nature revealed"),
            ("The Setback", T_SETBACK, "Elena weakened, Marcus leads")
        ]
        
        for title, timestamp, description in consistency_scenes:
            self.create_scene(title, timestamp, description)
            
        # Validate consistency at each major change
        validation_points = [T_INITIAL + 200, T_CHANGE1 + 100, T_REVEAL + 100, T_SETBACK + 100]
        
        for timestamp in validation_points:
            state = self.validate_story_consistency(timestamp)
            
            # Check Elena's consistency
            elena_knowledge = state["character_knowledge"].get("Elena")
            if elena_knowledge:
                knowledge_data = elena_knowledge["knowledge"]
                
                # Abilities should be consistent with timeline
                abilities = knowledge_data.get("psychic_abilities", [])
                if timestamp >= T_SETBACK:
                    assert any("damaged" in ability or "unreliable" in ability for ability in abilities)
                elif timestamp >= T_CHANGE1:
                    assert len(abilities) >= 3  # Enhanced abilities
                    
                # Case knowledge should progress logically
                if timestamp >= T_REVEAL:
                    case_status = knowledge_data.get("case_status", "")
                    assert "kane" in case_status.lower() or "killer" in case_status.lower()
                    
            # Check Marcus's awareness progression
            marcus_knowledge = state["character_knowledge"].get("Marcus")
            if marcus_knowledge:
                knowledge_data = marcus_knowledge["knowledge"]
                skepticism = knowledge_data.get("skepticism_level", "high")
                
                if timestamp >= T_REVEAL:
                    assert "converted" in skepticism or "believer" in skepticism
                elif timestamp >= T_CHANGE1:
                    assert "decreasing" in skepticism
                    
        print("Story consistency maintenance workflow completed successfully!")
        print("Maintained logical character development through major plot reveals and setbacks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements