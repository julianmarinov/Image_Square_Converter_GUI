# Image_Square_Converter_GUI
Description:
A user-friendly GUI tool designed to convert rectangular images with a white background into square images by padding them with white space.
This tool supports a variety of formats including .png, .jpg, .jpeg, and .gif.
It is particularly useful for website product images or any use case where uniform square images are required.

Features:
Easy-to-use graphical interface built with Tkinter.
Support for multiple image formats: .png, .jpg, .jpeg, and .gif.
Progress bar to track the conversion process in real-time.
Integrated directory browsers for selecting input and output paths.
Error handling and user feedback for improved user experience.
Subfolders are mirrored in the export folder, so files with the same name never overwrite each other.
Transparent areas are filled with white, and phone photos keep their correct orientation.
Broken or unreadable files are skipped and listed in a summary instead of stopping the whole batch.
The window stays responsive during large conversions.

Installation:
pip install -r requirements.txt
python main.py

Running tests:
pip install pytest
pytest

Usage:
Launch the script.
Use the "Browse" buttons to select the import and export directories.
Click on "Convert to Square" to start the conversion process.
Wait for the progress bar to fill up and a success message to be displayed.
Perfect for e-commerce platforms, website developers, or any individual needing a batch image converter to square format.
