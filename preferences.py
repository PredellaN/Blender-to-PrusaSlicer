import bpy, os
import subprocess
from .functions import modules as mod
from .functions.basic_functions import BaseList, ParamRemoveOperator, ParamAddOperator, reset_selection, dict_from_json
from .functions.prusaslicer_funcs import configs_to_cache
from .functions.caching import CACHE_INDEX_PATH

from . import PG_NAME_LC, DEPENDENCIES, DEPENDENCIES_FOLDER
from . import register, unregister, dependencies_installed  # Import the unregister and register functions

class EXAMPLE_OT_install_dependencies(bpy.types.Operator):
    bl_idname = f"{PG_NAME_LC}.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required python packages for this add-on")
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        try:
            mod.install_pip()
            for dependency in DEPENDENCIES:
                mod.install_and_import_module(module_name=dependency.module,
                                          package_name=dependency.package,
                                          global_name=dependency.name,
                                          path=DEPENDENCIES_FOLDER)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        unregister()
        register()
        return {"FINISHED"}
    
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
    conf_bundle: bpy.props.StringProperty(name='') # type: ignore

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

class PRUSASLICER_UL_BundleList(BaseList):
    delete_operator = f"{PG_NAME_LC}.pref_remove_param"
    def draw_properties(self, row, item):
        row.prop(item, "bundle_url")

def reload_manifest(self, context):
    prefs = bpy.context.preferences.addons[__package__].preferences
    prefs.update_config_bundle_manifest()

class BundleListItem(bpy.types.PropertyGroup):
    bundle_url: bpy.props.StringProperty(name='', update=reload_manifest) # type: ignore

class PrusaSlicerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def get_filtered_bundle_items(self, cat):
        items = [("","","")] + sorted(
            [
                (item.conf_id, item.conf_label, "")
                for item in self.prusaslicer_bundle_list
                if item.conf_cat == cat and item.conf_enabled
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

    def update_config_bundle_manifest(self):

        bundle_urls = [item.bundle_url for item in self.prusaslicer_bundle_urls]
        configs_to_cache(bundle_urls)

        configs = dict_from_json(CACHE_INDEX_PATH)

        ## Fill list
        existing_confs = [c.conf_id for c in self.prusaslicer_bundle_list]

        sorted_categories = {
            'printer' : '1',
            'filament' : '2',
            'print' : '3',
        }
        for key, config in configs.items():
            if '*' in key:
                continue
            if config['category'] not in ['printer', 'filament', 'print']:
                continue
            if key in existing_confs:
                continue
            new_item = self.prusaslicer_bundle_list.add()
            new_item.conf_id = key
            new_item.name = sorted_categories[config['category']] + " - " + config['id']
            new_item.conf_label = config['id']
            new_item.conf_cat = config['category']
            new_item.conf_bundle = config['bundle_url']
            new_item.conf_enabled = True if '.json' in config['bundle_url'] else False

        for idx in reversed(range(len(self.prusaslicer_bundle_list))):
            item = self.prusaslicer_bundle_list[idx]
            if item.conf_bundle not in bundle_urls:
                self.prusaslicer_bundle_list.remove(idx)

        return
    
    default_bundles_added: bpy.props.BoolProperty() #type: ignore
    def add_default_bundles(self):
        if not self.default_bundles_added:
            for url in [
                "https://raw.githubusercontent.com/PredellaN/MOS-3d-Printing-Library/refs/heads/main/manifest.json",
                "https://raw.githubusercontent.com/prusa3d/PrusaSlicer-settings-prusa-fff/refs/heads/main/PrusaResearch/2.1.1.ini",
                ]:
                item = self.prusaslicer_bundle_urls.add()
                item.bundle_url = url
            self.default_bundles_added = True

    prusaslicer_path: bpy.props.StringProperty(
        name="PrusaSlicer Path",
        description="Path to the PrusaSlicer executable",
        subtype='FILE_PATH',
        default="switcherooctl -g 1 /home/nicolas/Applications/prusa3d_linux_2_8_1/PrusaSlicer-2.8.1+linux-x64-older-distros-GTK3-202409181354.AppImage"
    ) #type: ignore

    prusaslicer_bundle_urls: bpy.props.CollectionProperty(type=BundleListItem) # type: ignore
    prusaslicer_bundle_urls_index: bpy.props.IntProperty(default=-1, update=lambda self, context: reset_selection(self, 'prusaslicer_bundle_urls_index')) # type: ignore

    prusaslicer_bundle_list: bpy.props.CollectionProperty(type=ConfListItem) # type: ignore
    prusaslicer_bundle_list_index: bpy.props.IntProperty(default=-1, update=lambda self, context: reset_selection(self, 'prusaslicer_bundle_list_index')) # type: ignore

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "prusaslicer_path")

        row = layout.row()
        active_list_id = 'prusaslicer_bundle_urls'
        row.template_list('PRUSASLICER_UL_BundleList', f"{active_list_id}",
                self, f"{active_list_id}",
                self, f"{active_list_id}_index"
                )
        row = layout.row()
        row.operator(f"{PG_NAME_LC}.pref_add_param").target=f"{active_list_id}"

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
        if dependencies_installed:
            layout.label(icon='CHECKMARK', text="Dependencies installed")
        else:
            layout.operator(f"{PG_NAME_LC}.install_dependencies", icon="CONSOLE")
