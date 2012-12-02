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

def m68k_status():
    registers = ['d0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7',
            'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
            'pc', 'sr', 'sp', 'usp']

    status = ''
    pc = 0
    for reg_i, register in enumerate(registers):
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

class Display(QTextEdit):
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)

        self.frames = 0

        timer = QTimer(self)
        timer.timeout.connect(self.frame)
        timer.start(16.667)

        self.font = QFont("Menlo", 16)
        self.setFont(self.font)

        self.frame()
        self.setWindowTitle("emu pie")
        self.resize(320*2, 224*2)


    def frame(self):
        frame()
        self.frames += 1

        if self.frames % 4 == 0:
            vdp_status = create_string_buffer(1024)
            md.vdp_debug_status(vdp_status)
            self.setText('Frame: {}\n\n{}\n\n{}'.format(self.frames, vdp_status.value, m68k_status()))

app = QApplication(sys.argv)
display = Display()
display.show()
app.exec_()
