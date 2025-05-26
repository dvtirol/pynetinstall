# pyNetinstall

Free and Open Source netInstall implementation for Flashing Mikrotik RouterBoards


## Introduction

pyNetinstall is meant as a component of a zero-touch deployment system. Using it
one can configure RouterBoards en masse easily. The plug-in system allows
interfacing pyNetinstall with existing data center infrastructure management
systems, uploading individual firmware and configuration per device based on MAC
address, model type and serial number.

It is possible to run pyNetinstall in a Container on a Routerboard itself,
providing a self-contained, (nearly) zero-touch deployment station.

Unlike the official tooling, pyNetinstall does not include DHCP and TFTP
servers; these services should be handled by e.g. `dnsmasq` or the one included
with RouterOS.

## Usage

`python -m pynetinstall [-c CONFIG] [-i INTERFACE] [-v]`

*-c CONFIG*: Path to the configuration file. Defaults to `/etc/pynetinstall.ini`.  
*-i INTERFACE*: MAC address or name of network interface. Defaults to `eth0`.  
*-l LOGGING*: [Python logging configuration]. Defaults to stderr.  
*-1*: Enable one-shot mode (exit after flashing once).  
*-v*: Increase verbosity. Default is errors and warnings.  
*-h*: Display help and exit.

Inferring the MAC address though the interface name is only supported on Linux.
When run on other operating systems, `-i MAC_ADDRESS` must be provided.

[Python logging configuration]: https://docs.python.org/3/library/logging.config.html#logging-config-fileformat

## Theory of Operation

Mikrotik provides a special boot image (embedded in the netinstall tools) that
will flash a RouterOS firmware and configuration file on the device. The
firmware and configuration is transmitted over a proprietary UDP based protocol,
which pyNetinstall implements.

The netinstall protocol provides some device information, including model and
serial numbers. By implementing a simple python module, these can be used as
parameters to dynamically select firmware and configuration, or directly stream
them from HTTP.

The boot image itself is loaded by the RouterBOOT bootloader using BOOTP/DHCP
and TFTP. Usually, RouterBoards can be set to boot from network once by pressing
reset for 15 seconds while powering on.

## Deploy on Mikrotik

By building a small [container] and setting up [DHCP] and [TFTP], pyNetinstall
can be deployed directly on another RouterBoard running RouterOS 7.4 or higher.

This process is a relatively involved; see [pyNetinstall on RouterOS] for an
example.

[container]: https://help.mikrotik.com/docs/display/ROS/Container
[DHCP]: https://help.mikrotik.com/docs/display/ROS/DHCP#DHCP-DHCPServer
[TFTP]: https://help.mikrotik.com/docs/display/ROS/TFTP
[pyNetinstall on RouterOS]: docs/routeros.md

## Deploy on Linux (dnsmasq)

Setup `dnsmasq` to provide DHCP and TFTP, so your RouterBoard can boot via
BOOTP. Boot images can be obtained either by [extracting them from
`netinstall.exe`], or alternatively, some can be downloaded from the
unaffiliated [rfdrake/MTM-Mikrotik] repo.

[rfdrake/MTM-Mikrotik]: https://github.com/rfdrake/MTM-Mikrotik/tree/master/Docs/Examples/TFTP-Images
[extracting them from `netinstall.exe`]: #extracting-boot-images

Below is a sample dnsmasq configuration. Depending on the CPU architecture of
your RouterBoard, a different boot file must be used. CPU architectures can be
differentiated through the vendor class identifier sent with the DHCP request.

```
interface=eth0

dhcp-range=10.0.0.101,10.0.0.200,10m
dhcp-boot=vendor:Mips_boot,netinstall.mips
dhcp-boot=vendor:MMipsBoot,netinstall.mmips
dhcp-boot=vendor:ARM__boot,netinstall.arm32
dhcp-boot=vendor:ARM64__boot,netinstall.arm64

enable-tftp
tftp-root=/var/ftpd
tftp-no-blocksize
```

## Using the default plugin

pyNetinstall includes a simple plugin that serves a single firmware and
optionally a single configuration file.

