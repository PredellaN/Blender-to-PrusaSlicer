# Blender to PrusaSlicer

![image](https://github.com/user-attachments/assets/a8722c22-4711-4717-a267-c1d2330d9729)

## Overview
This Blender add-on integrates PrusaSlicer directly within Blender, allowing for seamless 3D model slicing and export to G-code without leaving the Blender environment.

## Features
PrusaSlicer Integration: Slice models and open them in PrusaSlicer directly from Blender.

Custom Configurations: Load and apply custom PrusaSlicer configuration files (.ini).

## Installation
- Clone or download this repository.
- Open Blender and go to Edit > Preferences > Add-ons.
- Click Install and select the .zip file of the add-on.
- Enable the add-on in the preferences.
- Install psutil using the "Install dependencies" button in the add-on preferences
- In the add-on preferences also specify the path to the PrusaSlicer executable. Commands (such as flatpak run) are also supported.

## Usage
- Load a custom configuration file (.ini) for slicing settings. You can export the configuration file from a PrusaSlicer project using File > Export > Export Config. URLs are also supported.
- Select the objects to slice in Blender.
- Find the PrusaSlicer section in the Scene menu

![Screenshot from 2024-08-20 23-06-57](https://github.com/user-attachments/assets/9f58fdfb-c026-4b84-8f19-616d8ddf298f)
- Use the overrides panel to customize the slicing. The original configuration file itself will remain unchaged. After slicing one time, the used configuration will be loaded in an internal text file "prusaslicer_configuration.json"
- Click "Slice" to generate G-code (it will be saved in the same folder as the .blend file) or "Open with PrusaSlicer" to view the model in PrusaSlicer. It's also possible to Slice to USB device by clicking on the drive button, and unmounting using the unlock button.

## Requirements
- Blender 4.2.0 or higher.
- PrusaSlicer installed and accessible from the command line.

## License
This project is licensed under the MIT License.
