#!/usr/bin/env python3 --
#
# STELF: A tool to convert M68K ELF files to Atari ST
# GreaseMonkey, 2015, 2016, 2020 - Public Domain
#
# IMPORTANT: Use --emit-relocs on the linker, not -r!

import struct
import sys
from typing import Dict
from typing import List
from typing import Tuple

#
# LOAD FILE
#

fp = open(sys.argv[1], "rb")

# ELF Header
e_ident = fp.read(16)
if e_ident != b"\x7FELF\x01\x02\x01\x00" + b"\x00"*8:
	print(repr(e_ident))
	raise Exception("not a valid SVR4/Linux 32-bit Big-Endian ELF file")

e_type, e_machine, e_version, = struct.unpack(">HHI", fp.read(8))
#print e_type, e_machine, e_version
if e_version != 1: raise Exception("unsupported ELF version")
if e_machine != 4: raise Exception("not an m68k ELF binary")

e_entry, e_phoff, e_shoff, e_flags, = struct.unpack(">IIII", fp.read(16))
e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx, = struct.unpack(">HHHHHH", fp.read(12))
#print "%08X %08X %08X %08X" % (e_entry, e_phoff, e_shoff, e_flags,)
#print "%04X %04X %04X %04X %04X %04X" % (e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx,)
if e_ehsize not in [0x34] or e_phentsize not in [0x20, 0] or e_shentsize not in [0x28]: raise Exception("invalid sizes")

# Section Header
fp.seek(e_shoff)

shlist = []

for i in range(e_shnum):
	sh = {}
	sh["name"], sh["type"], sh["flags"], sh["addr"], = struct.unpack(">IIII", fp.read(16))
	sh["offset"], sh["size"], sh["link"], sh["info"], = struct.unpack(">IIII", fp.read(16))
	sh["addralign"], sh["entsize"], = struct.unpack(">II", fp.read(8))
	shlist.append(sh)

# String table
fp.seek(shlist[e_shstrndx]["offset"])
shstrtab = fp.read(shlist[e_shstrndx]["size"])

