'''
Debug information helpers.
'''

def m68k_status():
    '''
    Shows the status of the M68K CPU.
    '''
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

    lines = []
    for i in range(4):
        disasm = create_string_buffer(1024)
        old_pc = pc
        pc += md.m68k_disassemble(disasm, pc, 1)
        lines.append('{:06x}: {}'.format(old_pc, disasm.value.lower()))
    status = '> {}\n{}'.format('\n'.join(lines), status)

    return status

class PaletteDebug(QWidget):
    '''
    A widget that shows the current palette.
    '''
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
