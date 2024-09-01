import bpy, sys, os

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
    "description" : "",
    "blender" : (4, 2, 0),
    "version" : (0, 0, 2),  
    "location" : "",
    "warning" : "",
}
registered_classes = []
dependencies_installed = False
sys.path.append(DEPENDENCIES_FOLDER)


def register():
    from .functions import modules as mod

    global dependencies_installed
    dependencies_installed = mod.are_dependencies_installed(DEPENDENCIES, DEPENDENCIES_FOLDER)

    from . import preferences as pref
    mod.reload_modules([pref])
    registered_classes.extend(mod.register_classes(mod.get_classes([pref])))

    from . import operators as op
    from . import panels as pn
    from . import property_groups as pg
    mod.reload_modules([op, pn, pg])
    registered_classes.extend(mod.register_classes(mod.get_classes([op,pn,pg])))

    setattr(bpy.types.WorkSpace, PG_NAME_LC, bpy.props.PointerProperty(type=pg.PrusaSlicerPropertyGroup))

def unregister():   
    from .functions import modules as mod

    mod.unregister_classes(registered_classes)


if __name__ == "__main__":
    register()
