import bpy
import subprocess
from .constants import PG_NAME, DEPENDENCIES
from .functions import modules as mod

class EXAMPLE_OT_install_dependencies(bpy.types.Operator):
    bl_idname = f"{PG_NAME}.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required python packages for this add-on")
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        try:
            mod.install_pip()
            for dependency in DEPENDENCIES:
                mod.install_and_import_module(module_name=dependency.module,
                                          package_name=dependency.package,
                                          global_name=dependency.name)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        global dependencies_installed
        dependencies_installed = True

        return {"FINISHED"}

class PrusaSlicerPreferences(bpy.types.AddonPreferences):
    bl_idname = f"{PG_NAME}.preferences"

    prusaslicer_path: bpy.props.StringProperty(
        name="PrusaSlicer Path",
        description="Path to the PrusaSlicer executable",
        subtype='FILE_PATH',
        default="flatpak run com.prusa3d.PrusaSlicer"
    ) #type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "prusaslicer_path")

        try:
            for dependency in DEPENDENCIES:
                mod.import_module(module_name=dependency.module, global_name=dependency.name)
        except ModuleNotFoundError:
            return
        
        layout.operator(f"{PG_NAME}.install_dependencies", icon="CONSOLE")