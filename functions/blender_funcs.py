import bpy  # type: ignore
import os
import urllib.request
import json
import tempfile
import re
import hashlib
import numpy as np
import struct

from collections import Counter

TEXT_BLOCK_NAME = "prusaslicer_configuration.json"

def names_array_from_objects(objects):
    object_names = [re.sub(r'\.\d{0,3}$', '', obj.name) for obj in objects]
    name_counter = Counter(object_names)
    final_names = [f"{count}x_{name}" if count > 1 else name for name, count in name_counter.items()]
    final_names.sort()
    return final_names

class ConfigLoader:
    def __init__(self, text_block_id = None):
        self.config_dict = {}
        self.overrides_dict = {}
        self.original_file_path = None
        
        self.temp_dir = tempfile.gettempdir()

        if text_block_id:
            self._read_text_block(text_block_id)

    @property
    def config_with_overrides(self):
        if self.config_dict is None:
            return None

        config = self.config_dict.copy()
        
        if self.overrides_dict:
            config.update(self.overrides_dict)
        return config

    def load_config_from_path(self, path, append = False):
        if not path:
            return False

        self.original_file_path = path
        if path.startswith('http://') or path.startswith('https://'):
            encoded_path = urllib.parse.quote(path, safe="%/:=&?")
            request = urllib.request.Request(
                encoded_path, 
                headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
            )
            response = urllib.request.urlopen(request)
            file_content = response.read().decode('utf-8')

            temp_path = os.path.join(self.temp_dir, 'config.ini')
            with open(temp_path, 'w') as file:
                file.write(file_content)
            config_local_path = temp_path
        else:
            config_local_path = bpy.path.abspath(path)

        self.load_ini_file(config_local_path, append=append)
        self._write_text_block(TEXT_BLOCK_NAME)

        if 'temp_path' in locals():
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return True

    def write_ini_file(self, config_local_path, use_overrides = True):
        config = self.config_with_overrides if use_overrides else self.config_dict
        with open(config_local_path, 'w') as file:
            for key, value in config.items():
                file.write(f"{key} = {value}\n")
        return config_local_path

    def load_ini_file(self, config_local_path, append = False):
        if not append:
            self.config_dict = {}
        with open(config_local_path, 'r') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue

            key, value = line.split('=', 1)
            self.config_dict[key.strip()] = value.strip()

    def _write_text_block(self, text_block_id):
        if self.config_dict:
            json_content = json.dumps(self.config_dict, indent=4)
            
            if text_block_id in bpy.data.texts:
                text_block = bpy.data.texts[text_block_id]
                text_block.clear()
            else:
                text_block = bpy.data.texts.new(name=text_block_id)

            text_block.from_string(json_content)
            self.text_block_id = text_block_id

    def _read_text_block(self, text_block_id):
        text_block_id = self.text_block_id
        
        if text_block_id:
            if text_block_id in bpy.data.texts:
                text_block = bpy.data.texts[text_block_id]
                json_content = text_block.as_string()
                self.config_dict = json.loads(json_content)

    def load_list_to_overrides(self, list):
        for item in list:
            self.overrides_dict[item.param_id] = item.param_value
    
    def add_pauses_and_changes(self, list):
        colors = [
            "#79C543", "#E01A4F", "#FFB000", "#8BC34A", "#808080",
            "#ED1C24", "#A349A4", "#B5E61D", "#26A69A", "#BE1E2D",
            "#39B54A", "#CCCCCC", "#5A4CA2", "#D90F5A", "#A4E100",
            "#B97A57", "#3F48CC", "#F9E300", "#FFFFFF", "#00A2E8"
        ]
        combined_layer_gcode = self.config_dict['layer_gcode']
        pause_gcode = "\\n;PAUSE_PRINT\\n" + (self.config_dict.get('pause_print_gcode') or 'M0')
    
        for item in list:
            try:
                layer_num = int(item.param_value) - 1
            except:
                continue

            if item.param_type == 'pause':
                item_gcode = pause_gcode
            elif item.param_type == 'color_change':
                color_change_gcode = f"\\n;COLOR_CHANGE,T0,{colors[0]}\\n" + (self.config_dict.get('color_change_gcode') or 'M600')
                item_gcode = color_change_gcode
                colors.append(colors.pop(0))
            else:
                continue
        
            combined_layer_gcode += f"{{if layer_num=={layer_num}}}{item_gcode}{{endif}}"

        self.overrides_dict['layer_gcode'] = combined_layer_gcode 

def calculate_md5(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read the file in chunks to avoid using too much memory
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

def coll_from_selection():
    cx = None
    for obj in bpy.context.selected_objects:
        for coll in bpy.data.collections:
            if obj in [o for o in coll.objects]:
                cx = coll
                break
        if cx:
            break
    if not cx:
        cx = bpy.context.scene.collection
    return cx

def objects_to_tris(selected_objects, scale):
    tris_count = sum(len(obj.data.loop_triangles) for obj in selected_objects)
    tris = np.empty(tris_count * 4 * 3, dtype=np.float64).reshape(-1, 4, 3)

    col_idx = 0
    for obj in selected_objects:
        mesh = obj.data
        curr_tris_count = len(mesh.loop_triangles)
        curr_vert_count = len(mesh.vertices)

        tris_v_i = np.empty(curr_tris_count * 3, dtype=np.int32)
        mesh.loop_triangles.foreach_get("vertices", tris_v_i)
        tris_v_i = tris_v_i.reshape((-1, 3))

        tris_v_n = np.empty(curr_tris_count * 3)
        mesh.loop_triangles.foreach_get("normal", tris_v_n)
        tris_v_n = tris_v_n.reshape((-1, 3))

        tris_verts = np.empty(curr_vert_count * 3)
        mesh.vertices.foreach_get("co", tris_verts)
        tris_verts = tris_verts.reshape((-1, 3))
        
        world_matrix = np.array(obj.matrix_world.transposed())

        homogeneous_verts = np.hstack((tris_verts, np.ones((tris_verts.shape[0], 1))))
        transformed_verts = homogeneous_verts @ world_matrix
        transformed_verts = (transformed_verts[:, :3]) * scale

        homogeneous_norm = np.hstack((tris_v_n, np.ones((tris_v_n.shape[0], 1))))
        transformed_norm = homogeneous_norm @ world_matrix.T
        transformed_norm = transformed_norm[:, :3]
        transformed_norm = transformed_norm / np.linalg.norm(transformed_norm, axis=1, keepdims=True)

        tris_coords = transformed_verts[tris_v_i]
        tris_coords_and_norm = np.concatenate((tris_coords, transformed_norm[:, np.newaxis, :]), axis=1)
        
        tris[col_idx:col_idx + curr_tris_count,:] = tris_coords_and_norm
        
        col_idx += curr_tris_count

    return tris

def transform_tris(tris, v=np.array([.0, .0, .0])):
    tris[:, :3] += v
    return tris

def scale_tris(tris, s=0):
    tris[:, :3] *= s
    return tris

def save_stl(tris, filename):
    header = b'\0' * 80 + struct.pack('<I', tris.shape[0])

    with open(filename, 'wb') as f:
        f.write(header)
        for tri in tris:
            v1, v2, v3, normal = tri
            data = struct.pack('<12fH', *normal, *v1, *v2, *v3, 0)
            f.write(data)