import bpy
from bpy.utils import register_class, unregister_class
import os, subprocess, sys, importlib
from pathlib import Path
import inspect

def reload_modules(modules):
    for module in modules:
        importlib.reload(module)

def get_classes(modules):
    classes = []
    for module in modules:
        classes_in_module = [cls for name, cls in inspect.getmembers(module, inspect.isclass) if cls.__module__ == module.__name__ ]
        classes.extend(classes_in_module)
    return classes

def register_classes(classes):
    for class_to_register in classes:
        bpy.utils.register_class(class_to_register)
    return classes

def unregister_classes(classes):
    for class_to_register in classes:
        try:
            bpy.utils.unregister_class(class_to_register)
        except:
            continue
    return []

def install_pip():
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)

def import_module(module_name, global_name=None):
    if global_name is None:
        global_name = module_name

    if global_name in globals():
        importlib.reload(globals()[global_name])
    else:
        globals()[global_name] = importlib.import_module(module_name)

def install_and_import_module(module_name, package_name=None, global_name=None):
    package_name = module_name if package_name is None else package_name
    global_name = module_name if package_name is None else global_name

    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    if os.name == 'nt':
        pass #placeholder. not yet supported
    else:
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True, env=environ_copy)

    import_module(module_name, global_name)