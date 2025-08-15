import requests
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


def get_addon_preferences(context):
    """Get addon preferences safely"""
    addon_name = __package__.split('.')[0]
    prefs = context.preferences.addons.get(addon_name)
    if prefs is None:
        raise RuntimeError(
            f"Could not find addon preferences for {addon_name}")
    return prefs.preferences


def upload_template(context, template_data, thumbnail_path=None):
    preferences = get_addon_preferences(context)

    files = {}
    if thumbnail_path and Path(thumbnail_path).exists():
        files['thumbnail'] = ('thumbnail.png', open(
            thumbnail_path, 'rb'), 'image/png')

    template_data['logto_userId'] = preferences.user_id
    form_data = {
        'template_data': json.dumps(template_data)
    }

    try:
        response = requests.post(
            f"{preferences.api_url}/templates/create",
            files=files,
            data=form_data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to upload template: {str(e)}")


def fetch_templates(context, template_type: Optional[str] = None, name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch templates from the server"""
    preferences = get_addon_preferences(context)

    params = {
        'logto_userId': preferences.user_id
    }

    # Map Blender template types to API template types
    type_mapping = {
        'CAMERA': 'camera',
        'LIGHT': 'light',
        'PRODUCT': 'product'
    }

    if template_type:
        # Convert from Blender enum to API type
        api_template_type = type_mapping.get(template_type)
        if api_template_type:
            params['template_type'] = api_template_type

    if name:
        params['name'] = name

    try:
        response = requests.get(
            f"{preferences.api_url}/templates/list",
            params=params
        )
        response.raise_for_status()
        templates = response.json()
        return templates
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch templates: {str(e)}")
