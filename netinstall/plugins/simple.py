import os
from io import BufferedReader
from configparser import ConfigParser

from netinstall.device import DeviceInfo


class Plugin:
    """
    This is the setup of the Default Plugin

    The Plugin takes at least one argument to save the config to (`config`)
    It includes the Configuration of the programm loaded from the file (config.ini)
    When running the programm and the server is connected to the device, 
    there will be a new section called `device` where information is saved.
    (MAC Address, model, architecture, min OS)
    """
    def __init__(self, config: ConfigParser):
        self.config = config

    def get_files(self, info: DeviceInfo) -> tuple[BufferedReader or str, BufferedReader or str]:
        """
        Searches for the path of the .npk and .rsc files in the config

        Returns:
         - BufferedReader or str, BufferedReader or str: 
           Tuple including the path to the .npk and the .rsc file
           (ROUTEROS.npk, CONFIG.rsc)
        """
        firmw = self.config["pynetinstall"]["firmware"]
        conf = self.config["pynetinstall"]["config"]
        if firmw:
            if not os.path.exists(firmw):
                raise FileExistsError(f"File '{firmw}' doesn't exist")
        else:
            raise MissingArgument("RouterOS not defined")
        if conf:
            if not os.path.exists(conf):
                raise FileExistsError(f"File '{conf}' doesn't exist")
        else:
            raise MissingArgument("Configuration not defined")
        return open(firmw, "rb"), open(conf, "rb")


class MissingArgument(Exception):
    """
    Error raised when Plugin is missing an Configuration Argument
    """
    pass
