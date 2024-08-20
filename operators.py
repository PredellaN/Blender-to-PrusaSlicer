import bpy, bmesh
import os, subprocess, time, tempfile, threading, re
from .basic_functions import show_progress
from collections import Counter

def parse_config_file(file_path):
    config_dict = {}
    
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            key, value = line.split('=', 1)
            config_dict[key.strip()] = value.strip()
    
    return config_dict

class ExecutePrusaSlicerOperator(bpy.types.Operator):
    bl_idname = "bps.slice"
    bl_label = "Run PrusaSlicer"

    mode : bpy.props.StringProperty(name="") # type: ignore
    
    def execute(self, context):

        ws = context.workspace
        ws.bps.running = 1

        show_progress(ws, ws.bps, 0, "Exporting STL...")

        template_absolute_path = bpy.path.abspath(ws.bps.config)
        config_dict = parse_config_file(template_absolute_path)
        filament = config_dict['filament_type']
        printer = config_dict['printer_settings_id']

        selected_objects = context.selected_objects

        object_names = [re.sub(r'\.\d{0,3}$', '', obj.name) for obj in selected_objects]
        name_counter = Counter(object_names)
        final_names = [f"{count}x_{name}" if count > 1 else name for name, count in name_counter.items()]
        final_names.sort()

        base_filename = "-".join(final_names)

        temp_dir = tempfile.gettempdir() 
        stl_file_path = os.path.join(temp_dir, base_filename + ".stl")

        file_directory = os.path.dirname(bpy.data.filepath)
        if file_directory:
            gcode_dir = file_directory
        else:
            gcode_dir = os.path.join(temp_dir)

        bpy.ops.export_mesh.stl(filepath=stl_file_path, global_scale=1000, use_selection=True)

        if self.mode == "slice":
            show_progress(ws, ws.bps, 30, 'Slicing with PrusaSlicer...')
            command = [
                "--load", os.path.join(template_absolute_path), 
                "-g", os.path.join(stl_file_path), 
                "--output", os.path.join(gcode_dir, f"{base_filename}-{filament}-{printer}.gcode")
            ]

        if self.mode == "open":
            show_progress(ws, ws.bps, 30, 'Opening PrusaSlicer...')
            command = [
                "--load", os.path.join(template_absolute_path), 
                os.path.join(stl_file_path)
            ]

        thread = threading.Thread(target=do_slice, args=[command, ws, stl_file_path])
        thread.start()
        
        return {'FINISHED'}

def run_prusaslicer(command):
    preferences = bpy.context.preferences.addons[__package__].preferences
    prusaslicer_path = preferences.prusaslicer_path

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