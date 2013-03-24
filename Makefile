CC =     cc
WARNINGS = -Wall -pedantic -Wno-unused-function
CFLAGS = $(WARNINGS) -c -Im68k -I. -O2

all: megadrive.so

clean:
	rm megadrive.so *.o m68k/*.o hqx/*.o m68k/m68kops.h m68k/m68kmake

megadrive.so: m68k/m68kcpu.o m68k/m68kops.o m68k/m68kopac.o m68k/m68kopdm.o m68k/m68kopnz.o m68k/m68kdasm.o megadrive.o vdp.o input.o scale.o z80.o hqx/init.o hqx/hq2x.o hqx/hq3x.o hqx/hq4x.o
		@echo "Linking megadrive.so"
		@$(CC) m68k/m68kcpu.o m68k/m68kops.o m68k/m68kopac.o m68k/m68kopdm.o m68k/m68kopnz.o m68k/m68kdasm.o megadrive.o vdp.o input.o scale.o z80.o hqx/init.o hqx/hq2x.o hqx/hq3x.o hqx/hq4x.o -shared -o megadrive.so

%.o: %.c
		@echo "Compiling $<"
		@$(CC) $(CFLAGS) $^ -std=c99 -o $@

m68k/m68kcpu.o: m68k/m68kops.h m68k/m68k.h m68k/m68kconf.h m68k/m68kcpu.c
		@echo "Compiling m68k/m68kcpu.c"
		@$(CC) $(CFLAGS) m68k/m68kcpu.c -o m68k/m68kcpu.o

m68k/m68kdasm.o: m68k/m68kdasm.c m68k/m68k.h m68k/m68kconf.h
		@echo "Compiling m68k/m68kdasm.c"
		@$(CC) $(CFLAGS) m68k/m68kdasm.c -o m68k/m68kdasm.o

m68k/m68kops.o: m68k/m68kmake m68k/m68kops.h m68k/m68kops.c m68k/m68k.h m68k/m68kconf.h
		@echo "Compiling m68k/m68kops.c"
		@$(CC) $(CFLAGS) m68k/m68kops.c -o m68k/m68kops.o

m68k/m68kopac.o: m68k/m68kmake m68k/m68kops.h m68k/m68kopac.c m68k/m68k.h m68k/m68kconf.h
		@echo "Compiling m68k/m68kopac.c"
		@$(CC) $(CFLAGS) m68k/m68kopac.c -o m68k/m68kopac.o

m68k/m68kopdm.o: m68k/m68kmake m68k/m68kops.h m68k/m68kopdm.c m68k/m68k.h m68k/m68kconf.h
		@echo "Compiling m68k/m68kopdm.c"
		@$(CC) $(CFLAGS) m68k/m68kopdm.c -o m68k/m68kopdm.o

m68k/m68kopnz.o: m68k/m68kmake m68k/m68kops.h m68k/m68kopnz.c m68k/m68k.h m68k/m68kconf.h
		@echo "Compiling m68k/m68kopnz.c"
		@$(CC) $(CFLAGS) m68k/m68kopnz.c -o m68k/m68kopnz.o

m68k/m68kops.h: m68k/m68kmake
		@echo "Generating m68k/m68kops.h"
		@m68k/m68kmake m68k m68k/m68k_in.c >/dev/null

m68k/m68kmake: m68k/m68kmake.c m68k/m68k_in.c
		@echo "Compiling m68k/m68kmake"
		@$(CC) $(WARNINGS) m68k/m68kmake.c -o m68k/m68kmake

