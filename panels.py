import bpy
from .basic_functions import BasePanel

class PrusaSlicerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    prusaslicer_path: bpy.props.StringProperty(
        name="PrusaSlicer Path",
        description="Path to the PrusaSlicer executable",
        subtype='FILE_PATH',
        default="flatpak run com.prusa3d.PrusaSlicer"
    ) #type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "prusaslicer_path")

class PrusaSlicerPanel(BasePanel):
    bl_label = "PrusaSlicer"
    bl_idname = "SCENE_PT_PrusaSlicerPanel"

    def draw(self, context):
        ws = context.workspace
        layout = self.layout

        row = layout.row()
        row.prop(ws.bps, "config", text="Configuration (.ini)")

        row = layout.row()
        row.operator("bps.slice", text="Slice", icon="ALIGN_JUSTIFY").mode="slice"
        row.operator("bps.slice", text="Open with PrusaSlicer").mode="open"

        row = layout.row()
        row.prop(ws.bps, "progress", text=ws.bps.progress_text, slider=True)
        row.enabled = False