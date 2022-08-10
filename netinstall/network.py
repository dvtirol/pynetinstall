import socket
import struct
import fcntl


class UDPConnection(socket.socket):
    """
    This object represents the UDP connection to the Mikrotik Routerboard

    It handles the reading/writing between the devices
    """
    mac: bytes
    dev_mac: bytes
    _last_message: bytes = None
    _repeat: int = 0

    def __init__(self, addr: tuple = ("0.0.0.0", 5000), interface_name: str = "eth0", error_repeat: int = 5,
                 family: socket.AddressFamily or int = socket.AF_INET, kind: socket.SocketKind or int = socket.SOCK_DGRAM, *args, **kwargs) -> None:
        super().__init__(family, kind, *args, **kwargs)
        self._interface_name = interface_name
        self.MAX_ERRORS = error_repeat
        self.MAX_BYTES_RECV = 1024
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(addr)
        self._get_source_mac()

    def _get_source_mac(self) -> None:
        """
        This function gets the MAC-Address of the interface defined in ifname
        """
        arg = struct.pack('256s', bytes(self._interface_name, 'utf-8')[:15])
        self.mac = fcntl.ioctl(self.fileno(), 0x8927, arg)[18:24]

    def read(self, pos: tuple, check_mac: bytes = None, mac: bool = False) -> tuple:
        if self._repeat > self.MAX_ERRORS:
            raise Exception(f"The function was called more than {self.MAX_ERRORS} times")
        """
        Reads `MAX_BYTES_RECV` (int) from the socket and returns the bytes.

        This function also checks if the message was sent by the Raspberry Serever
        and restarts the function if this happens.
        """
        print("Started Reading...")
        data = self.recv(self.MAX_BYTES_RECV)
        print(f"Read Data{data}")
        header_pos = []
        print(f"SAME DATA {data == self._last_message} -> {data} - {self._last_message}")
        if data.startswith(bytes(self.mac)) or data == self._last_message:
            print("Read Startswith")
            self.read(pos, check_mac, mac)
            self._repeat += 1
        else:
            header_mac: bytes = data[:6]
            header_pos: list[int] = [struct.unpack(">H", data[16:18])[0], struct.unpack(">H", data[18:20])[0]]
            if header_pos == [256, 0] and pos != header_pos:
                self.read(pos, check_mac, mac)
                self._repeat += 1
            print(header_pos)
        print(f"Positions: {header_pos == pos} -> {header_pos} == {pos}")
        if header_pos == pos:
            print(f"MAC: {check_mac == header_mac} -> {check_mac} == {header_mac}")
            if check_mac is not None:
                print("CHECK_MAC")
                if check_mac == header_mac:
                    self._repeat = 0
                    if mac is True:
                        print(f"MAC-True: {data[6:]}, {header_pos}, {header_mac}")
                        return data[6:], header_pos, header_mac
                    print(f"MAC-False: {data[6:]}, {header_pos}")
                    return data[6:], header_pos
                else:
                    raise Exception("MAC Error")
            else:
                print("CHECK_MAC NONE")
                self._repeat = 0
                if mac is True:
                    print(f"MAC-True: {data[6:]}, {header_pos}, {header_mac}")
                    return data[6:], header_pos, header_mac
                print(f"MAC-False: {data[6:]}, {header_pos}")
                return data[6:], header_pos
        else:
            raise Exception("Position Error")

    def write(self, data: bytes, positions: list, recv_addr: tuple = ("10.192.3.255", 5000)) -> None:
        """
        Write a Broadcast message to all the connected devices including the data.

        To send Broadcast messages with a socket it is required to enable the `socket.SO_BROADCAST` option.
        """
        self.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = bytes(self.mac) + bytes(self.dev_mac) + b"0000" + bytes(len(data)) + bytes(positions[0]) + bytes(positions[1]) + data
        print(f"Write: {message}")
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

        Returns:
         - mac: bytes (e.g. \x00\x0cB\xac\x21)
         - model: str (e.g.: RB450G)
         - architecture: str (e.g.: mips)
         - minOS: str (e.g.: 6.45.9)
        """
        print("Searching for a Device...")
        data, _, mac = self.read([256, 0], mac=True)
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
            print(f"Device Search: {mac}, {rows[3].decode()}, {rows[4].decode()}, {rows[5].decode()}")
            self.dev_mac = mac
            return mac, rows[3].decode(), rows[4].decode(), rows[5].decode()
        else:
            raise Exception("Discovery Error: No data found")
