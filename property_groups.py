import bpy
from . import blender_globals

class ParamsListItem(bpy.types.PropertyGroup):
    param_id: bpy.props.StringProperty(name='') # type: ignore
    param_value: bpy.props.StringProperty(name='') # type: ignore

def sorted_enums(filter):
    if 'print_profiles' in blender_globals:
        profiles = blender_globals['print_profiles']
        enums = [(item['absolute_path'], item['label'], item['absolute_path']) for item in profiles if item['type'] == filter] + [("", "", "")]
        return sorted(enums, key=lambda x: x[1])
    return [("","","")]

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

    list : bpy.props.CollectionProperty(type=ParamsListItem) # type: ignore
    list_index : bpy.props.IntProperty(default=-1, update=lambda self, context: setattr(self, 'list_index', -1)) # Auto-deselect # type: ignore

    print_weight : bpy.props.StringProperty(name="") # type: ignore
    print_time : bpy.props.StringProperty(name="") # type: ignore

    cached_stl_chk : bpy.props.StringProperty() # type: ignore
    cached_ini_chk : bpy.props.StringProperty() # type: ignore
    cached_gcode_chk : bpy.props.StringProperty() # type: ignore