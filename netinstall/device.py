
class DeviceInfo:
    def __init__(self, mac: bytes, model: str, arch: str, min_os: str, lic_id: str = None, lic_key: str = None):
        self.mac = mac
        self.model = model
        self.arch = arch
        self.min_os = min_os
        if lic_id is not None:
            self.lic_id = lic_id
        if lic_key is not None:
            self.lic_key = lic_key

    @classmethod
    def from_data(cls, data: bytes) -> object:
        mac = data[:6]
        rows = data[20:].split(b"\n")
        rows.remove(rows[0])
        rows = list(map(lambda x: x.decode(), rows))
        print(rows)
        return cls(
            mac,
            *rows[2:5],
            *rows[0:2]
            )
