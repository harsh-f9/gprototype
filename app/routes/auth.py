from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from app.database import get_db
from app.db_models import User, UserProfile
from app.models import ContactForm
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate to 72 bytes for bcrypt compatibility
    password_bytes = plain_password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(truncated_password, hashed_password)

def get_password_hash(password: str) -> str:
    # bcrypt limit is 72 bytes. Truncate at byte level.
    password_bytes = password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_password)

# Helper to get current user from session
def get_current_user_id(request: Request) -> Optional[int]:
    return request.session.get("user_id")

def require_auth(request: Request) -> int:
    """Dependency to require authentication"""
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id

# --- Registration Routes ---

@router.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    # Get onboarding data from session if available
    category = request.session.get("user_category", "unknown")
    return templates.TemplateResponse("register.html", {
        "request": request,
        "category": category
    })

@router.post("/register", response_class=HTMLResponse)
async def post_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Validate password length (max 72 characters for bcrypt)
    if len(password) > 72:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error_msg": "Password must be 72 characters or less"
        })
    
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error_msg": "Passwords do not match"
        })
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error_msg": "Email already registered. Please login."
        })
    
    try:
        # Create new user
        hashed_pw = get_password_hash(password)
        new_user = User(email=email, hashed_password=hashed_pw)
        db.add(new_user)
        await db.flush()  # Get the user.id
        
        # Create user profile with onboarding data from session
        category = request.session.get("user_category")
        initial_data = request.session.get("initial_data")
        
        profile = UserProfile(
            user_id=new_user.id,
            category=category,
            initial_data=initial_data
        )
        db.add(profile)
        await db.commit()
        
        # Log user in
        request.session["user_id"] = new_user.id
        request.session["user_email"] = new_user.email
        
        # Redirect to intake form
        return RedirectResponse(url=f"/intake/{category}", status_code=303)
        
    except Exception as e:
        await db.rollback()
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error_msg": f"Error creating account: {str(e)}"
        })

# --- Login Routes ---

@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error_msg": "Invalid email or password"
        })
    
    # Set session
    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    
    # Check if user has a profile with category
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    
    if profile and profile.category:
        # User has completed onboarding, redirect to dashboard or intake
        if profile.intake_data:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return RedirectResponse(url=f"/intake/{profile.category}", status_code=303)
    else:
        # User needs to complete onboarding
        return RedirectResponse(url="/onboarding", status_code=303)

# --- Logout Route ---

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
