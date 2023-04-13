import sys
import argparse

from pynetinstall.flash import FlashInterface, FatalError, AbortFlashing

parser = argparse.ArgumentParser(__package__)
parser.add_argument("-c", "--config", default="/etc/pynetinstall.ini", help="set location of configuration file")
parser.add_argument("-i", "--interface", default="eth0", help="ethernet interface to listen on")
parser.add_argument("-1", "--oneshot", action="store_true", help="exit after flashing once")
args = parser.parse_args()

try:
    fl_dev = FlashInterface(args.interface, args.config)

    if args.oneshot:
        fl_dev.flash_once()
    else:
        fl_dev.flash_until_stopped()
except FatalError as e:
    parser.error(e)
except AbortFlashing as e:
    sys.exit(1)
except KeyboardInterrupt as e:
    sys.exit(130)
