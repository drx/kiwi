from ctypes import *
from vdp import VDP

CLOCK_NTSC = 53693175
CPL_M68K = int(CLOCK_NTSC / 7.0 / 60.0 / 262.0)

md = CDLL('megadrive.so')
vdp = VDP()

rom = open('sonic.bin', 'r').read()
md.set_rom(c_char_p(rom), len(rom))
md.m68k_pulse_reset()

vdp.init()

def frame():
    vdp.status &= 0xfff7
    hint_counter = vdp.get_hint_counter()

    for line in vdp.lines():
        vdp.set_hblank()
        md.m68k_execute(CPL_M68K - 404)
        vdp.clear_hblank()

        hint_counter -= 1
        if hint_counter < 0:
            hint_counter = vdp.get_hint_counter()
            md.m68k_set_irq(4)

        #if visible: render_line

        md.m68k_execute(CPL_M68K)

    vdp.set_vblank()
    md.m68k_execute(CPL_M68K - 360)
    vdp.clear_vblank()

    for line in vdp.invisible_lines():
        vdp.set_hblank()
        md.m68k_execute(CPL_M68K - 404)
        vdp.clear_hblank()

        md.m68k_execute(CPL_M68K)

    md.vdp_render_all()

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
        status += '{0}={1:08x} '.format(register, value)
        if register == 'pc':
            pc = value

    disasm = create_string_buffer(1024)
    md.m68k_disassemble(disasm, pc, 1)
    status = '{}\n{}'.format(disasm.value, status)

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

class Display(QWidget):
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)

        self.frames = 0

        timer = QTimer(self)
        timer.timeout.connect(self.frame)
        timer.start(16.667)

        self.debug = QLabel()
        self.debug.font = QFont("Menlo", 16)
        self.debug.setFont(self.debug.font)

        self.palette_debug = PaletteDebug()

        #start
        self.label = QLabel("Hello World")
        #screen = md.vdp_get_screen()
        #print screen
        self.label.show()
        #end

        self.frame()
        self.setWindowTitle("emu pie")
        self.resize(320*3, 224*3)
        self.debug.resize(320, 224)

        layout = QGridLayout()
        layout.addWidget(self.debug, 0, 0, 1, 2)
        layout.addWidget(self.palette_debug, 1, 0)
        layout.addWidget(self.label, 1, 1)
        layout.setRowMinimumHeight(1, 512)
        layout.setColumnMinimumWidth(1, 512)
        self.setLayout(layout)

        self.keys = ''

    def keyPressEvent(self, event):
        self.keys += ' {}'.format(event.key())
        print 'lol'


    def frame(self):
        frame()
        self.frames += 1
        self.palette_debug.update()

        ppm = 'P6 512 512 255 '+vdp.screen.raw
        p = QPixmap()
        p.loadFromData(QByteArray(ppm))
        self.label.setPixmap(p)

        if self.frames % 4 == 0:
            vdp_status = create_string_buffer(1024)
            md.vdp_debug_status(vdp_status)
            self.debug.setText('{}\nFrame: {}\n\n{}\n\n{}'.format(self.keys, self.frames, vdp_status.value, m68k_status()))


app = QApplication(sys.argv)
display = Display()
display.show()
app.exec_()
