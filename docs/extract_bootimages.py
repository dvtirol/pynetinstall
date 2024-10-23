#!/usr/bin/python3

import sys, io
import struct
import pefile # https://pypi.org/project/pefile/
from elftools.elf.elffile import ELFFile # https://pypi.org/project/pyelftools

elf_e_machines = {
    0x00: "unspecified",
    0x08: "MIPS",
    0x14: "PPC", # PowerPC
    0x28: "ARM",
    0xb7: "ARM64", # aarch64
    0xbf: "TILE",
}

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} /path/to/netinstall.exe")
    sys.exit(1)
netinstall_exe = sys.argv[1]

pe = pefile.PE(netinstall_exe)
mem = pe.get_memory_mapped_image()
rcdata = next(e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.struct.Id == pefile.RESOURCE_TYPE["RT_RCDATA"])
for entry in rcdata.directory.entries:
    resource = entry.directory.entries[0].data.struct
    resid = entry.id
    off = resource.OffsetToData
    siz = resource.Size
    rawdata = mem[off:off+siz]
    elfsize, elfdata = rawdata[:4], rawdata[4:]
    elfsize, = struct.unpack("<I", elfsize)
    elfdata = elfdata[:elfsize]
    if elfdata[:4] == b'\x7fELF':
        endianness = '<' if elfdata[0x05]==1 else '>'  # LE / BE
        arch, = struct.unpack(endianness + "H", elfdata[0x12:0x14])
        arch = elf_e_machines.get(arch, f"unknown0x{arch:02x}")
        if arch == "MIPS" and endianness == '<': arch = "MMIPS"
        if arch == "PPC":
            # there are three powerpc-bigendian images included. the only way to reliably differentiate them is to look for filenames in what is presumably the initramfs
            e = ELFFile(io.BytesIO(elfdata))
            rodata = e.get_section_by_name(".rodata")  # multiple subsections concatenated; format unknown
            candidates = [string for string in rodata.data().split(b"\0") if b"/lib/firmware/" in string]
            is_e500 = any(b"-e500" in c for c in candidates)
            is_440 = any(b"-440" in c for c in candidates)
            if is_e500: arch = f"PPCe500"
            if is_440: arch = f"PPC440"
        with open(f"netinstall-{resid}-{arch}.elf", "wb") as f:
            f.write(elfdata)
    elif elfdata[:2] == b'MZ':
        with open(f"netinstall-{resid}-x86.pxe", "wb") as f:
            f.write(elfdata)
    else:
        print(f"unexpected magic 0x{elfdata[:4].hex()} ({elfdata[:4]})")


"""
PXEClient
Etherboot
Mikroboot
Mips_boot
MMipsBoot
Powerboot
e500_boot
e500sboot
440__boot
tile_boot
ARM__boot
ARM64__boot
"""
