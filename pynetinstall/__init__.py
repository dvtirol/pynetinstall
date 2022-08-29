import logging
import logging.config

# Setup Logging
# Add a new Level to log the Steps of the Flash
logging.addLevelName(15, "STEP")
logging.config.fileConfig("pynetinstall/logging.ini")


__all__ = ["FlashInterface", "Flasher"]

from .flash import FlashInterface, Flasher