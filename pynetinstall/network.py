import fcntl
import socket
import struct

from pynetinstall.log import Logger
from pynetinstall.interface import InterfaceInfo


class UDPConnection(socket.socket):
    """
    `Subclass of socket.socket`

    This object represents the UDP connection to the Mikrotik Routerboard

    It handles the reading/writing between the interfaces

    Attributes
    ----------

    mac : bytes
        The MAC Address of the `interface_name` Interface of the Raspberry

    MAX_ERRORS : int
        How often a Function gets repeated before it raises an error
    MAX_BYTES_RECV : int
        The amount of bytes to receive at once

    Methods
    -------

    _get_source_mac() -> None
        Get the `mac` Address of the Raspberry
    
    read(state) -> tuple
        Read data from the Connection

    write(data, state, recv_addr=("255.255.255.255", 5000)) -> None
        Write `data` to the Connection

    get_interface_info() -> tuple
        Resolve some information about the Interface
    """
    mac: bytes

    def __init__(self, addr: tuple = ("0.0.0.0", 5000), interface_name: str = "eth0", error_repeat: int = 25, logger: Logger = None,
                 family: socket.AddressFamily or int = socket.AF_INET, kind: socket.SocketKind or int = socket.SOCK_DGRAM, *args, **kwargs) -> None:
        """
        Initialize a new UDPConnection

        Two options are set for the socket:
         - SO_REUSEADDR: To use the Address more than one time
         - SO_BROADCAST: To send Broadcast Messages

        Arguments
        ---------

        addr : tuple
            The Address Pair on which the socket will be binded (default: ("0.0.0.0", 5000))
        interface_name : str
            The name of the Interface where the Interface is connected to (default: "eth0")
        error_repeat : int
            How often a function is repeated until it gets the right response or it raises an error (default: 25)
        """
        super().__init__(family, kind, *args, **kwargs)
        self._interface_name = interface_name
        self.logger = logger
        self.MAX_ERRORS = error_repeat
        self.MAX_BYTES_RECV = 1024
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bind(addr)
        self.logger.debug(f"A New UDPConnection is created on {addr}")
        self._get_source_mac()

    def _get_source_mac(self) -> None:
        """
        This function gets the MAC-Address of the interface defined in `interface_name`
        """
        arg = struct.pack('256s', bytes(self._interface_name, 'utf-8')[:15])
        self.mac = fcntl.ioctl(self.fileno(), 0x8927, arg)[18:24]  # 0x8927: SIOCGIFHWADDR
        self.logger.debug(f"The MAC-Address of the Interface {self._interface_name} is {self.mac}")

    def read(self, state: list, _repeated = 0) -> tuple[bytes, list] or None:
        """
        Reads `MAX_BYTES_RECV` (int) from the socket and returns the bytes.

        This function also checks if the message was sent by the Raspberry Server
        and restarts the function if this happens (As long as `_repeated` is smaller than `MAX_ERRORS`).

        Arguments
        ---------

        state : tuple
            The State of the Flash Process [Server State, Interface State]

        Returns
        -------
        
         - bytes: The data received from the Interface, or None on error
         - list: The State displayed in the Header of the UDPPacket, or None on error
        """

        data, addr = self.recvfrom(self.MAX_BYTES_RECV)
        header_state = []

        # since we listen for broadcasts, we also receive any packets we sent ourselves, so we have to filter out packets with our ip in src
        if addr[0] == "0.0.0.0": # Routerboard sets this as srcip
            # The fist 6 bytes are the MAC Address of the source 
            header_mac: bytes = data[:6]
            # From bytes 16 to 20 the states are displayed
            header_state: list[int] = [*struct.unpack("<HH", data[16:20])]
            if header_state == state: # state not updated (happens during OFFR and FILE commands) means the device is not yet ready to continue
                return data[6:], header_state

        # otherwise, likely received an unrelated packet (wrong srcip or state)
        _repeated += 1
        if _repeated > self.MAX_ERRORS:
            self.logger.debug(f"State is {header_state}, but should be {state} (tried {_repeated} times), aborting.")
            return None, None

        return self.read(state, _repeated)

    def write(self, data: bytes, state: list, dev_mac: bytes, recv_addr: tuple = ("255.255.255.255", 5000)) -> None:
        """
        Write a Broadcast message to all the connected interfaces including the data.

        Arguments
        ---------

        data : bytes
            The `data` to send to the Interface
        state : list
            A list of the current State of the Flash [Server State, Interface State]
        dev_mac : bytes
            The MAC Address of the Interface
        recv_addr : tuple
            A Address pair to where the Connection sends the data to (default: ("255.255.255.255, 5000))
        """
        # Overview of the Data
        # 1. The MAC Address of the source          (6 bytes)
        # 2. The MAC Address of the destination     (6 bytes)
        # 3. A `0` as a Short                       (2 bytes)
        # 4. The length of the Data                 (2 bytes)
        # 5. The State of the Server                (2 bytes)
        # 6. The State of the Client                (2 bytes)
        # 7. The data                               (? bytes)
        message = self.mac + dev_mac + struct.pack("<HHHH", 0, len(data), state[1], state[0]) + data
        self.sendto(message, recv_addr)

    def get_interface_info(self) -> InterfaceInfo:
        r"""
        This function collects some information about the Routerboard

        Important Information:
         - Model (What type of Routerboard it is)
         - Architecture (The Architecture of the Routerboard)
         - min OS (The lowest OS you can install on the Routerboard)

        Other Information:
         - MAC Address (The MAC Address of the Interface)
         - License ID (The ID of the License)
         - License Key (The Key of the License)

        Returns
        -------

         - InterfaceInfo: A object with all the information of the Interface
        """
        
        self.logger.debug("Searching for a Interface...")
        data, addr = self.recvfrom(self.MAX_BYTES_RECV)

        if addr[0] == "0.0.0.0": # see self.read() for details.
            header_state = [*struct.unpack("<HH", data[16:20])]
            if header_state == [1, 0]:
                mac  = data[:6].hex(':').upper()
                self.logger.debug(f"Interface Found: {mac}")
                return InterfaceInfo.from_data(data)

        return None
