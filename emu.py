import sys
from ctypes import *

md = CDLL('megadrive.so')

try:
    rom_fn = sys.argv[1]
except IndexError:
    rom_fn = 'sonic.bin'

rom = open(rom_fn, 'r').read()
md.set_rom(c_char_p(rom), len(rom))
md.m68k_pulse_reset()

md.vdp_set_status(0x3400)
screen_buffer = create_string_buffer(320*224*3)
md.vdp_set_screen(screen_buffer)

def m68k_status():
    registers = ['d0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7',
            'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
            'pc', 'sr', 'sp', 'usp']

    status = ''
    pc = 0
    for reg_i, register in enumerate(registers):
        if reg_i%4 == 0:
            status += '\n'
        value = md.m68k_get_reg(0, reg_i)
        status += '{0}={1:08x} '.format(register, value&0xffffffff)
        if register == 'pc':
            pc = value

    disasm = create_string_buffer(1024)
    md.m68k_disassemble(disasm, pc, 1)
    status = '{}\n{}'.format(disasm.value.lower(), status)

    return status

import sys
from PySide.QtCore import *
from PySide.QtGui import *

class PaletteDebug(QWidget):
    def __init__(self):
        super(PaletteDebug, self).__init__()
        self.show()
        
    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        color = QColor(0, 0, 0, 0)
        qp.setPen(color)

        for y in range(4):
            for x in range(16):
                color = md.vdp_get_cram(y*16+x)
                red, green, blue = color >> 8, color >> 4, color
                red, green, blue = (blue&15)*16, (green&15)*16, (red&15)*16
                qp.setBrush(QColor(red, green, blue))
                qp.drawRect(x*16, y*16, 16, 16)

        qp.end()

buttons = ['up', 'down', 'left', 'right', 'b', 'c', 'a', 'start']
keymap = {
        Qt.Key_Left: 'left',
        Qt.Key_Right: 'right',
        Qt.Key_Up: 'up',
        Qt.Key_Down: 'down',
        Qt.Key_Z: 'a',
        Qt.Key_X: 'b',
        Qt.Key_C: 'c',
        Qt.Key_Q: 'start',
        }

def blit_screen(label):
    ppm = 'P6 320 224 255 '+screen_buffer.raw

    qba = QByteArray()
    qba.setRawData(ppm, len(ppm))

    pixmap = QPixmap()
    pixmap.loadFromData(qba)
    label.setPixmap(pixmap)

    del qba

class Display(QWidget):
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)

        self.frames = 0

        timer = QTimer(self)
        timer.timeout.connect(self.frame)
        timer.start(16.667)
        self.last_fps_time = QTime.currentTime()
        from collections import deque
        self.frame_times = deque([100], 100)

        self.debug = QLabel()
        self.debug.font = QFont("Menlo", 16)
        self.debug.setFont(self.debug.font)

        self.palette_debug = PaletteDebug()

        self.label = QLabel("")
        self.label.show()

        self.qba = QByteArray()
        self.frame()
        self.setWindowTitle("emu pie")
        self.debug.resize(320, 224)

        layout = QGridLayout()
        layout.addWidget(self.debug, 0, 0)
        layout.addWidget(self.palette_debug, 1, 0)
        layout.addWidget(self.label, 0, 1, 1, 2)
        layout.setRowMinimumHeight(0, 320)
        layout.setRowMinimumHeight(1, 100)
        layout.setColumnMinimumWidth(1, 224)
        self.setLayout(layout)

    def keyPressEvent(self, event):
        try:
            md.pad_press_button(0, buttons.index(keymap[event.key()]))
        except KeyError:
            super(Display, self).keyPressEvent(self, event)
        
    def keyReleaseEvent(self, event):
        try:
            md.pad_release_button(0, buttons.index(keymap[event.key()]))
        except KeyError:
            super(Display, self).keyReleaseEvent(self, event)

    def frame(self):
        md.frame()
        self.frames += 1
        self.palette_debug.update()

        blit_screen(self.label)

        vdp_status = create_string_buffer(1024)
        md.vdp_debug_status(vdp_status)
        self.debug.setText('Frame: {} (fps: {:.2f})\n\n{}\n\n{}'.format(self.frames, 1000.0/sum(self.frame_times)*len(self.frame_times), vdp_status.value, m68k_status()))

        self.frame_times.append(self.last_fps_time.msecsTo(QTime.currentTime()))
        self.last_fps_time = QTime.currentTime()        


app = QApplication(sys.argv)
display = Display()
display.show()
app.exec_()
