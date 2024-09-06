import bpy # type: ignore
import os, shutil, subprocess, time, tempfile, threading
from collections import namedtuple
from functools import partial

from .functions.basic_functions import show_progress
from .functions import blender_funcs as bf
from .functions import gcode_funcs as gf
from . import PG_NAME_LC

temp_dir = tempfile.gettempdir()
temp_files = []

class ParamAddOperator(bpy.types.Operator):
    bl_idname = f"{PG_NAME_LC}.add_param"
    bl_label = "Add Parameter"

    def execute(self, context):
        ws = context.workspace
        prop_group = getattr(ws, PG_NAME_LC)

        control_list = getattr(prop_group, f'list')
        control_list.add()
        return {'FINISHED'}

class ParamRemoveOperator(bpy.types.Operator):
    bl_idname = f"{PG_NAME_LC}.remove_param"
    bl_label = "Remove Parameter"
    item_index: bpy.props.IntProperty() # type: ignore

    def execute(self, context):
        ws = context.workspace
        prop_group = getattr(ws, PG_NAME_LC)

        control_list = getattr(prop_group, f'list')
        control_list.remove(self.item_index)
        return {'FINISHED'}

class UnmountUsbOperator(bpy.types.Operator):
    bl_idname = f"{PG_NAME_LC}.unmount_usb"
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
    bl_idname = f"{PG_NAME_LC}.slice"
    bl_label = "Run PrusaSlicer"

    mode: bpy.props.StringProperty(name="", default="slice") # type: ignore
    mountpoint: bpy.props.StringProperty(name="", default="") # type: ignore
    
    def execute(self, context):
        ws = context.workspace
        pg = getattr(ws, PG_NAME_LC)

        blendfile_directory = os.path.dirname(bpy.data.filepath)

        pg.running = 1

        show_progress(ws, pg, 0, "Exporting STL...")

        obj_names = bf.names_array_from_objects(context.selected_objects)

        base_filename = "-".join(obj_names)

        paths = namedtuple('Paths', ['ini_path', 'stl_path', 'stl_temp_path', 'gcode_path', 'gcode_temp_path'], defaults=[""]*5)

        stl_file_name = base_filename + ".stl"
        paths.stl_path = os.path.join(temp_dir, stl_file_name)

        global temp_files
        temp_files = []

        bpy.ops.wm.stl_export(filepath=paths.stl_path, global_scale=1000, export_selected_objects=True)
        temp_files.append(paths.stl_path)

        show_progress(ws, pg, 10, "Preparing Configuration...")
        loader = bf.ConfigLoader()
        if pg.use_single_config == False:
            loader.load_config_from_path(pg.printer_config_file, append=False)
            loader.load_config_from_path(pg.filament_config_file, append=True)
            loader.load_config_from_path(pg.print_config_file, append=True)
        else:
            loader.load_config_from_path(pg.config, append=False)

        if not loader.config_dict:
            show_progress(ws, pg, 30, 'Opening PrusaSlicer...')
            command = [os.path.join(paths.stl_path)]

            thread = threading.Thread(target=run_slice, args=[command, ws, None, None])
            thread.start()

            return {'FINISHED'}

        loader.overrides_dict = bf.load_list_to_dict(pg.list)
        
        filament = loader.config_with_overrides['filament_type']
        printer = loader.config_with_overrides['printer_settings_id']

        extension = "bgcode" if loader.config_with_overrides['binary_gcode'] == '1' else "gcode"
        gcode_filename = f"{base_filename}-{filament}-{printer}.{extension}"

        if self.mountpoint:
            gcode_dir = self.mountpoint
        elif blendfile_directory:
            gcode_dir = blendfile_directory
        else:
            gcode_dir = temp_dir
        paths.gcode_path = os.path.join(gcode_dir, gcode_filename)
        paths.gcode_temp_path = os.path.join(temp_dir, gcode_filename)

        paths.ini_path = os.path.join(temp_dir, 'config.ini')
        temp_files.append(loader.write_ini_file(paths.ini_path))

        if self.mode == "open":
            show_progress(ws, pg, 100, 'Opening PrusaSlicer...')
            command = [
                "--load", paths.ini_path, 
                os.path.join(paths.stl_path)
            ]
            thread = threading.Thread(target=exec_prusaslicer, args=[command])
            thread.start()

            getattr(ws, PG_NAME_LC).running = 0
            return {'FINISHED'}

        if os.path.exists(paths.gcode_temp_path):
            stl_chk = bf.calculate_md5(paths.stl_path)
            ini_chk = bf.calculate_md5(paths.ini_path)
            if stl_chk == gf.parse_gcode(paths.gcode_temp_path, 'stl_checksum') and ini_chk == gf.parse_gcode(paths.gcode_temp_path, 'ini_checksum'):
                shutil.copy(paths.gcode_temp_path, paths.gcode_path)
                if self.mode == "slice_and_preview":
                    thread = threading.Thread(target=show_preview, args=[paths.gcode_path])
                    thread.start()
                show_progress(ws, getattr(ws, PG_NAME_LC), 100, f'Done (copied from cached gcode)')
                display_stats(ws, paths.gcode_temp_path)

                getattr(ws, PG_NAME_LC).running = 0
                return {'FINISHED'}

        if self.mode in ("slice", "slice_and_preview"):
            show_progress(ws, pg, 30, 'Slicing with PrusaSlicer...')
            command = [
                "--load", paths.ini_path, 
                "-g", os.path.join(paths.stl_path), 
                "--output", os.path.join(paths.gcode_temp_path)
            ]

            callback = partial(show_preview, paths.gcode_path) if self.mode == "slice_and_preview" else None # if slicing to USB don't show a preview
            thread = threading.Thread(target=run_slice, args=[command, ws, paths, callback])
            thread.start()

            return {'FINISHED'}

