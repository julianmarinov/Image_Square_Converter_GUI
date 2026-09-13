# Image Square Converter

[![Tests](https://github.com/julianmarinov/Image_Square_Converter_GUI/actions/workflows/python-package.yml/badge.svg)](https://github.com/julianmarinov/Image_Square_Converter_GUI/actions/workflows/python-package.yml)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A small desktop app that turns a whole folder of rectangular images into square ones by padding them with white space. Nothing is cropped or stretched.

It's made for e-commerce product photos, marketplace listings and anywhere else that needs uniform square images. On a 2015 MacBook Pro it converted 3,300+ images in about 40 seconds.

![Before and after: a 600x300 image padded to 600x600](docs/before-after.png)

## Features

- **Batch conversion.** Pick a folder and every `.png`, `.jpg`, `.jpeg` and `.gif` inside it is converted, including subfolders.
- **Keeps your folder structure.** Subfolders are mirrored in the export folder, so files with the same name never overwrite each other.
- **Clean results.**
  - Transparent areas become white.
  - Phone photos keep their correct orientation.
  - JPEGs are saved at high quality with their color profile intact.
- **Safe by default.**
  - Your originals are never modified.
  - Choosing the same folder for import and export is blocked.
- **Handles problem files.** Broken or unreadable images are skipped and listed in a summary instead of stopping the batch.
- **Responsive window.** A live progress bar shows how far along the conversion is, and you can close the app at any time.

## Download

A ready-to-run macOS app is attached to the latest release on the [Releases page](https://github.com/julianmarinov/Image_Square_Converter_GUI/releases). Unzip it and move **Image Square Converter.app** to Applications.

The app isn't signed with an Apple Developer ID, so macOS will warn you the first time. Right-click the app, choose **Open**, then confirm.

## Run from source

Requires Python 3.9 or newer with Tkinter. Tkinter is included with the python.org installers; with Homebrew, run `brew install python-tk`.

```bash
git clone https://github.com/julianmarinov/Image_Square_Converter_GUI.git
cd Image_Square_Converter_GUI
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

On Windows, use `venv\Scripts\pip` and `venv\Scripts\python` instead.

## Usage

1. Click **Browse** next to **Import Path** and choose the folder with your images.
2. Click **Browse** next to **Export Path** and choose where the square images should go.
3. Click **Convert to Square** and wait for the summary.

## Build the macOS app

```bash
venv/bin/pip install pyinstaller
venv/bin/pyinstaller main.spec
```

The app is created at `dist/Image Square Converter.app`. It is built for the architecture of the Mac you build it on.

## Development

```bash
venv/bin/pip install pytest flake8
venv/bin/pytest
```

- `square_converter.py` holds the image logic and doesn't depend on Tkinter.
- `main.py` is the GUI.
- Tests live in `tests/` and run on GitHub Actions for Python 3.9–3.12.

## License

[MIT](LICENSE) © Julian Marinov
