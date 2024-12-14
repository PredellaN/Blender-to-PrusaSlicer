import bpy
from bpy.utils import register_class, unregister_class
import inspect

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