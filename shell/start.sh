#!/bin/sh

sudo service isc-dhcp-server restart
sudo service dnsmasq restart

python /home/pi/pyNetinstall/main.py
