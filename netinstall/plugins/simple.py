import os
from configparser import ConfigParser


class Plugin:
    def __init__(self, config: ConfigParser):
        self.config = config
        print(self.config)

    def get_files(self, *args, **kwargs):
        """
        Searches for the path of the .npk and .rsc files in the config

        Returns:
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
        return (open(firmw, "rb"), os.path.basename(firmw), os.stat(firmw).st_size), (open(conf, "rb"), os.path.basename(conf), os.stat(conf).st_size)


class MissingArgument(Exception):
    """
    Error raised when Plugin is missing an Configuration Argument
    """
    pass
