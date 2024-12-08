import bpy, sys, os
from . import globals

### Constants
ADDON_FOLDER = os.path.dirname(os.path.abspath(__file__))
DEPENDENCIES_FOLDER = os.path.join(ADDON_FOLDER, "deps")
PG_NAME = "BlenderToPrusaSlicer"
PG_NAME_LC = PG_NAME.lower()

### Dependencies
from collections import namedtuple
Dependency = namedtuple("Dependency", ["module", "package", "name"])
DEPENDENCIES = (
    Dependency(module="psutil", package=None, name=None),
    )

### Blender Addon Initialization
bl_info = {
    "name" : "Blender To PrusaSlicer",
    "author" : "Nicolas Predella",
    "description" : "PrusaSlicer integration into Blender",
    "blender" : (4, 2, 0),
    "version" : (0, 1, 0),  
    "location" : "",
    "warning" : "",
}

### Initialization
registered_classes = []

sys.path.append(DEPENDENCIES_FOLDER)


def register():
    from .functions import modules as mod

    globals.dependencies_installed = mod.are_dependencies_installed(DEPENDENCIES)

    from . import preferences as pref
    mod.reload_modules([pref])
    registered_classes.extend(mod.register_classes(mod.get_classes([pref])))
    prefs = bpy.context.preferences.addons[__package__].preferences
    prefs.update_config_bundle_manifest()

    from . import operators as op
    from . import panels as pn
    from . import property_groups as pg
    mod.reload_modules([op, pn, pg])
    registered_classes.extend(mod.register_classes(mod.get_classes([op,pn,pg])))

    setattr(bpy.types.Collection, PG_NAME_LC, bpy.props.PointerProperty(type=pg.PrusaSlicerPropertyGroup))

def unregister():   
    from .functions import modules as mod

    mod.unregister_classes(registered_classes)


if __name__ == "__main__":
    register()
