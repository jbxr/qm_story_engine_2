"""Scene and scene block business logic"""

from typing import List, Optional
from sqlmodel import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime
import logging

from ..models.entities import Scene, SceneBlock, SceneRead, SceneBlockRead, SceneCreate, SceneBlockCreate, SceneBlockUpdate, SceneBlockMoveRequest
from .database import DatabaseService

logger = logging.getLogger(__name__)


class SceneService(DatabaseService):
    """Business logic for scene and scene block operations"""
    
    async def create_scene(self, scene_data: SceneCreate) -> Scene:
        """Create a new scene"""
        try:
            scene = Scene(
                title=scene_data.title,
                description=scene_data.description,
                timestamp=scene_data.timestamp
            )
            self.db.add(scene)
            await self.db.commit()
            await self.db.refresh(scene)
            return scene
        except Exception as e:
            logger.error(f"Create scene failed: {e}")
            await self.db.rollback()
            raise
    
    async def get_scene(self, scene_id: UUID, include_blocks: bool = True) -> Optional[Scene]:
        """Get scene by ID with optional block loading"""
        try:
            query = select(Scene).where(Scene.id == scene_id)
            
            if include_blocks:
                query = query.options(selectinload(Scene.blocks))
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get scene failed: {e}")
            raise
    
    async def list_scenes(
        self, 
        limit: int = 50, 
        offset: int = 0, 
        include_blocks: bool = False
    ) -> List[Scene]:
        """List scenes with pagination"""
        try:
            query = select(Scene).order_by(Scene.created_at.desc()).limit(limit).offset(offset)
            
            if include_blocks:
                query = query.options(selectinload(Scene.blocks))
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"List scenes failed: {e}")
            raise
    
    async def update_scene(self, scene_id: UUID, scene_data: SceneCreate) -> Optional[Scene]:
        """Update scene"""
        try:
            scene = await self.get_scene(scene_id, include_blocks=False)
            if not scene:
                return None
            
            scene.title = scene_data.title
            scene.description = scene_data.description
            scene.timestamp = scene_data.timestamp
            
            await self.db.commit()
            await self.db.refresh(scene)
            return scene
        except Exception as e:
            logger.error(f"Update scene failed: {e}")
            await self.db.rollback()
            raise
    
    async def delete_scene(self, scene_id: UUID) -> bool:
        """Delete scene and all its blocks"""
        try:
            # Delete all scene blocks first
            await self.db.execute(
                delete(SceneBlock).where(SceneBlock.scene_id == scene_id)
            )
            
            # Delete the scene
            result = await self.db.execute(
                delete(Scene).where(Scene.id == scene_id)
            )
            
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Delete scene failed: {e}")
            await self.db.rollback()
            raise
    
    async def create_scene_block(self, scene_id: UUID, block_data: SceneBlockCreate) -> SceneBlock:
        """Create new block in scene with auto-ordering"""
        try:
            # Get current max order for scene
            max_order = await self._get_max_block_order(scene_id)
            order = block_data.order if hasattr(block_data, 'order') and block_data.order is not None else max_order + 1
            
            block = SceneBlock(
                scene_id=scene_id,
                block_type=block_data.block_type,
                content=block_data.content,
                order=order
            )
            
            self.db.add(block)
            await self.db.commit()
            await self.db.refresh(block)
            return block
        except Exception as e:
            logger.error(f"Create scene block failed: {e}")
            await self.db.rollback()
            raise
    
    async def create_multiple_blocks(
        self, 
        scene_id: UUID, 
        blocks_data: List[SceneBlockCreate]
    ) -> List[SceneBlock]:
        """Create multiple blocks in a scene"""
        try:
            base_order = await self._get_max_block_order(scene_id)
            blocks = []
            
            for i, block_data in enumerate(blocks_data):
                order = block_data.order if hasattr(block_data, 'order') and block_data.order is not None else base_order + i + 1
                
                block = SceneBlock(
                    scene_id=scene_id,
                    block_type=block_data.block_type,
                    content=block_data.content,
                    order=order
                )
                blocks.append(block)
                self.db.add(block)
            
            await self.db.commit()
            
            # Refresh all blocks
            for block in blocks:
                await self.db.refresh(block)
            
            return blocks
        except Exception as e:
            logger.error(f"Create multiple blocks failed: {e}")
            await self.db.rollback()
            raise
    
    async def get_scene_block(self, block_id: UUID) -> Optional[SceneBlock]:
        """Get scene block by ID"""
        try:
            result = await self.db.execute(
                select(SceneBlock).where(SceneBlock.id == block_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get scene block failed: {e}")
            raise
    
    async def update_block(self, block_id: UUID, block_data: SceneBlockUpdate) -> Optional[SceneBlock]:
        """Update block content or order"""
        try:
            block = await self.get_scene_block(block_id)
            if not block:
                return None
            
            if block_data.content is not None:
                block.content = block_data.content
            if block_data.order is not None:
                # Simple order update - for complex reordering use move_block
                block.order = block_data.order
            
            await self.db.commit()
            await self.db.refresh(block)
            return block
        except Exception as e:
            logger.error(f"Update block failed: {e}")
            await self.db.rollback()
            raise
    
    async def move_block(self, block_id: UUID, move_request: SceneBlockMoveRequest) -> Optional[SceneBlock]:
        """Reorder block within scene with proper gap management"""
        try:
            # Get the block to move
            block = await self.get_scene_block(block_id)
            if not block:
                return None
            
            current_order = block.order
            new_order = move_request.new_order
            scene_id = block.scene_id
            
            if current_order == new_order:
                return block  # No change needed
            
            # Update order of other blocks to make space
            if new_order < current_order:
                # Moving up - shift blocks down
                await self.db.execute(
                    update(SceneBlock)
                    .where(
                        SceneBlock.scene_id == scene_id,
                        SceneBlock.order >= new_order,
                        SceneBlock.order < current_order
                    )
                    .values(order=SceneBlock.order + 1)
                )
            else:
                # Moving down - shift blocks up
                await self.db.execute(
                    update(SceneBlock)
                    .where(
                        SceneBlock.scene_id == scene_id,
                        SceneBlock.order > current_order,
                        SceneBlock.order <= new_order
                    )
                    .values(order=SceneBlock.order - 1)
                )
            
            # Update the target block's order
            block.order = new_order
            
            await self.db.commit()
            await self.db.refresh(block)
            return block
        except Exception as e:
            logger.error(f"Move block failed: {e}")
            await self.db.rollback()
            raise
    
    async def delete_block(self, block_id: UUID) -> bool:
        """Delete block and reorder remaining blocks"""
        try:
            # Get the block to delete
            block = await self.get_scene_block(block_id)
            if not block:
                return False
            
            scene_id = block.scene_id
            deleted_order = block.order
            
            # Delete the block
            await self.db.execute(
                delete(SceneBlock).where(SceneBlock.id == block_id)
            )
            
            # Shift remaining blocks up to fill the gap
            await self.db.execute(
                update(SceneBlock)
                .where(
                    SceneBlock.scene_id == scene_id,
                    SceneBlock.order > deleted_order
                )
                .values(order=SceneBlock.order - 1)
            )
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Delete block failed: {e}")
            await self.db.rollback()
            raise
    
    async def get_scene_blocks(self, scene_id: UUID) -> List[SceneBlock]:
        """Get all blocks for a scene in order"""
        try:
            result = await self.db.execute(
                select(SceneBlock)
                .where(SceneBlock.scene_id == scene_id)
                .order_by(SceneBlock.order)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Get scene blocks failed: {e}")
            raise
    
    async def _get_max_block_order(self, scene_id: UUID) -> int:
        """Get maximum order value for blocks in scene"""
        try:
            result = await self.db.execute(
                select(func.max(SceneBlock.order))
                .where(SceneBlock.scene_id == scene_id)
            )
            max_order = result.scalar()
            return max_order if max_order is not None else 0
        except Exception as e:
            logger.error(f"Get max block order failed: {e}")
            return 0