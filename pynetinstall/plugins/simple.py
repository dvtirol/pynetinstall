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

    get_files(info) -> tuple[str]
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
        self.default_config = config.get("pynetinstall", "config", fallback=None)
        additional_packages = config.get("pynetinstall", "additional_packages", fallback="")

        if not self.firmware:
            raise KeyError(f"[pynetinstall]firmware= is not defined in the configuration")
        if not os.path.exists(self.firmware):
            raise ValueError(f"The firmware file {self.firmware!r} does not exist")
        if self.default_config and not os.path.exists(self.default_config):
            raise ValueError(f"The config file {self.default_config!r} does not exist")

        # Enhanced additional_packages parsing with flexible format support
        # Supports both comma-separated and multi-line formats with automatic whitespace trimming
        packages_list = []

        if ',' in additional_packages:
            # Comma-separated format: package1, package2, package3
            comma_split = [pkg.strip() for pkg in additional_packages.split(',')]
            packages_list.extend(comma_split)
        else:
            # Multi-line format (compatible with official documentation)
            packages_list = [line.strip() for line in additional_packages.splitlines()]

        # Filter out empty strings after trimming whitespace
        self.additional_packages = [pkg for pkg in packages_list if pkg]

        # Verify all additional packages exist
        for pkg in self.additional_packages:
            if not os.path.exists(pkg):
                raise ValueError(f"The package {pkg!r} does not exist")

    def get_files(self, info: InterfaceInfo) -> tuple[str]:
        """
        Searches for the path of the .npk and .rsc files in the config

        Arguments
        ---------

        info : InterfaceInfo
            Information about the Device (MAC Address, Model, Architecture, min OS, Licence)

        Returns
        -------

         - Tuple of the path to the .npk files and .rsc config
           If firmware is None, an error is assumed. If config is None, only
           the firmware will be installed.
        """
        return self.firmware, *self.additional_packages, self.default_config
