import io
import sys
import time
import importlib

from io import BufferedReader
from urllib import request, parse
from os.path import getsize, basename
from configparser import ConfigParser

from pynetinstall.device import DeviceInfo
from pynetinstall.network import UDPConnection
from pynetinstall.plugins.simple import Plugin


class Flasher:
    """
    Object to flash configurations on a Mikrotik routerboard

    To run the flash simply use the .run() function.

    During the installation the Raspberry Pi is connected to the board
    over a UDP-socket (`netinstall.network.UDPConnection`)

    
    Attributes
    ----------
    conn : UDPConnection
        A Socket Connection to send UDP Packets
    info : DeviceInfo
        Information about the Device
    state : list
        The current state of the flash (default: [0, 0])
    plugin : Plugin
        A Plugin to get the firmware and the configuration file 
        (Must include a .get_files(), has the Configuration as an attribute)
    
    MAX_BYTES : int
        How many bytes the connection can receive at once (default: 1024)

    Methods
    -------
    load_config(config_file="config.ini") -> tuple
        Loads the Plugin as configured in the `config_file`

    write(data) -> None
        Writes `data` over the Connection

    read(mac=False) -> tuple[bytes, list] or tuple[bytes, list, bytes]
        Read `data` from the Connection

    run() -> None
        The Flashing Process

    do(data, response=None) -> None
        Execute one step of the Flashing  Process

    do_file(file, max_pos, file_name) -> None
        Send a `file` over the Connection
    
    do_files() -> None
        Get the files from the `plugin` and execute do_file() for every file
    
    wait() -> None
        Wait for something

    reset() -> None
        Reset the Flasher to be able to start a new flash

    Static Methods
    --------------

    resolve_file_data(data) -> tuple
        Gets information about a file

    update_file_bar(curr_pos, max_pos, name, leng=50) -> None
        Updated a Loading bar to display the progress when flashig a file
    """

    info: DeviceInfo
    state: list = [0, 0]
    MAX_BYTES: int = 1024

    def __init__(self, config_file: str = "config.ini") -> None:
        self.conn = UDPConnection()
        self.plugin = self.load_config(config_file)

    def load_config(self, config_file: str = "config.ini") -> Plugin:
        """
        Load the Plugin as configured in the `config_file`
        Create a ConfigParser and import the Plugin using the `importlib` module

        Arguments
        ---------

        config_file : str
            The Path to the File or the Name of the file (default: "config.ini")

        Returns
        -------

         - The Plugin you have defined in the `config_file`

        Raises
        ------
        FileNotFoundError
            If the `config_file` does not exist or is not found
        """
        
        cparser = ConfigParser()
        if not cparser.read(config_file):
            raise FileNotFoundError("Configuration not found")
        try:
            mod, _, cls = cparser["pynetinstall"]["plugin"].partition(":")
            # Import the Plugin using the importlib library
            plug = getattr(importlib.import_module(mod, __name__), cls)
            return plug(config=cparser)
        except:
            return Plugin(config=cparser)

    def write(self, data: bytes) -> None:
        """
        Write the `data` to the UDPConnection
        
        This function is used to pass the value of `state` to the write function of the connection.

        Arguments
        ---------
        
        data : bytes
            The data you want to write to the connection as bytes
        """
        self.conn.write(data, self.state)

    def read(self, mac: bool = False) -> tuple[bytes, list] or tuple[bytes, list, bytes]:
        """
        Read `data` from the UDPConnection
        
        This function is used to pass the value of `state` and `dev_mac` 
        to the read function of the connection.

        Arguments
        ---------
        
        mac : bool
            If you want to reveive the MAC Address of the device who sent what u read
        get_state : bool
            If you want to check if the states are matching or not

        Returns
        -------

         - bytes: The Data received (Without the first 6 bytes where the Device MAC is displayed)
         - list: The Position the Device returned

        Optional (when mac is True)
         - bytes: The Mac address of the Device
        """
        return self.conn.read(self.state, self.info.mac, mac)

    def run(self) -> None:
        """
        Execute the 6 Steps displayed here:

         1.  Offer the Configuration to the routerboard
         2.  Formats the routerboard that the new Configuration can be flashed
         3.  Spacer to prepare the Routerboard for the Files
         4.1 Sends the .npk file
         4.2 Sends the .rsc file
         5.  Tells the board that the files can now be installed
         6.  Restarts the board
        """

        self.info = self.conn.get_device_info()
        # Offer the flash
        print("Sent the offer to flash")
        # Counter to count when you are not able to connect to the Network
        cnt = 0
        while True:
            try:
                self.state = [0, 0]
                self.do(b"OFFR\n\n", b"YACK\n")
                break
            # Errno 101 Network is unreachable
            except OSError:
                if cnt > 5:
                    raise Exception("Network is unreachable (Run the start.sh file again)")
                cnt += 1
                pass
        # Format the board
        print("Formatting the board")
        self.do(b"", b"STRT")
        # Spacer to give the board some time to prepare for the file
        print("Spacer")
        self.do(b"", b"RETR")
        # Send the files
        print("Files")
        self.do_files()
        # Tell the board that the installation is done
        print("Installation Done")
        self.do(b"FILE\n", b"WTRM")
        # Tell the board that it can now reboot and load the files
        print("Reboot")
        self.do(b"TERM\nInstallation successful\n")

        # Reset the Flasher to default
        self.reset()
        return

    def do(self, data: bytes, response: bytes = None) -> None:
        """
        Execute steps from the Flashing Process

        Arguments
        ---------

        data : bytes
            The Data to send to the Device
        response : bytes
            What to expect as a Response from the Device (default: None)
        """
        self.state[1] += 1
        self.write(data)
        self.state[0] += 1

        if response is None:
            return True
        else:
            self.wait()
            res, self.state = self.read()
            # Response includes
            # 1. Destination MAC Address    (6 bytes [:6])
            # 2. A `0` as a Short           (2 bytes [6:8])
            # 3. Length of the Data         (2 bytes [8:10])
            # 4. State of the Flash         (4 bytes [10:14])
            # 5. The Response we want       (? bytes [14:])
            if response == res[14:]:
                return True
            else:
                return False

    def do_file(self, file: io.BufferedReader, max_pos: int, file_name: str) -> None:
        """
        Send one file to the Device.
        It sends multiple smaller Packets because of the `MAX_BYTES`

        Arguments
        ---------

        file : BufferedReader
            A File object to send to the Device
        max_pos : int
            The lenght of the file to check when the whole file is sent
        file_name : str
            The name of the file to send
        """
        file_pos = 0
        while True:
            self.state[1] += 1
            data = file.read(self.MAX_BYTES)
            self.write(data)
            self.state[0] += 1
            # Waiting for a response from device to check that the device received the Data
            self.wait()

            file_pos += len(data)
            self.update_file_bar(file_pos, max_pos, file_name)
            if file_pos >= max_pos:
                res, self.state = self.read()
                # Response includes
                # 1. Destination MAC Address    (6 bytes [:6])
                # 2. A `0` as a Short           (2 bytes [6:8])
                # 3. Length of the Data         (2 bytes [8:10])
                # 4. State of the Flash         (4 bytes [10:14])
                # 5. The Response we want       (? bytes [14:])
                if b"RETR" == res[14:]:
                    # Close the file when the installation is done
                    file.close()
                    return True
                else:
                    raise Exception("File was not received properly")
            else:
                # main reason why the flash is so slow but without this sleep state errors occur
                time.sleep(35 / 10000)
        
    def do_files(self) -> None:
        """
        Sends the npk and the rsc file to the Connection using the do_files() Function
        It requests both files from the get_files() Function of the Plugin
        """
        npk, rsc = self.plugin.get_files(self.info)

        # Send the .npk file
        npk_file, npk_file_name, npk_file_size = self.resolve_file_data(npk)
        self.do(bytes(f"FILE\n{npk_file_name}\n{str(npk_file_size)}\n", "utf-8"), b"RETR")
        self.do_file(npk_file, npk_file_size, npk_file_name)

        self.do(b"", b"RETR")
        # \n because update_file_bar() is printing raw strings on one line
        print("\nDone with the Firmware")

        # Send the .rsc file
        rsc_file, rsc_file_name, rsc_file_size = self.resolve_file_data(rsc)
        self.do(bytes(f"FILE\n{rsc_file_name}\n{str(rsc_file_size)}\n", "utf-8"), b"RETR")
        self.do_file(rsc_file, rsc_file_size, rsc_file_name)

        self.do(b"", b"RETR")
        # \n because update_file_bar() is printing raw strings on one line
        print("\nDone with the Configuration File")

    def wait(self) -> None:
        """
        Read some data from the connection to let some time pass
        """
        self.read()

    def reset(self) -> None:
        """
        Reset the flasher to start the next flash
        """
        self.info = None
        self.state = [0, 0]

    @staticmethod
    def resolve_file_data(data) -> tuple[BufferedReader or parse.ParseResult, str, int]:
        """
        This function resolves some data from a file

        Arguments
        ---------
        data : str, BufferedReader
            The information that is available for the file
            (url, filename, path, BufferedReader)

        Returns
        -------

         - BufferedReader or ParseResult: object with a .read() function 
         - str: The name of the file
         - int: The size of the file

        Raises
        ------

        Exception
            data does not result in any data
        """
        # data is already Readable
        if isinstance(data, BufferedReader):
            # Working
            size = getsize(data.name)
            name = basename(data.name)
            file = data
        else:
            # data is a url to a file
            try:
                # Not tested yet
                par = parse.urlparse(data)
                size = getsize(par)
                name = basename(par)
                file = request.urlopen(data)
            except:
                # data is a filename/path
                try:
                    # Working
                    size = getsize(data)
                    name = basename(data)
                    file = open(data, "rb")
                except:
                    raise Exception("Unable to get file file information")
        return file, name, size

    @staticmethod
    def update_file_bar(curr_pos: int, max_pos: int, name: str, leng: int = 50):
        """
        Updates a Loading Bar when no print statements get executed duning updating

        Calculates how many percent are already processed and displays that.

        Arguments
        ---------

        curr_pos : int
            The current pos what is already processed
        max_pos : int
            The highest pos what should be processed
        name : str
            A Text to display in front of the progress bar
        leng : int
            The length of the progress bar (default: 50)
        """
        # Calculate the percentage of the progress
        proz = round((curr_pos/max_pos) * 100)
        # Calculate how much > have to bo displayed
        done = round((leng/100) * proz)
        # Create the string inside of the loading bar (`[]`)
        inner = "".join([">" for i in range(done)] + [" " for i in range(leng-done)])
        sys.stdout.write(f"\rFlashing {name} - [{inner}] {proz}%")
