/*OUTPUT_ARCH(m68000);*/
/* change these to where things are really pointed */
SEARCH_DIR("/usr/lib/gcc/m68k-none-elf/6.1.0/m68000");
SEARCH_DIR("/usr/m68k-none-elf/lib");

SECTIONS
{
	/*. = 0x00001000-0x1C;*/
	/*. = 0x00008000;*/
	. = 0x00000000;
	_FILE_BEG = .;
	. = . + 0;

	text_beg_real = .;
	text_beg = . + 0x1C;
	.text : {
		*(.boot)
		*(.text) *(.text.*)
		*(.rodata)
		*(.rodata1)
		*(.rodata.str1.1)
	}
	.rela : { *(.rela) }
	.rela.plt : { *(.rela.plt) }
	_RELA_TEXT = .;
	.rela.text : { *(.rela.text) *(.rela.text.*) }
	_RELA_TEXT_END = .;
	.rela.data : { *(.rela.data) }
	.rela.got : { *(.rela.got) }

	/*_GLOBAL_OFFSET_TABLE_ = .;*/
	.got : { *(.got) }
	.got.plt : { *(.got.plt) }
	.plt : { *(.plt) }
	.dynsym : { *(.dynsym) }
	.dynstr : { *(.dynstr) }
	.dynamic : { *(.dynamic) }
	.hash : { *(.hash) }
	text_end = .;
	data_beg = .; .data : { *(.data) } data_end = .;

	bss_beg = .;
	.footer : { *(.footer) }
	bss_beg_real = .;
	.bss : { *(.bss) }
	bss_end = .;
	end = .;
	/DISCARD/ : { *(.comment) }

	_TEXT_LEN = text_end - text_beg;
	_DATA_LEN = data_end - data_beg;
	_BSS_LEN = bss_end - bss_beg;
}