def run_slice(command, ws, paths, callback = None):
    
    getattr(ws, PG_NAME_LC).print_time = ""
    getattr(ws, PG_NAME_LC).print_weight = ""

    start_time = time.time()
    res = exec_prusaslicer(command)
    end_time = time.time()

    if res:
        show_progress(ws, getattr(ws, PG_NAME_LC), 100, f'Failed ({res})')
    else:
        show_progress(ws, getattr(ws, PG_NAME_LC), 100, f'Done (in {(end_time - start_time):.2f}s)')
        if paths.gcode_temp_path:
            with open(paths.gcode_temp_path, 'a') as file:
                file.write(f"; stl_checksum = {bf.calculate_md5(paths.stl_path)}\n")
                file.write(f"; ini_checksum = {bf.calculate_md5(paths.ini_path)}\n")
            
            shutil.copy(paths.gcode_temp_path, paths.gcode_path)
            display_stats(ws, paths.gcode_temp_path)

    getattr(ws, PG_NAME_LC).running = 0

    if callback:
        callback()

    cleanup()

    return {'FINISHED'}

def exec_prusaslicer(command):
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
                err_to_tempfile(result.stdout)
                return error_part
            
            if "slicing result exported" in line.lower():
                return
            
        err_to_tempfile(result.stdout)
        return "No error message returned, check your model size"

def err_to_tempfile(text):
    temp_file_path = os.path.join(temp_dir, "prusa_slicer_err_output.txt")
    with open(temp_file_path, "w") as temp_file:
        temp_file.write(text)

def show_preview(gcode_path):
    if gcode_path and os.path.exists(gcode_path):
        gcode_thread = threading.Thread(target=exec_prusaslicer, args=[["--gcodeviewer", gcode_path]])
        gcode_thread.start()
    else:
        print("Gcode file not found: skipping preview.")

def display_stats(ws, gcode_path):
    print_time, print_weight = gf.parse_print_stats(gcode_path)
    getattr(ws, PG_NAME_LC).print_time = print_time if print_time else None
    getattr(ws, PG_NAME_LC).print_weight = print_weight if print_weight else None
    
def cleanup():
    global temp_files
    for file in temp_files:
        os.remove(file)
    temp_files = []