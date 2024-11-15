import bpy # type: ignore
import numpy as np

import os, subprocess, time, tempfile, threading, json
from collections import namedtuple
from functools import partial

from .functions import prusaslicer_funcs as psf 

from .functions.basic_functions import show_progress, threaded_copy, dict_from_json
from .functions import blender_funcs as bf
from .functions import gcode_funcs as gf
from . import PG_NAME_LC

temp_files = []

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

    def progress_callback(self, context):
        ws = context.workspace
        cx = bf.coll_from_selection()
        pg = getattr(cx, PG_NAME_LC)
        show_progress(pg, 0, "Preparing Configuration...")
    
    def execute(self, context):
        ws = context.workspace
        cx = bf.coll_from_selection()
        pg = getattr(cx, PG_NAME_LC)

        prefs = bpy.context.preferences.addons[__package__].preferences
        global prusaslicer_path
        prusaslicer_path = prefs.prusaslicer_path

        pg.running = 1

        show_progress(pg, 0, "Preparing Configuration...")

        loader = bf.ConfigLoader()

        # try:
        loader.load_config(pg.printer_config_file, append=False)
        loader.load_config(pg.filament_config_file, append=True)
        loader.load_config(pg.print_config_file, append=True)
        loader.load_list_to_overrides(pg.list)
        loader.add_pauses_and_changes(pg.pause_list)
        # except:
        #     show_progress(pg, 0, f'Error: failed to load configuration')

        #     pg.running = 0
        #     return {'FINISHED'}

        show_progress(pg, 10, "Exporting STL...")

        obj_names = bf.names_array_from_objects(context.selected_objects)

        if not len(obj_names):
            show_progress(pg, 0, f'Error: selection empty')
            getattr(cx, PG_NAME_LC).running = 0
            return{'FINISHED'}

        paths = determine_paths(loader.config_with_overrides, "-".join(obj_names), self.mountpoint)

        global temp_files
        temp_files = []

        depsgraph = bpy.context.evaluated_depsgraph_get()
        selected_objects = [obj.evaluated_get(depsgraph) for obj in bpy.context.selected_objects if obj.type == 'MESH']

        tris = bf.objects_to_tris(selected_objects, 1000)

        vertices = tris[:, :3, :]
        min_coords = vertices.min(axis=(0, 1))
        max_coords = vertices.max(axis=(0, 1))
        bed_size = gf.get_bed_size(loader.config_with_overrides['bed_shape']) if 'bed_shape' in loader.config_with_overrides else (0, 0)
        transform = -((min_coords + max_coords) / 2) + np.array([bed_size[0]/2,bed_size[1]/2,0])
        tris = bf.transform_tris(tris, transform)

        bf.save_stl(tris, paths.stl_path)
        temp_files.append(paths.stl_path)

        if not loader.config_dict:
            show_progress(pg, 100, 'Opening PrusaSlicer')
            command = [
                os.path.join(paths.stl_path),
            ]

            thread = threading.Thread(target=run_slice, args=[command, cx, ws, None, None])
            thread.start()

            getattr(cx, PG_NAME_LC).running = 0
            return {'FINISHED'}

        temp_files.append(loader.write_ini(paths.ini_path))

        if self.mode == "open":
            show_progress(pg, 100, 'Opening PrusaSlicer')
            command = [
                "--load", paths.ini_path, 
                os.path.join(paths.stl_path),
            ]
            thread = threading.Thread(target=psf.exec_prusaslicer, args=[command, prusaslicer_path])
            thread.start()

            pg.running = 0
            return {'FINISHED'}

        if os.path.exists(paths.gcode_temp_path) and os.path.exists(paths.json_temp_path):
            cached_data = dict_from_json(paths.json_temp_path)
            stl_chk = bf.calculate_md5(paths.stl_path)
            ini_chk = bf.calculate_md5(paths.ini_path)

            if stl_chk == cached_data.get('stl_chk') and ini_chk == cached_data.get('ini_chk'):

                threaded_copy(paths.gcode_temp_path, paths.gcode_path)
                if self.mode == "slice_and_preview":
                    thread = threading.Thread(target=show_preview, args=[paths.gcode_temp_path])
                    thread.start()
                append_done = f" to {self.mountpoint.split('/')[-1]}" if self.mountpoint else ""
                show_progress(pg, 100, f'Done (copied from cached gcode){append_done}')
                display_stats(cx, paths.gcode_temp_path)

                getattr(cx, PG_NAME_LC).running = 0
                return {'FINISHED'}

        if self.mode in ("slice", "slice_and_preview"):
            show_progress(pg, 30, 'Slicing with PrusaSlicer...')
            command = [
                "--load", paths.ini_path, 
                "-g", os.path.join(paths.stl_path),
                "--output", os.path.join(paths.gcode_temp_path)
            ]

            callback = partial(show_preview, paths.gcode_temp_path) if self.mode == "slice_and_preview" else None # if slicing to USB don't show a preview
            thread = threading.Thread(target=run_slice, args=[command, cx, ws, paths, [callback]])
            thread.start()

            return {'FINISHED'}

