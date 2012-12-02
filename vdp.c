unsigned char VRAM[0x10000];
unsigned short CRAM[0x40];
unsigned short VSRAM[40];
unsigned char regs[0x1f];

int control_code = 0;
int control_address = 0;
int control_pending = 0;

void vdp_data_write(unsigned int value)
{
    if (control_code & 1)  // check if write is set
    {
        if ((control_code & 0xe) == 0)  // VRAM write
        {
            VRAM[control_address++] = (value >> 8) & 0xff;
            VRAM[control_address++] = (value) & 0xff;
        }
        else if ((control_code & 0xe) == 1)  // CRAM write
        {
            CRAM[(control_address & 0x7f) >> 1] = value;
        }
        else if ((control_code & 0xe) == 4)  // VSRAM write
        {
            VSRAM[(control_address & 0x7f) >> 1] = value;
        }
    }

    control_pending = 0;
}

void vdp_set_reg(int reg, unsigned char value)
{
    regs[reg] = value;

    control_code = 0;
}

void vdp_control_write(unsigned int value)
{
    if (!control_pending)
    {
        if ((value & 0xc000) == 0xc000)
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
    }
}

void vdp_write(unsigned int address, unsigned int value)
{
    address &= 0x1f;

    if (address >= 0x00 && address < 0x04)
    {
        vdp_data_write(value);
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
