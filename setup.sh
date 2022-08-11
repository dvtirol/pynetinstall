#!/bin/sh


if lsmod | grep "isc-dhcp-server" &> /dev/null ; then
    pass
else
    sudo systemctl restart isc-dhcp-server
if lsmod | grep "isc-dhcp-server" &> /dev/null ; then
    pass
else
    sudo systemctl restart dnsmasq