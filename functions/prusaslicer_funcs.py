
import os
import tempfile
import subprocess

from .basic_functions import load_manifest
from .caching import update_cache

temp_dir = tempfile.gettempdir()

def exec_prusaslicer(command, prusaslicer_path):

    if os.path.exists(prusaslicer_path):
        command=[f'{prusaslicer_path}'] + command
    else:
        command=[*prusaslicer_path.split() + command]

    print(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    except subprocess.CalledProcessError as e:
        if e.stderr:
            print("PrusaSlicer error output:")
            print(e.stderr)
            return f"PrusaSlicer failed with error output: {e.stderr}"
        return f"PrusaSlicer failed with return code {e.returncode}"

    if result.stdout:
        print("PrusaSlicer output:")
        print(result.stdout)
        for line in result.stdout.splitlines():
            if "[error]" in line.lower():
                error_part = line.lower().split("[error]", 1)[1].strip()
                err_to_tempfile(result.stderr)
                return error_part

            if "slicing result exported" in line.lower():
                return

        tempfile = err_to_tempfile(result.stderr + "\n\n" + result.stdout)
        return f"Slicing failed, error log at {tempfile}."
    
def err_to_tempfile(text):
    temp_file_path = os.path.join(temp_dir, "prusa_slicer_err_output.txt")
    with open(temp_file_path, "w") as temp_file:
        temp_file.write(text)
    return temp_file_path

def filter_prusaslicer_dict_by_section(dict, section):
    return {k.split(":")[1]: v for k, v in dict.items() if k.split(":")[0] == section}

def configs_to_cache(urls):
    entries = []
    for url in urls:
        if url.endswith(".json"):
            manifest = load_manifest(url)
            entries.extend([{
                'bundle_url' : url,
                'url' : item['absolute_path'],
                'header' : f"{item['type']}:{item['label']}",
            } for item in manifest])
        else:
            entries.extend([{
                'bundle_url' : url,
                'url' : url,
                'header' : "unknown:unknown",
            }])

    update_cache(entries)

    return