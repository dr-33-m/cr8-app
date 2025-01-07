from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.db.session import get_db
from supabase import Client

router = APIRouter()


@router.post("/register", response_model=User)
async def register_user(user_data: dict, db: Client = Depends(get_db)) -> Any:
    logto_id = user_data.get("logto_id")
    email = user_data.get("email")
    username = user_data.get("username")
    subscription_active = True

    if not all([logto_id, email, username]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Check if user exists using Supabase query
    existing_user = db.table("user").select(
        "*").eq("logto_id", logto_id).execute()
    if existing_user.data:
        raise HTTPException(status_code=400, detail="User already exists")

    # Insert new user using Supabase
    new_user_data = {
        "logto_id": logto_id,
        "email": email,
        "username": username,
        "subscription_active": subscription_active,
    }

    result = db.table("user").insert(new_user_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    # Map the Supabase response to the User model (only returning basic fields)
    user = result.data[0]  # Assuming this is a dictionary from Supabase
    user_model = User(
        id=user.get("id"),
        logto_id=user.get("logto_id"),
        email=user.get("email"),
        username=user.get("username"),
        subscription_active=user.get("subscription_active", True),
    )

    return user_model


@router.get("/check/{logto_id}")
async def check_user_exists(logto_id: str, db: Client = Depends(get_db)) -> dict:
    """
    Check if a user exists based on their Logto ID.
    Returns 200 if user exists, 404 if not found.
    """
    try:
        print(f"Checking for user with logto_id: {logto_id}")

        if not db:
            raise HTTPException(
                status_code=500,
                detail="Database connection not available"
            )

        result = db.table("user").select("id").eq(
            "logto_id", logto_id).execute()
        print(f"Query result: {result}")

        if result.data and len(result.data) > 0:
            return {"exists": True, "message": "User found"}

        # Change this from return to raise
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        print(f"Full error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking user existence: {str(e)}"
        )
