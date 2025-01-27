import logging
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.db.session import get_db
from supabase import Client
from app.models.moodboard import Moodboard, MoodboardImage
from app.helpers.minio_helper import upload_file_to_minio
import json
from datetime import datetime
import uuid


# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create_moodboard", response_model=Moodboard)
async def create_moodboard(moodboard_data: dict, db: Client = Depends(get_db)) -> Any:
    name = moodboard_data.get("name")
    description = moodboard_data.get("description")
    logto_userId = moodboard_data.get('logto_userId')

    if not name or not description or not logto_userId:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: name, description, and/or logto_userId"
        )

    # Query for the user ID in the db, filtering by logto_id
    user_data = db.table("user").select(
        "id").eq("logto_id", logto_userId).execute()

    if user_data.data:
        print("First Record:", user_data.data[0])

    # Check if user exists and get their ID
    if not user_data.data or len(user_data.data) == 0:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Extract the user ID from the query result
    user_id = user_data.data[0]['id']
    print("Extracted User ID:", user_id)

    # Insert new moodboard using Supabase
    new_moodboard_data = {
        "name": name,
        "description": description,
        "user_id": user_id,
        'created_at': "2024-01-05T00:00:00Z",
        "updated_at": "2024-01-05T00:00:00Z",
    }

    result = db.table("moodboard").insert(new_moodboard_data).execute()

    # Debug print for moodboard creation result
    print("Moodboard Creation Result:", result.data)

    if not result.data:
        raise HTTPException(
            status_code=500,
            detail="Failed to create moodboard"
        )

    # Map the Supabase response to the Moodboard model
    moodboard = result.data[0]
    moodboard_model = Moodboard(
        id=moodboard.get("id"),
        name=moodboard.get("name"),
        description=moodboard.get("description"),
        user_id=moodboard.get("user_id"),
        storyline="",
        keywords=[],
        industry=None,
        targetAudience="",
        theme=None,
        tone=None,
        videoReferences=[],
        colorPalette=[],
        usage_intent=None,
    )

    return moodboard_model


@router.put("/update_moodboard/{moodboard_id}")
async def update_moodboard(
    moodboard_id: int,
    moodboard_data: str = Form(...),  # JSON string of moodboard data
    images: List[UploadFile] = File(None),  # Optional list of images
    db: Client = Depends(get_db)
) -> Any:
    try:
        # Parse the moodboard_data JSON string
        moodboard_update = json.loads(moodboard_data)

        # Verify moodboard exists
        existing_moodboard = db.table("moodboard").select(
            "*").eq("id", moodboard_id).execute()
        if not existing_moodboard.data:
            raise HTTPException(status_code=404, detail="Moodboard not found")

        # Update moodboard fields
        update_data = {
            "storyline": moodboard_update.get("storyline"),
            "keywords": moodboard_update.get("keywords", []),
            "industry": moodboard_update.get("industry"),
            "targetAudience": moodboard_update.get("targetAudience"),
            "theme": moodboard_update.get("theme"),
            "tone": moodboard_update.get("tone"),
            "videoReferences": moodboard_update.get("videoReferences", []),
            "colorPalette": moodboard_update.get("colorPalette", []),
            "usage_intent": moodboard_update.get("usage_intent"),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Remove None values from update_data
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # Update moodboard in database
        updated_moodboard = db.table("moodboard").update(
            update_data
        ).eq("id", moodboard_id).execute()

        # Handle image uploads if provided
        if images:
            image_records = []
            # Get the images_metadata array from moodboard_update
            images_metadata = moodboard_update.get("images_metadata", [])

            for index, image in enumerate(images):
                # Get metadata for this specific image
                image_metadata = images_metadata[index] if index < len(
                    images_metadata) else {}

                # Extract category and annotation from metadata
                # Default to compositions if not specified
                category = image_metadata.get("category", "compositions")
                annotation = image_metadata.get("annotation", "")
                filename = image_metadata.get("filename", f"image_{index}.jpg")
                # Read the file content
                file_content = await image.read()
                # Upload image to MinIO using the updated helper function
                file_url = await upload_file_to_minio(file_content, f"moodboard_{moodboard_id}", filename)

                # Generate a unique ID for the image
                image_id = uuid.uuid4().int % (2**31)

                # Create image record
                image_data = {
                    "id": image_id,  # Set a unique ID
                    "moodboard_id": moodboard_id,
                    "file": file_url,
                    "annotation": annotation,
                    "category": category
                }

                # Insert image record into database
                image_result = db.table("moodboardimage").insert(
                    image_data).execute()
                image_records.extend(image_result.data)
                # Reset file pointer for potential future use
                await image.seek(0)

        # Fetch the complete updated moodboard with images
        result = db.table("moodboard").select(
            "*",
            "images:moodboardimage(*)"
        ).eq("id", moodboard_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to fetch updated moodboard")

        # Convert to Moodboard model
        moodboard_data = result.data[0]
        return Moodboard(
            id=moodboard_data.get("id"),
            user_id=moodboard_data.get("user_id"),
            name=moodboard_data.get("name"),
            description=moodboard_data.get("description"),
            storyline=moodboard_data.get("storyline"),
            keywords=moodboard_data.get("keywords", []),
            industry=moodboard_data.get("industry"),
            targetAudience=moodboard_data.get("targetAudience"),
            theme=moodboard_data.get("theme"),
            tone=moodboard_data.get("tone"),
            videoReferences=moodboard_data.get("videoReferences", []),
            colorPalette=moodboard_data.get("colorPalette", []),
            usage_intent=moodboard_data.get("usage_intent"),
            created_at=moodboard_data.get("created_at"),
            updated_at=moodboard_data.get("updated_at")
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON in moodboard_data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[Moodboard])
async def list_moodboards(
    db: Client = Depends(get_db),
    logto_userId: Optional[str] = None
) -> Any:
    try:
        # Base query to fetch moodboards with all required fields
        query = db.table("moodboard").select(
            "id", "name", "description", "user_id",
            "storyline", "keywords", "industry", "targetAudience",
            "theme", "tone", "videoReferences", "colorPalette",
            "usage_intent", "created_at", "updated_at"
        )

        # If user ID is provided, filter moodboards by user
        if logto_userId:
            user_data = db.table("user").select("id").eq(
                "logto_id", logto_userId).execute()
            if user_data.data:
                user_id = user_data.data[0]['id']
                query = query.eq("user_id", user_id)

        # Execute the query
        result = query.execute()

        # Convert to Moodboard models
        moodboards = [
            Moodboard(
                id=moodboard.get("id"),
                name=moodboard.get("name"),
                description=moodboard.get("description"),
                user_id=moodboard.get("user_id"),
                storyline=moodboard.get("storyline"),
                # Replace None with []
                keywords=moodboard.get("keywords") or [],
                industry=moodboard.get("industry"),
                targetAudience=moodboard.get("targetAudience"),
                theme=moodboard.get("theme"),
                tone=moodboard.get("tone"),
                videoReferences=moodboard.get(
                    "videoReferences") or [],  # Replace None
                colorPalette=moodboard.get(
                    "colorPalette") or [],  # Replace None
                usage_intent=moodboard.get("usage_intent"),
                created_at=moodboard.get("created_at"),
                updated_at=moodboard.get("updated_at")
            ) for moodboard in (result.data or [])
        ]

        return moodboards
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
