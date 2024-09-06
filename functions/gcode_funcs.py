import re

def parse_print_stats(file_path):
    # Initialize variables to hold print time and weight
    print_time = None
    filament_weight = None

    # Define regex patterns for extracting data
    time_pattern = re.compile(r'^; estimated printing time \(normal mode\) = (\d+?h \d+?m \d+?s)$')
    weight_pattern = re.compile(r'^; filament used \[g\] = (\d+?\.\d+?)$')

    # Read the G-code file in reverse
    with open(file_path, 'r') as file:
        lines = file.readlines()[::-1]  # Read all lines and reverse the order
        
        for line in lines:
            # Search for estimated printing time
            time_match = time_pattern.search(line)
            if time_match:
                print_time = time_match.group(1)
            
            # Search for filament weight
            weight_match = weight_pattern.search(line)
            if weight_match:
                filament_weight = weight_match.group(1) + 'g'

            # If both print time and weight are found, break the loop
            if print_time and filament_weight:
                break

    return print_time, filament_weight

def parse_gcode(file_path, name):
    val = None
    pattern = re.compile(r'^; ' + name + r' = (.+)$')
    with open(file_path, 'r') as file:
        lines = file.readlines()[::-1]  # Read all lines and reverse the order
        for line in lines:
            val = pattern.search(line)
            if val:
                return val.group(1)