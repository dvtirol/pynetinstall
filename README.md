pyNetinstall
===============

Running a netinstall on a Mikrotik Router Board using a Raspberry Pi and Python

-----------

## What u need:
* [Raspberry Pi 3](https://www.raspberrypi.com/products/) or newer
* [Mikrotik Router Board](https://www.mikrotik-store.eu/en/MikroTik-CA150) or similar


## Quick start
```shell
pi@raspberrypi:~$ git clone https://github.com/dvtirol/pynetinstall
pi@raspberrypi:~$ chmod a+rx setup.sh
pi@raspberrypi:~$ ./setup.sh

```

------------

## Step by Step

1. **Set up the Interface**
   * Update the interfaces File -> `sudo nano /etc/network.interfaces`
```
auto eth0
allow-hotplug eth0
iface eht0 inet static
address 10.192.3.1
netmask 255.255.255.0
gateway 10.192.3.1
dns-nameservers 10.192.3.2
```
   * Check if the IP Address is configured using this command
   `ip addr`
   	If the Address `10.192.3.1` is displayed in the eth0 section you are ready to go

------------

2. **Set up the TFTP-Server**
   * Install [dnsmasq](https://wiki.archlinux.org/title/dnsmasq)\
   `sudo apt install dnsmasq`
   * Update the Configuration File -> `sudo nano /etc/dnsmasq.conf`
```
##/etc/dnsmasq.conf
enable-tftp
tftp-root=/var/lib/misc/
tftp-no-blocksize
interface=eth0
log-facility=/var/log/dnsmasq.log
```
   Add these lines to the end of the file

   * Start the service\
   `sudo systemctl start dnsmasq`
   * Check if the service is running\
   `sudo systemctl status dnsmasq`\
   If you can see a **RUNNING** the service successfully started

------------

3. **Set up the DHCP-Server**
   * Install [isc-dhcp-server](https://www.isc.org/dhcp/)\
   `sudo apt install isc-dhcp-server`
   * Update the Configuration File -> `sudo nano /etc/dhcp/dhcpd.conf`
    **Make sure that you replace the <> with your Configuration**
```
##/etc/dhcp/dhcpd.conf
ddns-update-style interim;
default-lease-time 300;
max-lease-time 600;
authoritative;
allow booting;
allow bootp;
##tftp server is located on the edge provisioning device
next-server <YOUR IP-ADDRESS>;
interfaces="eth0";
class "mmipsBoot" {
        match if substring(option vendor-class-identifier, 0, 9) = "MMipsBoot";
}
class "armBoot" {
        match if substring(option vendor-class-identifier, 0, 9) = "ARM__boot";
}
class "Mips_boot" {
        match if substring(option vendor-class-identifier, 0, 9) = "Mips_boot";
}
subnet <YOUR SUBNET> netmask <YOUR NETMASK> {
        option domain-name-servers <DNS-SERVER IP-ADDRESS>, <DNS-SERVER IP-ADDRESS>;
        option routers <ROUTER IP-ADDRESS>;
        option broadcast-address <BROADCAST IP-ADDRESS>;
        pool {
                allow dynamic bootp clients;
                allow members of "mmipsBoot";
                allow members of "armBoot";
                allow members of "Mips_boot";
                range dynamic-bootp <START-ADDRESS DYNAMIC-BOOTP> <END-ADDRESS DYNAMIC-BOOTP>;

                if substring(option vendor-class-identifier, 0, 9) = "MMipsBoot" {
                    filename "mmips_boot_6.42.5";
                } elsif substring(option vendor-class-identifier, 0, 9) = "ARM__boot" {
                    filename "arm_boot_6.42.5";
                } elsif substring(option vendor-class-identifier, 0, 9) = "Mips_boot" {
                    filename "Mips_boot_netinstall_6.48";
                }
        }
        pool {
                range <START-ADDRESS POOL> <END-ADDRESS POOL>;
        }
}
```

   * Start the service\
   `sudo systemctl start isc-dhcp-server`
   * Check if the service is running\
   `sudo systemctl status isc-dhcp-server`

------------

4. **Install the python library**
   * Use [pip](https://pypi.org/) to install the Library\
   `pip install pynetinstall`

------------

5. **Update the ___config.ini___**
```
[pynetinstall]
firmware=<PATH_TO_ROUTER_OS>
config=<PATH_TO_CONFIGURATION_FILE>
plugin=<PATH_TO_PLUGIN>
```

------------

6. **Create a ___mail.py___ file**
```python
from pynetinstall import FlashInterface
fl_int = FlashInterface()
fl_int.flash_until_stopped()
```

7. **Start the Routerboard using [Etherboot](https://wiki.mikrotik.com/wiki/Manual:Etherboot)**
When you see the line (in the CLI of the Routerboard):
`Waiting for installation Server...`

	You can start the program
`python -m pynetinstall`


## Logging

This module implements the Python Standard [logging](https://docs.python.org/3/library/logging.html) module to keep track on errors and other information during the program runtime.

There are 4 different Loggers:

|  Name  |  Qualname  |  Level  |  File  |
| ------------ | ------------ | ------------ | ------------ |
|  Debug Logger  |  pynet-deb  |  10  |  *logs/pynetdebug.log*  |
|  Step Logger  |  pynet-stp  |  15  |  *logs/pynetsteps.log*  |
|  Info Logger  |  pynet-inf  |  20  |  *logs/pynetinfo.log*  |
|  Error Logger  |  pynet-err  |  40  |  *logs/pyneterror.log*  |


To change what logs should be made you are able to use the **update_level()** function of the Logger. Or you insert an valid Level to the level Argument when initializing a new **FlashInterface**.
