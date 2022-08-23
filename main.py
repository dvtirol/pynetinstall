import logging.config

# Setup Logging
logging.config.fileConfig("pynetinstall/logging.ini")

import time
import logging
from multiprocessing import Process

from pynetinstall.log import Logger
from pynetinstall.flash import Flasher
from pynetinstall.device import DeviceInfo
from pynetinstall.network import UDPConnection


logger = Logger()
proc = None
last_mac: bytes = None
already_cnt: int = 0
MAX_ALREADY: int = 5
try:
    connection = UDPConnection(logger=logger)
    last_info = DeviceInfo(None, None, None, None)
    while True:
        info = connection.get_device_info()
        time.sleep(5)
        if info is None:
            continue
        if info.mac != last_mac and proc is None:
            flash = Flasher(logger=logger)
            flash.conn.dev_mac = info.mac
            proc = Process(target=flash.run, args=(info,))
            proc.start()
            proc.join()
            if proc.exitcode == 0:
                last_mac = info.mac
                time.sleep(10)
            if not proc.is_alive():
                proc = None
        else:
            logger.debug("The new device is already configured")
except KeyboardInterrupt:
    logger.info("The KeyboardInterrupt stopped the Flash")
