#!/usr/bin/env python
import sys
from ctypes import *
from zipfile import is_zipfile, ZipFile
from collections import OrderedDict
from PySide.QtCore import *
from PySide.QtGui import *
from debug import *

'''
The Kiwi emulator
'''

md = CDLL('./megadrive.so')
render_filters = ('None', 'EPX', 'hqx')

screen_buffer = create_string_buffer(320*240*4)  # allocate screen buffer

# keyboard mappings
buttons = ['up', 'down', 'left', 'right', 'b', 'c', 'a', 'start']
keymap = OrderedDict((
        ('left', (Qt.Key_Left, Qt.Key_J)),
        ('right', (Qt.Key_Right, Qt.Key_L)),
        ('up', (Qt.Key_Up, Qt.Key_I)),
        ('down', (Qt.Key_Down, Qt.Key_K)),
        ('a', (Qt.Key_Z, Qt.Key_F)),
        ('b', (Qt.Key_X, Qt.Key_G)),
        ('c', (Qt.Key_C, Qt.Key_H)),
        ('start', (Qt.Key_Q, Qt.Key_W)),
        ))

keymap_r = {}
for button, keys in keymap.items():
    keymap_r[keys[0]] = (button, 0)
    keymap_r[keys[1]] = (button, 1)

def blit_screen(label, scaled_buffer, zoom_level):
    '''
    Blits the screen to a QLabel.

    Creates a QImage from a RGB32 formatted buffer, creates a QPixmap from the QImage
    and loads the pixmap into a QLabel.
    '''
    image = QImage(scaled_buffer, 320*zoom_level, 240*zoom_level, QImage.Format_RGB32)
    pixmap = QPixmap.fromImage(image)

    label.setPixmap(pixmap)

class Controllers(QLabel):
    '''
    Controller mapping help window.
    '''
    def __init__(self, parent=None):
        super(Controllers, self).__init__(parent)

        text = '<table style="background-color: #222; color: #ddd"><tr><td valign="middle" style="padding: 10"><img src="images/megadrive.jpg"></td><td>'
        text += '<table style="font-family: Verdana" cellpadding="10">'
        text += '<tr style="color: #9b4"><th>Button</th><th>Player 1 Key</th><th>Player 2 Key</th></tr>'
        for button, keys in keymap.items():
            text += '<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>'.format(button.title(), QKeySequence(keys[0]).toString(), QKeySequence(keys[1]).toString())
        text += '</table></td></tr></table>'
        self.setText(text)
        self.setWindowTitle('Controllers')

