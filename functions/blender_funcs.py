import bpy  # type: ignore
import os
import urllib.request
import json
import tempfile
import re

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
        self.config_dict = None
        self.overrides_dict = None
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
        self.original_file_path = path
        if path.startswith('http://') or path.startswith('https://'):
            response = urllib.request.urlopen(path)
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

def load_list_to_dict(list):
    param_dict = {}
    for item in list:
        param_dict[item.param_id] = item.param_value
    return param_dict