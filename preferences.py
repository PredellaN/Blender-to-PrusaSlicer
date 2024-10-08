import bpy, os
import subprocess
from .functions import modules as mod
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

        layout = self.layout
        if dependencies_installed:
            layout.label(icon='CHECKMARK', text="Dependencies installed")
        else:
            layout.operator(f"{PG_NAME_LC}.install_dependencies", icon="CONSOLE")