class Display(QWidget):
    '''
    The main window.

    Handles the menu bar, keyboard input and displays the screen.
    '''
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)

        self.frames = 0
        self.pause_emulation = False
        self.zoom_level = 2
        self.render_filter = 'None'
        self.rom_fn = ''
        self.debug = False

        self.set_vdp_buffers()

        timer = QTimer(self)
        timer.timeout.connect(self.frame)
        timer.start(16.667)
        self.timer = timer
        self.turbo = False

        self.last_fps_time = QTime.currentTime()
        from collections import deque
        self.frame_times = deque([20], 1000)

        self.debug_label = QLabel()
        self.debug_label.font = QFont("Menlo", 16)
        self.debug_label.font.setStyleHint(QFont.TypeWriter)
        self.debug_label.setFont(self.debug_label.font)

        self.palette_debug = PaletteDebug()

        self.label = QLabel("<b style='color: #eee'>Welcome to <span style='color: #9b4'>Kiwi</span>!</b>")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: #222; color: #ddd; font-family: Verdana")
        self.label.show()

        self.qba = QByteArray()
        self.frame()
        self.setWindowTitle("Kiwi")

        layout = QGridLayout()
        layout.setRowMinimumHeight(0, 480)
        layout.setColumnMinimumWidth(1, 630)
        layout.addWidget(self.debug_label, 0, 0)
        layout.addWidget(self.palette_debug, 1, 0)
        layout.addWidget(self.label, 0, 1, 1, 2)
        layout.setContentsMargins(0, 0, 0, 0)
        self.debug_label.hide()
        self.palette_debug.hide()
        self.setLayout(layout)
        self.layout = layout
        self.create_menus()


    def create_menus(self):
        '''
        Create the menu bar.
        '''
        self.menubar = QMenuBar()
        file_menu = self.menubar.addMenu('&File')
        options_menu = self.menubar.addMenu('&Options')
        help_menu = self.menubar.addMenu('&Help')
        zoom_menu = options_menu.addMenu('Video zoom')
        render_menu = options_menu.addMenu('Rendering filter')
        file_menu.addAction('Open ROM', self, SLOT('open_file()'), QKeySequence.Open)
        file_menu.addSeparator()
        file_menu.addAction('Pause emulation', self, SLOT('toggle_pause()'), QKeySequence('Ctrl+P')).setCheckable(True)
        file_menu.addAction('Reset emulation', self, SLOT('reset_emulation()'), QKeySequence('Ctrl+R'))
        file_menu.addSeparator()
        file_menu.addAction('Quit', self, SLOT('quit()'), QKeySequence.Quit)

        zoom_group = QActionGroup(self)
        zoom_group.triggered.connect(self.set_zoom_level)
        for zoom_level in ('1x', '2x', '3x', '4x'):
            action = QAction(zoom_level, zoom_group)
            action.setCheckable(True)
            zoom_menu.addAction(action)
            if zoom_level == '2x':
                action.setChecked(True)

        render_group = QActionGroup(self)
        render_group.triggered.connect(self.set_render_filter)
        for i, render_filter in enumerate(render_filters):
            action = QAction(render_filter, render_group)
            if i < 9:
                action.setShortcut(QKeySequence('Ctrl+{0}'.format(i+1)))
            action.setCheckable(True)
            render_menu.addAction(action)
            if render_filter == 'None':
                action.setChecked(True)

        options_menu.addAction('Show debug information', self, SLOT('toggle_debug()'), QKeySequence('Ctrl+D')).setCheckable(True)
        help_menu.addAction('Controllers', self, SLOT('show_controllers()'), QKeySequence('Ctrl+I'))

    @Slot()
    def quit(self):
        app.quit()

    @Slot()
    def show_controllers(self):
        self.controllers_window = Controllers()
        self.controllers_window.show()


    @Slot()
    def toggle_debug(self):
        self.debug = not self.debug
        self.debug_label.setVisible(self.debug)
        self.palette_debug.setVisible(self.debug)
        self.layout.setRowMinimumHeight(1, 100 if self.debug else 0)
        if self.debug:
            self.layout.setContentsMargins(10, 10, 10, 10)
        else:
            self.layout.setContentsMargins(0, 0, 0, 0)

        self.adjustSize()

    @Slot()
    def set_render_filter(self, action):
        render_filter = action.text()
        if render_filter not in render_filters:
            return

        self.render_filter = render_filter


    @Slot()
    def set_zoom_level(self, action):
        try:
            self.zoom_level = {'1x': 1, '2x': 2, '3x': 3, '4x': 4}[action.text()]
            self.layout.setRowMinimumHeight(0, self.zoom_level*240)
            self.layout.setColumnMinimumWidth(1, self.zoom_level*320-10)
            self.set_vdp_buffers()

        except KeyError:
            pass

    def set_vdp_buffers(self):
        '''
        Allocate buffer for upscaled image and set the VDP buffers.
        '''
        self.scaled_buffer = create_string_buffer(320*240*4*self.zoom_level*self.zoom_level)
        md.vdp_set_buffers(screen_buffer, self.scaled_buffer)

    @Slot()
    def open_file(self):
        '''
        Open a ROM.
        '''
        import os
        rom_fn, _ = QFileDialog.getOpenFileName(self, "Open ROM", os.getcwd(), "Sega Genesis ROMs (*.bin *.gen *.zip)")

        if not rom_fn:
            return

        self.rom_fn = rom_fn

        if is_zipfile(rom_fn):
            # if the file is a ZIP, try to open the largest file inside
            zipfile = ZipFile(rom_fn, 'r')
            contents = [(f.file_size, f.filename) for f in zipfile.infolist()]
            contents.sort(reverse=True)
            rom = zipfile.read(contents[0][1])
        else:
            rom = open(rom_fn, 'r').read()
        md.set_rom(c_char_p(rom), len(rom))
        self.reset_emulation()
        self.activateWindow()

    @Slot()
    def reset_emulation(self):
        md.m68k_pulse_reset()

    @Slot()
    def toggle_pause(self):
        self.pause_emulation = not self.pause_emulation

    def keyPressEvent(self, event):
        try:
            key, pad = keymap_r[event.key()]
            md.pad_press_button(pad, buttons.index(key))
        except KeyError:
            if event.key() == Qt.Key_Space:
                if self.pause_emulation:
                    md.m68k_execute(7)
                else:
                    self.turbo = not self.turbo
                    self.timer.setInterval(4 if self.turbo else 16.67)
            else:
                super(Display, self).keyPressEvent(event)
        
    def keyReleaseEvent(self, event):
        try:
            key, pad = keymap_r[event.key()]
            md.pad_release_button(pad, buttons.index(key))
        except KeyError:
            super(Display, self).keyReleaseEvent(event)

    def show_fps(self):
        from itertools import islice
        values = []
        for last_n in (1000, 100, 20):
            start = max(0, len(self.frame_times)-last_n)
            l = len(self.frame_times)-start
            q = islice(self.frame_times, start, None)
            values.append('{:.1f}'.format(1000.0/sum(q)*l))
        return ' '.join(values)

    def frame(self):
        '''
        Do a single frame.

        Perform a Megadrive frame, upscale the screen if necessary.
        Update debug information if debug is on.
        '''
        if not self.pause_emulation and self.rom_fn:
            md.frame()
            self.frames += 1

        if self.debug:
            self.palette_debug.update()

        if self.rom_fn:
            md.scale_filter(c_char_p(self.render_filter), self.zoom_level)
            blit_screen(self.label, self.scaled_buffer.raw, self.zoom_level)
            self.adjustSize()

        self.frame_times.append(self.last_fps_time.msecsTo(QTime.currentTime()))
        self.last_fps_time = QTime.currentTime()        

        if self.debug:
            vdp_status = create_string_buffer(1024)
            md.vdp_debug_status(vdp_status)
            if self.frames % 2:
                self.debug_label.setText('Frame: {} (fps: {})\n\n{}\n\n{}'.format(self.frames, self.show_fps(), vdp_status.value, m68k_status()))


app = QApplication(sys.argv)
display = Display()
display.show()
display.raise_()
app.exec_()
