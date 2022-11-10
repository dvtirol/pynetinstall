import os

from io import BufferedReader
from configparser import ConfigParser

from pynetinstall.interface import InterfaceInfo


class Plugin:
    """
    This is the setup of the Default Plugin

    The Plugin takes at least one argument to save the config to (`config`)
    It includes the Configuration of the programm loaded from the file (config.ini)

    Attributes
    ----------

    config : ConfigParser
        The Configuration loaded from `config.ini`

    Methods
    -------

    get_files(info) -> tuple[BufferedReader, BufferedReader]
        Get a Reader object of the npk and the rsc file

    Raises
    ------

    KeyError
        A File is not defined in the configuration
    ValueError
        A File does not exist
    """
    def __init__(self, config: ConfigParser):
        self.firmware = config.get("pynetinstall", "firmware", fallback=None)
        self.default_config.get("pynetinstall", "config", fallback=None)

        if not self.firmware:
            raise KeyError("[pynetinstall]firmware is not defined in the configuration")
        if not os.path.exists(self.firmware):
            raise ValueError("The file [pynetinstall]firmware={self.firmware!r} does not exist")
        if self.default_config and not os.path.exists(self.default_config):
            raise ValueError("The file [pynetinstall]config={self.config!r} does not exist")

    def get_files(self, info: InterfaceInfo) -> tuple[BufferedReader, BufferedReader]:
        """
        Searches for the path of the .npk and .rsc files in the config

        Arguments
        ---------

        info : InterfaceInfo
            Information about the Device (MAC Address, Model, Architecture, min OS, Licence)

        Returns
        -------

         - (BufferedReader or str or None, BufferedReader or str or None):
           Tuple of the path or URL to the .npk and the .rsc file
           (ROUTEROS.npk, CONFIG.rsc), or a file handle to them.
           If firmware is None, an error is assumed. If config is None, only
           the firmware will be installed.
        """
        return open(self.firmware, "rb"), open(self.default_config, "rb")
