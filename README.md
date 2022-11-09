# pyNetinstall

Free and Open-Source netInstall implementation for Flashing Mikrotik RouterBoards


## Usage

`python -m pynetinstall [NAME_OF_ETHERNET_INTERFACE]`

You must provide the name of your ethernet interface if it is not named `eth0`.


## Setup

Setup `dnsmasq` to provide DHCP and TFTP, so your RouterBoard can boot via
BOOTP. Boot images can be obtained either by extracting them from
`netinstall.exe`, or alternatively, some can be downloaded from the
[merlinthemagic/MTM-Mikrotik] repo.

Provide the path to the firmware you want to install in pyNetinstall's
`config.ini` (searched in the current working directory). A custom default
configuration script can be provided as well:

```
[pynetinstall]
firmware=<PATH_TO_ROUTEROS_NPK>
config=<PATH_TO_CONFIG_RSC>
```

<!--
By setting `plugin=<python_module>:<a_class>` in `config.ini`, you can create a
custom Python module for dynamically fetching different configuration files by
matching the MAC address of the connected RouterBoard. The module will be
searched for in Python's path ($PWD, $PATH or $PYTHONPATH). This is not well
documented; please see the source at `pynetinstall/plugins/simple.py`.

More information on setting up dnsmasq can be obtained from here:
https://openwrt.org/toh/mikrotik/common#netboot_of_openwrt_uses_dhcpbootptftp
-->

[merlinthemagic/MTM-Mikrotik]: https://github.com/merlinthemagic/MTM-Mikrotik/tree/master/Docs/Examples/TFTP-Images

Below is a sample dnsmasq configuration. Depending on the CPU architecture of
your RouterBoard, a different boot file must be used. You can differentiate
architectures through the vendor class identifier sent with the DHCP request.

```
interface=eth0

dhcp-range=10.0.0.101,10.0.0.200,10m
dhcp-boot=vendor:MMipsBoot,mmips_boot_6.42.5
dhcp-boot=vendor:ARM__boot,arm_boot_6.42.5
dhcp-boot=vendor:Mips_boot,Mips_boot_netinstall_6.48

enable-tftp
tftp-root=/var/ftpd
tftp-no-blocksize
```
