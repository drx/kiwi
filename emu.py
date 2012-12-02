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
    for line in vdp.lines():
        vdp.set_hblank()
        md.m68k_execute(CPL_M68K - 404)
        vdp.clear_hblank()

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

import sys
from PySide.QtCore import *
from PySide.QtGui import *

class Display(QLCDNumber):
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)

        self.setSegmentStyle(QLCDNumber.Filled)

        self.frames = 0

        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(16.667)

        self.showTime()
        self.setWindowTitle("emu pie")
        self.resize(320*2, 224*2)


    def showTime(self):
        frame()
        self.frames += 1
        time = QTime.currentTime()
        self.display(str(self.frames))

app = QApplication(sys.argv)
display = Display()
display.show()
app.exec_()
