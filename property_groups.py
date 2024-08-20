import bpy, os, tempfile, sys
import json

class PrusaPropertyGroup(bpy.types.PropertyGroup):
    running : bpy.props.BoolProperty(name="is running", default=0) # type: ignore
    progress : bpy.props.IntProperty(name="", min=0, max=100, default=0) # type: ignore
    progress_text : bpy.props.StringProperty(name="") # type: ignore
    stop_process: bpy.props.BoolProperty(name="stop", default=0) # type: ignore

    config : bpy.props.StringProperty(
        name="PrusaSlicer Configuration (.ini)",  # type: ignore
        subtype='FILE_PATH'
    )
