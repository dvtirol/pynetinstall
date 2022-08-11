#!/bin/sh

if systemctl status isc-dhcp-server | grep "failed\|inactive" &> /dev/null ; then
    sudo systemctl start isc-dhcp-server &> /dev/null
    echo "Started isc-dhcp-server!"
fi
if systemctl status dnsmasq | grep "failed\|inactive" &> /dev/null ; then
    sudo systemctl start dnsmasq &> /dev/null
    echo "Started dnsmasq!"
fi

python /home/pi/pyNetinstall/main.py
