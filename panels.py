import bpy # type: ignore
from .functions.basic_functions import BasePanel, is_usb_device
from .constants import WS_ATTRIBUTE_NAME
import psutil

class PRUSASLICER_UL_IdValue(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()

        delete_op = row.operator(f"{WS_ATTRIBUTE_NAME}.remove_param", text="", icon='X')
        delete_op.item_index = index

        row.prop(item, "param_id")
        row.prop(item, "param_value")

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
    bl_label = "Blender to PrusaSlicer"
    bl_idname = "SCENE_PT_PrusaSlicerPanel"

    def draw(self, context):
        ws = context.workspace
        prop_group = getattr(ws, WS_ATTRIBUTE_NAME)

        layout = self.layout

        row = layout.row()
        row.prop(prop_group, "config", text="Configuration (.ini)")

        row = layout.row()
        row.operator(f"{WS_ATTRIBUTE_NAME}.slice", text="Slice", icon="ALIGN_JUSTIFY").mode="slice"
        row.operator(f"{WS_ATTRIBUTE_NAME}.slice", text="Open with PrusaSlicer").mode="open"

        row = layout.row()
        row.prop(prop_group, "progress", text=prop_group.progress_text, slider=True)
        row.enabled = False

        ### USB Devices

        partitions = psutil.disk_partitions()

        for partition in partitions:
            if is_usb_device(partition):
                row = layout.row()
                row.label(text="Detected USB Devices:")
                break

        for partition in partitions:
            if is_usb_device(partition):
                row = layout.row()
                mountpoint = partition.mountpoint
                row.enabled = False if prop_group.running else True
                row.operator(f"{WS_ATTRIBUTE_NAME}.unmount_usb", text="", icon='UNLOCKED').mountpoint=mountpoint
                row.operator(f"{WS_ATTRIBUTE_NAME}.slice", text="", icon='DISK_DRIVE').mountpoint=mountpoint
                row.label(text=f"{mountpoint.split('/')[-1]} mounted at {mountpoint} ({partition.device})")

        ### Config Overrides

        row = layout.row()
        row.label(text="Configuration Overrides")

        row = layout.row()
        row.template_list(f"PRUSASLICER_UL_IdValue", "Params",
                prop_group, f"list",
                prop_group, f"list_index"
                )
        row = layout.row()
        row.operator(f"{WS_ATTRIBUTE_NAME}.add_param")
