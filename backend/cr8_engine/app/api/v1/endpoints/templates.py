from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.db.session import get_db
from supabase import Client
from app.models.template import Template
from app.schemas.template import TemplateRead, TemplateCreate
from app.helpers.minio_helper import upload_file_to_minio
import uuid
from datetime import datetime
import json

router = APIRouter()


@router.post("/create", response_model=TemplateRead)
async def create_template(
    thumbnail: UploadFile = File(None),
    template_data: str = Form(...),
    db: Client = Depends(get_db)
) -> Any:
    # Parse JSON data from form field
    try:
        template_data_dict = json.loads(template_data)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON data: {str(e)}")

    # Extract user ID
    logto_userId = template_data_dict.get("logto_userId")
    if not logto_userId:
        raise HTTPException(status_code=400, detail="logto_userId is required")

    # Fetch user data
    user_data = db.table("user").select("id").eq(
        "logto_id", logto_userId).execute()
    if not user_data.data:
        raise HTTPException(status_code=404, detail="User not found")
    creator_id = user_data.data[0]['id']

    # Handle thumbnail upload
    thumbnail_url = None
    if thumbnail:
        thumbnail_content = await thumbnail.read()
        thumbnail_folder = "templates"
        thumbnail_filename = f"thumbnail_{thumbnail.filename}"
        thumbnail_url = await upload_file_to_minio(thumbnail_content, thumbnail_folder, thumbnail_filename)

    # Prepare template payload
    template_payload = {
        "name": template_data_dict.get("name"),
        "template_type": template_data_dict.get("type", "camera"),
        "templateData": {
            "relative_transform": template_data_dict.get("relative_transform"),
            "focal_length": template_data_dict.get("focal_length"),
            "dof_distance": template_data_dict.get("dof_distance"),
            "animation_data": template_data_dict.get("animation_data"),
            "constraints": template_data_dict.get("constraints", []),
        },
        "thumbnail": thumbnail_url,
        "creator_id": creator_id,
        "is_public": template_data_dict.get("is_public", True),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    try:
        result = db.table("template").insert(template_payload).execute()
        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to create template")
        return result.data[0]
    except Exception as e:
        print("Database error:", str(e))
        print("Full exception:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[TemplateRead])
async def list_templates(
    db: Client = Depends(get_db),
    logto_userId: Optional[str] = None,
    template_type: Optional[str] = None,
    name: Optional[str] = None,
    is_public: Optional[bool] = True
):
    try:
        # Start with base query
        query = db.table("template").select("*")

        # Handle user-specific and public templates
        if logto_userId:
            # First get the user_id from logto_id
            user_data = db.table("user").select("id").eq(
                "logto_id", logto_userId).execute()

            if user_data.data and len(user_data.data) > 0:
                user_id = user_data.data[0]['id']
                # Use an OR filter
                query = query.filter('is_public', 'eq', True).filter(
                    'creator_id', 'eq', user_id)
        else:
            # If no user ID provided, only show public templates
            query = query.eq("is_public", True)

        # Add type filter if provided
        if template_type:
            query = query.eq("template_type", template_type)

        # Add name filter if provided
        if name:
            query = query.ilike("name", f"%{name}%")

        # Execute the query
        result = query.execute()

        if result.data is None:
            return []

        # Convert to TemplateRead schema
        return [
            TemplateRead(
                id=template.get("id"),
                name=template.get("name"),
                template_type=template.get("template_type"),
                templateData=template.get("templateData"),
                thumbnail=template.get("thumbnail"),
                compatible_templates=template.get("compatible_templates"),
                is_public=template.get("is_public"),
                created_at=template.get("created_at"),
                updated_at=template.get("updated_at"),
                creator_id=template.get("creator_id")
            ) for template in result.data
        ]

    except Exception as e:
        print(f"Error in list_templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
