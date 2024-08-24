# Blender to PrusaSlicer

![image](https://github.com/user-attachments/assets/94925990-3329-4e52-9700-27dc8e269551)

## Overview
This Blender add-on integrates PrusaSlicer directly within Blender, allowing for seamless 3D model slicing and export to G-code without leaving the Blender environment.

## Features
Slice models and open them in PrusaSlicer directly from Blender.
- Import configurations either as a single .ini file (You can export this configuration file from a PrusaSlicer project using File > Export > Export Config.) or individual configuration files for printer, filament and print. URLs are also supported, which enables to for example fetch automatically the latest production version of the configuration.
- Slicing directly to USB devices.
- Customizing the slicing using overrides. The original configuration file itself will remain unchaged. After slicing one time, the base configuration will be loaded in an internal text file named "prusaslicer_configuration.json".

## Installation
- Clone or download this repository.
- Open Blender and go to Edit > Preferences > Add-ons.
- Click Install and select the .zip file of the add-on.
- Enable the add-on in the preferences.
- Install psutil using the "Install dependencies" button in the add-on preferences
- In the add-on preferences also specify the path to the PrusaSlicer executable. Commands (such as flatpak run) are also supported.

## Usage
- Load a custom configuration file (.ini) for slicing settings. 
- Select the objects to slice in Blender.
- Find the PrusaSlicer section in the Scene menu:

![Screenshot from 2024-08-20 23-06-57](https://github.com/user-attachments/assets/9f58fdfb-c026-4b84-8f19-616d8ddf298f)
- Use the overrides panel to change settings on the fly.
- Click "Slice" to generate and preview the G-code (it will be saved in the same folder as the .blend file) or "Open with PrusaSlicer" to export and open the model in the regular PrusaSlicer UI.

## Requirements
- Blender 4.2.0 or higher.
- PrusaSlicer installed and accessible from the command line.

## License
This project is licensed under the MIT License.
