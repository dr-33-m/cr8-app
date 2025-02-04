from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.db.session import get_db
from supabase import Client
from app.models.template import Template
from app.helpers.minio_helper import upload_file_to_minio
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/create", response_model=Template)
async def create_template(
    template_data: dict,
    db: Client = Depends(get_db)
) -> Any:
    # Extract required fields
    name = template_data.get("name")
    description = template_data.get("description")
    tags = template_data.get("tags")
    price = template_data.get("price")
    is_public = template_data.get("is_public", False)
    template_file = template_data.get("template_file")
    thumbnail = template_data.get("thumbnail")
    logto_userId = template_data.get("logto_userId")
    try:
        # Get user ID
        user_data = db.table("user").select("id").eq(
            "logto_id", logto_userId).execute()
        if not user_data.data:
            raise HTTPException(status_code=404, detail="User not found")

        creator_id = user_data.data[0]['id']

        # Upload template file to MinIO
        template_file_content = await template_file.read()
        template_path = f"templates/{uuid.uuid4()}/{template_file.filename}"
        template_minio_url = await upload_file_to_minio(template_file_content, template_path)

        # Optional: Upload thumbnail
        thumbnail_path = None
        if thumbnail:
            thumbnail_content = await thumbnail.read()
            thumbnail_path = f"templates/{uuid.uuid4()}/thumbnail_{thumbnail.filename}"
            thumbnail_minio_url = await upload_file_to_minio(thumbnail_content, thumbnail_path)

        # Prepare template data
        template_data = {
            "name": name,
            "description": description,
            "minio_path": template_minio_url,
            "thumbnail_path": thumbnail_minio_url if thumbnail else None,
            "tags": tags or [],
            "creator_id": creator_id,
            "price": price,
            "is_public": is_public,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Insert template
        result = db.table("template").insert(template_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to create template")

        # Convert to Template model
        template = result.data[0]
        template_model = Template(
            id=template.get("id"),
            name=template.get("name"),
            description=template.get("description"),
            minio_path=template.get("minio_path"),
            thumbnail_path=template.get("thumbnail_path"),
            tags=template.get("tags"),
            creator_id=template.get("creator_id"),
            price=template.get("price"),
            is_public=template.get("is_public")
        )

        return template_model

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[Template])
async def list_templates(
    db: Client = Depends(get_db),
    logto_userId: Optional[str] = None,
    is_public: Optional[bool] = True
):
    try:
        # If user ID is provided, filter templates by user or public templates
        query = db.table("template").select("*")

        if logto_userId:
            user_data = db.table("user").select("id").eq(
                "logto_id", logto_userId).execute()
            if user_data.data:
                user_id = user_data.data[0]['id']
                query = query.or_(
                    f"creator_id.eq.{user_id}",
                    "is_public.eq.true"
                )
        else:
            # If no user ID, only fetch public templates
            query = query.eq("is_public", True)

        result = query.execute()

        # Convert to Template models
        templates = [
            Template(
                id=template.get("id"),
                name=template.get("name"),
                description=template.get("description"),
                minio_path=template.get("minio_path"),
                thumbnail_path=template.get("thumbnail_path"),
                tags=template.get("tags"),
                creator_id=template.get("creator_id"),
                price=template.get("price"),
                is_public=template.get("is_public")
            ) for template in result.data or []
        ]

        return templates

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
