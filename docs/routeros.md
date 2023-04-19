# pyNetinstall on RouterOS

## Build pyNetinstall Container

The following Dockerfile placed in the root of this repository suffices.

```
FROM alpine:3

RUN apk update && apk add python3
COPY pynetinstall /pynetinstall

VOLUME /config
ENTRYPOINT /usr/bin/python3 -m pynetinstall -c /config/pynetinstall.ini -v
```

It can be built using podman and buildah like so:

```
export arch=arm # or arm64, amd64, ...
buildah build --arch=${arch} --format docker --tag pynetinstall-${arch} .
podman save pynetinstall-${arch} > pynetinstall-${arch}.tar
```

The resulting `.tar` file can be uploaded to the RouterBoard.

## Extract Boot Images

Refer to the [Extracting Boot Images] section of the README, then upload them
to the RouterBoard.

[Extracting Boot Images]: ../README.md#extracting-boot-images

## Prepare Firmware, Default Config and .ini

Using winbox or [this hack], create a directory that will be mounted in the
container. It will contain the firmware to flash on other devices, the config
to install on other devices and the configuration file for pyNetinstall (named
as specified in the `-c` flag in the Dockerfile).

[this hack]: https://forum.mikrotik.com/viewtopic.php?t=102769#p989260

Download the RouterOS firmware to install with pyNetinstall from Mikrotik.com
and upload them to the RouterBoard. These must be placed in a subdirectory,
otherwise RouterOS will attempt to update itself from these images and delete
them.

Place the default config to install on flashed devices in this directory as
well. This default config can also be a complex script that e.g. downloads a
different config from a remote server, downloads packages, etc.

Create `pynetinstall.ini` and upload it to the subdirectory. See the section
[Using the default plugin], or [Providing a custom plugin].

[Using the default plugin]: ../README.md#using-the-default-plugin
[Providing a custom plugin]: ../README.md#providing-a-custom-plugin


## Configure a Virtual Interface and Bridge

The virtual ethernet interface will be assigned to the container, and bridged
to at least one physical port on which RouterBoards can be connected for
flashing. The subnet in the example below was chosen at random.

```
/interface bridge
add name=bridgeNetinstall
/interface veth
add address=192.168.30.2/24 gateway=192.168.30.1 name=vethNetinstall
/ip address
add address=192.168.30.1/24 interface=bridgeNetinstall network=192.168.30.0
/interface bridge port
add bridge=bridgeNetinstall interface=ether2
add bridge=bridgeNetinstall interface=vethNetinstall
```

## Configure TFTP and DHCP

Enable the TFTP server and enable downloading the boot files with the following
config. Any number of them can be specified, but note that the default plugin
can only serve firmware for one architecture.

```
/ip tftp
add real-filename=/arm_boot req-filename=arm_boot
add real-filename=/arm64_boot req-filename=arm64_boot
```

When a connected RouterBoard boots from Ethernet, it will send its CPU
architecture in DHCP option 60. Based on this we can select a different IP
range, and based on the IP range we can set which boot image should be loaded
over TFTP. A list of code60 values can be found in the README section
[Extracting Boot Images].

```
/ip pool
add name=poolNetinstall ranges=192.168.30.10-192.168.30.150
add name=poolNetinstallARM ranges=192.168.30.209-192.168.30.214
add name=poolNetinstallARM64 ranges=192.168.30.249-192.168.30.254

/ip dhcp-server
add address-pool=poolNetinstall bootp-support=dynamic interface=bridgeNetinstall lease-time=1h name=dhcpNetinstall

/ip dhcp-server matcher
add address-pool=poolNetinstallARM code=60 name=matcherARM server=dhcpNetinstall value=ARM__boot
add address-pool=poolNetinstallARM64 code=60 name=matcherARM64 server=dhcpNetinstall value=ARM64__boot

/ip dhcp-server network
add address=192.168.30.0/24 gateway=192.168.30.1
add address=192.168.30.208/29 boot-file-name=arm_boot gateway=192.168.30.1 next-server=192.168.30.1
add address=192.168.30.248/29 boot-file-name=arm64_boot gateway=192.168.30.1 next-server=192.168.30.1
```

## Install the Container

Add a mount to the configuration subdirectory (`netinstall`) at `/config` in
the container (as specified in Dockerfile), then create the container from the
`.tar` archive and start it.

```
/container mounts
add dst=/config name=pynetinstall-config src=/netinstall
/container
add interface=vethDocker logging=yes start-on-boot=yes mounts=pynetinstall-config file=pynetinstall-arm.tar
start 0
```

If `logging=yes` the output of pyNetinstall will be pushed into `/log print`;
if everything is working, it should print `Waiting for devices...` and a
RouterBoard can be connected. While plugging in power, press and hold the reset
button for 15 seconds to make the device boot from ethernet and begin flashing.

Below is a sample log of a successful operation.

```
[INFO ] -> Device found! mac=aa:aa:aa:aa:aa:aa, model=RB5009UG+S+, arch=arm64
[INFO ] -> Formatting aa:aa:aa:aa:aa:aa ...
[INFO ] -> Uploading routeros-arm64-7.8.npk
[INFO ] ->     routeros-arm64-7.8.npk: 10%
[INFO ] ->     routeros-arm64-7.8.npk: 20%
[INFO ] ->     routeros-arm64-7.8.npk: 30%
[INFO ] ->     routeros-arm64-7.8.npk: 40%
[INFO ] ->     routeros-arm64-7.8.npk: 50%
[INFO ] ->     routeros-arm64-7.8.npk: 60%
[INFO ] ->     routeros-arm64-7.8.npk: 70%
[INFO ] ->     routeros-arm64-7.8.npk: 80%
[INFO ] ->     routeros-arm64-7.8.npk: 90%
[INFO ] ->     routeros-arm64-7.8.npk: 100%
[INFO ] -> Uploading config.rsc
[INFO ] -> aa:aa:aa:aa:aa:aa was successfully flashed.
```
