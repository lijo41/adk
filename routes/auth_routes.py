"""Authentication routes for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db
from schemas.simplified_schemas import UserDB
from models.auth_models import UserRegister, UserLogin, Token, UserResponse, UserUpdate
from auth.jwt_utils import verify_password, get_password_hash, create_user_token
from auth.dependencies import get_current_active_user

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])


@auth_router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(UserDB).filter(
        (UserDB.email == user_data.email) | (UserDB.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Check if GSTIN already exists
    existing_gstin = db.query(UserDB).filter(UserDB.gstin == user_data.gstin).first()
    if existing_gstin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GSTIN already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = UserDB(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        company_name=user_data.company_name,
        gstin=user_data.gstin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@auth_router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(UserDB).filter(UserDB.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_user_token(
        user_id=user.id,
        email=user.email,
        company_name=user.company_name,
        gstin=user.gstin
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserDB = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@auth_router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information."""
    # Update fields if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.company_name is not None:
        current_user.company_name = user_update.company_name
    if user_update.gstin is not None:
        # Check if new GSTIN already exists
        existing_gstin = db.query(UserDB).filter(
            UserDB.gstin == user_update.gstin,
            UserDB.id != current_user.id
        ).first()
        if existing_gstin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GSTIN already registered by another user"
            )
        current_user.gstin = user_update.gstin
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user
