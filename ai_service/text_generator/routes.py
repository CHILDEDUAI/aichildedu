from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from aichildedu.common.auth import get_current_user_id, get_optional_user_id
from aichildedu.common.exceptions import ErrorResponse

from .db import db
from .generator import generator
from .models import TaskStatus
from .schemas import (
    GenerateQuizRequest, 
    GenerateStoryRequest, 
    QuizResponse, 
    StoryResponse, 
    TaskResponse, 
    TaskStatusResponse, 
    TextGenerationError
)

router = APIRouter(prefix="/text", tags=["Text Generation"])


@router.post("/story", response_model=TaskResponse)
async def generate_story(
    request: GenerateStoryRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
) -> Dict:
    """
    Start a story generation task
    
    Creates an asynchronous task to generate a story based on the provided parameters.
    Returns a task ID that can be used to check the status and retrieve the result.
    """
    try:
        task_id = await generator.create_story_task(request, user_id)
        
        # Create response
        return {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "estimated_time_seconds": 30,  # Approximate time estimate
            "status_check_url": f"/api/v1/ai/text/tasks/{task_id}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create story generation task: {str(e)}"
        )


@router.post("/quiz", response_model=TaskResponse)
async def generate_quiz(
    request: GenerateQuizRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
) -> Dict:
    """
    Start a quiz generation task
    
    Creates an asynchronous task to generate a quiz based on the provided parameters.
    Returns a task ID that can be used to check the status and retrieve the result.
    """
    try:
        task_id = await generator.create_quiz_task(request, user_id)
        
        # Create response
        return {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "estimated_time_seconds": 20,  # Approximate time estimate
            "status_check_url": f"/api/v1/ai/text/tasks/{task_id}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create quiz generation task: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse, responses={
    404: {"model": TextGenerationError}
})
async def get_task_status(
    task_id: str = Path(..., description="Task ID"),
) -> Dict:
    """
    Get the status of a generation task
    
    Returns the current status of the specified task, including timestamps
    for creation, start, and completion (if applicable).
    """
    status = await generator.get_task_status(task_id)
    
    if not status:
        raise HTTPException(
            status_code=404, 
            detail=f"Task with ID {task_id} not found"
        )
        
    # Add progress information
    if status["status"] == TaskStatus.PENDING:
        progress = 0
    elif status["status"] == TaskStatus.PROCESSING:
        progress = 50  # Arbitrary progress value
    elif status["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        progress = 100
    else:
        progress = 0
        
    status["progress"] = progress
    return status


@router.get("/tasks/{task_id}/result", response_model=Union[StoryResponse, QuizResponse], responses={
    404: {"model": TextGenerationError},
    400: {"model": TextGenerationError}
})
async def get_task_result(
    task_id: str = Path(..., description="Task ID"),
) -> Dict:
    """
    Get the result of a completed generation task
    
    Returns the generated content for a completed task.
    Returns an error if the task is not found or not completed.
    """
    # Get task status
    status = await generator.get_task_status(task_id)
    
    if not status:
        raise HTTPException(
            status_code=404, 
            detail=f"Task with ID {task_id} not found"
        )
        
    # Check if task is completed
    if status["status"] != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed (current status: {status['status']})"
        )
        
    # Get task result
    result = await generator.get_task_result(task_id)
    
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Task marked as completed but no result found"
        )
        
    # Add task_id to result
    result["task_id"] = task_id
    return result


@router.delete("/tasks/{task_id}", response_model=Dict[str, bool], responses={
    404: {"model": TextGenerationError},
    400: {"model": TextGenerationError}
})
async def cancel_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, bool]:
    """
    Cancel a pending or processing task
    
    Attempts to cancel a task that is still in the pending or processing state.
    Returns an error if the task is not found or cannot be cancelled.
    """
    # Check if task exists and belongs to user
    task = await db.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404, 
            detail=f"Task with ID {task_id} not found"
        )
        
    if task.get("user_id") and task.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to cancel this task"
        )
        
    # Cancel task
    cancelled = await generator.cancel_task(task_id)
    
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail=f"Task cannot be cancelled (current status: {task['status']})"
        )
        
    return {"success": True}


@router.get("/tasks", response_model=List[TaskStatusResponse])
async def get_user_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    limit: int = Query(10, description="Maximum number of tasks to return"),
    skip: int = Query(0, description="Number of tasks to skip"),
    user_id: str = Depends(get_current_user_id)
) -> List[Dict]:
    """
    Get tasks for the current user
    
    Returns a list of tasks for the authenticated user, with optional filtering by status.
    """
    # Convert status string to TaskStatus enum if provided
    task_status = None
    if status:
        try:
            task_status = TaskStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status value: {status}"
            )
    
    # Get tasks from database
    tasks = await db.get_user_tasks(
        user_id=user_id,
        status=task_status,
        skip=skip,
        limit=limit
    )
    
    # Format response
    result = []
    for task in tasks:
        # Add progress information
        if task["status"] == TaskStatus.PENDING:
            progress = 0
        elif task["status"] == TaskStatus.PROCESSING:
            progress = 50  # Arbitrary progress value
        elif task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            progress = 100
        else:
            progress = 0
            
        result.append({
            "task_id": task["id"],
            "status": task["status"],
            "progress": progress,
            "created_at": task.get("created_at"),
            "started_at": task.get("started_at"),
            "completed_at": task.get("completed_at"),
            "error": task.get("error"),
            "type": task.get("type")
        })
        
    return result


@router.get("/templates", response_model=List[Dict])
async def get_templates(
    theme: Optional[str] = Query(None, description="Filter by theme"),
    age_min: Optional[int] = Query(None, description="Minimum age (inclusive)"),
    age_max: Optional[int] = Query(None, description="Maximum age (inclusive)"),
    educational_focus: Optional[str] = Query(None, description="Filter by educational focus"),
    limit: int = Query(10, description="Maximum number of templates to return"),
    skip: int = Query(0, description="Number of templates to skip")
) -> List[Dict]:
    """
    Get story templates
    
    Returns a list of available story templates, with optional filtering.
    """
    templates = await db.get_templates(
        theme=theme,
        age_min=age_min,
        age_max=age_max,
        educational_focus=educational_focus,
        skip=skip,
        limit=limit
    )
    
    return templates


@router.get("/templates/{template_id}", response_model=Dict, responses={
    404: {"model": TextGenerationError}
})
async def get_template(
    template_id: str = Path(..., description="Template ID")
) -> Dict:
    """
    Get a story template by ID
    
    Returns the details of a specific story template.
    """
    template = await db.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with ID {template_id} not found"
        )
        
    return template 