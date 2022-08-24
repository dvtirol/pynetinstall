import logging
import logging.config

# Setup Logging
logging.addLevelName(15, "STEP")
logging.config.fileConfig("pynetinstall/logging.ini")

from pynetinstall import FlashDevice

fl_dev = FlashDevice()
fl_dev.flash_until_stopped()
