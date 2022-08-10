# pyNetinstall

How to run a flash using the pyNetinstall

## What u need:
* [Raspberry Pi 3](https://www.raspberrypi.com/products/) or newer
* [Mikrotik Router Board](https://www.mikrotik-store.eu/en/MikroTik-CA150) or similar

## Getting started

### setup.sh

```shell
pi@raspberrypi:~$ chmod a+rx setup.sh
pi@raspberrypi:~$ ./setup.sh
```

### step by step
1. **Set up the Interface**
   * Check your IP-Address with the following command\
   `ip address`
2. **Set up the TFTP-Server**
   * Install [dnsmasq](https://wiki.archlinux.org/title/dnsmasq)\
   `sudo apt install dnsmasq`
   * Update the Configuration File -> `/etc/dnsmasq.conf`
   ```editorconfig
    ##/etc/dhcp/dhcpd.conf
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
3. **Set up the DHCP-Server** 
   * Install [isc-dhcp-server](https://www.isc.org/dhcp/)
   * Update the Configuration File -> `/etc/dhcp/dhcpd.conf`
    ```editorconfig
    ##/etc/dnsmasq.conf
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

4. **Clone this Repository to your Raspberry Pi**
   * Use [git](https://git-scm.com/docs/git-clone) commands to clone the Repository to your local device\
   `git clone https://github.com/dvtirol/pynetinstall`
5. **Update the ___config.ini___**

### Current Errors:
 * The board does not return the ACKY to acept the offer

### TODO
 * Implement other Plugins
 * Document the Project
 * Check if 255.255.255.255 or 10.192.3.255 is the Broadcast
    * Currently only 10.192.3.255 is able to send to the board
