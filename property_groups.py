import bpy

class ParamsListItem(bpy.types.PropertyGroup):
    param_id: bpy.props.StringProperty(name='') # type: ignore
    param_value: bpy.props.StringProperty(name='') # type: ignore

class PrusaSlicerPropertyGroup(bpy.types.PropertyGroup):
    running: bpy.props.BoolProperty(name="is running", default=0) # type: ignore
    progress: bpy.props.IntProperty(name="", min=0, max=100, default=0) # type: ignore
    progress_text: bpy.props.StringProperty(name="") # type: ignore

    config: bpy.props.StringProperty(
        name="PrusaSlicer Configuration (.ini)",  # type: ignore
        subtype='FILE_PATH'
    )

    list : bpy.props.CollectionProperty(type=ParamsListItem) # type: ignore
    list_index : bpy.props.IntProperty(default=-1, update=lambda self, context: setattr(self, 'list_index', -1)) # Auto-deselect # type: ignore 