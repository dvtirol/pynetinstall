#!/bin/sh

sudo systemctl restart isc-dhcp-server
sudo systemctl restart dnsmasq

python /home/pi/pyNetinstall/main.py
