#!/bin/sh

echo "Setting up Python Netinstall"

echo "\nPlease connect the Raspberry to the Internet\n[Enter] When connected"
read Internet

echo "Install the missing packages"

sudo apt install isc-dhcp-server dnsmasq -y -q

sudo service isc-dhcp-server stop
sudo service dnsmasq stop

echo "\nCopying Configuration Files"

sudo cp configs/dhcpd.conf /etc/dhcp/dhcpd.conf
sudo cp configs/dnsmasq.conf /etc/dnsmasq.conf

echo "\n\nPlease connect the Raspberry to the Routerboard and disconnect it from the Internet\n[Enter] When connected"
read disconnect

echo "Add IP Addresses to eth0"

sudo ip addr add 10.192.3.1/24 dev eth0
sudo ip addr add 10.192.3.151/24 dev eth0
echo "\nStart the Services"

sudo service isc-dhcp-server start
sudo service dnsmasq start

python main.py
