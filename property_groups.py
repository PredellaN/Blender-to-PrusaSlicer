import bpy
import os
from .functions.basic_functions import parse_csv_to_tuples, reset_selection
from . import ADDON_FOLDER

prefs = bpy.context.preferences.addons[__package__].preferences

class ParamSearchListItem(bpy.types.PropertyGroup):
    param_id: bpy.props.StringProperty(name='') # type: ignore
    param_name: bpy.props.StringProperty(name='') # type: ignore
    param_description: bpy.props.StringProperty(name='') # type: ignore

class ParamsListItem(bpy.types.PropertyGroup):
    param_id: bpy.props.StringProperty(name='') # type: ignore
    param_value: bpy.props.StringProperty(name='') # type: ignore

class PauseListItem(bpy.types.PropertyGroup):
    param_type: bpy.props.EnumProperty(name='', items=[
        ('pause', "Pause", "Pause action"),
        ('color_change', "Color Change", "Trigger color change"),
        ('custom_gcode', "Custom Gcode", "Add a custom Gcode command"),
    ]) # type: ignore
    param_cmd: bpy.props.StringProperty(name='') # type: ignore
    param_value_type: bpy.props.EnumProperty(name='', items=[
        ('layer', "on layer", "on layer"),
        ('height', "at height", "at height"),
    ]) # type: ignore
    param_value: bpy.props.StringProperty(name='') # type: ignore

def selection_to_list(object, search_term, search_list, search_index, search_field, target_list, target_list_field):
    if getattr(object, search_index) > -1:
        selection = getattr(object,search_list)[getattr(object, search_index)]
        new_item = getattr(object, target_list).add()
        setattr(new_item, search_field, getattr(selection, target_list_field))
        reset_selection(object, search_index)
        setattr(object, search_term, "")

def get_enum(self, cat):
    value = prefs.get_filtered_bundle_item_index(cat, getattr(self, f"{cat}_config_file"))
    return value

def set_enum(self, value, cat):
    val = prefs.get_filtered_bundle_item_by_index(cat, value)
    if val:
        setattr(self, f"{cat}_config_file", val[0])
    else:
        setattr(self, f"{cat}_config_file", "")
    return

cached_bundle_items = {'printer' : None, 'filament' : None, 'print' : None}
def get_items(self, cat):
    global cached_bundle_items
    cached_bundle_items = prefs.get_filtered_bundle_items(cat)
    return cached_bundle_items

class PrusaSlicerPropertyGroup(bpy.types.PropertyGroup):

    running: bpy.props.BoolProperty(name="is running", default=0) # type: ignore
    progress: bpy.props.IntProperty(name="", min=0, max=100, default=0) # type: ignore
    progress_text: bpy.props.StringProperty(name="") # type: ignore

    config: bpy.props.StringProperty(
        name="PrusaSlicer Configuration (.ini)", 
        subtype='FILE_PATH'
    ) # type: ignore

    use_single_config: bpy.props.BoolProperty(
        name="Single Configuration",
        description="Use a single .ini configuration file",
        default=True
    ) # type: ignore

    printer_config_file: bpy.props.StringProperty() # type: ignore
    printer_config_file_enum: bpy.props.EnumProperty(
        name="Printer Configuration",
        items=lambda self, context: get_items(self, 'printer'),
        get=lambda self: get_enum(self, 'printer'),
        set=lambda self, value: set_enum(self, value, 'printer'),
    ) # type: ignore

    filament_config_file: bpy.props.StringProperty() # type: ignore
    filament_config_file_enum: bpy.props.EnumProperty(
        name="Filament Configuration",
        items=lambda self, context: get_items(self, 'filament'),
        get=lambda self: get_enum(self, 'filament'),
        set=lambda self, value: set_enum(self, value, 'filament'),
    ) # type: ignore

    print_config_file: bpy.props.StringProperty() # type: ignore
    print_config_file_enum: bpy.props.EnumProperty(
        name="Print Configuration",
        items=lambda self, context: get_items(self, 'print'),
        get=lambda self: get_enum(self, 'print'),
        set=lambda self, value: set_enum(self, value, 'print'),
    ) # type: ignore
    
    def search_param_list(self, context):
        if not self.search_term:
            return
        
        self.search_list.clear()
        self.search_list_index = -1

        search_db_path = os.path.join(ADDON_FOLDER, 'functions', 'prusaslicer_fields.csv')
        search_db = parse_csv_to_tuples(search_db_path)
        filtered_tuples = [tup for tup in search_db if all(word in (tup[1] + ' ' + tup[2]).lower() for word in self.search_term.lower().split())]
        sorted_tuples = sorted(filtered_tuples, key=lambda tup: tup[0])

        for param_id, param_name, param_description in sorted_tuples:
            new_item = self.search_list.add()
            new_item.param_id = param_id
            new_item.param_name = param_name
            new_item.param_description = param_description

    search_term : bpy.props.StringProperty(name="Search", update=search_param_list) # type: ignore
    search_list : bpy.props.CollectionProperty(type=ParamSearchListItem) # type: ignore
    search_list_index : bpy.props.IntProperty(default=-1, update=lambda self, context: selection_to_list(self, 'search_term', 'search_list', 'search_list_index', 'param_id', 'list', 'param_id')) # type: ignore

    list : bpy.props.CollectionProperty(type=ParamsListItem) # type: ignore
    list_index : bpy.props.IntProperty(default=-1, update=lambda self, context: reset_selection(self, 'list_index')) # type: ignore

    pause_list : bpy.props.CollectionProperty(type=PauseListItem) # type: ignore
    pause_list_index : bpy.props.IntProperty(default=-1, update=lambda self, context: reset_selection(self, 'pause_list_index')) # type: ignore

    print_weight : bpy.props.StringProperty(name="") # type: ignore
    print_time : bpy.props.StringProperty(name="") # type: ignore

    cached_stl_chk : bpy.props.StringProperty() # type: ignore
    cached_ini_chk : bpy.props.StringProperty() # type: ignore
    cached_gcode_chk : bpy.props.StringProperty() # type: ignore