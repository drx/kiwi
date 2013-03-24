#include <stdio.h>
#include <string.h>
#include "m68k/m68k.h"
#include "z80.h"
#include "VDP.h"
#include "input.h"

/*
 * Megadrive memory map as well as main execution loop.
 */

unsigned char ROM[0x400000];
unsigned char RAM[0x10000];
unsigned char ZRAM[0x2000];

const int MCLOCK_NTSC = 53693175;
const int MCYCLES_PER_LINE = 3420;

int lines_per_frame = 262; /* NTSC: 262, PAL: 313 */

int cycle_counter = 0;

void set_rom(unsigned char *buffer, size_t size)
{
    memcpy(ROM, buffer, size);
}

unsigned int read_memory(unsigned int address)
{
    unsigned int range = (address & 0xff0000) >> 16;

    if (range <= 0x3f)
    {
        /* ROM */
        return ROM[address];
    }
    else if (range == 0xa0)
    {
        /* Z80 space */
        if (address >= 0xa00000 && address < 0xa04000)
        {
            return ZRAM[address & 0x1fff];
        }
        return 0;
    }
    else if (range == 0xa1)
    {
        /* I/O and registers */
        if (address >= 0xa10000 && address < 0xa10020)
        {
            return io_read_memory(address & 0x1f);
        }
        else if (address >= 0xa11100 && address < 0xa11300)
        {
            return z80_ctrl_read(address & 0xffff);
        }
        return 0;
    }
    else if (range >= 0xc0 && range <= 0xdf)
    {
        /* VDP */
        return vdp_read(address);
    }
    else if (range >= 0xe0 && range <= 0xff)
    {
        /* RAM */
        return RAM[address & 0xffff];
        // RAM
    }
    printf("read(%x)\n", address);
    return 0;
}

void write_memory(unsigned int address, unsigned int value)
{
    unsigned int range = (address & 0xff0000) >> 16;

    if (range <= 0x3f)
    {
        /* ROM */
        ROM[address] = value;
        return;
    }
    else if (range == 0xa0)
    {
        /* Z80 space */
        if (address >= 0xa00000 && address < 0xa04000)
        {
            ZRAM[address & 0x1fff] = value;
        }
        return;
    }
    else if (range == 0xa1)
    {
        /* I/O and registers */
        if (address >= 0xa10000 && address < 0xa10020)
        {
            io_write_memory(address & 0x1f, value);
            return;
        }
        else if (address >= 0xa11100 && address < 0xa11300)
        {
            z80_ctrl_write(address & 0xffff, value);
            return;
        }
        return;
    }
    else if (range >= 0xc0 && range <= 0xdf)
    {
        /* VDP */
        return;
    }
    else if (range >= 0xe0 && range <= 0xff)
    {
        /* RAM */
        RAM[address & 0xffff] = value;
        return;
    }
    printf("write(%x, %x)\n", address, value);
    return;
}

unsigned int m68k_read_memory_8(unsigned int address)
{
    return read_memory(address);
}
unsigned int m68k_read_memory_16(unsigned int address)
{

    unsigned int range = (address & 0xff0000) >> 16;

    if (range >= 0xc0 && range <= 0xdf)
    {
        return vdp_read(address);
    }
    else
    {
        unsigned int word = read_memory(address)<<8 | read_memory(address+1);
        return word;
    }
}
unsigned int m68k_read_memory_32(unsigned int address)
{
    unsigned int longword = read_memory(address) << 24 |
                            read_memory(address+1) << 16 |
                            read_memory(address+2) << 8 |
                            read_memory(address+3);
    return longword;
}
void m68k_write_memory_8(unsigned int address, unsigned int value)
{
    write_memory(address, value);

    return;
}
void m68k_write_memory_16(unsigned int address, unsigned int value)
{
    unsigned int range = (address & 0xff0000) >> 16;

    if (range >= 0xc0 && range <= 0xdf)
    {
        vdp_write(address, value);
    }
    else
    {
        write_memory(address, (value>>8)&0xff);
        write_memory(address+1, (value)&0xff);
    }
}
void m68k_write_memory_32(unsigned int address, unsigned int value)
{
    m68k_write_memory_16(address, (value>>16)&0xffff);
    m68k_write_memory_16(address+2, (value)&0xffff);

    return;
}

/*
 * The Megadrive frame, called every 1/60th second 
 * (or 1/50th in PAL mode)
 */
void frame()
{
    extern unsigned char vdp_reg[0x20], *screen;
    extern unsigned int vdp_status;
    extern int screen_width, screen_height;
    int hint_counter = vdp_reg[10];
    int line;

    cycle_counter = 0;

    screen_width = (vdp_reg[12] & 0x01) ? 320 : 256;
    screen_height = (vdp_reg[1] & 0x08) ? 240 : 224;

    vdp_clear_vblank();
    memset(screen, 0, 320*240*3); /* clear the screen before rendering */

    for (line=0; line < screen_height; line++)
    {
        m68k_execute(2560+120);

        if (--hint_counter < 0)
        {
            hint_counter = vdp_reg[10];
            if (vdp_reg[0] & 0x10)
            {
                m68k_set_irq(4); /* HInt */
                //m68k_execute(7000);
            }
        }

        vdp_set_hblank();
        m68k_execute(64+313+259); /* HBlank */
        vdp_clear_hblank();

        m68k_execute(104);

        vdp_render_line(line); /* render line */
    }

    vdp_set_vblank();

    m68k_execute(588);

    vdp_status |= 0x80;

    m68k_execute(200);

    if (vdp_reg[1] & 0x20)
    {
        m68k_set_irq(6); /* HInt */
    }

    m68k_execute(3420-788);
    line++;

    for (;line < lines_per_frame; line++)
    {
        m68k_execute(3420); /**/
    }

}
