# it is possible to run pyNetinstall on a RouterBoard running RouterOS7.4 in a Container. instead of setting up dnsmasq, here is a dhcp server configuration that can be adapted to be used instead. note that you will also need a tftp server (set as next-server) for providing boot files. at the end, there are some other useful options to set.
/interface bridge
add name=bridgeInstall
/interface veth
add address=192.168.30.2/24 gateway=192.168.30.1 name=vethContainer
/ip pool
add name=poolDhcpInstall ranges=192.168.30.10-192.168.30.150
add name=poolDhcpMikrotikARMInstall ranges=192.168.30.209-192.168.30.214
add name=poolDhcpMikrotikMMIPSInstall ranges=192.168.30.217-192.168.30.222
add name=poolDhcpMikrotikTILERAInstall ranges=192.168.30.225-192.168.30.230
add name=poolDhcpMikrotikPPCInstall ranges=192.168.30.233-192.168.30.238
add name=poolDhcpMikrotikMIPSInstall ranges=192.168.30.241-192.168.30.246
/ip dhcp-server
add address-pool=poolDhcpInstall bootp-support=dynamic interface=bridgeInstall lease-time=1h name=dhcpInstall
/interface bridge port
add bridge=bridgeInstall interface=ether2
add bridge=bridgeInstall interface=ether3
add bridge=bridgeInstall interface=ether4
add bridge=bridgeInstall interface=ether5
add bridge=bridgeInstall interface=vethContainer
/ip address
add address=192.168.30.1/24 interface=bridgeInstall network=192.168.30.0
/ip dhcp-server matcher
add address-pool=poolDhcpMikrotikMMIPSInstall code=60 name=MikrotikMMIPSInstall server=dhcpInstall value=MMipsBoot
add address-pool=poolDhcpMikrotikTILERAInstall code=60 name=MikrotikTILERAInstall server=dhcpInstall value=tile_boot
add address-pool=poolDhcpMikrotikPPCInstall code=60 name=MikrotikPPCInstall server=dhcpInstall value=e500_boot
add address-pool=poolDhcpMikrotikPPCInstall code=60 name=MikrotikPPC2Install server=dhcpInstall value=e500sboot
add address-pool=poolDhcpMikrotikMIPSInstall code=60 name=MikrotikMIPSInstall server=dhcpInstall value=Mips_boot
add address-pool=poolDhcpMikrotikARMInstall code=60 name=MikrotikARMInstall server=dhcpInstall value=ARM__boot
/ip dhcp-server network
add address=192.168.30.208/29 boot-file-name=arm_boot gateway=192.168.30.1 next-server=192.168.30.1
add address=192.168.30.216/29 boot-file-name=mmips_boot gateway=192.168.30.1 next-server=192.168.30.1
add address=192.168.30.224/29 boot-file-name=tilera_boot gateway=192.168.30.1 next-server=192.168.30.1
add address=192.168.30.232/29 boot-file-name=powerpc_boot gateway=192.168.30.1 next-server=192.168.30.1
add address=192.168.30.240/29 boot-file-name=mips_boot gateway=192.168.30.1 next-server=192.168.30.1


# disable getty on the serial port. this allows you to check the status of the to-be-flashed board from your flasher:
#/port set 0 name=serial0

# make your flasher get a dynamic IP itself:
#/ip dhcp-client add interface=ether1

# if you want the to-be-flashed board to be able to access the internet:
#/ip dns set allow-remote-requests=yes
#/ip firewall nat add action=masquerade chain=srcnat out-interface=ether1 src-address=192.168.30.0/24

