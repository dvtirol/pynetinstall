import io
import logging
import sys
import time
import importlib

from io import BufferedReader
from urllib import request
from http.client import HTTPResponse
from os.path import getsize, basename
from configparser import ConfigParser

from pynetinstall.log import Logger
from pynetinstall.interface import InterfaceInfo
from pynetinstall.network import UDPConnection
from pynetinstall.plugins.simple import Plugin


class AbortFlashing(Exception):
    """ Abort the currently running flashing process. """
    pass


class FatalError(Exception):
    """ Indicates a configuration error. """
    pass


class Flasher:
    """
    Object to flash configurations on a Mikrotik Routerboard

    To run the flash simply use the .run() function.

    During the installation the Raspberry Pi is connected to the board
    over a UDP-socket (`pynetinstall.network.UDPConnection`)


    Attributes
    ----------
    conn : UDPConnection
        A Socket Connection to send UDP Packets
    info : InterfaceInfo
        Information about the Interface
    state : list
        The current state of the flash (default: [0, 0])
    plugin : Plugin
        A Plugin to get the firmware and the configuration file 
        (Must include a .get_files(), has the Configuration as an attribute)
    logger : Logger
        Object to log LogRecords
    
    MAX_BYTES : int
        How many bytes the connection can receive at once (default: 1024)

    Methods
    -------
    load_config(config_file="config.ini") -> Plugin
        Loads the Plugin as configured in the `config_file`

    write(data) -> None
        Writes `data` over the Connection

    read(mac=False) -> tuple[bytes, list] or tuple[bytes, list, bytes]
        Read `data` from the Connection

    run(info=None) -> None
        The Flashing Process

    do(data, response=None) -> None
        Execute one step of the Flashing  Process

    do_file(file, max_pos, file_name) -> None
        Send a `file` over the Connection
    
    do_files() -> None
        Get the files from the `plugin` and execute do_file() for every file
    
    wait() -> None
        Wait for something

    resolve_file_data(data) -> tuple[BufferedReader or parse.ParseResult, str, int]
        Gets information about a file
    """

    info: InterfaceInfo
    state: list = [0, 0]
    MAX_BYTES: int = 1024

    def __init__(self, connection: UDPConnection, config_file: str = "config.ini",
                 logger: Logger = None) -> None:
        """
        Initialization of a new Flasher
        
        Loading the Configuration
        Creating a Connection to the Interface

        Arguments
        ---------

        connection : UDPConnection
            The Connection object to reuse from flash_once or flash_until_stopped.
        config_file : str
            The location of the configuration file (default: config.ini)
        logger : Logger
            Object to log LogRecords
        """
        self.logger = logger
        self.logger.debug("Initialization of a new Flasher object")
        self.plugin = self.load_config(config_file)
        self.conn = connection

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
            raise FatalError(f"Configuration File ({config_file}) not found")
        try:
            plugin = cparser.get("pynetinstall", "plugin", fallback="pynetinstall.plugins.simple:Plugin")
            mod, _, cls = plugin.partition(":")
            if not cls:
                cls = "Plugin"

            plug = getattr(importlib.import_module(mod, __name__), cls)
            self.logger.debug(f"The Plugin ({plug}) is successfully imported")

            try:
                # attempt to initialize plugin with config
                return plug(config=cparser)
            except TypeError:
                # if no custom __init__() was defined, no config will be available
                return plug()
        except Exception as e:
            raise FatalError(f"Could not load {plug.__module__}.{plug.__name__}: {e} ({type(e).__name__})")

    def verify_npk(self, info: InterfaceInfo) -> None:
        """
        Checks that the RouterOS file the plugin returned is valid to avoid
        formatting the Routerboard without being able to install an OS.
        """
        npk, *_ = self.plugin.get_files(info)
        if npk is None:
            raise AbortFlashing("Verification failed: Plugin did not return RouterOS.")

        npk_file, _, _ = self.resolve_file_data(npk)
        if npk_file.read(4) != b'\x1e\xf1\xd0\xba': # npk magic bytes 0x1EF1D0BA (via binwalk)
            raise AbortFlashing("Verification failed: RouterOS file does not look like an NPK.")

        npk_file.close()

    def write(self, data: bytes) -> None:
        """
        Write the `data` to the UDPConnection
        
        This function is used to pass the value of `state` to the write function of the connection.

        Arguments
        ---------
        
        data : bytes
            The data you want to write to the connection as bytes
        """
        self.conn.write(data, self.state, self.info.mac)

    def read(self) -> tuple[bytes, list]:
        """
        Read `data` from the UDPConnection
        
        This function is used to pass the value of `state` and `dev_mac` 
        to the read function of the connection.

        Returns
        -------

         - bytes: The Data received (Without the first 6 bytes where the Interface MAC is displayed)
         - list: The Position the Interface returned
        """
        try:
            data = self.conn.read(self.state)
        except TimeoutError as e:
            raise AbortFlashing(f"Device did not respond")
        return data

    def run(self, info: InterfaceInfo) -> None:
        """
        Execute the 6 Steps displayed here:

        (0.  Waits for a new Interface if no `info` is given)
         1.  Offer the Configuration to the Routerboard
         2.  Formats the Routerboard that the new Configuration can be flashed
         3.  Spacer to prepare the Routerboard for the Files
         4.1 Sends the .npk file
         4.2 Sends the .rsc file
         5.  Tells the board that the files can now be installed
         6.  Restarts the board
        """
        self.info = info
        # Offer the flash
        self.logger.debug("Sending the offer to flash")
        try:
            self.state = [0, 0]
            self.do(f"OFFR\n{info.lic_key}\n\n\n\0".encode(), b"YACK\n")
        # Errno 101 Network is unreachable
        except OSError as e:
            raise AbortFlashing(f"Network error: {e}")
        # Format the board
        self.logger.info(f"Formatting {info.mac.hex(':')} ...")
        self.do(b"", b"STRT")
        # Spacer to give the board some time to prepare for the file
        self.logger.debug("Waiting until the Board is ready to receive the file")
        self.do(b"", b"RETR")
        # Send the files
        self.logger.debug("Sending the Files to the Board")
        self.do_files()
        # Tell the board that the installation is done
        self.logger.debug("Installation Done")
        self.do(b"FILE\n", b"WTRM")
        # Tell the board that it can now reboot and load the files
        self.logger.debug("Rebooting the Board")
        self.do(b"TERM\n")

        self.logger.info(f"{info.mac.hex(':')} was successfully flashed.")
        return

    def do(self, data: bytes, response: bytes = None) -> None:
        """
        Execute steps from the Flashing Process

        Arguments
        ---------

        data : bytes
            The Data to send to the Interface
        response : bytes
            What to expect as a Response from the Interface (default: None)
        """
        self.logger.debug(f"Executing the {data} command")
        self.state[1] += 1
        self.write(data)
        self.state[0] += 1

        if response is None:
            return True
        else:
            self.logger.debug(f"Waiting for the Response {response}")
            res, new_state = self.read()
            if res is None:
                raise AbortFlashing(f"Did not receive response to {data} (expected {response})")
            self.state = new_state
            # Response includes
            # 1. Destination MAC Address    (6 bytes [:6])
            # 2. A `0` as a Short           (2 bytes [6:8])
            # 3. Length of the Data         (2 bytes [8:10])
            # 4. State of the Flash         (4 bytes [10:14])
            # 5. The Response we want       (? bytes [14:])
            if response == res[14:]:
                self.logger.debug(f"Received Response {response}")
                return True

    def do_file(self, file: io.BufferedReader, max_pos: int, file_name: str) -> None:
        """
        Send one file to the Interface.
        It sends multiple smaller Packets because of the `MAX_BYTES`

        Arguments
        ---------

        file : BufferedReader
            A File object to send to the Interface
        max_pos : int
            The length of the file to check when the whole file is sent
        file_name : str
            The name of the file to send (Would be used if the file_bar would be updated)
        """
        file_pos = 0
        next_log = 10 # output log message every 10% (for large files only)
        while True:
            self.state[1] += 1
            data = file.read(self.MAX_BYTES)
            self.write(data)
            self.state[0] += 1
            # Waiting for a response from interface to check that the interface received the Data
            self.read() # should be b"RETR"

            file_pos += len(data)
            file_percent = round(100*file_pos/(max_pos or 1))
            if file_percent >= next_log and max_pos > 100000: # 100kB
                self.logger.info(f"    {file_name}: {file_percent}%")
                next_log += 10
            if file_pos >= max_pos:
                res, new_state = self.read()
                if res is None:
                    raise AbortFlashing(f"Did not receive response to file upload (state {self.state})")
                self.state = new_state
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
                # main reason why flashing is so slow but without this sleep state errors occur
                time.sleep(0.005)

    def do_files(self) -> None:
        """
        Sends the npk and the rsc file to the Connection using the do_files() Function
        It requests both files from the get_files() Function of the Plugin
        """
        *npks, rsc = self.plugin.get_files(self.info)
        if not all(npks):
            raise AbortFlashing("Plugin did not return RouterOS or an additional package is 'None'.")
        for npk in npks:
            # Send the .npk file
            npk_file, npk_file_name, npk_file_size = self.resolve_file_data(npk)
            try:
                self.do(bytes(f"FILE\n{npk_file_name}\n{str(npk_file_size)}\n", "utf-8"), b"RETR")
            except AbortFlashing:
                # NOTE: it appears that not all devices send a 'RETR' response here, so we ignore it.
                pass
            self.logger.info(f"Uploading {npk_file_name}")
            self.do_file(npk_file, npk_file_size, npk_file_name)

            # wait before sending the next file
            self.do(b"", b"RETR")

        self.logger.debug("Done with the Firmware")

        # Send the initial config file. routerOS expects filename to be autorun.scr.
        if rsc:
            rsc_file, rsc_file_name, rsc_file_size = self.resolve_file_data(rsc)
            self.do(bytes(f"FILE\nautorun.scr\n{str(rsc_file_size)}\n", "utf-8"), b"RETR")
            self.logger.info(f"Uploading {rsc_file_name}")
            self.do_file(rsc_file, rsc_file_size, rsc_file_name)

            self.do(b"", b"RETR")
            self.logger.debug("Done with the Configuration File")

    def resolve_file_data(self, data) -> tuple[BufferedReader or HTTPResponse, str, int]:
        """
        This function resolves some data from a file

        Arguments
        ---------
        data : str, BufferedReader
            The information that is available for the file
            (url, filename, path, BufferedReader)

        Returns
        -------

         - BufferedReader or HTTPResponse: object with a .read() function 
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
            self.logger.debug("Resolved File-Data from the BufferedReader")
        else:
            # data is a url to a file
            try:
                # Working
                file = request.urlopen(data)
                size = int(file.getheader("Content-Length"))
                try: # use server provided file name if available
                    name = file.getheader("Content-Disposition")
                    name = name.split("=")[1]
                except: # extract basename from URL
                    _, _, name = data.rpartition('/')
                    name, _, _ = name.partition('?')
                self.logger.debug("Resolved File-Data from the URL")
            except:
                # data is a filename/path
                try:
                    # Working
                    size = getsize(data)
                    name = basename(data)
                    file = open(data, "rb")
                    self.logger.debug("Resolved File-Data from the Path/Filename")
                except:
                    raise AbortFlashing(f"Unable to read file/url/BufferedReader ({data})")
        return file, name, size

class FlashInterface:
    """
    Object to run a loop to run multiple flashes after each other

    Attributes
    ----------

    connection : UDPConnection
        The Connection to wait for new Interfaces
    config_file : str
        The location of the configuration file (default: config.ini)
    logger : Logger
        The Logger to log LogRecords

    Methods
    -------

    flash_once() -> None
        Execute a flash once

    flash_until_stopped() -> None
        Run flash until someone stops the program
    """
    def __init__(self, interface_name : str = None, mac_address : str = None, config_file : str = "config.ini", log_level: int = logging.INFO) -> None:
        """
        Initialize a new FlashInterface

        Create a new Logger instance and a new `connection` to wait for new
        Interfaces. One of `interface_name` or `mac_address` must be provided.

        Argument
        --------

        interface_name : str
            The name of the interface to listen on

        mac_address : str|bytes
            The mac address of the interface to listen on

        log_level : int
            What level should be logged by the `logger`
        """
        self.logger = Logger(log_level)
        self.config_file = config_file
        try:
            self.connection = UDPConnection(logger=self.logger, interface_name=interface_name, mac_address=mac_address)
        except (OSError, ValueError) as e:
            raise FatalError(f"{e} ({interface_name or mac_address})")

    def flash_once(self) -> None:
        """
        Flash one Interface
        """
        flash = Flasher(self.connection, config_file=self.config_file, logger=self.logger)
        interface = self.connection.get_interface_info()
        flash.verify_npk(interface)
        flash.run(interface)
        self.connection.close()

    def flash_until_stopped(self) -> None:
        """
        Flash until someone stops the program
        """
        try:
            while True:
                try:
                    flash = Flasher(self.connection, config_file=self.config_file, logger=self.logger)
                    self.logger.info(f"Waiting for devices...")
                    interface = None
                    while not interface:
                        interface = self.connection.get_interface_info()
                    self.logger.info(f"Device found! mac={interface.mac.hex(':')}, model={interface.model}, arch={interface.arch}")
                    flash.verify_npk(interface)
                    flash.run(interface)
                except AbortFlashing as e:
                    self.logger.error(f"Flashing failed: {e}")
                    continue
        finally:
            self.connection.close()