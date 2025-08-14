"""
Tests for advanced content operations - Content Team

Covers:
- Batch operations (create/update multiple blocks)
- Block reordering with integrity validation
- Content workflows (duplicate, merge)
- Content search functionality
- Scene content validation
- Integration with knowledge snapshots
"""

import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.content_service import ContentService
from app.models.api_models import (
    BlockBatchCreate, BlockBatchUpdate, BlockReorder,
    BlockDuplicate, BlockMerge, ContentSearchRequest,
    SceneBlockCreate, ValidationResult
)


client = TestClient(app)


class TestBatchOperations:
    """Test batch create and update operations"""
    
    @patch('app.api.content.ContentService')
    def test_batch_create_blocks_success(self, mock_service_class):
        """Test successful batch creation of blocks"""
        # Mock service response
        mock_service = mock_service_class.return_value
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.processed = 3
        mock_result.failed = 0
        mock_result.created_blocks = [
            {"id": str(uuid4()), "content": "Block 1"},
            {"id": str(uuid4()), "content": "Block 2"},
            {"id": str(uuid4()), "content": "Block 3"}
        ]
        mock_result.errors = None
        mock_result.model_dump.return_value = {
            "success": True,
            "processed": 3,
            "failed": 0,
            "created_blocks": mock_result.created_blocks,
            "errors": None
        }
        mock_service.batch_create_blocks.return_value = mock_result
        
        # Test data
        scene_id = str(uuid4())
        batch_data = {
            "scene_id": scene_id,
            "blocks": [
                {
                    "scene_id": scene_id,
                    "block_type": "prose",
                    "order": 0,
                    "content": "First block content"
                },
                {
                    "scene_id": scene_id,
                    "block_type": "dialogue",
                    "order": 1,
                    "summary": "Character conversation"
                },
                {
                    "scene_id": scene_id,
                    "block_type": "milestone",
                    "order": 2,
                    "verb": "arrives",
                    "subject_id": str(uuid4())
                }
            ]
        }
        
        # Make request
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully created 3 blocks" in data["message"]
        assert data["data"]["processed"] == 3
        assert data["data"]["failed"] == 0
    
    @patch('app.api.content.ContentService')
    def test_batch_create_blocks_partial_failure(self, mock_service_class):
        """Test batch creation with some failures"""
        mock_service = mock_service_class.return_value
        mock_service.batch_create_blocks.return_value = MagicMock(
            success=False,
            processed=2,
            failed=1,
            created_blocks=[
                {"id": str(uuid4()), "content": "Block 1"},
                {"id": str(uuid4()), "content": "Block 2"}
            ],
            errors=["Block 2: Invalid subject_id format"]
        )
        
        batch_data = {
            "scene_id": str(uuid4()),
            "blocks": [
                {"scene_id": str(uuid4()), "block_type": "prose", "order": 0},
                {"scene_id": str(uuid4()), "block_type": "prose", "order": 1},
                {"scene_id": str(uuid4()), "block_type": "milestone", "order": 2}
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "partially failed" in data["error"]
        assert "Invalid subject_id format" in data["details"][0]
    
    @patch('app.api.content.ContentService')
    def test_batch_update_blocks_success(self, mock_service_class):
        """Test successful batch update of blocks"""
        mock_service = mock_service_class.return_value
        mock_service.batch_update_blocks.return_value = MagicMock(
            success=True,
            processed=2,
            failed=0,
            updated_blocks=[
                {"id": str(uuid4()), "content": "Updated block 1"},
                {"id": str(uuid4()), "content": "Updated block 2"}
            ],
            errors=None
        )
        
        update_data = {
            "updates": [
                {
                    "id": str(uuid4()),
                    "updates": {"content": "Updated content 1"}
                },
                {
                    "id": str(uuid4()),
                    "updates": {"content": "Updated content 2"}
                }
            ]
        }
        
        response = client.put("/api/v1/content/blocks/batch", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully updated 2 blocks" in data["message"]


class TestBlockReordering:
    """Test block reordering functionality"""
    
    @patch('app.api.content.ContentService')
    def test_reorder_blocks_success(self, mock_service_class):
        """Test successful block reordering"""
        mock_service = mock_service_class.return_value
        mock_service.reorder_blocks.return_value = [
            {"id": str(uuid4()), "order": 0, "content": "First block"},
            {"id": str(uuid4()), "order": 1, "content": "Second block"},
            {"id": str(uuid4()), "order": 2, "content": "Third block"}
        ]
        
        reorder_data = {
            "scene_id": str(uuid4()),
            "block_order": {
                str(uuid4()): 2,
                str(uuid4()): 0,
                str(uuid4()): 1
            }
        }
        
        response = client.post("/api/v1/content/blocks/reorder", json=reorder_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Blocks reordered successfully" in data["message"]
        assert len(data["data"]["blocks"]) == 3
    
    @patch('app.api.content.ContentService')
    def test_get_ordered_blocks(self, mock_service_class):
        """Test getting ordered blocks for a scene"""
        mock_service = mock_service_class.return_value
        mock_service.get_ordered_blocks.return_value = [
            {"id": str(uuid4()), "order": 0, "block_type": "prose"},
            {"id": str(uuid4()), "order": 1, "block_type": "dialogue"},
            {"id": str(uuid4()), "order": 2, "block_type": "milestone"}
        ]
        
        scene_id = str(uuid4())
        response = client.get(f"/api/v1/content/blocks/scene/{scene_id}/ordered")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["blocks"]) == 3
        assert data["data"]["count"] == 3
    
    @patch('app.api.content.ContentService')
    def test_get_ordered_blocks_with_filter(self, mock_service_class):
        """Test getting ordered blocks with type filter"""
        mock_service = mock_service_class.return_value
        mock_service.get_ordered_blocks.return_value = [
            {"id": str(uuid4()), "order": 0, "block_type": "prose"},
            {"id": str(uuid4()), "order": 2, "block_type": "prose"}
        ]
        
        scene_id = str(uuid4())
        response = client.get(
            f"/api/v1/content/blocks/scene/{scene_id}/ordered?block_types=prose"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["blocks"]) == 2


class TestContentWorkflows:
    """Test duplicate and merge operations"""
    
    @patch('app.api.content.ContentService')
    def test_duplicate_block_success(self, mock_service_class):
        """Test successful block duplication"""
        mock_service = mock_service_class.return_value
        mock_service.duplicate_block.return_value = {
            "id": str(uuid4()),
            "content": "Duplicated content",
            "order": 3
        }
        
        block_id = str(uuid4())
        duplicate_data = {
            "modifications": {
                "content": "Modified duplicated content"
            }
        }
        
        response = client.post(
            f"/api/v1/content/blocks/{block_id}/duplicate",
            json=duplicate_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Block duplicated successfully" in data["message"]
        assert data["data"]["block"]["content"] == "Duplicated content"
    
    @patch('app.api.content.ContentService')
    def test_merge_blocks_success(self, mock_service_class):
        """Test successful block merging"""
        mock_service = mock_service_class.return_value
        mock_service.merge_blocks.return_value = {
            "id": str(uuid4()),
            "content": "Merged content from multiple blocks",
            "metadata": {"merged_from": [str(uuid4()), str(uuid4())]}
        }
        
        merge_data = {
            "target_block_id": str(uuid4()),
            "source_block_ids": [str(uuid4()), str(uuid4())],
            "merge_strategy": "concatenate"
        }
        
        response = client.post("/api/v1/content/blocks/merge", json=merge_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Blocks merged successfully" in data["message"]
        assert "merged_from" in data["data"]["block"]["metadata"]


class TestContentSearch:
    """Test content search functionality"""
    
    @patch('app.api.content.ContentService')
    def test_search_content_success(self, mock_service_class):
        """Test successful content search"""
        mock_service = mock_service_class.return_value
        mock_service.search_content.return_value = {
            "results": [
                {
                    "block_id": str(uuid4()),
                    "scene_id": str(uuid4()),
                    "block_type": "prose",
                    "order": 0,
                    "content_snippet": "...found matching content...",
                    "match_score": 0.85,
                    "scene_title": "Test Scene"
                }
            ],
            "total": 1,
            "query": "matching content"
        }
        
        search_data = {
            "query": "matching content",
            "limit": 10
        }
        
        response = client.post("/api/v1/content/blocks/search", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert data["data"]["query"] == "matching content"
        assert len(data["data"]["results"]) == 1
        assert data["data"]["results"][0]["match_score"] == 0.85
    
    @patch('app.api.content.ContentService')
    def test_search_content_with_filters(self, mock_service_class):
        """Test content search with filters"""
        mock_service = mock_service_class.return_value
        mock_service.search_content.return_value = {
            "results": [],
            "total": 0,
            "query": "test query"
        }
        
        search_data = {
            "query": "test query",
            "scene_id": str(uuid4()),
            "block_types": ["prose", "dialogue"],
            "metadata_filters": {"author": "test"},
            "limit": 50
        }
        
        response = client.post("/api/v1/content/blocks/search", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0


class TestContentValidation:
    """Test scene content validation"""
    
    @patch('app.api.content.ContentService')
    def test_validate_scene_content_success(self, mock_service_class):
        """Test successful scene validation"""
        mock_service = mock_service_class.return_value
        mock_service.validate_scene_content.return_value = MagicMock(
            scene_id=UUID(str(uuid4())),
            valid=True,
            rules_checked=5,
            rules_passed=5,
            issues=[],
            model_dump=lambda: {
                "scene_id": str(uuid4()),
                "valid": True,
                "rules_checked": 5,
                "rules_passed": 5,
                "issues": []
            }
        )
        
        scene_id = str(uuid4())
        response = client.post(f"/api/v1/content/validation/scene/{scene_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "5/5 rules passed" in data["message"]
        assert data["data"]["valid"] is True
        assert data["data"]["rules_checked"] == 5
        assert data["data"]["rules_passed"] == 5
    
    @patch('app.api.content.ContentService')
    def test_validate_scene_content_with_issues(self, mock_service_class):
        """Test scene validation with issues found"""
        mock_service = mock_service_class.return_value
        mock_service.validate_scene_content.return_value = MagicMock(
            scene_id=UUID(str(uuid4())),
            valid=False,
            rules_checked=5,
            rules_passed=3,
            issues=[
                {
                    "rule_name": "block_ordering",
                    "passed": False,
                    "message": "Block ordering has gaps",
                    "details": {"gap_at": 2}
                },
                {
                    "rule_name": "milestone_consistency",
                    "passed": False,
                    "message": "Missing subject_id in milestone",
                    "details": {"invalid_count": 1}
                }
            ],
            model_dump=lambda: {
                "scene_id": str(uuid4()),
                "valid": False,
                "rules_checked": 5,
                "rules_passed": 3,
                "issues": [
                    {
                        "rule_name": "block_ordering",
                        "passed": False,
                        "message": "Block ordering has gaps"
                    },
                    {
                        "rule_name": "milestone_consistency",
                        "passed": False,
                        "message": "Missing subject_id in milestone"
                    }
                ]
            }
        )
        
        scene_id = str(uuid4())
        response = client.post(f"/api/v1/content/validation/scene/{scene_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "3/5 rules passed" in data["message"]
        assert data["data"]["valid"] is False
        assert len(data["data"]["issues"]) == 2


class TestContentServiceUnit:
    """Unit tests for ContentService methods"""
    
    @patch('app.services.content_service.get_db')
    def test_content_service_initialization(self, mock_get_db):
        """Test ContentService initializes correctly"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        service = ContentService()
        assert service.db == mock_db
    
    def test_merge_block_content_concatenate(self):
        """Test content merging with concatenate strategy"""
        service = ContentService()
        
        target = {"content": "Target content", "metadata": {"key": "value"}}
        sources = [
            {"id": "source1", "content": "Source 1 content"},
            {"id": "source2", "content": "Source 2 content"}
        ]
        
        result = service._merge_block_content(target, sources, "concatenate")
        
        expected_content = "Target content\n\nSource 1 content\n\nSource 2 content"
        assert result["content"] == expected_content
        assert result["metadata"]["merged_from"] == ["source1", "source2"]
    
    def test_merge_block_content_replace(self):
        """Test content merging with replace strategy"""
        service = ContentService()
        
        target = {"content": "Target content", "metadata": {"key": "value"}}
        sources = [
            {"id": "source1", "content": "Source 1 content"},
            {"id": "source2", "content": "Source 2 content"}
        ]
        
        result = service._merge_block_content(target, sources, "replace")
        
        assert result["content"] == "Source 2 content"
        assert result["metadata"]["replaced_from"] == ["source1", "source2"]
    
    def test_calculate_match_score(self):
        """Test match score calculation"""
        service = ContentService()
        
        block = {
            "content": "This is a test content block",
            "summary": "Test summary",
            "verb": "test"
        }
        
        # Perfect match
        score = service._calculate_match_score(block, "test")
        assert score == 1.0  # Found in all three fields
        
        # Partial match
        score = service._calculate_match_score(block, "content")
        assert score == 0.4  # Found only in content field
        
        # No match
        score = service._calculate_match_score(block, "nonexistent")
        assert score == 0.0
    
    def test_create_content_snippet(self):
        """Test content snippet creation"""
        service = ContentService()
        
        block = {"content": "This is a very long content block that should be truncated properly when creating snippets for search results."}
        
        # With query match
        snippet = service._create_content_snippet(block, "long content")
        assert "...very long content block..." in snippet
        
        # Without query
        snippet = service._create_content_snippet(block, "")
        assert len(snippet) <= 203  # 200 chars + "..."


class TestValidationRules:
    """Test individual validation rules"""
    
    def test_validate_block_ordering_success(self):
        """Test block ordering validation - success case"""
        service = ContentService()
        blocks = [
            {"order": 0}, {"order": 1}, {"order": 2}
        ]
        
        result = service._validate_block_ordering(blocks)
        assert result.rule_name == "block_ordering"
        assert result.passed is True
    
    def test_validate_block_ordering_gaps(self):
        """Test block ordering validation - gaps detected"""
        service = ContentService()
        blocks = [
            {"order": 0}, {"order": 2}, {"order": 3}  # Missing order 1
        ]
        
        result = service._validate_block_ordering(blocks)
        assert result.rule_name == "block_ordering"
        assert result.passed is False
        assert "gaps or duplicates" in result.message
    
    def test_validate_milestone_consistency_success(self):
        """Test milestone consistency validation - success case"""
        service = ContentService()
        blocks = [
            {"block_type": "prose"},
            {"block_type": "milestone", "subject_id": str(uuid4())},
            {"block_type": "dialogue"}
        ]
        
        result = service._validate_milestone_consistency(blocks)
        assert result.rule_name == "milestone_consistency"
        assert result.passed is True
    
    def test_validate_milestone_consistency_missing_subject(self):
        """Test milestone consistency validation - missing subject"""
        service = ContentService()
        blocks = [
            {"block_type": "milestone", "subject_id": None},
            {"block_type": "milestone", "subject_id": str(uuid4())}
        ]
        
        result = service._validate_milestone_consistency(blocks)
        assert result.rule_name == "milestone_consistency"
        assert result.passed is False
        assert "missing subject_id" in result.message
    
    def test_validate_content_completeness_success(self):
        """Test content completeness validation - success case"""
        service = ContentService()
        blocks = [
            {"block_type": "prose", "content": "Some content"},
            {"block_type": "dialogue", "summary": "Some dialogue"}
        ]
        
        result = service._validate_content_completeness(blocks)
        assert result.rule_name == "content_completeness"
        assert result.passed is True
    
    def test_validate_content_completeness_empty_content(self):
        """Test content completeness validation - empty content"""
        service = ContentService()
        blocks = [
            {"block_type": "prose", "content": ""},
            {"block_type": "prose", "content": "Valid content"}
        ]
        
        result = service._validate_content_completeness(blocks)
        assert result.rule_name == "content_completeness"
        assert result.passed is False
        assert "empty content" in result.message


class TestErrorHandling:
    """Test error handling in content operations"""
    
    @patch('app.api.content.ContentService')
    def test_batch_create_service_error(self, mock_service_class):
        """Test handling of service errors in batch create"""
        mock_service = mock_service_class.return_value
        mock_service.batch_create_blocks.side_effect = Exception("Database connection failed")
        
        batch_data = {
            "scene_id": str(uuid4()),
            "blocks": [{"scene_id": str(uuid4()), "block_type": "prose", "order": 0}]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        
        assert response.status_code == 200  # Error response with success=False
        data = response.json()
        assert data["success"] is False
        assert "Database connection failed" in data["error"]
    
    @patch('app.api.content.ContentService')
    def test_reorder_blocks_service_error(self, mock_service_class):
        """Test handling of service errors in reorder"""
        mock_service = mock_service_class.return_value
        mock_service.reorder_blocks.side_effect = Exception("Invalid scene ID")
        
        reorder_data = {
            "scene_id": str(uuid4()),
            "block_order": {str(uuid4()): 0}
        }
        
        response = client.post("/api/v1/content/blocks/reorder", json=reorder_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid scene ID" in data["error"]
    
    @patch('app.api.content.ContentService')
    def test_validation_service_error(self, mock_service_class):
        """Test handling of service errors in validation"""
        mock_service = mock_service_class.return_value
        mock_service.validate_scene_content.side_effect = Exception("Scene not found")
        
        scene_id = str(uuid4())
        response = client.post(f"/api/v1/content/validation/scene/{scene_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Scene not found" in data["error"]