import sys
from pynetinstall import FlashInterface

interface = "eth0"
if len(sys.argv) > 1:
    if sys.argv[1] == "-h":
        print(f"Usage: {sys.argv[0]} [IFACE]")
        sys.exit(0)
    interface = sys.argv[1]

fl_dev = FlashInterface(interface, "config.ini")
fl_dev.flash_until_stopped()
