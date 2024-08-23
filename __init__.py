import bpy
from .functions import modules as mod
from .constants import PG_NAME, DEPENDENCIES

bl_info = {
    "name" : "Blender to PrusaSlicer",
    "author" : "Nicolas Predella",
    "description" : "",
    "blender" : (4, 2, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

def register():

    from . import preferences as pref
    mod.register_classes(mod.get_classes([pref]))

    try:
        for dependency in DEPENDENCIES:
            mod.import_module(module_name=dependency.module, global_name=dependency.name)
    except ModuleNotFoundError:
        return

    from . import operators as op
    from . import panels as pn
    from . import property_groups as pg
    mod.register_classes(mod.get_classes([op,pn,pg]))

    setattr(bpy.types.WorkSpace, PG_NAME, bpy.props.PointerProperty(type=pg.PrusaSlicerPropertyGroup))

def unregister():
    from . import preferences as pref
    from . import operators as op
    from . import panels as pn
    from . import property_groups as pg
    mod.unregister_classes(mod.get_classes([op,pn,pg,pref]))

if __name__ == "__main__":
    register()