
class DeviceInfo:
    """
    A Class to have a collection of all the information about a Device

    Attributes
    ----------

    mac : bytes
        The MAC Address of the Device
    model : str
        What model the Device is 
    arch : str
        The Architecture of the Device
    min_os : str
        The lowest OS Version to use for the Device
    lic_id : str
        The ID of the Licence (default: None)
    lic_key : str
        The Licence Key (default: None)

    Classmethods
    -------

    from_data(bytes) -> DeviceInfo
        Returns an object of DeviceInfo from bytes that are received from the Device
    """
    def __init__(self, mac: bytes, model: str, arch: str, min_os: str, lic_id: str = None, lic_key: str = None):
        self.mac = mac
        self.model = model
        self.arch = arch
        self.min_os = min_os
        self.lic_id = lic_id
        self.lic_key = lic_key

    @classmethod
    def from_data(cls, data: bytes) -> object:
        """
        Create DeviceInfo from the data received from the Device

        Argument
        --------

        data : bytes
            The bytes to convert to a DeviceInfo object

        Returns
        -------

         - DeviceInfo: The converted object
        """
        mac = data[:6]
        rows = data[20:].split(b"\n") # Device sends 6 bytes of the MAC Address and 14 more unused bytes
        rows.remove(rows[0]) # Remove the first unused information
        rows = list(map(lambda x: x.decode(), rows))
        return cls(
            mac,
            *rows[2:5], # Model, Architecture, minOS
            *rows[0:2]  # Licence ID, Licence Key
            )
