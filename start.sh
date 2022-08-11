#!/bin/sh

if systemctl status isc-dhcp-server | grep "failed"|"inactive" &> /dev/null ; then
    print("Started isc-dhcp-server!")
    sudo systemctl start isc-dhcp-server &> /dev/null
fi
if systemctl status dnsmasq | grep "failed"|"inactive" &> /dev/null ; then
    print("Started dnsmasq!")
    sudo systemctl start dnsmasq &> /dev/null
fi

python /home/pi/pyNetinstall/main.py
