import bpy # type: ignore
import os, subprocess, time, tempfile, threading, re
from collections import Counter

from .functions.basic_functions import show_progress
from .functions import blender_funcs as bf
from .constants import WS_ATTRIBUTE_NAME

temp_dir = tempfile.gettempdir()

class ParamAddOperator(bpy.types.Operator):
    bl_idname = f"{WS_ATTRIBUTE_NAME}.add_param"
    bl_label = "Add Parameter"

    def execute(self, context):
        ws = context.workspace
        prop_group = getattr(ws, WS_ATTRIBUTE_NAME)

        control_list = getattr(prop_group, f'list')
        control_list.add()
        return {'FINISHED'}

class ParamRemoveOperator(bpy.types.Operator):
    bl_idname = f"{WS_ATTRIBUTE_NAME}.remove_param"
    bl_label = "Remove Parameter"
    item_index: bpy.props.IntProperty() # type: ignore

    def execute(self, context):
        ws = context.workspace
        prop_group = getattr(ws, WS_ATTRIBUTE_NAME)

        control_list = getattr(prop_group, f'list')
        control_list.remove(self.item_index)
        return {'FINISHED'}

class UnmountUsbOperator(bpy.types.Operator):
    bl_idname = f"{WS_ATTRIBUTE_NAME}.unmount_usb"
    bl_label = "Unmount USB"
    mountpoint: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        try:
            if os.name == 'nt':
                result = os.system(f'mountvol {self.mountpoint} /D')
            else:
                # Use subprocess to capture output
                result = subprocess.run(['umount', self.mountpoint], capture_output=True, text=True)
                
                if result.returncode != 0:
                    if 'target is busy' in result.stderr:
                        self.report({'ERROR'}, f"Failed to unmount {self.mountpoint}: device busy")
                    else:
                        self.report({'ERROR'}, f"Failed to unmount {self.mountpoint}: {result.stderr}")
                    return {'CANCELLED'}
            
            self.report({'INFO'}, f"Successfully unmounted {self.mountpoint}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to unmount {self.mountpoint}: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}
class RunPrusaSlicerOperator(bpy.types.Operator):
    bl_idname = f"{WS_ATTRIBUTE_NAME}.slice"
    bl_label = "Run PrusaSlicer"

    mode: bpy.props.StringProperty(name="", default="slice") # type: ignore
    mountpoint: bpy.props.StringProperty(name="", default="") # type: ignore
    
    def execute(self, context):
        ws = context.workspace
        prop_group = getattr(ws, WS_ATTRIBUTE_NAME)

        prop_group.running = 1

        show_progress(ws, prop_group, 0, "Exporting STL...")

        loader = bf.ConfigLoader()
        loader.load_config_from_path(prop_group.config)
        loader.overrides_dict = bf.load_list_to_dict(prop_group.list)
        
        filament = loader.config_with_overrides['filament_type']
        printer = loader.config_with_overrides['printer_settings_id']

        selected_objects = context.selected_objects

        object_names = [re.sub(r'\.\d{0,3}$', '', obj.name) for obj in selected_objects]
        name_counter = Counter(object_names)
        final_names = [f"{count}x_{name}" if count > 1 else name for name, count in name_counter.items()]
        final_names.sort()

        base_filename = "-".join(final_names)

        stl_file_path = os.path.join(temp_dir, base_filename + ".stl")

        file_directory = os.path.dirname(bpy.data.filepath)

        if self.mountpoint:
            gcode_dir = self.mountpoint
        elif file_directory:
            gcode_dir = file_directory
        else:
            gcode_dir = temp_dir

        temp_files = []

        bpy.ops.wm.stl_export(filepath=stl_file_path, global_scale=1000, export_selected_objects=True)
        temp_files.append(stl_file_path)

        ini_file_path = os.path.join(temp_dir, 'config.ini')
        temp_files.append(loader.write_ini_file(ini_file_path))

        if self.mode == "slice":
            show_progress(ws, prop_group, 30, 'Slicing with PrusaSlicer...')
            command = [
                "--load", ini_file_path, 
                "-g", os.path.join(stl_file_path), 
                "--output", os.path.join(gcode_dir, f"{base_filename}-{filament}-{printer}.gcode")
            ]

        if self.mode == "open":
            show_progress(ws, prop_group, 30, 'Opening PrusaSlicer...')
            command = [
                "--load", ini_file_path, 
                os.path.join(stl_file_path)
            ]

        thread = threading.Thread(target=do_slice, args=[command, ws, temp_files])
        thread.start()
        
        return {'FINISHED'}
    
def delete_tempfiles(temp_files):
    for file in temp_files:
        os.remove(file)

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

    if result.stdout:
        print("PrusaSlicer output:")
        print(result.stdout)
        for line in result.stdout.splitlines():
            if "[error]" in line.lower():
                error_part = line.lower().split("[error]", 1)[1].strip()
                return error_part
            
            if "slicing result exported" in line.lower():
                return
            
        return "No error message returned, check your model size"

def do_slice(command, ws, temp_files):
    
    start_time = time.time()
    res = run_prusaslicer(command)
    end_time = time.time()

    delete_tempfiles(temp_files)

    if res:
        show_progress(ws, getattr(ws, WS_ATTRIBUTE_NAME), 100, f'Failed ({res})')
    else:
        show_progress(ws, getattr(ws, WS_ATTRIBUTE_NAME), 100, f'Done (in {(end_time - start_time):.2f}s)')

    getattr(ws, WS_ATTRIBUTE_NAME).running = 0

    return {'FINISHED'}