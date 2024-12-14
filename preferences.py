import bpy, os, sys # type: ignore
from bpy_extras.io_utils import ExportHelper, ImportHelper

import subprocess
from .functions import modules as mod
from .functions.basic_functions import ParamRemoveOperator, ParamAddOperator, reset_selection, dump_dict_to_json, dict_from_json, redraw
from .functions.caching_local import LocalCache

from . import PG_NAME_LC
    
class ExportConfig(bpy.types.Operator, ExportHelper):
    bl_idname = f"{PG_NAME_LC}.export_configs"
    bl_label = "Export Selected Configurations list"

    filename_ext = ".json"

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        configs = [t[0] for t in prefs.get_filtered_bundle_items('') if t[0]]
        dump_dict_to_json(configs, self.filepath)
        return {'FINISHED'}
    
class ImportConfig(bpy.types.Operator, ImportHelper):
    bl_idname = f"{PG_NAME_LC}.import_configs"
    bl_label = "Import Selected Configurations list"

    filename_ext = ".json"

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        try:
            configs = dict_from_json(self.filepath)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load configurations: {str(e)}")
            return {'CANCELLED'}

        for key, item in prefs.prusaslicer_bundle_list.items():
            item.conf_enabled = True if item.name in configs else False
            
        redraw()
        return {'FINISHED'}
    
# Configuration Lists
class PRUSASLICER_UL_ConfListBase(bpy.types.UIList):
    filter_conf_cat = None  # Set this in subclasses

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):        
        row = layout.row()
        row.prop(item, 'conf_enabled')
        
        # Set icon based on conf_cat
        icon = 'OUTPUT' if item.conf_cat == 'print' else ('RENDER_ANIMATION' if item.conf_cat == 'filament' else 'STATUSBAR')
        
        # Display conf_cat with icon
        sub_row = row.row(align=True)
        sub_row.label(text=item.conf_cat, icon=icon)
        sub_row.scale_x = 0.3
        
        # Display conf_id
        sub_row = row.row(align=True)
        sub_row.label(text=item.conf_label)

class ConfListItem(bpy.types.PropertyGroup):
    conf_id: bpy.props.StringProperty(name='') # type: ignore
    conf_label: bpy.props.StringProperty(name='') # type: ignore
    conf_enabled: bpy.props.BoolProperty(name='') # type: ignore
    conf_cat: bpy.props.StringProperty(name='') # type: ignore
    conf_cache_path: bpy.props.StringProperty(name='') # type: ignore

class SelectedCollRemoveOperator(ParamRemoveOperator):
    bl_idname = f"{PG_NAME_LC}.pref_remove_param"
    bl_label = "Remove Bundle"
    def get_pg(self):
        return bpy.context.preferences.addons[__package__].preferences
    def triggers(self):
        prefs = bpy.context.preferences.addons[__package__].preferences
        prefs.update_config_bundle_manifest()
    
class SelectedCollAddOperator(ParamAddOperator):
    bl_idname = f"{PG_NAME_LC}.pref_add_param"
    bl_label = "Add Bundle"
    def get_pg(self):
        return bpy.context.preferences.addons[__package__].preferences

def guess_prusaslicer_path():
    # Original fallback default
    fallback = "switcherooctl -g 1 /home/nicolas/Applications/prusa3d_linux_2_8_1/PrusaSlicer-2.8.1+linux-x64-older-distros-GTK3-202409181354.AppImage"
    
    if sys.platform.startswith("win"):
        # Common default path on Windows
        candidate = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer.exe"
        if os.path.isfile(candidate):
            return candidate
    elif sys.platform.startswith("darwin"):  # macOS
        # Common macOS application path
        candidate = "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"
        if os.path.isfile(candidate) or os.access(candidate, os.X_OK):
            return candidate

    # If no suitable guess was found, return fallback
    return fallback
class PrusaSlicerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    profile_cache = LocalCache()

    def get_filtered_bundle_items(self, cat):
        items = [("","","")] + sorted(
            [
                (item.conf_id, item.conf_label, "")
                for item in self.prusaslicer_bundle_list
                if (item.conf_cat == cat or not cat) and item.conf_enabled
            ],
            key=lambda x: x[1]
        )
        return items

    def get_filtered_bundle_item_index(self, cat, id):
        items = self.get_filtered_bundle_items(cat)
        for idx, (conf_id, _, _) in enumerate(items):
            if conf_id == id:
                return idx
        return 0

    def get_filtered_bundle_item_by_index(self, cat, idx):
        items = self.get_filtered_bundle_items(cat)
        return items[idx] if idx < len(items) else ("", "", "")

    def update_config_bundle_manifest(self, context=None):
        self.profile_cache.directory = self.prusaslicer_bundles_folder
        self.profile_cache.load_ini_files()
        self.profile_cache.process_all_files()
    
        if self.profile_cache.has_changes():
            existing_confs = [c.conf_id for c in self.prusaslicer_bundle_list]
            cache_conf_ids = set(self.profile_cache.config_headers.keys())

            for idx in reversed(range(len(self.prusaslicer_bundle_list))):
                item = self.prusaslicer_bundle_list[idx]
                if item.conf_id not in cache_conf_ids:
                    self.prusaslicer_bundle_list.remove(idx)

            for key, config in self.profile_cache.config_headers.items():
                if '*' in key:
                    continue
                if config['category'] not in ['printer', 'filament', 'print']:
                    continue
                if key in existing_confs:
                    continue
                new_item = self.prusaslicer_bundle_list.add()
                new_item.conf_id = key
                new_item.name = key
                new_item.conf_label = config['id']
                new_item.conf_cat = config['category']
                new_item.conf_enabled = not config['has_header']

        return
    
    default_bundles_added: bpy.props.BoolProperty() #type: ignore

    prusaslicer_path: bpy.props.StringProperty(
        name="PrusaSlicer path",
        description="Path or command for the PrusaSlicer executable",
        subtype='FILE_PATH',
        default=guess_prusaslicer_path(),
    ) #type: ignore

    prusaslicer_bundles_folder: bpy.props.StringProperty(
        name="PrusaSlicer .ini bundles path",
        description="Path to the folder containing the PrusaSlicer configurations (recursive)",
        subtype='FILE_PATH',
        default="//profiles",
        update=update_config_bundle_manifest,
    ) #type: ignore

    prusaslicer_bundle_list: bpy.props.CollectionProperty(type=ConfListItem) # type: ignore
    prusaslicer_bundle_list_index: bpy.props.IntProperty(default=-1, update=lambda self, context: reset_selection(self, 'prusaslicer_bundle_list_index')) # type: ignore

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "prusaslicer_path")
        row = layout.row()
        row.prop(self, "prusaslicer_bundles_folder")

        box = layout.box()
        row = box.row()
        row.label(text="Configurations:")
        row = box.row()
        active_list_id = 'prusaslicer_bundle_list'
        row.template_list('PRUSASLICER_UL_ConfListBase', f"{active_list_id}",
                self, f"{active_list_id}",
                self, f"{active_list_id}_index"
                )
        
        layout = self.layout
        row = layout.row()
        row.operator(f"{PG_NAME_LC}.export_configs")
        row.operator(f"{PG_NAME_LC}.import_configs")