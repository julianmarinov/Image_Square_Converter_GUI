import os

from PIL import Image, ImageOps

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')
JPEG_EXTENSIONS = ('.jpg', '.jpeg')


def _same_path(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def validate_dirs(import_dir, export_dir):
    """
    Return an error message if the folders can't be used, otherwise None.
    """
    if not import_dir or not os.path.isdir(import_dir):
        return "Please select a valid import folder."
    if not export_dir or not os.path.isdir(export_dir):
        return "Please select a valid export folder."
    if _same_path(import_dir, export_dir):
        return "The export folder must be different from the import folder, " \
               "otherwise the original images would be overwritten."
    return None


def make_square(im, fill_color=(255, 255, 255)):
    """
    Add white space to the image to make it square.
    """
    im = ImageOps.exif_transpose(im)

    if im.mode in ('RGBA', 'LA', 'PA') or 'transparency' in im.info:
        im = im.convert('RGBA')
        mask = im
    else:
        im = im.convert('RGB')
        mask = None

    x, y = im.size
    size = max(x, y)
    new_im = Image.new('RGB', (size, size), fill_color)
    new_im.paste(im, ((size - x) // 2, (size - y) // 2), mask)
    return new_im


def find_images(import_dir, export_dir=None):
    """
    Return a sorted list of image paths under import_dir, skipping hidden files
    (including macOS "._" files) and the export folder if it's nested inside.
    """
    paths = []
    for folder, dirs, files in os.walk(import_dir):
        dirs[:] = sorted(
            d for d in dirs
            if not d.startswith('.')
            and not (export_dir and _same_path(os.path.join(folder, d), export_dir))
        )
        for filename in sorted(files):
            if filename.startswith('.'):
                continue
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                paths.append(os.path.join(folder, filename))
    return paths


def output_path(src, import_dir, export_dir):
    """
    Mirror the source's location relative to import_dir inside export_dir.
    """
    return os.path.join(export_dir, os.path.relpath(src, import_dir))


def convert_one(src, dst):
    """
    Square a single image and save it to dst, creating folders as needed.
    """
    if os.path.exists(dst) and os.path.samefile(src, dst):
        raise ValueError("output would overwrite the source image")

    with Image.open(src) as img:
        icc_profile = img.info.get('icc_profile') if img.mode != 'CMYK' else None
        squared_image = make_square(img)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    save_kwargs = {}
    if icc_profile and not dst.lower().endswith('.gif'):
        save_kwargs['icc_profile'] = icc_profile
    if dst.lower().endswith(JPEG_EXTENSIONS):
        save_kwargs['quality'] = 95
    squared_image.save(dst, **save_kwargs)


def convert_all(paths, import_dir, export_dir, on_progress=None, cancel_event=None):
    """
    Convert every path, carrying on past bad files.
    Returns (converted_count, [(path, error_message), ...]).
    """
    converted = 0
    failures = []
    for index, src in enumerate(paths, start=1):
        if cancel_event is not None and cancel_event.is_set():
            break
        try:
            convert_one(src, output_path(src, import_dir, export_dir))
            converted += 1
        except Exception as e:  # one broken file shouldn't stop the batch
            failures.append((src, str(e)))
        if on_progress is not None:
            on_progress(index, len(paths))
    return converted, failures
