# Dokumentation von MikroTik Netinstall auf dem Rapberry Pi

## Notwendige Dienste am Raspberry:
* dnsmasq für TFTP-Server
* isc-dhcp-server

## Config am Raspberry Pi
Die Configs der zwei Dienste sind unter der annahme entstanden, dass die IP-Addresse
vom Raspberry `10.192.3.1` lautet. Um diese zu configurieren kann man den command 
`sudo ip addr add 10.192.3.1/24 dev eth0` verwenden, jedoch ist diese dann nur
temporär und ist beim nächsten neustart vom Raspi wieder weg und muss neu 
hinterlegt werden. Man kann diese auch statisch Anlegen in dem man die config in
das File `/etc/network/interfaces` schreibt. Dies könnte dann wie folgt aussehen:

    # Ethernet
    auto eth0
    allow-hotplug eth0
    iface eth0 inet static
    address 10.192.3.1
    netmask 255.255.255.0
    gateway 10.192.3.1
    dns-nameservers 10.192.3.2

## Logfile und Configfile
Die Logfiles für den Dienst `dnsmasq` befinden sich in `/var/log/dnsmasq.log` und 
für `isc.dhcp-server` können mit dem Befehl `journalctl -u isc-dhcp-server`
ausgelesen werden.

Die Configfile finden sich unter `/etc/dnsmasq.conf` für `dnsmasq` bzw. unter
`/etc/dhcp/dhcpd.conf` für `isc-dhcp-server`. Der DHCP erkennt automatisch welchen Kernel 
bereitzustellen ist anhand des `vendor-class-identifier`. In der Config müssen folgene Parameter angepasst werden:
* `next-server`
* `interfaces`
* `subnet netmask`
* `domain-name-server`
* `router`
* `broadcast-address`
* `range dynamic-bootp`
* und `pool range`

`isc-dhcp-server` Config:

    ddns-update-style interim;
    default-lease-time 300;
    max-lease-time 600;
    authoritative;
    allow booting;
    allow bootp;
    ##tftp server is located on the edge provisioning device
    next-server 10.192.3.1;
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

    subnet 10.192.3.0 netmask 255.255.255.0 {

            option domain-name-servers 10.192.1.2, 10.192.1.3;
            option routers 10.192.3.1;
            option broadcast-address 10.192.3.255;
            pool {
                    allow dynamic bootp clients;
                    allow members of "mmipsBoot";
                    allow members of "armBoot";
                    allow members of "Mips_boot";
                    range dynamic-bootp 10.192.3.51 10.192.3.150;

                    if substring(option vendor-class-identifier, 0, 9) = "MMipsBoot" {
                        filename "mmips_boot_6.42.5";
                    } elsif substring(option vendor-class-identifier, 0, 9) = "ARM__boot" {
                        filename "arm_boot_6.42.5";
                    } elsif substring(option vendor-class-identifier, 0, 9) = "Mips_boot" {
                        filename "Mips_boot_netinstall_6.48";
                    }
            }
            pool {
                    range 10.192.3.151 10.192.3.250;
            }
    }

`dnsmasq` Config:

Diese Zeilen am Ende vom File einfügen:

	enable-tftp
	tftp-root=/var/lib/misc/
	tftp-no-blocksize
	interface=eth0
	log-facility=/var/log/dnsmasq.log

**Wichtig:** Die Kernel Files für den MikroTik müssen im `tftp-root` Ordner liegen, 
ansosnten kann der DHCP Server finden. Standartmässig ist der der Root Ordner in 
`/var/lib/misc` zu finden.

## Mikrotik flashen
Zum flashen von einem Gerät werden keine Root Rechte benötigt, man muss die python 
Datei `flash.py` lediglich wie folget ausführen:
`python flash.py /PATH/TO/FLASH-FILE.npk /PATH/TO/CONFIG-FILE.rsc`

**Wichtig:** das Programm prüft die Dateiendungen und müssen deshalb genau
wie oben angegeben werden.

Das Programm sucht sich die IP Addresse und MAC Addresse vom Server als auch
die vom Miktotik selbständig. Der MikroTik muss im netinstall Modus sein damit 
dies funktioniert.

## Bekannte Fehler (Stand 04.08.2022)
### MikoTik Bootloader Error UDP1:
Wenn dieser Fehler meist auf wenn der TFTP Server neu gestartet wird.
Zum lösen des Problemes sind folgende Schritte zu tätigen:

* Beim Booten vom Mirkotik das Bootprotokoll unter dem Punkt 
 `p - boot protocol` auf `2 - dhcp protocol` umstellen
* Dannach versuchen über DHCP den netinstall auszuführen, dieser wird fehlschlagen
* Beim erneuten booten das Bootprotokoll wieder auf `1 - bootp protocol` zurückstellen
