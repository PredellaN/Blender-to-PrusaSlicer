from .functions import basic_functions as bf

PG_NAME = "BlenderPrusaSlicer"
PG_NAME_LC = PG_NAME.lower()
DEPENDENCIES = (
    bf.Dependency(module="psutil", package=None, name=None),
    )