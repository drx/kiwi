from ctypes import *

md = CDLL('megadrive.so')

class VDP(object):
    def init(self):
        md.vdp_set_status(0x3400)
        self.screen = create_string_buffer(320*224*3)
        md.vdp_set_screen(self.screen)
        print 'init vdp'
