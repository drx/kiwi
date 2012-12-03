#include <stdio.h>
#include "m68k/m68k.h"

unsigned char VRAM[0x10000];
unsigned short CRAM[0x40];
unsigned short VSRAM[40];
unsigned char regs[0x20];

unsigned char *screen;

int control_code = 0;
int control_address = 0;
int control_pending = 0;
unsigned int status = 0;

#define set_pixel(scr, pixel, index) \
    do {\
        scr[(pixel)*3] = (CRAM[index]<<4)&0xe0; \
        scr[(pixel)*3+1] = (CRAM[index])&0xe0; \
        scr[(pixel)*3+2] = (CRAM[index]>>4)&0xe0; \
    } while(0);

void vdp_render_line(int line)
{
    int h_cells = 32, v_cells = 32;

    switch (regs[16] & 3)
    {
        case 0: h_cells = 32; break;
        case 1: h_cells = 64; break;
        case 2: h_cells = 128; break;
    }
    switch ((regs[16]>>4) & 3)
    {
        case 0: v_cells = 32; break;
        case 1: v_cells = 64; break;
        case 2: v_cells = 128; break;
    }

    int hscroll_type = regs[11]&3;
    unsigned char *hscroll_table = &VRAM[regs[13]<<10];
    unsigned int hscroll_mask;
    switch (hscroll_type)
    {
        case 0x00: hscroll_mask = 0x0000; break;
        case 0x01: hscroll_mask = 0x0007; break;
        case 0x02: hscroll_mask = 0xfff8; break;
        case 0x03: hscroll_mask = 0xffff; break;
    }

    for (int scroll_i = 0; scroll_i<2; scroll_i++)
    {
        unsigned char *scroll;
        if (scroll_i == 0)
            scroll = &VRAM[regs[4]<<13];
        else
            scroll = &VRAM[regs[2]<<10];

        short hscroll = (hscroll_table[((line & hscroll_mask))*4+(scroll_i^1)*2]<<8)
                                | hscroll_table[((line & hscroll_mask))*4+(scroll_i^1)*2+1];
        for (int column = 0; column < 320; column++)
        {
            int cell_line = line >> 3;
            int e_column = (column-hscroll)&(h_cells*8-1);
            int cell_column = e_column >> 3;
            int cell = (scroll[(cell_line*h_cells+cell_column)*2]<<8)
                        | scroll[(cell_line*h_cells+cell_column)*2+1];
            unsigned char *pattern = &VRAM[0x20*(cell&0x7ff)];

            int pattern_index = 0;
            if (cell & 0x1000)  // v flip
                pattern_index = (7-(line&7))*4;
            else
                pattern_index = (line&7)*4; 

            if (cell & 0x800)  // h flip
                pattern_index += (7-(e_column&7))/2;
            else
                pattern_index += (e_column&7)/2;

            unsigned char color_index = pattern[pattern_index];
            if ((e_column&1)^(cell>>11)) color_index &= 0xf;
            else color_index >>= 4;

            if (color_index)
            {
                color_index += (cell & 0x6000)>>9;
                set_pixel(screen, line*512+column, color_index);
            }
        }
    }
}

void vdp_render_all()
{
    for (int i=0; i<(512*512); i++)
    {
        set_pixel(screen, i, regs[7]&0x3f);
    }

    for (int line=0; line<224; line++)
    {
        vdp_render_line(line);
    }
}

void vdp_set_screen(unsigned char* buf)
{
    screen = buf;
}

void vdp_debug_status(char *s)
{
    int i = 0;
    s[0] = 0;
    s += sprintf(s, "VDP regs: ");
    s += sprintf(s, "%04x ", status);
    for (i = 0; i < 0x20; i++)
    {
        s += sprintf(s, "%02x ", regs[i]);
    }
}

enum ram_type {
    T_VRAM,
    T_CRAM,
    T_VSRAM
};


