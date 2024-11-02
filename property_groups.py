import bpy
from . import blender_globals
from .functions.basic_functions import parse_csv_to_tuples

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
    ]) # type: ignore
    param_value: bpy.props.StringProperty(name='') # type: ignore

def sorted_enums(filter):
    if 'print_profiles' in blender_globals:
        profiles = blender_globals['print_profiles']
        enums = [(item['absolute_path'], item['label'], item['absolute_path']) for item in profiles if item['type'] == filter] + [("", "", "")]
        return sorted(enums, key=lambda x: x[1])
    return [("","","")]

def reset_selection(object, field):
    if getattr(object, field) > -1:
        setattr(object, field, -1)

def selection_to_list(object, search_term, search_list, search_index, search_field, target_list, target_list_field):
    if getattr(object, search_index) > -1:
        selection = getattr(object,search_list)[getattr(object, search_index)]
        new_item = getattr(object, target_list).add()
        setattr(new_item, search_field, getattr(selection, target_list_field))
        reset_selection(object, search_index)
        setattr(object, search_term, "")

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
    
    printer_config_file: bpy.props.StringProperty(
        name="Printer Configuration (.ini)",
        subtype='FILE_PATH'
    ) # type: ignore
    
    filament_config_file: bpy.props.StringProperty(
        name="Filament Configuration (.ini)",
        subtype='FILE_PATH'
    ) # type: ignore
    
    print_config_file: bpy.props.StringProperty(
        name="Print Configuration (.ini)",
        subtype='FILE_PATH'
    ) # type: ignore

    printer_config_file_enum: bpy.props.EnumProperty(
        name="Printer Configuration",
        items=lambda self, context: sorted_enums('printer'),
        update=lambda self, context: setattr(self, 'printer_config_file', self.printer_config_file_enum),
    ) # type: ignore

    filament_config_file_enum: bpy.props.EnumProperty(
        name="Filament Configuration",
        items=lambda self, context: sorted_enums('filament'),
        update=lambda self, context: setattr(self, 'filament_config_file', self.filament_config_file_enum),
    ) # type: ignore

    print_config_file_enum: bpy.props.EnumProperty(
        name="Print Configuration",
        items=lambda self, context: sorted_enums('print'),
        update=lambda self, context: setattr(self, 'print_config_file', self.print_config_file_enum),
    ) # type: ignore

    def search_param_list(self, context):
        if not self.search_term:
            return
        
        self.search_list.clear()
        self.search_list_index = -1

        search_db = parse_csv_to_tuples('functions/prusaslicer_fields.csv')
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