#include "z80.h"

int bus_ack = 0;
int reset = 0;

void z80_ctrl_write(unsigned int address, unsigned int value)
{
    if (address == 0x1100) // BUSREQ
    {
        if (value)
        {
            bus_ack = 1;
        }
        else
        {
            bus_ack = 0;
        }
    }
    else if (address == 0x1200) // RESET
    {
        if (value)
        {
            reset = 1;
        }
        else
        {
            reset = 0;
        }
    }
}

unsigned int z80_ctrl_read(unsigned int address)
{
    if (address == 0x1100)
    {
        return !(reset && bus_ack);
    }
    return 0;
}
