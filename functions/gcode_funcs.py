import re

def parse_gcode(file_path, name):
    val = None
    pattern = re.compile(rb'^;? ?' + name.encode('utf-8') + rb' ?= ?(.+)$')
    with open(file_path, 'rb') as file:  # Open in binary mode
        lines = file.readlines()[::-1] # Read all lines and reverse the order
        for line in lines:
            try:
                val = pattern.search(line)
                if val:
                    return val.group(1).decode()
            except UnicodeDecodeError:
                continue
    return None