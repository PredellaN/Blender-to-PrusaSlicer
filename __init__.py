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
registered_classes = []

def register():
    from . import preferences as pref
    registered_classes.extend(mod.register_classes(mod.get_classes([pref])))

    from . import operators as op
    from . import panels as pn
    from . import property_groups as pg
    registered_classes.extend(mod.register_classes(mod.get_classes([op,pn,pg])))

    setattr(bpy.types.WorkSpace, PG_NAME, bpy.props.PointerProperty(type=pg.PrusaSlicerPropertyGroup))

    pass
def unregister():
    mod.unregister_classes(registered_classes)
    pass

if __name__ == "__main__":
    register()