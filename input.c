#include <stdio.h>
#include "input.h"

/*
 * Sega Megadrive joypad support
 */

enum pad_button
{
    PAD_UP,
    PAD_DOWN,
    PAD_LEFT,
    PAD_RIGHT,
    PAD_B,
    PAD_C,
    PAD_A,
    PAD_S
};

unsigned short button_state[3];
unsigned short pad_state[3];
unsigned char io_reg[16] = {0xa0, 0x7f, 0x7f, 0x7f, 0, 0, 0, 0xff, 0, 0, 0xff, 0, 0, 0xff, 0, 0}; /* initial state */

void pad_press_button(int pad, int button)
{
    button_state[pad] |= (1<<button);
}

void pad_release_button(int pad, int button)
{
    button_state[pad] &= ~(1<<button);
}

void pad_write(int pad, int value)
{
    unsigned char mask = io_reg[pad+4];

    pad_state[pad] &= ~mask;
    pad_state[pad] |= value & mask;
}

unsigned char pad_read(int pad)
{
    unsigned char value;

    value = pad_state[pad] & 0x40;
    value |= 0x3f;

    if (value & 0x40)
    {
        value &= ~(button_state[pad] & 0x3f);
    }
    else
    {
        value &= ~(0xc | (button_state[pad] & 3) | ((button_state[pad] >> 2) & 0x30));
    }
    return value;
}

void io_write_memory(unsigned int address, unsigned int value)
{
    address >>= 1;

    if (address >= 0x1 && address < 0x4)
    {
        /* port data */
        io_reg[address] = value;
        pad_write(address-1, value);
        return;
    }
    else if (address >= 0x4 && address < 0x7)
    {
        /* port ctrl */
        if (io_reg[address] != value)
        {
            io_reg[address] = value;
            pad_write(address-4, io_reg[address-3]);
        }
        return;
    }

    printf("io_write_memory(%x, %x)\n", address, value);
}

unsigned int io_read_memory(unsigned int address)
{
    address >>= 1;

    if (address >= 0x1 && address < 0x4)
    {
        unsigned char mask = 0x80 | io_reg[address+3];
        unsigned char value;
        value = io_reg[address] & mask;
        value |= pad_read(address-1) & ~mask;
        return value;
    }
    else
    {
        return io_reg[address];
    }
}
