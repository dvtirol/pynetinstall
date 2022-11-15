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

## Extracting Boot Images

You will need to aquire the boot images that the official netinstall tool uses.
These are not included as they are not licensed for re-distribution. However, it
is fairly easy to extract them from the Mikrotik's Netinstall tool. This guide
describes the Linux CLI version, but the same techniques should work on the
Windows GUI version as well.

1. **Download `netinstall-<version>.tar.gz`**  
   You can use the latest version that is linked in the [Downloads page] General
   section for all RouterOS versions.

2. **Start `netinstall-cli`**  
   `sudo ./netinstall-cli -a 127.0.0.2 netinstall-cli`  

3. **Run `dhtest`**  
   `sudo dhtest -T 5 -o ARM64__boot -i lo`  
   This will set up extraction of the arm64/aarch64 image. Other valid options
   are `Mips_boot`, `MMipsBoot`, `Powerboot`, `e500_boot`==`e500sboot`,
   `440__boot`, `tile_boot`, `ARM__boot` and `ARM64__boot`.

4. **Download the image**  
   `curl tftp://127.0.0.1/linux.arm > netinstall.arm64`  
   The filename is always `linux.arm`. Restart `netinstall-cli` and run `dhtest`
   agagin before downloading another image.

[Downloads page]: https://mikrotik.com/download
[Download Archive]: https://mikrotik.com/download/archive
