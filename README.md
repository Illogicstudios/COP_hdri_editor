# Copernicus HDRI Editor
HDRI editor in Copernicus (houdini)

## Overview

This recipe allows the user to edit an HDRI in Copernicus with extra functions.

https://github.com/user-attachments/assets/9fd6f6ee-1e30-49da-b41d-e3f36a47bd4a

## Features

- Edit light settings with light_maker node
- Preview your HDRI directly in your scene
- Toggle a fake Houdini light to help the user editing light

## Installation

Simply add hda located in `./hda/` in your otls/hda houdini location.

If you want to use the multi add node in `./template/HDRI_cop_editor.hip` 
you will need to add the `./scripts/` somewhere Houdini can parse you python script.
For more details : [https://www.sidefx.com/docs/houdini/hom/locations.html](https://www.sidefx.com/docs/houdini/hom/locations.html)

## How to use it

1 - Enter in the COP Network\
![image](https://github.com/user-attachments/assets/068c91f2-3b48-4c11-a323-a3e900259fcc)

Tips: You can pin your scene to keep seeing it

2 - Create a Light Maker 2 Node (Please ignore the Light Maker node here):\
![navigation](https://github.com/user-attachments/assets/5166abcc-5a80-4977-a836-b9d6cadd8690)

3 - Here you can edit light settings\
![light_settings](https://github.com/user-attachments/assets/3bd142c3-9d46-4b1c-a8ee-be7bec3c63d3)

4 - You can also tick the Toggle Light to edit the light position in 3D with houdini light handler :\
![image](https://github.com/user-attachments/assets/efb5216d-5ad4-4946-a590-1e2da1f4a319) \
![image](https://github.com/user-attachments/assets/4aba29bf-5460-4cc2-af4a-fc2e0eab1891)

5 - If you lose your light you can select it again with the Select Light button :\
![image](https://github.com/user-attachments/assets/dd7a0969-daa5-46b7-b397-58bb4aaa97d3)
