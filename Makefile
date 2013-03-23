CC =     cc
WARNINGS = -Wall -pedantic
CFLAGS = $(WARNINGS) -c -Im68k -I. -O2

all: megadrive.so

clean:
	rm megadrive.so *.o m68k/*.o

megadrive.so: m68k/m68kcpu.o m68k/m68kops.o m68k/m68kopac.o m68k/m68kopdm.o m68k/m68kopnz.o m68k/m68kdasm.o megadrive.o vdp.o input.o scale.o z80.o
		$(CC) m68k/m68kcpu.o m68k/m68kops.o m68k/m68kopac.o m68k/m68kopdm.o m68k/m68kopnz.o m68k/m68kdasm.o megadrive.o vdp.o input.o scale.o z80.o -shared -o megadrive.so

%.o: %.c
		$(CC) $(CFLAGS) $^ -std=c99 -o $@

m68k/m68kcpu.o: m68k/m68kops.h m68k/m68k.h m68k/m68kconf.h m68k/m68kcpu.c
		$(CC) $(CFLAGS) m68k/m68kcpu.c -o m68k/m68kcpu.o

m68k/m68kdasm.o: m68k/m68kdasm.c m68k/m68k.h m68k/m68kconf.h
		$(CC) $(CFLAGS) m68k/m68kdasm.c -o m68k/m68kdasm.o

m68k/m68kops.o: m68k/m68kmake m68k/m68kops.h m68k/m68kops.c m68k/m68k.h m68k/m68kconf.h
		$(CC) $(CFLAGS) m68k/m68kops.c -o m68k/m68kops.o

m68k/m68kopac.o: m68k/m68kmake m68k/m68kops.h m68k/m68kopac.c m68k/m68k.h m68k/m68kconf.h
		$(CC) $(CFLAGS) m68k/m68kopac.c -o m68k/m68kopac.o

m68k/m68kopdm.o: m68k/m68kmake m68k/m68kops.h m68k/m68kopdm.c m68k/m68k.h m68k/m68kconf.h
		$(CC) $(CFLAGS) m68k/m68kopdm.c -o m68k/m68kopdm.o

m68k/m68kopnz.o: m68k/m68kmake m68k/m68kops.h m68k/m68kopnz.c m68k/m68k.h m68k/m68kconf.h
		$(CC) $(CFLAGS) m68k/m68kopnz.c -o m68k/m68kopnz.o

m68k/m68kops.h: m68k/m68kmake
		m68k/m68kmake m68k m68k/m68k_in.c

m68k/m68kmake: m68k/m68kmake.c m68k/m68k_in.c
		$(CC) $(WARNINGS) m68k/m68kmake.c -o m68k/m68kmake

