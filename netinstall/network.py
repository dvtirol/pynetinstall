import socket
import struct
import fcntl


class UDPConnection(socket.socket):
    """
    This object represents the UDP connection to the Mikrotik Routerboard

    It handles the reading/writing between the devices

    Attributes
    ----------

    mac : bytes
        The MAC Address of the `interface_name` Interface of the Raspberry
    dev_mac : bytes
        The MAC Address of the Device
    MAX_ERRORS : int
        How often a Function gets repeated before it raises an error
    MAX_BYTES_RECV : int
        The amout of bytes to receive at once

    _last_message : bytes
        The last sended message
    _repeat : int
        A Counter how often a Function was repeat

    Methods
    -------

    _get_source_mac() -> None
        Get the `mac` Address of the Raspberry
    
    read(state, check_mac=None, mac=False) -> tuple
        Read data from the Connection

    write(data, state, recv_addr=("255.255.255.255", 5000)) -> None
        Write `data` to the Connection

    get_device_info() -> tuple
        Resolve some informations about the Device
    """
    mac: bytes
    dev_mac: bytes
    _last_message: bytes = None
    _repeat: int = 0

    def __init__(self, addr: tuple = ("0.0.0.0", 5000), interface_name: str = "eth0", error_repeat: int = 5,
                 family: socket.AddressFamily or int = socket.AF_INET, kind: socket.SocketKind or int = socket.SOCK_DGRAM, *args, **kwargs) -> None:
        """
        Initialize a new UDPConnection

        Two otions are set for the socket:
         - SO_REUSEADDR: To use the Address more than one time
         - SO_BROADCAST: To send Broadcast Messages

        Agruments
        ---------

        addr : tuple
            The Address Pair on which the socket will be binded (default: ("0.0.0.0", 5000))
        interface_name : str
            The name of the Interface where the Device is connected to (default: "eth0")
        error_repeat : int
            How often a function is repeaten until it gets the right response or it raises an error (default: 5)
        """
        super().__init__(family, kind, *args, **kwargs)
        self._interface_name = interface_name
        self.MAX_ERRORS = error_repeat
        self.MAX_BYTES_RECV = 1024
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bind(addr)
        self._get_source_mac()

    def _get_source_mac(self) -> None:
        """
        This function gets the MAC-Address of the interface defined in `interface_name`
        """
        arg = struct.pack('256s', bytes(self._interface_name, 'utf-8')[:15])
        self.mac = fcntl.ioctl(self.fileno(), 0x8927, arg)[18:24]

    def read(self, state: tuple, check_mac: bytes = None, mac: bool = False) -> tuple:
        """
        Reads `MAX_BYTES_RECV` (int) from the socket and returns the bytes.

        This function also checks if the message was sent by the Raspberry Server
        and restarts the function if this happens (As long as `_repeat` is smaller than `MAX_ERRORS`).

        Arguments
        ---------

        state : tuple
            The State of the Flash Process [Server State, Device State]
        check_mac : bytes
            The MAC Address of the Device to check if the packet was sent by the Device (default: None)
        mac : bool
            If the function should return the MAC Address of the Source (default: False)

        Returns
        -------
        
         - bytes: The data received from the Device
         - list: The State displayed in the Header of the UDPPacket
        Optional (When `mac` is True)
         - bytes: The MAC Address of the Source
        """
        if self._repeat > self.MAX_ERRORS:
            raise Exception(f"The function was called more than {self.MAX_ERRORS} times")
        
        print("Started Reading...")
        data = self.recv(self.MAX_BYTES_RECV)
        header_state = []
        print(f"SAME DATA {data == self._last_message} -> {data} - {self._last_message}")
        if data != self._last_message:
            header_mac: bytes = data[:6]
            header_state: list[int] = [struct.unpack("<H", data[16:18])[0], struct.unpack("<H", data[18:20])[0]]
            print(header_state)
            print(f"Positions: {header_state == state} -> {header_state} == {state}")
            if header_state == state:
                print(f"MAC: {check_mac == header_mac} -> {check_mac} == {header_mac}")
                if check_mac is not None:
                    print("CHECK_MAC")
                    if check_mac == header_mac:
                        self._repeat = 0
                        if mac is True:
                            print(f"MAC-True: {data[6:]}, {header_state}, {header_mac}")
                            return data[6:], header_state, header_mac
                        print(f"MAC-False: {data[6:]}, {header_state}")
                        return data[6:], header_state
                else:
                    print("CHECK_MAC NONE")
                    self._repeat = 0
                    if mac is True:
                        print(f"MAC-True: {data[6:]}, {header_state}, {header_mac}")
                        return data[6:], header_state, header_mac
                    print(f"MAC-False: {data[6:]}, {header_state}")
                    return data[6:], header_state
        self._repeat += 1
        self.read(state, check_mac, mac)

    def write(self, data: bytes, state: list, recv_addr: tuple = ("255.255.255.255", 5000)) -> None:
        """
        Write a Broadcast message to all the connected devices including the data.

        Arguments
        ---------

        data : bytes
            The `data` to send to the Device
        state : list
            A list of the current State of the Flash [Server State, Device State]
        recv_addr : tuple
            A Address pair to where the Connection sends the data to (default: ("255.255.255.255, 5000))
        """
        message = self.mac + self.dev_mac + int(0).to_bytes(2, "little") + len(data).to_bytes(2, "little") + state[0].to_bytes(2, "little") + state[1].to_bytes(2, "little") + data
        print(f"Write: {len(message)} bytes")
        self.sendto(message, recv_addr)
        self._last_message = message

    def get_device_info(self) -> tuple:
        r"""
        This function collects some information about the routerboard

        Important Information:
         - Model (What type of routerboard it is)
         - Architecture (The Architecture of the routerboard)
         - min OS (The lowest OS you can install on the routerboard)

        Other Information:
         - MAC Address (The MAC Address of the Device)
         - Licence ID (The ID of the Licence)
         - Licence Key (The Key of the Licence)

        Returns
        -------

         - bytes: The MAC Address of the Device (e.g. \x00\x0cB\xac\x21)
         - str: What model the Device is (e.g.: RB450G)
         - str: The Architecture of the Device (e.g.: mips)
         - str: The min OS what the Device Requires (e.g.: 6.45.9)
        """
        print("Searching for a Device...")
        data, _, self.dev_mac = self.read([1, 0], mac=True)
        print(f"MAC Address: \n - Raspberry: {self.mac}\n - Board: {self.dev_mac}")
        print("Device Found")
        infoData = data[20:]
        rows = infoData.split(b"\n")
        if len(rows) == 6:
            if rows[1] != b"":
                lic_id = rows[1]
            if rows[2] != b"":
                lic_key = rows[2]
            rb_model = rows[3]
            rb_arch = rows[4]
            rb_minOS = rows[5]

            """print("model:", rb_model)
            print("arch:", rb_arch)
            print("min os:", rb_minOS)
            print("device mac:", mac)
            print("lic key:", lic_key)
            print("lic id:", lic_id)"""
            print(f"Device Search: {self.dev_mac}, {rows[3].decode()}, {rows[4].decode()}, {rows[5].decode()}")
            self.dev_mac = self.dev_mac
            return self.dev_mac, rows[3].decode(), rows[4].decode(), rows[5].decode()
        else:
            raise Exception("Discovery Error: No data found")
