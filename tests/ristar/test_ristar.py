import hashlib
import tempfile

from PySide.QtCore import Qt
from PySide.QtGui import QAction, QFileDialog


def get_bmp_sha1(filename):
    """
    Get the sha1 hash of the pixel data in a bmp file.

    This is used to check if two bitmaps are identical.
    """
    bitmap_data_offset = 0x36  # skip the BMP header (it's not standard across all platforms)

    with open(filename, 'rb') as f:
        contents = f.read()
        bitmap_data = contents[bitmap_data_offset:]
        bitmap_hash = hashlib.sha1(bitmap_data)

        return bitmap_hash.hexdigest()


def run_frames(display, n):
    """
    Emulate n frames.
    """
    for i in range(n):
        display.frame()


def test_ristar(qtbot, mock):
    """
    Run Ristar.

      - Run for 7000 frames.
      - Select every zoom/render filter combo, run for 5 frames
        and check if the video output (screenshot) is correct.
      - Enable debug mode, press Start, check if the debug text is correct.
    """
    from kiwi import MainWindow, render_filters
    window = MainWindow()
    qtbot.addWidget(window)

    display = window.display

    display.set_zoom_level(QAction('1x', window))
    mock.patch.object(QFileDialog, 'getOpenFileName', return_value=('./tests/ristar/Ristar (UE) [!].zip', '*.zip'))
    display.open_file()

    run_frames(display, 7000)

    assert display.frames == 7000

    for scale_factor in ('1x', '2x', '3x', '4x'):
        for render_filter in render_filters:
            display.set_zoom_level(QAction(scale_factor, window))
            display.set_render_filter(QAction(render_filter, window))

            run_frames(display, 5)

            filename_suffix = '-{}-{}.bmp'.format(scale_factor, render_filter.lower())

            _, filename = tempfile.mkstemp(suffix=filename_suffix)
            display.save_screenshot(filename)

            assert get_bmp_sha1(filename) == get_bmp_sha1('./tests/ristar/ristar-screenshot'+filename_suffix)

    display.set_zoom_level(QAction('1x', window))
    display.toggle_debug()

    qtbot.keyPress(window, Qt.Key_Q)
    run_frames(display, 50)
    qtbot.keyRelease(window, Qt.Key_Q)

    run_frames(display, 500)

    debug_text = display.debug_label.text() + '\n'
    _, _, debug_text = debug_text.partition('\n\n')

    with open('./tests/ristar/debug-output.txt') as f:
        expected_debug_text = f.read()

    assert debug_text == expected_debug_text