void vdp_data_write(unsigned int value, enum ram_type type, int dma)
{
    if (type == T_VRAM)  // VRAM write
    {
        VRAM[control_address] = (value >> 8) & 0xff;
        VRAM[control_address+1] = (value) & 0xff;
    }
    else if (type == T_CRAM)  // CRAM write
    {
        CRAM[(control_address & 0x7f) >> 1] = value;
    }
    else if (type == T_VSRAM)  // VSRAM write
    {
        VSRAM[(control_address & 0x7f) >> 1] = value;
    }
}

void vdp_data_port_write(unsigned int value)
{
    if (control_code & 1)  // check if write is set
    {
        enum ram_type type;
        if ((control_code & 0xe) == 0)  // VRAM write
        {
            type = T_VRAM;
        }
        else if ((control_code & 0xe) == 1)  // CRAM write
        {
            type = T_CRAM;
        }
        else if ((control_code & 0xe) == 4)  // VSRAM write
        {
            type = T_VSRAM;
        }
        vdp_data_write(value, type, 0);
    }
    control_address += 2;
    control_pending = 0;
}

void vdp_set_reg(int reg, unsigned char value)
{
    regs[reg] = value;

    control_code = 0;
}

unsigned int vdp_get_reg(int reg)
{
    return regs[reg];
}

int dma_length;
unsigned int dma_source;

void vdp_control_write(unsigned int value)
{
    if (!control_pending)
    {
        if ((value & 0xc000) == 0x8000)
        {
            int reg = (value >> 8)&0x1f;
            unsigned char reg_value = value & 0xff;

            vdp_set_reg(reg, reg_value);
        }
        else
        {
            control_code = (control_code & 0x3c) | (value >> 14);
            control_address = (control_address & 0xc000) | (value & 0x3fff);
            control_pending = 1;
        }
    }
    else
    {
        control_code = (control_code & 0x3) | ((value >> 2) & 0x3c);
        control_address = (control_address & 0x3fff) | ((value & 3) << 14); 
        control_pending = 0;

        if ((control_code & 0x20) && (regs[1] & 0x10) && (regs[23] & 0x80) == 0)
        {
            // DMA
            dma_length = regs[19] | (regs[20] << 8);
            dma_source = (regs[21]<<1) | (regs[22]<<9) | (regs[23]<<17);

            unsigned int word;
            enum ram_type type;
            if ((control_code & 0x7) == 1)
            {
                type = T_VRAM;
            }
            else if ((control_code & 0x7) == 3)
            {
                type = T_CRAM;
            }
            else if ((control_code & 0x7) == 5)
            {
                type = T_VSRAM;
            }

            while (dma_length--)
            {
                word = m68k_read_memory_16(dma_source);
                dma_source += 2;
                vdp_data_write(word, type, 1);
                control_address += regs[15];
            }
        }
    }
}

void vdp_write(unsigned int address, unsigned int value)
{
    address &= 0x1f;

    if (address >= 0x00 && address < 0x04)
    {
        vdp_data_port_write(value);
    }
    else if (address >= 0x04 && address < 0x08)
    {
        vdp_control_write(value);
    }
    else
    {
        printf("vdp_write(%x, %x)\n", address, value);
    }
}

unsigned int vdp_read(unsigned int address)
{
    address &= 0x1f;

    if (0 && address >= 0x00 && address < 0x04)
    {
        //vdp_data_write(value);
    }
    else if (address >= 0x04 && address < 0x08)
    {
        return status;
    }
    else
    {
        printf("vdp_read(%x)\n", address);
    }
    return 0;
}

void vdp_set_status(unsigned int value)
{
    unsigned int change = status^value;
    status = value;

    if (change & 8)
    {
        m68k_set_irq(6);
    }
    else if (change & 4)
    {
    }
}

unsigned int vdp_get_status()
{
    return status;
}

unsigned short vdp_get_cram(int index)
{
    return CRAM[index & 0x3f];
}