# Handle sections
progbits = {}
progbits_offs = {}
progbits_addr = {}
nobits = {}
relas: Dict[bytes, List[Tuple[int, int, int, int]]] = {}
symtab = None
strtab = None
for i in range(e_shnum):
	sh = shlist[i]
	shname = shstrtab[sh["name"]:].partition(b"\x00")[0]
	print("%i: %i %08X %08X %s" % (i, sh["type"],
		sh["offset"], sh["size"],
		repr(shname), ))
	
	if sh["type"] == 1: # SHT_PROGBITS
		print("- Loading progbits")
		fp.seek(sh["offset"])
		assert sh["type"] not in progbits
		progbits[shname] = fp.read(sh["size"])
		progbits_offs[shname] = sh["offset"]
		progbits_addr[shname] = sh["addr"]

	elif sh["type"] == 2: # SHT_SYMTAB
		print("- symtab")
		fp.seek(sh["offset"])
		assert symtab == None
		assert sh["size"] % 16 == 0
		symtab = []
		for i in range(sh["size"]//16):
			symtab.append(struct.unpack(">IIIBBH", fp.read(16)))

		print(symtab)

	elif sh["type"] == 4: # SHT_RELA
		print("- Loading rela")
		fp.seek(sh["offset"])
		assert sh["type"] not in relas
		assert sh["size"] % 12 == 0
		assert shname.startswith(b".rela")
		shname = shname[5:]
		relas[shname] = []
		for i in range(sh["size"]//12):
			ra, rb, rc, = struct.unpack(">III", fp.read(12))
			relas[shname].append((ra, rb&0xFF, rb>>8, rc))

		print(relas[shname])

	elif sh["type"] == 8: # SHT_NOBITS
		print("- NOBITS")
		nobits[shname] = sh

print("")

if b".text" not in relas: relas[b".text"] = []
if b".data" not in relas: relas[b".data"] = []

# Align
while len(progbits[b".text"]) % 4 != 0: progbits[b".text"] += b"\x00"
while len(progbits[b".data"]) % 4 != 0: progbits[b".data"] += b"\x00"

# Do relocations
file_offs = 0
reloc_addrs = []
for name in [b".text", b".data"]:
	base_offs = progbits_offs[name]
	base_addr = progbits_addr[name]

	print("Relocating %s from %08X -> %08X:" % (repr(name), base_addr, file_offs))

	for (addr, typ, symidx, offs, ) in relas[name]:
		symoffs = symtab[symidx][1]

		if typ == 0x01: # R_68K_32
			addr -= base_addr
			#print("R_68K_32 %08X %08X+%08X" % (addr, symoffs, offs))
			data, = struct.unpack(">I", progbits[name][addr:][:4])
			newloc = (symoffs+offs-base_addr+file_offs) & 0xFFFFFFFF
			print("R_68K_32 %08X %08X+%08X (%08X) -> %08X" % (addr, symoffs, offs, data, newloc))
			reloc_addrs.append(addr+file_offs)
			assert data == 0 or data == (symoffs + offs) & 0xFFFFFFFF
			progbits[name] = (progbits[name][:addr]
				+ struct.pack(">I", newloc)
				+ progbits[name][addr+4:])

		elif typ == 0x02: # R_68K_16
			print("R_68K_16 %08X %08X+%08X" % (addr, symoffs, offs))
			raise Exception("16-bit relocations not supported")

		elif typ == 0x05: # R_68K_PC16
			# Everything stays nicely aligned, nothing to do here
			data, = struct.unpack(">H", progbits[name][addr - base_addr:][:2])
			print("R_68K_PC16 %08X %08X+%08X (%08X)" % (addr, symoffs-addr, offs, data))
			"""
			newloc = symoffs+offs-base_addr-(addr-base_addr)+file_offs
			assert data == 0 or data == newloc
			progbits[name] = (progbits[name][:addr]
				+ struct.pack(">H", newloc)
				+ progbits[name][addr+2:])
			"""

		else:
			print(typ, symidx, addr, offs)
			assert False

	file_offs += len(progbits[name])
	print("")

print("")

# Get data
print(".text: %08X, %08X bytes, %i relocations" % (progbits_offs[b".text"], len(progbits[b".text"]), len(relas[b".text"]), ))
print(".data: %08X, %08X bytes, %i relocations" % (progbits_offs[b".data"], len(progbits[b".data"]), len(relas[b".data"]), ))
print(".bss : %08X, %08X bytes" % (nobits[b".bss"]["offset"], nobits[b".bss"]["size"], ))
print("")

# Generate reloc table

print("Generating relocations")
reloc_addrs.sort()
print(reloc_addrs)

# CLOSE
fp.close()

#
# SAVE FILE
#

print("SAVING!")
fp = open(sys.argv[2], "wb")
fp.write(struct.pack(">HIIIIIIH", 0x601A
	, len(progbits[b".text"])
	, len(progbits[b".data"])
	, nobits[b".bss"]["size"]
	, 0, 0
	, 0b000000
	, 0
	))
fp.write(progbits[b".text"])
fp.write(progbits[b".data"])

# RELOC TABLE
base_reloc = 0
addr = reloc_addrs[0] if len(reloc_addrs) >= 1 else -base_reloc
fp.write(struct.pack(">I", base_reloc + addr))

for v in reloc_addrs[1:]:
	while (v-addr) > 254:
		fp.write(b"\x01")
		addr += 254

	assert (v-addr) % 2 == 0
	assert (v-addr) >= 2
	assert (v-addr) <= 254

	fp.write(bytes([v-addr]))

	addr += (v-addr)
	assert addr == v

fp.write(b"\x00")
fp.close()

