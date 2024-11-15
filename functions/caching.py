import os
import json
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor, wait
from configparser import ConfigParser, MissingSectionHeaderError
from .. import ADDON_FOLDER

# Paths for cache storage
CACHE_DIR = os.path.join(ADDON_FOLDER, 'cache', 'profile_cache')
CACHE_INDEX_PATH = os.path.join(ADDON_FOLDER, 'cache', 'cache.json')

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def load_cache_index():
    if os.path.exists(CACHE_INDEX_PATH):
        with open(CACHE_INDEX_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_cache_index(cache_index):
    with open(CACHE_INDEX_PATH, 'w') as f:
        json.dump(cache_index, f, indent=4)

def get_etag(url):
    try:
        print("Web Access: Requesting etag")
        response = requests.head(url)
        return response.headers.get('ETag')
    except requests.RequestException:
        return None

def generate_cache_path(key):
    """Generate a unique cache file path based on the header."""
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{key_hash}.json")

def download_file(url):
    """Download the file from URL."""
    print("Web Access: Requesting file")
    response = requests.get(url)
    response.raise_for_status()
    return response

def process_ini_to_cache_dict(header, content):
    # Parsing the ini content into a dictionary
    config = ConfigParser(interpolation=None)
    try:
        config.read_string(content)
    except MissingSectionHeaderError:
        default_section = f"[{header}]\n" + content
        config.read_string(default_section)

    # Converting ConfigParser to a dictionary
    ini_dict = {
        section: dict(sorted(config.items(section)))
        for section in sorted(config.sections())
    }

    configs_flat = {}
    for key, val in ini_dict.items():
        if ":" in key:
            configs_flat[key] = {
                'profile': val,
                'id': key.split(':')[1] if len(key.split(':')) > 1 else key,
                'category': key.split(':')[0] if len(key.split(':')) > 1 else None
            }
    return configs_flat

def update_cache_for_entry(entry, cache_index, force_refetch = False):
    """Update the cache for a single entry and update the cache index accordingly."""
    cache_path = generate_cache_path(entry['url'])

    if os.path.exists(cache_path) and not force_refetch:
        return "SKIP"

    # Download the file and update cache
    response = download_file(entry['url'])
    configs_flat = process_ini_to_cache_dict(entry['header'], response.text)

    # Save the configs_flat to cache file
    with open(cache_path, 'w') as f:
        json.dump(configs_flat, f, indent=4)

    # Update the cache_index
    for key in configs_flat:
        cache_index[key] = {
            'header': key,
            'path': cache_path,
            'bundle_url': entry['bundle_url'],
            'url': entry['url'],
            'id': configs_flat[key]['id'],
            'category': configs_flat[key]['category'],
        }
    
    return "UPDATED"

def purge_outdated_entries(cache_index):
    # Build set of cache files that are referenced in cache_index
    cache_files_in_index = set(os.path.basename(entry['path']) for entry in cache_index.values())

    # Get all cache files in the cache directory
    cache_files_on_disk = set(os.listdir(CACHE_DIR))

    # Remove any cache files that are not referenced in cache_index
    orphaned_files = cache_files_on_disk - cache_files_in_index
    for filename in orphaned_files:
        filepath = os.path.join(CACHE_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

def update_cache(entries):
    ensure_cache_dir()
    cache_index = load_cache_index()

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(update_cache_for_entry, entry, cache_index) for entry in entries]
        wait(futures)

    save_cache_index(cache_index)
    purge_outdated_entries(cache_index)

def update_cache_for_id(id):
    ensure_cache_dir()
    cache_index = load_cache_index()

    cache_entry = cache_index[id]
    res = update_cache_for_entry(cache_entry, cache_index, force_refetch = True)
    
    if res == "SKIP":
        return

    save_cache_index(cache_index)
    purge_outdated_entries(cache_index)
