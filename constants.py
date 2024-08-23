from .functions import basic_functions as bf

PG_NAME = __package__.lower()
DEPENDENCIES = (
    bf.Dependency(module="psutil", package=None, name=None),
    bf.Dependency(module="psutilsasd", package=None, name=None),
    )