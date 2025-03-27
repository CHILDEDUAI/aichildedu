from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from common.database import get_db_session

from . import auth, crud, models, schemas

# Create a database session dependency
get_db = get_db_session()

# Create API router
router = APIRouter()

# Authentication routes
@router.post("/auth/login", response_model=schemas.TokenResponse)
async def login(
    request: Request,
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login and get access token
    """
    user, access_token, expiry_time = auth.login_user(
        db, 
        login_data.email, 
        login_data.password,
        request
    )
    
    # Convert to seconds since epoch for client-side expiry calculation
    expires_at = int(expiry_time.timestamp())
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "user": user
    }

@router.post("/auth/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    reset_request: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset token
    """
    # Generate token
    token = auth.generate_password_reset_token(db, reset_request.email)
    
    # Always return success, even if email doesn't exist (security)
    return {"message": "If your email is registered, you will receive a password reset link"}

@router.post("/auth/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_confirm: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using a reset token
    """
    success = auth.reset_password_with_token(
        db, 
        reset_confirm.token, 
        reset_confirm.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
        
    return {"message": "Password has been reset successfully"}

# User routes
@router.get("/users/me", response_model=schemas.UserResponse)
async def get_current_user_profile(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile
    """
    return user

@router.put("/users/me", response_model=schemas.UserResponse)
async def update_current_user_profile(
    user_update: schemas.UserUpdate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    """
    updated_user = crud.update_user(db, user.id, user_update)
    return updated_user

@router.put("/users/me/password", status_code=status.HTTP_200_OK)
async def update_current_user_password(
    password_update: schemas.UserPasswordUpdate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user password
    """
    success = crud.update_user_password(
        db, 
        user.id, 
        password_update.current_password, 
        password_update.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
        
    return {"message": "Password updated successfully"}

@router.get("/users/me/settings", response_model=schemas.UserSettingsResponse)
async def get_current_user_settings(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user settings
    """
    settings = crud.get_user_settings(db, user.id)
    if not settings:
        # Create default settings if not exist
        settings = crud.create_user_settings(db, user.id, schemas.UserSettingsCreate())
    return settings

@router.put("/users/me/settings", response_model=schemas.UserSettingsResponse)
async def update_current_user_settings(
    settings_update: schemas.UserSettingsUpdate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user settings
    """
    settings = crud.update_user_settings(db, user.id, settings_update)
    if not settings:
        # Create settings if not exist
        settings = crud.create_user_settings(db, user.id, settings_update)
    return settings

# Child related routes
@router.get("/users/me/children", response_model=List[schemas.ChildResponse])
async def get_current_user_children(
    skip: int = 0,
    limit: int = 100,
    user: models.User = Depends(auth.check_parent_or_admin_access),
    db: Session = Depends(get_db)
):
    """
    Get all children for current user (parent role)
    """
    return crud.get_children_by_parent(db, user.id, skip, limit)

@router.post("/users/me/children", response_model=schemas.ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child_account(
    child: schemas.ChildCreate,
    user: models.User = Depends(auth.check_parent_or_admin_access),
    db: Session = Depends(get_db)
):
    """
    Create a child account for current user (parent role)
    """
    return crud.create_child(db, user.id, child)

@router.get("/children/{child_id}", response_model=schemas.ChildResponse)
async def get_child(
    child_id: str,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a child by ID
    """
    # Get the child
    child = crud.get_child(db, child_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
        
    # Check if user is parent of this child or an admin
    if child.parent_id != user.id and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    return child

@router.put("/children/{child_id}", response_model=schemas.ChildResponse)
async def update_child(
    child_id: str,
    child_update: schemas.ChildUpdate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a child
    """
    # Get the child
    child = crud.get_child(db, child_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
        
    # Check if user is parent of this child or an admin
    if child.parent_id != user.id and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    # Update child
    updated_child = crud.update_child(db, child_id, child_update)
    return updated_child

@router.delete("/children/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: str,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a child
    """
    # Get the child
    child = crud.get_child(db, child_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
        
    # Check if user is parent of this child or an admin
    if child.parent_id != user.id and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    # Delete child
    crud.delete_child(db, child_id)

@router.get("/children/{child_id}/preferences", response_model=schemas.ChildPreferencesResponse)
async def get_child_preferences(
    child_id: str,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get child preferences
    """
    # Get the child
    child = crud.get_child(db, child_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
        
    # Check if user is parent of this child or an admin
    if child.parent_id != user.id and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    # Get preferences
    preferences = crud.get_child_preferences(db, child_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
        
    return preferences

@router.put("/children/{child_id}/preferences", response_model=schemas.ChildPreferencesResponse)
async def update_child_preferences(
    child_id: str,
    preferences: schemas.ChildPreferencesUpdate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update child preferences
    """
    # Get the child
    child = crud.get_child(db, child_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
        
    # Check if user is parent of this child or an admin
    if child.parent_id != user.id and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    # Update preferences
    updated_preferences = crud.update_child_preferences(db, child_id, preferences)
    if not updated_preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
        
    return updated_preferences

@router.get("/children/{child_id}/restrictions", response_model=schemas.ChildRestrictionsResponse)
async def get_child_restrictions(
    child_id: str,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get child restrictions
    """
    # Get the child
    child = crud.get_child(db, child_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
        
    # Check if user is parent of this child or an admin
    if child.parent_id != user.id and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    # Get restrictions
    restrictions = crud.get_child_restrictions(db, child_id)
    if not restrictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restrictions not found"
        )
        
    return restrictions

@router.put("/children/{child_id}/restrictions", response_model=schemas.ChildRestrictionsResponse)
async def update_child_restrictions(
    child_id: str,
    restrictions: schemas.ChildRestrictionsUpdate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update child restrictions
    """
    # Get the child
    child = crud.get_child(db, child_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
        
    # Check if user is parent of this child or an admin
    if child.parent_id != user.id and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    # Update restrictions
    updated_restrictions = crud.update_child_restrictions(db, child_id, restrictions)
    if not updated_restrictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restrictions not found"
        )
        
    return updated_restrictions

# Admin routes
@router.get("/admin/users", response_model=List[schemas.UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only)
    """
    return crud.get_users(db, skip, limit, is_active)

@router.get("/admin/users/{user_id}", response_model=schemas.UserResponse)
async def get_user_by_id(
    user_id: str,
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only)
    """
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.put("/admin/users/{user_id}", response_model=schemas.UserResponse)
async def admin_update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Update user (admin only)
    """
    updated_user = crud.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str,
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only)
    """
    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

# Role management (admin only)
@router.get("/admin/roles", response_model=List[schemas.RoleResponse])
async def get_all_roles(
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Get all roles (admin only)
    """
    return crud.get_roles(db)

@router.post("/admin/roles", response_model=schemas.RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: schemas.RoleCreate,
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Create a new role (admin only)
    """
    # Check if role already exists
    existing_role = crud.get_role_by_name(db, role.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role.name}' already exists"
        )
        
    return crud.create_role(db, role)

@router.put("/admin/roles/{role_id}", response_model=schemas.RoleResponse)
async def update_role(
    role_id: int,
    role: schemas.RoleUpdate,
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Update a role (admin only)
    """
    updated_role = crud.update_role(db, role_id, role)
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return updated_role

@router.delete("/admin/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    user: models.User = Depends(auth.check_admin_access),
    db: Session = Depends(get_db)
):
    """
    Delete a role (admin only)
    """
    success = crud.delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        ) 