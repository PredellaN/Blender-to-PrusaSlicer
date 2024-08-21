import bpy # type: ignore
import os, subprocess, time, tempfile, threading, re, json
from collections import Counter
import urllib.request

from .functions.basic_functions import show_progress

temp_dir = tempfile.gettempdir() 

def load_config_file(file_path_or_url):
    config_dict = {}

    if file_path_or_url.startswith('http://') or file_path_or_url.startswith('https://'):
        response = urllib.request.urlopen(file_path_or_url)
        file_content = response.read().decode('utf-8')

        config_local_path = os.path.join(temp_dir, 'config.ini')
        with open(config_local_path, 'w') as file:
            file.write(file_content)

    else:
        config_local_path = bpy.path.abspath(file_path_or_url)

    with open(config_local_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue

        key, value = line.split('=', 1)
        config_dict[key.strip()] = value.strip()

    # Convert the dictionary to a JSON string
    json_content = json.dumps(config_dict, indent=4)

    # Check if the text block exists, and overwrite if it does
    text_block_name = "prusaslicer_configuration.json"
    if text_block_name in bpy.data.texts:
        text_block = bpy.data.texts[text_block_name]
        text_block.clear()
    else:
        text_block = bpy.data.texts.new(name=text_block_name)

    # Write the JSON content to the text block
    text_block.from_string(json_content)
    
    return config_local_path, config_dict

class ExecutePrusaSlicerOperator(bpy.types.Operator):
    bl_idname = "bps.slice"
    bl_label = "Run PrusaSlicer"

    mode : bpy.props.StringProperty(name="") # type: ignore
    
    def execute(self, context):

        ws = context.workspace
        ws.bps.running = 1

        show_progress(ws, ws.bps, 0, "Exporting STL...")

        config_path, config_dict = load_config_file(ws.bps.config)
        
        filament = config_dict['filament_type']
        printer = config_dict['printer_settings_id']

        selected_objects = context.selected_objects

        object_names = [re.sub(r'\.\d{0,3}$', '', obj.name) for obj in selected_objects]
        name_counter = Counter(object_names)
        final_names = [f"{count}x_{name}" if count > 1 else name for name, count in name_counter.items()]
        final_names.sort()

        base_filename = "-".join(final_names)

        stl_file_path = os.path.join(temp_dir, base_filename + ".stl")

        file_directory = os.path.dirname(bpy.data.filepath)
        if file_directory:
            gcode_dir = file_directory
        else:
            gcode_dir = os.path.join(temp_dir)

        bpy.ops.wm.stl_export(filepath=stl_file_path, global_scale=1000, export_selected_objects=True)

        if self.mode == "slice":
            show_progress(ws, ws.bps, 30, 'Slicing with PrusaSlicer...')
            command = [
                "--load", os.path.join(config_path), 
                "-g", os.path.join(stl_file_path), 
                "--output", os.path.join(gcode_dir, f"{base_filename}-{filament}-{printer}.gcode")
            ]

        if self.mode == "open":
            show_progress(ws, ws.bps, 30, 'Opening PrusaSlicer...')
            command = [
                "--load", os.path.join(config_path), 
                os.path.join(stl_file_path)
            ]

        thread = threading.Thread(target=do_slice, args=[command, ws, stl_file_path])
        thread.start()
        
        return {'FINISHED'}

def run_prusaslicer(command):
    preferences = bpy.context.preferences.addons[__package__].preferences
    prusaslicer_path = preferences.prusaslicer_path

    if os.path.exists(prusaslicer_path):
        command=[f'{prusaslicer_path}'] + command
    else:
        command=[*prusaslicer_path.split() + command]

    print(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")

        if e.stderr:
            print("PrusaSlicer error output:")
            print(e.stderr)

        return {'CANCELLED'}

    if result.stdout:
        print("PrusaSlicer output:")
        print(result.stdout)

def do_slice(command, ws, stl_file_path):
    start_time = time.time()
    run_prusaslicer(command)
    end_time = time.time()

    os.remove(stl_file_path)

    show_progress(ws, ws.bps, 100, f'Done (in {(end_time - start_time):.2f}s)')
    ws.bps.running = 0

    return {'FINISHED'}