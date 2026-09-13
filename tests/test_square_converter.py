import os
import threading

from PIL import Image

from square_converter import (
    convert_all,
    find_images,
    make_square,
    output_path,
    validate_dirs,
)

RED = (255, 0, 0)
WHITE = (255, 255, 255)


def save_image(path, size=(40, 20), color=RED, mode='RGB', **kwargs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.new(mode, size, color).save(path, **kwargs)
    return path


def test_landscape_is_padded_top_and_bottom():
    result = make_square(Image.new('RGB', (40, 20), RED))
    assert result.size == (40, 40)
    assert result.getpixel((20, 0)) == WHITE
    assert result.getpixel((20, 20)) == RED
    assert result.getpixel((20, 39)) == WHITE


def test_portrait_is_padded_left_and_right():
    result = make_square(Image.new('RGB', (20, 40), RED))
    assert result.size == (40, 40)
    assert result.getpixel((0, 20)) == WHITE
    assert result.getpixel((20, 20)) == RED
    assert result.getpixel((39, 20)) == WHITE


def test_transparent_pixels_become_white():
    im = Image.new('RGBA', (20, 20), (0, 0, 0, 0))
    im.putpixel((10, 10), (255, 0, 0, 255))
    result = make_square(im)
    assert result.mode == 'RGB'
    assert result.getpixel((0, 0)) == WHITE
    assert result.getpixel((10, 10)) == RED


def test_palette_gif_transparency_becomes_white(tmp_path):
    im = Image.new('P', (20, 10), 0)
    im.putpalette([0, 0, 0, 255, 0, 0] + [0] * 762)
    im.putpixel((5, 5), 1)
    path = str(tmp_path / 'a.gif')
    im.save(path, transparency=0)
    with Image.open(path) as loaded:
        result = make_square(loaded)
    assert result.getpixel((0, 5)) == WHITE
    assert result.getpixel((5, 10)) == RED


def test_exif_orientation_is_applied(tmp_path):
    im = Image.new('RGB', (40, 20), RED)
    exif = im.getexif()
    exif[0x0112] = 6  # rotate 90° clockwise when displayed
    path = str(tmp_path / 'phone.jpg')
    im.save(path, exif=exif)
    with Image.open(path) as loaded:
        result = make_square(loaded)
    # Displayed image is 20 wide x 40 tall, so padding goes left/right, not top/bottom.
    assert result.size == (40, 40)
    assert result.getpixel((2, 20)) == WHITE
    r, g, b = result.getpixel((20, 2))
    assert r > 200 and g < 60 and b < 60


def test_find_images_skips_hidden_non_images_and_nested_export(tmp_path):
    src = tmp_path / 'in'
    export = src / 'out'
    save_image(str(src / 'a.jpg'))
    save_image(str(src / 'sub' / 'B.JPG'))
    save_image(str(src / '.hidden.png'), format='PNG')
    (src / '._a.jpg').write_bytes(b'\x00\x05\x16\x07 AppleDouble')
    (src / 'notes.txt').write_text('hi')
    save_image(str(export / 'old.jpg'))

    found = find_images(str(src), str(export))

    assert [os.path.relpath(p, str(src)) for p in found] == ['a.jpg', os.path.join('sub', 'B.JPG')]


def test_convert_all_mirrors_subfolders_without_collisions(tmp_path):
    src = tmp_path / 'in'
    out = tmp_path / 'out'
    out.mkdir()
    save_image(str(src / 'shirts' / '1.jpg'), color=RED)
    save_image(str(src / 'shoes' / '1.jpg'), color=(0, 0, 255), size=(20, 40))

    paths = find_images(str(src), str(out))
    converted, failures = convert_all(paths, str(src), str(out))

    assert (converted, failures) == (2, [])
    for rel in ('shirts/1.jpg', 'shoes/1.jpg'):
        with Image.open(str(out / rel)) as im:
            assert im.size == (40, 40)


def test_convert_all_nested_export_is_not_reprocessed(tmp_path):
    src = tmp_path / 'in'
    out = src / 'squared'
    out.mkdir(parents=True)
    save_image(str(src / 'a.jpg'))

    converted, failures = convert_all(find_images(str(src), str(out)), str(src), str(out))
    assert (converted, failures) == (1, [])
    # Running again must not pick up squared/a.jpg as a new source.
    assert find_images(str(src), str(out)) == [str(src / 'a.jpg')]


def test_bad_files_are_reported_and_batch_continues(tmp_path):
    src = tmp_path / 'in'
    out = tmp_path / 'out'
    out.mkdir()
    save_image(str(src / 'a_good.jpg'))
    (src / 'b_broken.jpg').write_bytes(b'not really an image')
    save_image(str(src / 'c_good.png'), format='PNG')

    progress = []
    converted, failures = convert_all(
        find_images(str(src), str(out)), str(src), str(out),
        on_progress=lambda done, total: progress.append((done, total)),
    )

    assert converted == 2
    assert [os.path.basename(p) for p, _ in failures] == ['b_broken.jpg']
    assert progress == [(1, 3), (2, 3), (3, 3)]
    assert (out / 'c_good.png').exists()


def test_cancel_stops_before_next_file(tmp_path):
    src = tmp_path / 'in'
    out = tmp_path / 'out'
    out.mkdir()
    for name in ('a.jpg', 'b.jpg', 'c.jpg'):
        save_image(str(src / name))
    cancel = threading.Event()

    converted, _ = convert_all(
        find_images(str(src), str(out)), str(src), str(out),
        on_progress=lambda done, total: cancel.set(),
        cancel_event=cancel,
    )
    assert converted == 1


def test_validate_dirs(tmp_path):
    a = tmp_path / 'a'
    b = tmp_path / 'b'
    a.mkdir()
    b.mkdir()
    assert validate_dirs(str(a), str(b)) is None
    assert validate_dirs(str(a), str(a)) is not None
    assert validate_dirs(str(a), str(tmp_path / 'missing')) is not None
    assert validate_dirs('', str(b)) is not None


def test_output_path_mirrors_relative_location():
    assert output_path(os.path.join('in', 'x', 'y.png'), 'in', 'out') == os.path.join('out', 'x', 'y.png')
