STELF: ELF to Atari ST executable converter

by GreaseMonkey, 2015, 2016, 2020 - Public Domain

Here's my build file:

	echo "=== C FILES ===" && \
	m68k-elf-gcc -flto -O3 -m68000 -msoft-float -fomit-frame-pointer -c -o main.o main.c -nostdlib && \
	echo "=== HEADER ===" && \
	m68k-elf-as -m68000 -o afmt.o afmt.S && \
	echo "=== LINK ===" && \
	m68k-elf-ld -flto -O3 --emit-relocs -T ST.ld -o output.elf afmt.o main.o -lgcc -lc && \
	echo "=== CONVERT ===" && \
	python3 path/to/stelf.py output.elf output.prg && \
	true

afmt.S in my case is just a simple booter which goes into supervisor mode then runs `_start`.

ST.ld is a linker script that covers `.text`, `.data`, `.bss`, and `.rela.text` as well as some other things but those are the important things. It also ensures that the booter is called first.

I may modify this to not require the linker script.

