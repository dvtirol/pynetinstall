
class InterfaceInfo:
    """
    A Class to have a collection of all the information about a Interface

    Attributes
    ----------

    mac : bytes
        The MAC Address of the Interface
    model : str
        What model the Interface is 
    arch : str
        The Architecture of the Interface
    min_os : str
        The lowest OS Version to use for the Interface
    lic_id : str
        The ID of the License (default: None)
    lic_key : str
        The License Key (default: None)

    Classmethod
    -----------

    from_data(bytes) -> InterfaceInfo
        Returns an object of InterfaceInfo from bytes that are received from the Interface
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
        Create InterfaceInfo from the data received from the Interface

        Argument
        --------

        data : bytes
            The bytes to convert to a InterfaceInfo object

        Returns
        -------

         - InterfaceInfo: The converted object
        """
        mac = data[:6]
        rows = data[20:].split(b"\n") # Interface sends 6 bytes of the MAC Address and 14 more unused bytes
        rows.remove(rows[0]) # Remove the first unused information
        rows = list(map(lambda x: x.decode(), rows))
        return cls(
            mac,
            *rows[2:5], # Model, Architecture, minOS
            *rows[0:2]  # License ID, License Key
            )
