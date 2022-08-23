from pynetinstall.device import DeviceInfo
from pynetinstall.network import UDPConnection
from pynetinstall import Flasher
from pynetinstall.log import setup_logger

import time
from logging import getLogger, DEBUG, ERROR, INFO
from multiprocessing import Process


setup_logger("pynet-deb", DEBUG, "logs/pynetdebug.log", "%(asctime)s - [%(levelname)s] -> %(message)s", True)
setup_logger("pynet-err", ERROR, "logs/pyneterr.log", "%(asctime)s - [%(levelname)s] (%(module)s.%(funcName)s:%(lineno)s) -> %(message)s", True)
setup_logger("pynet-inf", INFO, "logs/pynetinfo.log", "%(asctime)s - [%(levelname)s] -> %(message)s", True)

deb_logger = getLogger("pynet-deb")
inf_logger = getLogger("pynet-inf")
err_logger = getLogger("pynet-err")


proc = None
try:
    connection = UDPConnection()
    last_info = DeviceInfo(None, None, None, None)
    while True:
        info = connection.get_device_info()
        if info is None:
            continue
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
            deb_logger.debug("The new device is already configured")
except KeyboardInterrupt:
    inf_logger.info("The KeyboardInterrupt stopped the Flash")