The default plugin reads the `firmware` and `config` parameters from
`pynetinstall.ini`. To disable uploading a config file and use MikroTik's
default config instead, just remove the line from `pynetinstall.ini`. To not
upload any config at all (and configure the device through MAC-Telnet/MAC-Winbox
manually afterwards), specify a config file containing a single newline char.
Additional packages can be specified one per line, each indented by some spaces.

```
[pynetinstall]
firmware=<PATH_TO_ROUTEROS_NPK>
config=<PATH_TO_CONFIG_RSC>
additional_packages=
    <ADDITIONAL_PACKAGE>
    <ADDITIONAL_PACKAGE>
    <ADDITIONAL_PACKAGE>
```

## Providing a custom plugin

By writing a small python module the served firmware and configuration file can
be varied at runtime, based on the device connected.

To load a custom plugin, the `plugin` parameter should be defined in
`pynetinstall.ini`. It expects the name of a Python module, a colon, and the
name of a class. The module will be searched for in Python's path ($PWD, $PATH
or $PYTHONPATH). The class is loaded once on startup and reused for each
flashing operation.

```
[pynetinstall]
plugin=<PYTHON_MODULE>:<CLASS_NAME>
# additional keys or sections defined by the plugin
```

Such a plugin is simply a python class that implements `get_files(info)`,
returning a tuple (firmware, config). Firmware and config may be returned as a
path on disk (string), an HTTP  or HTTPS URL (string), or a [file object] as
returned by e.g. `open()`.

Additionally, config may be `None` if no custom default configuration is
desired. If firmware is `None`, an error is assumed and the current flashing
process is aborted and pyNetinstall resets for the next flashing cycle.

`get_files()` is passed an InterfaceInfo object, which contains information on
the connected RouterBoard. The available attributes are described in the example
below.

Implementing `__init__(config)` is optional and only required if access
to `pynetinstall.ini` is needed through the passed [ConfigParser] object.
Exceptions raised during `__init__()` will result in pyNetinstall exiting.

[file object]: https://docs.python.org/3/glossary.html#term-file-object
[ConfigParser]: https://docs.python.org/3/library/configparser.html#configparser.ConfigParser

```
class Plugin:
    def __init__(self, config: ConfigParser):
        ...

    def get_files(self, info: InterfaceInfo):
        ...
        # info.mac.hex(':') = MAC address
        # info.model        = model name
        # info.arch         = CPU architecture
        # info.min_os       = oldest supported rOS version
        # info.lic_id       = installed license id
        # info.lic_key      = installed license key

        return firmware, configuration_or_None
```

## Extracting Boot Images

You will need to aquire the boot images that the official netinstall tool uses.
These are not included as they are not licensed for re-distribution. However, it
is fairly easy to extract them from the Mikrotik's Netinstall tool.

**Note**: You must use at least the netinstall version that a device was shipped
with. Check `/system routerboard print` -> `factory-firmware` if unsure.

1. **Download `netinstall-<version>.zip` for Windows and extract it**  
   The latest version that is linked in the [Downloads page] General section
   should work fine for all RouterOS versions. The [Download Archive] has links
   to older versions. <!-- for rOS 6.x no links are given, but the URLs follow
   the same schema as for 7.x. Both 32 and 64 bit versions should work. -->

2. **Install the `pefile` and `pyelftools` Python packages**  
   `pip install --user pefile pyelftools`  

3. **Extract the images**  
   `./docs/extract_bootimages.py netinstall64.exe`  
   This will extract all images into the current directory.

[Downloads page]: https://mikrotik.com/download
[Download Archive]: https://mikrotik.com/download/archive

## Acknowledgements

This project is based on the wonderful reverse engineering work of
[merlinthemagic].

[merlinthemagic]: https://github.com/merlinthemagic/MTM-Mikrotik/tree/master/Src/Tools/NetInstall

## License

Copyright 2022-2023 DVT - Daten-Verarbeitung Tirol GmbH. Made available under
the terms of the [GNU General Public License, version 3].

[GNU General Public License, version 3]: LICENSE
