import bpy
from .functions import modules as mod
from .constants import PG_NAME_LC, PG_NAME

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

def register():
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
    mod.unregister_classes(registered_classes)


if __name__ == "__main__":
    register()
