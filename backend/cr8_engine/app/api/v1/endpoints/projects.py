from typing import Any, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.db.session import get_db
from app.models.project import Project
from app.models.template import Template


router = APIRouter()


@router.post("/create", response_model=Project)
async def create_project(
    project_data: dict,
    db: Client = Depends(get_db)
) -> Any:
    # Extract required fields
    name = project_data.get("name")
    description = project_data.get("description")
    project_type = project_data.get("project_type")
    subtype = project_data.get("subtype")
    project_status = project_data.get("project_status", "draft")
    template = project_data.get("template")
    logto_userId = project_data.get(
        "logto_userId")  # Now extracted from payload

    # Validate logto_userId is provided
    if not logto_userId:
        raise HTTPException(status_code=400, detail="User ID is required")

    # Query for the user ID
    user_data = db.table("user").select("id").eq(
        "logto_id", logto_userId).execute()
    if not user_data.data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data.data[0]['id']

    # Prepare project data for insertion
    new_project_data = {
        "name": name,
        "description": description,
        "user_id": user_id,
        "project_type": project_type,
        "subtype": subtype,
        "project_status": project_status,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Insert project
    result = db.table("project").insert(new_project_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create project")

    # If template is provided, create project-template association
    if template:
        try:
            # Validate template exists and is accessible
            template_data = db.table("template").select(
                "id", "is_public", "creator_id").eq("id", template).execute()

            if not template_data.data:
                raise HTTPException(
                    status_code=404, detail="Template not found")

            template_info = template_data.data[0]
            # Optional: Check template accessibility (public or created by user)
            if not template_info['is_public'] and template_info['creator_id'] != user_id:
                raise HTTPException(
                    status_code=403, detail="Template not accessible")

            # Create project-template association
            template_project_data = {
                "project_id": result.data[0]['id'],
                "template_id": template,
                "associated_at": datetime.utcnow().isoformat()
            }

            db.table("project_template").insert(
                template_project_data).execute()

        except Exception as e:
            # Log the error, but don't block project creation
            print(f"Template association error: {e}")

    # Convert to Project model
    project = result.data[0]
    project_model = Project(
        id=project.get("id"),
        name=project.get("name"),
        description=project.get("description"),
        user_id=project.get("user_id"),
        project_type=project.get("project_type"),
        subtype=project.get("subtype"),
        project_status=project.get("project_status")
    )
    return project_model
