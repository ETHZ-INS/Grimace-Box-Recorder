# Grimace Recorder Project

## UI

    .
    ├── ui                # Qt Designer .ui files
    ├── app               
    │   ├── layout        # Python .py layout files auto-generated from .ui files
    │   └── controller    # Python controller files for the UI
    └── main.py           # Main entry point for the application - controller file for the main window

The UI for the grimace recorder was created using Qt. The layout was designed using Qt Designer. 
The .ui files produced by Qt Designer are located in the ui folder. 

The Qt .ui files are converted to python .py files  using the `pyuic5` command.
These auto-generated python files are located in the app/layout folder and contain the layout of the UI, 
without any logic. They should not be edited manually as they get overwritten every time the UI is compiled.

For each layout file, there is a corresponding controller file in the app/controller folder, 
which contains the logic for the UI. The controller files are created manually.

## Machine Learning Models

    .
    ├── models               # PyTorch model weight .pt files
    └── grimace              # PyTorch model definition (Needs restructuring, will be changed soon)
        └── preprocessing    # Preprocessing functions to crop and resize images before feeding them to the models

There are three individual machine learning models used in the grimace recorder project.

The frame quality scorer is used to determine how usable a frame is for grimace scoring.
The face cropper is used to find the face of the mouse within the frame and crop it out.
The grimace scorer is used to determine the grimace score of the mouse from the cropped face.

The machine learning models are implemented using PyTorch. The model definitions are located in the grimace folder.
The grimace/preprocessing folder contains functions to crop and resize images before feeding them to the models.

The model weights are saved as .pt files in the models folder.
The model weights are currently not included in the GitHub repository because they should be stored more centrally for different projects.


## Application