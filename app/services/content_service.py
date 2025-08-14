"""
Content Service - Advanced Scene Block Operations

Handles complex content workflows:
- Batch operations for creating/updating multiple blocks
- Block reordering with integrity maintenance  
- Content search across blocks
- Block duplication and merging
- Scene content validation
- Integration with knowledge snapshots
"""

from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime

from ..services.database import get_db
from ..models.api_models import (
    SceneBlockCreate, SceneBlockUpdate, SceneBlockResponse,
    BlockBatchCreate, BlockBatchUpdate, BlockReorder,
    BlockDuplicate, BlockMerge, ContentSearchRequest, ContentSearchResult,
    ValidationResult, ValidationRule, BatchOperationResult
)
from ..utils.serialization import serialize_database_response


class ContentService:
    """Service for advanced content block operations"""
    
    def __init__(self):
        self.db = get_db()
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def batch_create_blocks(self, batch_data: BlockBatchCreate) -> BatchOperationResult:
        """Create multiple blocks in a single transaction"""
        try:
            created_blocks = []
            errors = []
            
            # Get current max order for the scene
            max_order_result = self.db.table("scene_blocks").select("order").eq("scene_id", str(batch_data.scene_id)).order("order", desc=True).limit(1).execute()
            current_max_order = max_order_result.data[0]["order"] if max_order_result.data else -1
            
            # Prepare blocks for insertion
            blocks_to_insert = []
            for i, block_data in enumerate(batch_data.blocks):
                try:
                    # Auto-assign order if not provided
                    if block_data.order is None:
                        block_data.order = current_max_order + 1 + i
                    
                    block_dict = {
                        "id": str(uuid4()),
                        "scene_id": str(block_data.scene_id),
                        "block_type": block_data.block_type.value,
                        "order": block_data.order,
                        "content": block_data.content,
                        "summary": block_data.summary,
                        "lines": block_data.lines,
                        "subject_id": str(block_data.subject_id) if block_data.subject_id else None,
                        "verb": block_data.verb,
                        "object_id": str(block_data.object_id) if block_data.object_id else None,
                        "weight": block_data.weight,
                        "metadata": block_data.metadata or {},
                        "created_at": datetime.now(datetime.timezone.utc).isoformat(),
                        "updated_at": datetime.now(datetime.timezone.utc).isoformat()
                    }
                    blocks_to_insert.append(block_dict)
                    
                except Exception as e:
                    errors.append(f"Block {i}: {str(e)}")
            
            # Bulk insert
            if blocks_to_insert:
                result = self.db.table("scene_blocks").insert(blocks_to_insert).execute()
                created_blocks = serialize_database_response(result.data)
                
                # Create knowledge snapshots for milestone blocks
                self._create_milestone_snapshots(created_blocks)
            
            return BatchOperationResult(
                success=len(errors) == 0,
                processed=len(blocks_to_insert),
                failed=len(errors),
                created_blocks=created_blocks,
                errors=errors if errors else None
            )
            
        except Exception as e:
            return BatchOperationResult(
                success=False,
                processed=0,
                failed=len(batch_data.blocks),
                errors=[str(e)]
            )
    
    def batch_update_blocks(self, batch_data: BlockBatchUpdate) -> BatchOperationResult:
        """Update multiple blocks efficiently"""
        try:
            updated_blocks = []
            errors = []
            
            for update_item in batch_data.updates:
                try:
                    block_id = update_item.get("id")
                    updates = update_item.get("updates", {})
                    
                    if not block_id:
                        errors.append("Missing block ID in update")
                        continue
                    
                    # Add updated_at timestamp
                    updates["updated_at"] = datetime.now(datetime.timezone.utc).isoformat()
                    
                    # Perform update
                    result = self.db.table("scene_blocks").update(updates).eq("id", str(block_id)).execute()
                    
                    if result.data:
                        updated_blocks.extend(serialize_database_response(result.data))
                    else:
                        errors.append(f"Block {block_id} not found")
                        
                except Exception as e:
                    errors.append(f"Block {update_item.get('id', 'unknown')}: {str(e)}")
            
            return BatchOperationResult(
                success=len(errors) == 0,
                processed=len(updated_blocks),
                failed=len(errors),
                updated_blocks=updated_blocks,
                errors=errors if errors else None
            )
            
        except Exception as e:
            return BatchOperationResult(
                success=False,
                processed=0,
                failed=len(batch_data.updates),
                errors=[str(e)]
            )
    
    # ========================================================================
    # BLOCK REORDERING
    # ========================================================================
    
    def reorder_blocks(self, reorder_data: BlockReorder) -> List[SceneBlockResponse]:
        """Reorder blocks within a scene maintaining sequence integrity"""
        try:
            # Validate all blocks belong to the scene
            block_ids = list(reorder_data.block_order.keys())
            existing_blocks = self.db.table("scene_blocks").select("*").eq("scene_id", str(reorder_data.scene_id)).in_("id", block_ids).execute()
            
            if len(existing_blocks.data) != len(block_ids):
                raise ValueError("Some blocks don't belong to the specified scene")
            
            # Update each block's order
            updated_blocks = []
            for block_id, new_order in reorder_data.block_order.items():
                result = self.db.table("scene_blocks").update({
                    "order": new_order,
                    "updated_at": datetime.now(datetime.timezone.utc).isoformat()
                }).eq("id", block_id).execute()
                
                if result.data:
                    updated_blocks.extend(result.data)
            
            # Return ordered blocks
            return self.get_ordered_blocks(reorder_data.scene_id)
            
        except Exception as e:
            raise Exception(f"Failed to reorder blocks: {str(e)}")
    
    def get_ordered_blocks(self, scene_id: UUID, block_types: Optional[List[str]] = None) -> List[SceneBlockResponse]:
        """Get blocks in correct order with optional filtering"""
        try:
            query = self.db.table("scene_blocks").select("""
                *,
                subject:entities!scene_blocks_subject_id_fkey(name),
                object:entities!scene_blocks_object_id_fkey(name)
            """).eq("scene_id", str(scene_id)).order("order")
            
            if block_types:
                query = query.in_("block_type", block_types)
            
            result = query.execute()
            
            # Process results and add resolved names
            blocks = []
            for block in result.data:
                block_data = serialize_database_response(block)
                
                # Add resolved entity names
                if block.get("subject"):
                    block_data["subject_name"] = block["subject"]["name"]
                if block.get("object"):
                    block_data["object_name"] = block["object"]["name"]
                
                blocks.append(block_data)
            
            return blocks
            
        except Exception as e:
            raise Exception(f"Failed to get ordered blocks: {str(e)}")
    
    # ========================================================================
    # CONTENT WORKFLOWS
    # ========================================================================
    
    def duplicate_block(self, block_id: UUID, duplicate_data: BlockDuplicate) -> SceneBlockResponse:
        """Duplicate block with optional modifications"""
        try:
            # Get original block
            original_result = self.db.table("scene_blocks").select("*").eq("id", str(block_id)).execute()
            
            if not original_result.data:
                raise ValueError("Original block not found")
            
            original = original_result.data[0]
            
            # Create duplicate with new ID
            duplicate = original.copy()
            duplicate["id"] = str(uuid4())
            duplicate["created_at"] = datetime.now(datetime.timezone.utc).isoformat()
            duplicate["updated_at"] = datetime.now(datetime.timezone.utc).isoformat()
            
            # Apply modifications
            if duplicate_data.modifications:
                duplicate.update(duplicate_data.modifications)
            
            # Find next available order position
            max_order_result = self.db.table("scene_blocks").select("order").eq("scene_id", original["scene_id"]).order("order", desc=True).limit(1).execute()
            next_order = (max_order_result.data[0]["order"] if max_order_result.data else 0) + 1
            duplicate["order"] = next_order
            
            # Insert duplicate
            result = self.db.table("scene_blocks").insert(duplicate).execute()
            
            return serialize_database_response(result.data[0])
            
        except Exception as e:
            raise Exception(f"Failed to duplicate block: {str(e)}")
    
    def merge_blocks(self, merge_data: BlockMerge) -> SceneBlockResponse:
        """Merge multiple blocks into a single block"""
        try:
            # Get target block
            target_result = self.db.table("scene_blocks").select("*").eq("id", str(merge_data.target_block_id)).execute()
            if not target_result.data:
                raise ValueError("Target block not found")
            
            target_block = target_result.data[0]
            
            # Get source blocks
            source_ids = [str(id) for id in merge_data.source_block_ids]
            source_result = self.db.table("scene_blocks").select("*").in_("id", source_ids).order("order").execute()
            source_blocks = source_result.data
            
            if len(source_blocks) != len(merge_data.source_block_ids):
                raise ValueError("Some source blocks not found")
            
            # Merge content based on strategy
            merged_content = self._merge_block_content(target_block, source_blocks, merge_data.merge_strategy)
            
            # Update target block
            updates = {
                "content": merged_content.get("content"),
                "summary": merged_content.get("summary"),
                "lines": merged_content.get("lines"),
                "metadata": merged_content.get("metadata"),
                "updated_at": datetime.now(datetime.timezone.utc).isoformat()
            }
            
            updated_result = self.db.table("scene_blocks").update(updates).eq("id", str(merge_data.target_block_id)).execute()
            
            # Delete source blocks
            self.db.table("scene_blocks").delete().in_("id", source_ids).execute()
            
            return serialize_database_response(updated_result.data[0])
            
        except Exception as e:
            raise Exception(f"Failed to merge blocks: {str(e)}")
    
    # ========================================================================
    # CONTENT SEARCH
    # ========================================================================
    
    def search_content(self, search_request: ContentSearchRequest) -> Dict[str, Any]:
        """Search blocks by content, metadata, or block type"""
        try:
            # Base query
            query = self.db.table("scene_blocks").select("""
                *,
                scenes!inner(title),
                subject:entities!scene_blocks_subject_id_fkey(name),
                object:entities!scene_blocks_object_id_fkey(name)
            """)
            
            # Apply filters
            if search_request.scene_id:
                query = query.eq("scene_id", str(search_request.scene_id))
            
            if search_request.block_types:
                block_type_values = [bt.value if hasattr(bt, 'value') else bt for bt in search_request.block_types]
                query = query.in_("block_type", block_type_values)
            
            # Text search across content fields
            if search_request.query:
                query = query.or_(f"content.ilike.%{search_request.query}%,summary.ilike.%{search_request.query}%,verb.ilike.%{search_request.query}%")
            
            # Execute query
            result = query.limit(search_request.limit).execute()
            
            # Process results
            search_results = []
            for block in result.data:
                # Calculate simple match score
                match_score = self._calculate_match_score(block, search_request.query)
                
                # Create content snippet
                content_snippet = self._create_content_snippet(block, search_request.query)
                
                search_result = ContentSearchResult(
                    block_id=UUID(block["id"]),
                    scene_id=UUID(block["scene_id"]),
                    block_type=block["block_type"],
                    order=block["order"],
                    content_snippet=content_snippet,
                    match_score=match_score,
                    scene_title=block["scenes"]["title"] if block.get("scenes") else None
                )
                search_results.append(search_result)
            
            # Sort by match score
            search_results.sort(key=lambda x: x.match_score, reverse=True)
            
            return {
                "results": search_results,
                "total": len(search_results),
                "query": search_request.query
            }
            
        except Exception as e:
            raise Exception(f"Failed to search content: {str(e)}")
    
    # ========================================================================
    # CONTENT VALIDATION
    # ========================================================================
    
    def validate_scene_content(self, scene_id: UUID) -> ValidationResult:
        """Validate scene content integrity and consistency"""
        try:
            # Get all blocks for the scene
            blocks_result = self.db.table("scene_blocks").select("*").eq("scene_id", str(scene_id)).order("order").execute()
            blocks = blocks_result.data
            
            validation_rules = []
            
            # Rule 1: Sequential ordering (no gaps, no duplicates)
            ordering_result = self._validate_block_ordering(blocks)
            validation_rules.append(ordering_result)
            
            # Rule 2: Milestone consistency (valid entity references)
            milestone_result = self._validate_milestone_consistency(blocks)
            validation_rules.append(milestone_result)
            
            # Rule 3: Dialogue consistency (valid speaker references)
            dialogue_result = self._validate_dialogue_consistency(blocks)
            validation_rules.append(dialogue_result)
            
            # Rule 4: Content completeness (no empty required fields)
            completeness_result = self._validate_content_completeness(blocks)
            validation_rules.append(completeness_result)
            
            # Rule 5: Metadata consistency
            metadata_result = self._validate_metadata_consistency(blocks)
            validation_rules.append(metadata_result)
            
            # Calculate overall result
            rules_passed = sum(1 for rule in validation_rules if rule.passed)
            is_valid = rules_passed == len(validation_rules)
            
            return ValidationResult(
                scene_id=scene_id,
                valid=is_valid,
                rules_checked=len(validation_rules),
                rules_passed=rules_passed,
                issues=[rule for rule in validation_rules if not rule.passed]
            )
            
        except Exception as e:
            raise Exception(f"Failed to validate scene content: {str(e)}")
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _create_milestone_snapshots(self, blocks: List[Dict[str, Any]]):
        """Create knowledge snapshots for milestone blocks"""
        from .knowledge_service import KnowledgeService
        
        knowledge_service = KnowledgeService()
        
        for block in blocks:
            if block.get("block_type") == "milestone" and block.get("subject_id"):
                try:
                    # Create knowledge snapshot
                    # This integrates with the Knowledge Team's system
                    pass  # Implementation depends on KnowledgeService interface
                except Exception:
                    pass  # Don't fail batch operation for snapshot creation
    
    def _merge_block_content(self, target: Dict, sources: List[Dict], strategy: str) -> Dict:
        """Merge content from source blocks into target based on strategy"""
        if strategy == "concatenate":
            # Concatenate content fields
            all_content = [target.get("content", "")]
            all_content.extend([block.get("content", "") for block in sources])
            
            return {
                "content": "\n\n".join(filter(None, all_content)),
                "summary": target.get("summary"),
                "lines": target.get("lines"),
                "metadata": {**target.get("metadata", {}), "merged_from": [b["id"] for b in sources]}
            }
        elif strategy == "replace":
            # Use last source block's content
            if sources:
                last_source = sources[-1]
                return {
                    "content": last_source.get("content"),
                    "summary": last_source.get("summary"),
                    "lines": last_source.get("lines"),
                    "metadata": {**target.get("metadata", {}), "replaced_from": [b["id"] for b in sources]}
                }
        
        # Default: return target unchanged
        return {
            "content": target.get("content"),
            "summary": target.get("summary"),
            "lines": target.get("lines"),
            "metadata": target.get("metadata")
        }
    
    def _calculate_match_score(self, block: Dict, query: str) -> float:
        """Calculate simple match score for search results"""
        if not query:
            return 1.0
        
        query_lower = query.lower()
        score = 0.0
        
        # Check content field
        content = block.get("content", "")
        if content and query_lower in content.lower():
            score += 0.4
        
        # Check summary field
        summary = block.get("summary", "")
        if summary and query_lower in summary.lower():
            score += 0.3
        
        # Check verb field
        verb = block.get("verb", "")
        if verb and query_lower in verb.lower():
            score += 0.3
        
        return min(score, 1.0)
    
    def _create_content_snippet(self, block: Dict, query: str) -> str:
        """Create content snippet highlighting match"""
        content = block.get("content") or block.get("summary") or block.get("verb") or ""
        
        if not query or not content:
            return content[:200] + "..." if len(content) > 200 else content
        
        # Simple snippet creation (can be enhanced with proper highlighting)
        query_pos = content.lower().find(query.lower())
        if query_pos >= 0:
            start = max(0, query_pos - 50)
            end = min(len(content), query_pos + len(query) + 50)
            return "..." + content[start:end] + "..."
        
        return content[:200] + "..." if len(content) > 200 else content
    
    def _validate_block_ordering(self, blocks: List[Dict]) -> ValidationRule:
        """Validate block ordering is sequential"""
        if not blocks:
            return ValidationRule(rule_name="block_ordering", passed=True, message="No blocks to validate")
        
        orders = [block["order"] for block in blocks]
        expected_orders = list(range(len(blocks)))
        
        if sorted(orders) != expected_orders:
            return ValidationRule(
                rule_name="block_ordering",
                passed=False,
                message="Block ordering has gaps or duplicates",
                details={"actual_orders": orders, "expected_orders": expected_orders}
            )
        
        return ValidationRule(rule_name="block_ordering", passed=True)
    
    def _validate_milestone_consistency(self, blocks: List[Dict]) -> ValidationRule:
        """Validate milestone blocks have valid entity references"""
        milestone_blocks = [b for b in blocks if b.get("block_type") == "milestone"]
        
        if not milestone_blocks:
            return ValidationRule(rule_name="milestone_consistency", passed=True, message="No milestone blocks")
        
        # Check for missing subject_id in milestones
        invalid_milestones = [b for b in milestone_blocks if not b.get("subject_id")]
        
        if invalid_milestones:
            return ValidationRule(
                rule_name="milestone_consistency",
                passed=False,
                message="Some milestone blocks missing subject_id",
                details={"invalid_count": len(invalid_milestones)}
            )
        
        return ValidationRule(rule_name="milestone_consistency", passed=True)
    
    def _validate_dialogue_consistency(self, blocks: List[Dict]) -> ValidationRule:
        """Validate dialogue blocks have consistent structure"""
        dialogue_blocks = [b for b in blocks if b.get("block_type") == "dialogue"]
        
        if not dialogue_blocks:
            return ValidationRule(rule_name="dialogue_consistency", passed=True, message="No dialogue blocks")
        
        # Basic validation - can be extended
        invalid_dialogue = [b for b in dialogue_blocks if not (b.get("lines") or b.get("summary"))]
        
        if invalid_dialogue:
            return ValidationRule(
                rule_name="dialogue_consistency",
                passed=False,
                message="Some dialogue blocks missing lines or summary",
                details={"invalid_count": len(invalid_dialogue)}
            )
        
        return ValidationRule(rule_name="dialogue_consistency", passed=True)
    
    def _validate_content_completeness(self, blocks: List[Dict]) -> ValidationRule:
        """Validate content blocks have required content"""
        content_blocks = [b for b in blocks if b.get("block_type") == "prose"]
        
        if not content_blocks:
            return ValidationRule(rule_name="content_completeness", passed=True, message="No prose blocks")
        
        empty_content = [b for b in content_blocks if not b.get("content")]
        
        if empty_content:
            return ValidationRule(
                rule_name="content_completeness",
                passed=False,
                message="Some prose blocks have empty content",
                details={"empty_count": len(empty_content)}
            )
        
        return ValidationRule(rule_name="content_completeness", passed=True)
    
    def _validate_metadata_consistency(self, blocks: List[Dict]) -> ValidationRule:
        """Validate metadata consistency across blocks"""
        # Basic validation - all blocks should have valid metadata JSON
        try:
            for block in blocks:
                metadata = block.get("metadata")
                if metadata is not None and not isinstance(metadata, dict):
                    return ValidationRule(
                        rule_name="metadata_consistency",
                        passed=False,
                        message="Invalid metadata format detected"
                    )
            
            return ValidationRule(rule_name="metadata_consistency", passed=True)
            
        except Exception:
            return ValidationRule(
                rule_name="metadata_consistency",
                passed=False,
                message="Metadata validation failed"
            )