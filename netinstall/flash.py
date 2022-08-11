import importlib

from time import sleep
from configparser import ConfigParser

from netinstall.network import UDPConnection
from netinstall.plugins.simple import Plugin


class Flasher:
    """
    Object to flash configurations on a Mikrotik routerboard

    To run the flash simply use the .run() function.

    The .run() executes following steps:
    1. Offer the Configuration to the routerboard
    2. Formats the routerboard that the new Configuration can be flashed
    3. Sends the .npk file
    4. Sends the .rsc file
    5. Tells the board that the files can now be installed
    6. Restarts the board

    During the installation the Raspberry Pi is connected to the board
    over a UDP-socket (`netinstall.network.UDPConnection`)

    Overview of the States
                    Raspi Side                            Boad Side
    1       The Raspi Offered the flash         The Board Acknoleged the flash
    2        Tells the Board to Format               Formated the Board
    3       

    """

    # The socket connection to the board
    conn: UDPConnection
    # The mac address of the board
    dev_mac: bytes
    # The current state of the flash [Raspi State, Board State]
    pos: tuple
    # The Plugin class
    plugin: Plugin
    # Max amout of Bytes the Server can receive at once
    MAX_BYTES: int = 1024

    def __init__(self) -> None:
        self.conn = UDPConnection()
        self.pos = [0, 0]
        self.plugin = self.load_config()

    def load_config(self, filename: str = "config.ini") -> tuple:
        self.dev_mac, model, arch, min_os = self.conn.get_device_info()
        """ 
        Resolve the Plugin from the Configuration

        Arguments:
            filename (str): The location of the Configuration file (default=config.ini)

        Returns:
            The Plugin defined in the Configuration file including the configuration
        """
        cparser = ConfigParser()
        if not cparser.read(filename):
            raise FileNotFoundError("Configuration not found")
        cparser.sections()
        mod, _, cls = cparser["pynetinstall"]["plugin"].partition(":")
        Plugin = getattr(importlib.import_module(mod, __name__), cls)
        return Plugin(config=cparser)

    def write(self, data: bytes) -> None:
        self.conn.write(data, self.pos)

    def read(self, mac: bool = False) -> tuple:
        print(self.pos)
        return self.conn.read(self.pos, self.dev_mac, mac)

    def run(self) -> None:
        # Offer the flash
        print("Sent the offer to flash")
        self.pos[0] += 1
        while not self.do(b"OFFR\n\n", b"YACK\n"):
            pass
        # Format the board
        print("Formatting the board")
        self.pos[0] += 1
        self.do(b"", b"STRT")
        # Spacer to give the board some time to prepare for the file
        print("Spacer")
        self.pos[0] += 1
        self.do(b"", b"RETR")
        # Send the files
        print("Files")
        self.pos[0] += 1
        self.do_files()
        # Tell the board that the installation is done
        print("Installation Done")
        self.pos[0] += 1
        self.do(b"FILE\n", b"WTRM")
        # Tell the board that it can now reboot and load the files
        print("Reboot")
        self.pos[0] += 1
        self.do(b"TERM\nInstallation successful\n")

    def do(self, data: bytes, response: bytes = None):
        # try:
        print(f"1_ Do: {data}")
        # self.pos[0] += 1
        self.write(data)
        print("2_ Waiting")
        self.wait()

        if response is None:
            print("3_ Response None")
            return True
        else:
            print("3_ Get Response")
            res, self.pos = self.read()
            print(f"4_ Response {res[14:]}\n{response}")
            if response == res[14:]:
                self.pos[1] += 1
                return True
            else:
                return False
        """except Exception as e:
            exc_type, exc_object, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, "-", fname, "on line", exc_tb.tb_lineno)"""

    def do_file(self, file, max_pos: bytes):
        file_pos = 0
        while True:
            data = file.read(self.MAX_BYTES)
            self.write(data)

            file_pos = file_pos + len(data)
            if file_pos >= max_pos:
                # try:
                resp = self.wait()

                # check
                res = self.read()
                print(res)
                return True if b"RETR" == res[20:] else False
                """except Exception as e:
                    exc_type, exc_object, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(e, "-", fname, "on line", exc_tb.tb_lineno)
                    break"""
            else:
                # dieses sleep ist der hauptgrund wieso das file so lange zum
                # flashen braucht. je niedrieger desto schneller
                # kann zu position errors durch timing issues fuehren
                sleep(35 / 10000)

    def do_files(self):
        npk, rsc = self.plugin.get_files()

        # Send the .npk file
        name = npk[1].split("\\")
        if isinstance(name, list):
            name = name[-1]
        else:
            name = npk[1].split("/")
            if isinstance(name, list):
                name = name[-1]
            else:
                name = npk[1]
        self.do(bytes(f"FILE\n{name}\n{str(npk[2])}\n", "utf-8"), b"RETR")
        self.do_file(npk[0], npk[2])

        self.do(b"", b"RETR")

        # Send the .rsc file
        name = rsc[1].split("\\")
        if isinstance(name, list):
            name = name[-1]
        else:
            name = rsc[1].split("/")
            if isinstance(name, list):
                name = name[-1]
            else:
                name = rsc[1]
        self.do(bytes(f"FILE\n{name}\n{str(rsc[2])}\n", "utf-8"), b"RETR")
        self.do_file(rsc[0], rsc[2])

        self.do(b"", b"RETR")

    def wait(self):
        self.pos[1] = self.pos[0]
        self.read()

