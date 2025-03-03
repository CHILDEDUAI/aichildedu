from datetime import datetime
from typing import Dict, List, Optional, Union

import motor.motor_asyncio
from bson import ObjectId

from aichildedu.common.config import settings
from aichildedu.common.utils import generate_uuid

from .models import StoryTemplate, TaskStatus, TextGenerationTask


class Database:
    """MongoDB database operations for text generator service"""
    
    def __init__(self):
        """Initialize database connection"""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]
        self.tasks = self.db["text_generation_tasks"]
        self.templates = self.db["story_templates"]
        
        # Create indexes
        self._setup_indexes()
        
    async def _setup_indexes(self):
        """Set up database indexes"""
        # Task indexes
        await self.tasks.create_index("id", unique=True)
        await self.tasks.create_index("status")
        await self.tasks.create_index("user_id")
        await self.tasks.create_index("created_at")
        
        # Template indexes
        await self.templates.create_index("id", unique=True)
        await self.templates.create_index("name")
        await self.templates.create_index("is_active")
        
    # Task operations
    async def create_task(self, task_type: str, prompt: Dict, user_id: Optional[str] = None) -> str:
        """
        Create a new generation task
        
        Args:
            task_type: Type of content to generate (story, quiz, etc.)
            prompt: Generation prompt parameters
            user_id: Optional user ID
            
        Returns:
            Task ID
        """
        task_id = f"task_{generate_uuid()}"
        
        task = TextGenerationTask(
            id=task_id,
            user_id=user_id,
            type=task_type,
            status=TaskStatus.PENDING,
            prompt=prompt,
            created_at=datetime.utcnow()
        )
        
        await self.tasks.insert_one(task.dict())
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Get a task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dict or None if not found
        """
        task = await self.tasks.find_one({"id": task_id})
        return task
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus,
        error: Optional[str] = None
    ) -> bool:
        """
        Update task status
        
        Args:
            task_id: Task ID
            status: New status
            error: Optional error message if status is FAILED
            
        Returns:
            True if task was updated, False otherwise
        """
        update_data = {"status": status}
        
        if status == TaskStatus.PROCESSING:
            update_data["started_at"] = datetime.utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            update_data["completed_at"] = datetime.utcnow()
            
        if error and status == TaskStatus.FAILED:
            update_data["error"] = error
            
        result = await self.tasks.update_one(
            {"id": task_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def update_task_result(self, task_id: str, result: Dict) -> bool:
        """
        Update task result
        
        Args:
            task_id: Task ID
            result: Generation result
            
        Returns:
            True if task was updated, False otherwise
        """
        result = await self.tasks.update_one(
            {"id": task_id},
            {
                "$set": {
                    "result": result,
                    "status": TaskStatus.COMPLETED,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def update_task_model(self, task_id: str, model_name: str) -> bool:
        """
        Update the model used for a task
        
        Args:
            task_id: Task ID
            model_name: Model name
            
        Returns:
            True if task was updated, False otherwise
        """
        result = await self.tasks.update_one(
            {"id": task_id},
            {"$set": {"model_used": model_name}}
        )
        
        return result.modified_count > 0
    
    async def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """
        Get pending tasks
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of pending tasks
        """
        cursor = self.tasks.find({"status": TaskStatus.PENDING})
        cursor = cursor.sort("created_at", 1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_user_tasks(
        self, 
        user_id: str, 
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get tasks for a user
        
        Args:
            user_id: User ID
            status: Optional status or list of statuses to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of tasks
        """
        query = {"user_id": user_id}
        
        if status:
            if isinstance(status, list):
                query["status"] = {"$in": status}
            else:
                query["status"] = status
                
        cursor = self.tasks.find(query)
        cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
        
    async def count_user_tasks(
        self, 
        user_id: str, 
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None
    ) -> int:
        """
        Count tasks for a user
        
        Args:
            user_id: User ID
            status: Optional status or list of statuses to filter by
            
        Returns:
            Number of tasks
        """
        query = {"user_id": user_id}
        
        if status:
            if isinstance(status, list):
                query["status"] = {"$in": status}
            else:
                query["status"] = status
                
        return await self.tasks.count_documents(query)
    
    # Template operations
    async def create_template(self, template: StoryTemplate) -> str:
        """
        Create a new template
        
        Args:
            template: Template data
            
        Returns:
            Template ID
        """
        template_dict = template.dict()
        await self.templates.insert_one(template_dict)
        return template.id
    
    async def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Get a template by ID
        
        Args:
            template_id: Template ID
            
        Returns:
            Template dict or None if not found
        """
        return await self.templates.find_one({"id": template_id, "is_active": True})
    
    async def get_templates(
        self, 
        theme: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        educational_focus: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get templates with optional filtering
        
        Args:
            theme: Optional theme to filter by
            age_min: Optional minimum age to filter by
            age_max: Optional maximum age to filter by
            educational_focus: Optional educational focus to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of templates
        """
        query = {"is_active": True}
        
        if theme:
            query["themes"] = theme
            
        if educational_focus:
            query["educational_focus"] = educational_focus
            
        if age_min is not None:
            query["age_range.1"] = {"$gte": age_min}
            
        if age_max is not None:
            query["age_range.0"] = {"$lte": age_max}
            
        cursor = self.templates.find(query)
        cursor = cursor.sort("name", 1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def count_templates(
        self, 
        theme: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        educational_focus: Optional[str] = None
    ) -> int:
        """
        Count templates with optional filtering
        
        Args:
            theme: Optional theme to filter by
            age_min: Optional minimum age to filter by
            age_max: Optional maximum age to filter by
            educational_focus: Optional educational focus to filter by
            
        Returns:
            Number of templates
        """
        query = {"is_active": True}
        
        if theme:
            query["themes"] = theme
            
        if educational_focus:
            query["educational_focus"] = educational_focus
            
        if age_min is not None:
            query["age_range.1"] = {"$gte": age_min}
            
        if age_max is not None:
            query["age_range.0"] = {"$lte": age_max}
            
        return await self.templates.count_documents(query)
    
    async def update_template(self, template_id: str, updates: Dict) -> bool:
        """
        Update a template
        
        Args:
            template_id: Template ID
            updates: Updates to apply
            
        Returns:
            True if template was updated, False otherwise
        """
        updates["updated_at"] = datetime.utcnow()
        
        result = await self.templates.update_one(
            {"id": template_id},
            {"$set": updates}
        )
        
        return result.modified_count > 0
    
    async def delete_template(self, template_id: str) -> bool:
        """
        Delete a template (mark as inactive)
        
        Args:
            template_id: Template ID
            
        Returns:
            True if template was deleted, False otherwise
        """
        result = await self.templates.update_one(
            {"id": template_id},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0


# Create global database instance
db = Database() 