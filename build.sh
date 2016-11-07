#!/bin/sh

# change this to suit
GCCPREFIX=m68k-none-elf-

echo "=== C FILES ===" && \
${GCCPREFIX}gcc -g -O3 -flto -funroll-loops -m68000 -msoft-float -fomit-frame-pointer -c -o obj/main.o src/main.c -nostdlib && \
echo "=== ASM FILES ===" && \
${GCCPREFIX}as -g -m68000 -o obj/afmt.o src/afmt.S && \
echo "=== LINK ===" && \
${GCCPREFIX}gcc -nostdlib -g -O3 -flto -funroll-loops -m68000 -Wl,--emit-relocs,-T,ST.ld -o output.linux-elf obj/main.o obj/afmt.o -lgcc -lc && \
echo "=== CONVERT ===" && \
python stelf.py output.linux-elf demo.prg && \
true

