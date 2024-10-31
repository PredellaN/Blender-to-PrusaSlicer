import bpy # type: ignore
from .functions.basic_functions import BasePanel, BaseList, is_usb_device
from .functions import blender_funcs as bf
from . import PG_NAME_LC, dependencies_installed, blender_globals

class PRUSASLICER_UL_IdValue(BaseList):
    def draw_properties(self, row, item):
        row.prop(item, "param_id")
        row.prop(item, "param_value")

class PRUSASLICER_UL_PauseValue(BaseList):
    def draw_properties(self, row, item):
        row.prop(item, "param_type")
        row.label(text="on layer")
        row.prop(item, "param_value")

class PrusaSlicerPanel(BasePanel):
    bl_label = "Blender to PrusaSlicer"
    bl_idname = f"SCENE_PT_{PG_NAME_LC}"

    def draw(self, context):
        cx = bf.coll_from_selection()
        pg = getattr(cx, PG_NAME_LC)

        layout = self.layout

        # Toggle button for single or multiple configuration files
        row = layout.row()

        global blender_globals
        sliceable = (pg.use_single_config and pg.config) or ((not pg.use_single_config or blender_globals["uses_manifest"]) and pg.printer_config_file and pg.filament_config_file and pg.print_config_file)

        if blender_globals["uses_manifest"]:
            row = layout.row()
            row.prop(pg, "printer_config_file_enum", text="Printer")
            
            row = layout.row()
            row.prop(pg, "filament_config_file_enum", text="Filament")
            
            row = layout.row()
            row.prop(pg, "print_config_file_enum", text="Print")

        else:
            row.prop(pg, "use_single_config", text="Use Single Configuration")
            if pg.use_single_config:
                row = layout.row()
                row.prop(pg, "config", text="Configuration (.ini)")
            else:
                row = layout.row()
                row.prop(pg, "printer_config_file", text="Printer (.ini)")
                
                row = layout.row()
                row.prop(pg, "filament_config_file", text="Filament (.ini)")
                
                row = layout.row()
                row.prop(pg, "print_config_file", text="Print (.ini)")

        row = layout.row()

        if sliceable:
            
            op = row.operator(f"{PG_NAME_LC}.slice", text="Slice", icon="ALIGN_JUSTIFY")
            op.mode="slice"
            op.mountpoint=""
            op = row.operator(f"{PG_NAME_LC}.slice", text="Slice and Preview", icon="ALIGN_JUSTIFY")
            op.mode="slice_and_preview"
            op.mountpoint=""
            
        row.operator(f"{PG_NAME_LC}.slice", text="Open with PrusaSlicer").mode="open"
        # row.enabled = False if pg.running else True

        if pg.print_time:
            row = layout.row()
            row.label(text=f"Printing time: {pg.print_time}")
        if pg.print_weight:
            row = layout.row()
            row.label(text=f"Print weight: {pg.print_weight}g")

        row = layout.row()
        row.prop(pg, "progress", text=pg.progress_text, slider=True)
        row.enabled = False

        ### USB Devices
        if dependencies_installed:
            import psutil
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
                    row.enabled = False if pg.running else True
                    row.operator(f"{PG_NAME_LC}.unmount_usb", text="", icon='UNLOCKED').mountpoint=mountpoint
                    op = row.operator(f"{PG_NAME_LC}.slice", text="", icon='DISK_DRIVE')
                    op.mountpoint=mountpoint
                    op.mode = "slice"
                    row.label(text=f"{mountpoint.split('/')[-1]} mounted at {mountpoint} ({partition.device})")

class SlicerPanel_0_Overrides(BasePanel):
    bl_label = "Configuration Overrides"
    bl_idname = f"SCENE_PT_{PG_NAME_LC}_Overrides"
    bl_parent_id = f"SCENE_PT_{PG_NAME_LC}"
    list_id = f"list"

    def draw(self, context):
        cx = bf.coll_from_selection()
        pg = getattr(cx, PG_NAME_LC)

        layout = self.layout

        row = layout.row()
        
        row.template_list(f"PRUSASLICER_UL_IdValue", f"{self.list_id}",
                pg, f"{self.list_id}",
                pg, f"{self.list_id}_index"
                )
        row = layout.row()
        row.operator(f"{PG_NAME_LC}.add_param").target=f"{self.list_id}"

class SlicerPanel_1_Pauses(BasePanel):
    bl_label = "Pauses and Color Changes"
    bl_idname = f"SCENE_PT_{PG_NAME_LC}_Pauses"
    bl_parent_id = f"SCENE_PT_{PG_NAME_LC}"
    list_id = f"pause_list"

    def draw(self, context):
        cx = bf.coll_from_selection()
        pg = getattr(cx, PG_NAME_LC)

        layout = self.layout

        row = layout.row()
        row.template_list(f"PRUSASLICER_UL_PauseValue", f"{self.list_id}",
                pg, f"{self.list_id}",
                pg, f"{self.list_id}_index"
                )
        row = layout.row()
        row.operator(f"{PG_NAME_LC}.add_param").target=f"{self.list_id}"