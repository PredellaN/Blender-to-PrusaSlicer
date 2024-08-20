# Blender to PrusaSlicer

![image](https://github.com/user-attachments/assets/f13cccaf-884a-4c8c-8190-55c6d848d2cf)

## Overview
This Blender addon integrates PrusaSlicer directly within Blender, allowing for seamless 3D model slicing and export to G-code without leaving the Blender environment.

## Features
PrusaSlicer Integration: Slice models and open them in PrusaSlicer directly from Blender.

Custom Configurations: Load and apply custom PrusaSlicer configuration files (.ini).

## Installation
- Clone or download this repository.
- Open Blender and go to Edit > Preferences > Add-ons.
- Click Install and select the .zip file of the addon.
- Enable the addon in the preferences.
- In the Addon configuration, specify the path to the PrusaSlicer executable. Also commands (such as flatpak run) are supported.

## Usage
- Load a custom configuration file (.ini) for slicing settings. You can export the configuration file from a prusaslicer project using File > Export > Export Config
- Select the objects to slice in Blender.
- Click "Slice" to generate G-code or "Open with PrusaSlicer" to view the model in PrusaSlicer.

## Requirements
- Blender 4.2.0 or higher.
- PrusaSlicer installed and accessible from the command line.

## License
This project is licensed under the MIT License.
