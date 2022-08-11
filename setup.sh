#!/bin/sh

echo "Check if the required Services are installed"
if systemctl status isc-dhcp-server | grep "not-found\|could not be found" &> /dev/null ; then
    echo "Installing the DHCP-Server..."
    sudo apt-get -y install isc-dhcp-server
else
    echo "DHCP-Server is already installed!"
if systemctl status dnsmasq | grep "not-found\|could not be found" &> /dev/null ; then
    echo "Installing the TFTP-Server..."
    sudo apt-get -y install dnsmasq
else
    echo "TFTP-Server is already installed!"

sudo cp /home/pi/pyNetinstall/configs/dhcpd.conf /etc/dhcp/dhcpd.conf
sudo cp /home/pi/pyNetinstall/configs/dnsmasq.conf /etc/dnsmasq.conf