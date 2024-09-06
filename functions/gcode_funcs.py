import re

def parse_gcode(file_path, name):
    val = None
    pattern = re.compile(rb'^;? ?' + name.encode('utf-8') + rb' ?= ?(.+)$')
    with open(file_path, 'rb') as file:  # Open in binary mode
        lines = file.readlines() # Read all lines and reverse the order
        for line in lines:
            try:
                # Attempt to decode each line as UTF-8
                val = pattern.search(line)
                if val:
                    return val.group(1).decode('utf-8')  # Return the decoded match
            except UnicodeDecodeError:
                # If a line contains binary data that can't be decoded, skip it
                continue
    return None