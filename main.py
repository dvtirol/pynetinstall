from pynetinstall.device import DeviceInfo
from pynetinstall.network import UDPConnection
from pynetinstall import Flasher

import time
import logging
from multiprocessing import Process

logging.basicConfig(level=logging.DEBUG)

proc = None
connection = UDPConnection()
last_info = DeviceInfo(None, None, None, None)
while True:
    info = UDPConnection().get_device_info()
    try:
        if info.mac != last_info.mac and proc is None:
            flash = Flasher()
            flash.conn.dev_mac = info.mac
            proc = Process(target=flash.run, args=(info,))
            proc.start()
            proc.join()
            if proc.exitcode == 0:
                last_info = info
                time.sleep(10)
            if not proc.is_alive():
                proc = None
        else:
            logging.debug("The new device is already configured")
    except KeyboardInterrupt:
        logging.info("The KeyboardInterrupt stopped the Flash")
