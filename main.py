import logging.config

# Setup Logging
logging.config.fileConfig("pynetinstall/logging.ini")

from pynetinstall import FlashDevice

fl_dev = FlashDevice()
fl_dev.flash_until_stopped()
