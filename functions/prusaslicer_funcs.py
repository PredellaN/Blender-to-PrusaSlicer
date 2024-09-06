
import os, tempfile
import subprocess

temp_dir = tempfile.gettempdir()

def exec_prusaslicer(command, prusaslicer_path):

    if os.path.exists(prusaslicer_path):
        command=[f'{prusaslicer_path}'] + command
    else:
        command=[*prusaslicer_path.split() + command]

    print(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")

        if e.stderr:
            print("PrusaSlicer error output:")
            print(e.stderr)

    if result.stdout:
        print("PrusaSlicer output:")
        print(result.stdout)
        for line in result.stdout.splitlines():
            if "[error]" in line.lower():
                error_part = line.lower().split("[error]", 1)[1].strip()
                err_to_tempfile(result.stdout)
                return error_part

            if "slicing result exported" in line.lower():
                return

        err_to_tempfile(result.stdout)
        return "No error message returned, check your model size"
    
def err_to_tempfile(text):
    temp_file_path = os.path.join(temp_dir, "prusa_slicer_err_output.txt")
    with open(temp_file_path, "w") as temp_file:
        temp_file.write(text)