def determine_paths(config, base_filename, mountpoint):
    paths = namedtuple('Paths', ['ini_path', 'stl_path', 'stl_temp_path', 'gcode_path', 'gcode_temp_path', 'json_temp_path'], defaults=[""]*5)

    filament = config.get('filament_type', 'Unknown filament')
    printer = config.get('printer_model', 'Unknown printer')

    stl_file_name = base_filename + ".stl"
    extension = "bgcode" if config.get('binary_gcode', '0') == '1' else "gcode"
    full_filename = f"{base_filename}-{filament}-{printer}"
    gcode_filename = f"{full_filename}.{extension}"
    json_filename = f"{full_filename}.json"

    temp_dir = tempfile.gettempdir()

    blendfile_directory = os.path.dirname(bpy.data.filepath)
    paths.stl_path = os.path.join(temp_dir, stl_file_name)

    if mountpoint:
        gcode_dir = mountpoint
    elif blendfile_directory:
        gcode_dir = blendfile_directory
    else:
        gcode_dir = temp_dir

    paths.gcode_path = os.path.join(gcode_dir, gcode_filename)
    paths.gcode_temp_path = os.path.join(temp_dir, gcode_filename)
    paths.json_temp_path = os.path.join(temp_dir, json_filename)
    paths.ini_path = os.path.join(temp_dir, 'config.ini')
    return paths

def run_slice(command, cx, ws, paths, callbacks = None):

    pg = getattr(cx, PG_NAME_LC)
    
    getattr(cx, PG_NAME_LC).print_time = ""
    getattr(cx, PG_NAME_LC).print_weight = ""

    start_time = time.time()
    res = psf.exec_prusaslicer(command, prusaslicer_path)
    
    if res:
        end_time = time.time()
        show_progress(pg, 0, f'Failed ({res})')
    else:
        
        if paths.gcode_temp_path:
            checksums = {
                "stl_chk": bf.calculate_md5(paths.stl_path),
                "ini_chk": bf.calculate_md5(paths.ini_path)
            }
            with open(paths.json_temp_path, 'w') as json_file:
                json.dump(checksums, json_file, indent=4)
            
            display_stats(cx, paths.gcode_temp_path)
            threaded_copy(paths.gcode_temp_path, paths.gcode_path)
            
        end_time = time.time()
        show_progress(pg, 100, f'Done (in {(end_time - start_time):.2f}s)')
            
    pg.running = 0

    if callbacks:
        for callback in callbacks:
            callback()

    cleanup()

    return {'FINISHED'}

def show_preview(gcode_path):
    if gcode_path and os.path.exists(gcode_path):
        gcode_thread = threading.Thread(target=psf.exec_prusaslicer, args=[["--gcodeviewer", gcode_path], prusaslicer_path])
        gcode_thread.start()
    else:
        print("Gcode file not found: skipping preview.")

def display_stats(ws, gcode_path):
    print_time = gf.parse_gcode(gcode_path, 'estimated printing time \(normal mode\)')
    print_weight = gf.parse_gcode(gcode_path, 'filament used \[g\]')
    getattr(ws, PG_NAME_LC).print_time = print_time if print_time else ""
    getattr(ws, PG_NAME_LC).print_weight = print_weight if print_weight else ""
    
def cleanup():
    global temp_files
    for file in temp_files:
        os.remove(file)
    temp_files = []