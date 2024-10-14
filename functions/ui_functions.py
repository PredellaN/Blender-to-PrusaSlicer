import bpy
import requests
import json
import os
from .. import blender_globals

def update_manifest(preferences):
    global blender_globals
    blender_globals["print_profiles"] = load_manifest(preferences.manifest_path)
    return

def load_manifest(profiles_manifest_path):
    if not profiles_manifest_path:
        return {}
    profiles_manifest = json_to_dict(profiles_manifest_path)
    if profiles_manifest is None:
        return {}
    profiles_manifest = make_absolute_path(profiles_manifest, profiles_manifest_path)
    return profiles_manifest

def make_absolute_path(profiles_manifest, profiles_manifest_path):
    # Extract the directory path from profiles_manifest_path
    base_path = os.path.dirname(profiles_manifest_path)
    
    for profile in profiles_manifest:
        if profiles_manifest_path.startswith("http://") or profiles_manifest_path.startswith("https://"):
            # If it's a URL, concatenate using a forward slash
            profile['absolute_path'] = base_path.rstrip("/") + "/" + profile['path'].lstrip("/")
        else:
            # If it's a local file path, use os.path.join
            profile['absolute_path'] = os.path.join(base_path, profile['path'])
    return profiles_manifest

def json_to_dict(source):
    try:
        # Check if the source is a URL
        if source.startswith('http://') or source.startswith('https://'):
            response = requests.get(source)
            response.raise_for_status()  # Raise an exception for HTTP errors
            profiles = response.json()   # Parse JSON from the URL content
        else:
            # Assume it's a file path and read from the local file system
            with open(source, 'r') as file:
                profiles = json.load(file)
        
        return profiles

    except (FileNotFoundError, json.JSONDecodeError, requests.RequestException) as e:
        print(f"Error loading profiles: {e}")
        return None