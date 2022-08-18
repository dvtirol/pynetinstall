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
pi@raspberrypi:~$ cd pyNetinstall
pi@raspberrypi:~$ chmod a+rx shell/setup.sh
pi@raspberrypi:~$ ./shell/setup.sh
```

------------

## Step by Step

1. **Set up the Interface**
   * Check your IP-Address with the following command\
   `ip address`
------------
2. **Set up the TFTP-Server**
   * Install [dnsmasq](https://wiki.archlinux.org/title/dnsmasq)\
   `sudo apt install dnsmasq`
   * Update the Configuration File -> `/etc/dnsmasq.conf`
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
   * Install [isc-dhcp-server](https://www.isc.org/dhcp/)
   * Update the Configuration File -> `/etc/dhcp/dhcpd.conf`
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
from pynetinstall import Flasher
flasher = Flasher()
flasher.run()
```
7. **Start the Routerboard using [Etherboot](https://wiki.mikrotik.com/wiki/Manual:Etherboot)**
When you see the line (in the CLI of the Routerboard):
`Waiting for installation Server...`

	You can start the main.py
`python main.py`

**-----------------------------------------------------------------------------------------------------------------------------------------------------------**

###### Error that still exist and is not able to be fixed
	OSError [Errno 101] Network is unreachable
Start the start.sh file this should "fix" this error

