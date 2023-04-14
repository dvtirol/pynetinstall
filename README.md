# pyNetinstall

Free and Open Source netInstall implementation for Flashing Mikrotik RouterBoards


## Introduction

pyNetinstall is meant as a component of a zero-touch deployment system. Using it
one can configure RouterBoards en masse easily. The plug-in system allows
interfacing pyNetinstall with existing data center infrastructure management
systems, uploading individual firmware and configuration per device based on MAC
address, model type and serial number.

Unlike the official tooling, pyNetinstall does not include DHCP and TFTP
servers; these services should be handled by `dnsmasq`.

## Usage

`python -m pynetinstall [-c CONFIG] [-i INTERFACE] [-v]`

*-c CONFIG*: Path to the configuration file. Defaults to `/etc/pynetinstall.ini`.  
*-i INTERFACE*: Ethernet interface to listen on. Defaults to `eth0`.  
*-l LOGGING*: [Python logging configuration]. Defaults to stderr.  
*-1*: Enable one-shot mode (exit after flashing once).  
*-v*: Increase verbosity. Default is errors and warnings.  
*-h*: Display help and exit.

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

## Setup dnsmasq

Setup `dnsmasq` to provide DHCP and TFTP, so your RouterBoard can boot via
BOOTP. Boot images can be obtained either by [extracting them from
`netinstall.exe`], or alternatively, some can be downloaded from the
unaffiliated [merlinthemagic/MTM-Mikrotik] repo.

[merlinthemagic/MTM-Mikrotik]: https://github.com/merlinthemagic/MTM-Mikrotik/tree/master/Docs/Examples/TFTP-Images
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
`pynetinstall.ini`. To disable uploading the config file, just remove the line
from `pynetinstall.ini`.

```
[pynetinstall]
firmware=<PATH_TO_ROUTEROS_NPK>
config=<PATH_TO_CONFIG_RSC>
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
is fairly easy to extract them from the Mikrotik's Netinstall tool. This guide
describes the Linux CLI version, but the same techniques should work on the
Windows GUI version as well.

1. **Download `netinstall-<version>.tar.gz`**  
   The latest version that is linked in the [Downloads page] General section
   should work fine for all RouterOS versions. The [Download Archive] has links
   to older versions. <!-- for rOS 6.x no links are given, but the URLs follow
   the same schema as for 7.x -->

2. **Start `netinstall-cli`**  
   `sudo ./netinstall-cli -a 127.0.0.2 netinstall-cli`  

3. **Install `dhtest`**  
   For Fedora, openSuse and RHEL packages are in the default repositories. On
   Debian or Ubuntu download the [dhtest sources] and compile them with `make`.

4. **Run `dhtest`**  
   `sudo dhtest -T 5 -o ARM64__boot -i lo`  
   This will set up extraction of the arm64/aarch64 image. Other valid options
   are `Mips_boot`, `MMipsBoot`, `Powerboot`, `e500_boot`, `e500sboot`,
   `440__boot`, `tile_boot`, `ARM__boot` and `ARM64__boot`.
   <!-- Note: e500_boot and e500sboot seem to return the same file. -->

5. **Download the image**  
   `curl tftp://127.0.0.1/linux.arm > netinstall.arm64`  
   The filename is always `linux.arm`. Restart `netinstall-cli` and run `dhtest`
   agagin before downloading another image.

[Downloads page]: https://mikrotik.com/download
[Download Archive]: https://mikrotik.com/download/archive
[dhtest sources]: https://github.com/saravana815/dhtest

## Acknowledgements

This project is based on the wonderful reverse engineering work of
[merlinthemagic].

[merlinthemagic]: https://github.com/merlinthemagic/MTM-Mikrotik/tree/master/Src/Tools/NetInstall
