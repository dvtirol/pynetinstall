#!/usr/bin/env python3

"""
Bearbeitet von Preissler Matthias, DVT
"""

import socket
import os
import sys
import fcntl
import struct
from time import sleep

def get_ip_and_mac(ifname:str)->tuple:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    arg = struct.pack('256s', bytes(ifname, 'utf-8')[:15])
    ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, arg)[20:24])
    hw = ''.join('%02x'%b for b in fcntl.ioctl(s.fileno(), 0x8927, arg)[18:24])
    s.close()
    return ip, hw # ioctls: 0x8915=SIOCGIFADDR, 0x8927=SIOCGIFHWADDR

class Converter():
    # Dezimalwert in Hexadezimalfolge
    def deCounterToHex(decimal:int)->str:
        oHex	= hex(decimal)[2:]
        oHex	= "0"*abs(4 - len(oHex)) + str(oHex)
        hPs	    = [oHex[index : index + 2] for index in range(0, len(oHex), 2)]
        oHex	= hPs[1] + hPs[0]
        return oHex

    # Hexerdezimalfolge in Dezimalfolge
    def hexCounterToDecimal(hexStr:str)->int:
        dPs = [hexStr[index : index + 2] for index in range(0, len(hexStr), 2)]
        return Converter.hexToDec(dPs[1]+dPs[0])

    # convertiert ein Array in einen Hexadezimalfolge
    def arrayToHex(array:tuple)->str:
        hexStr = ""
        for i in range(0, len(array)):
            if isinstance(array[i], int):
                hexd = hex(array[i]).replace('x','')
            else:
                hexd = hex(ord(array[i]))[2:]
            hexStr = hexStr + ("0"*(2-len(hexd))) + hexd
        return hexStr

    # convertiert Hexadezimalfolgen Binärfolge
    def hexToBin(hex_number:str)->bytes:
        return bytes.fromhex(hex_number)

    # convertiert Binärfolge in Hexadezimalfolge
    def binToHex(bin_row:bytes)->bytes:
        return bytes(bin_row.hex(), 'ascii')

    # Hexadezimalfolge in Dezimalwert
    def hexToDec(hexStr)->int:
        return int(hexStr,16)


# erstellt socket connection
class socketConn():
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", 5000))

    # funktion um daten über die socket connection an das gerät zu schreiben
    def socketWrite(self, data:bytes):
        #broadcast permission für den socket
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.sendto(data, ("255.255.255.255", 5000))

    # funktion um daten von dem routerboard zu empfangen und zu verarbeiten
    def socketRead(self, srcMac:str)->bytes:
        self.headsMac = None
        self.headdMac = None
        self.headsPos = None
        self.headdPos = None
        self.deviceMac = None

        while True:
            data = self.sock.recv(1024)
            hexData = Converter.binToHex(data)
            if hexData.startswith(srcMac.encode()):
                # der socket liesst auch die pakete die an den mikrotik gesendet werden darum
                # dropen wir beim lesen jedes packet welches vom raspi server versendet wird
                socketConn.socketRead(self, srcMac)
            else:
                self.headsMac = (hexData[0:12])
                self.headdMac = (hexData[12:24])
                self.headsPos = Converter.hexCounterToDecimal(hexData[32:36])
                self.headdPos = Converter.hexCounterToDecimal(hexData[36:40])

                return hexData

def getDeviceInfo(sock, srcMac:str)->str:
    while True:
        try:
            data = sock.socketRead(srcMac)
            print("Device Found")
            infoData = bytes.fromhex(data[40:].decode()).decode("ASCII")
            rows = infoData.split("\n")
            if (len(rows) == 7):
                macAddr = data[0:12].decode()
                if ((macAddr in rows) == False):
                    rb_model = ""
                    rb_arch = ""
                    rb_minOS = ""
                    lic_key = ""
                    lic_id = ""
                    
                    if (rows[1] != b""):
                        lic_id = rows[1]
                    if (rows[2] != b""):
                        lic_key = rows[2]
                    
                    rb_model = rows[3]
                    rb_arch = rows[4]
                    rb_minOS = rows[5]

                    print("model:", rb_model)
                    print("arch:", rb_arch)
                    print("min os:", rb_minOS)
                    print("device mac:", macAddr)
                    print("lic key:", lic_key)
                    print("lic id:", lic_id)
                    return macAddr
                else:
                    break
            else:
                raise Exception("Discovery Error: No data found")
        except Exception as e:
            exc_type, exc_object, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, "-", fname, "on line", exc_tb.tb_lineno)
            break

# funktion um daten zu schreiben
def flashWrite(sock, srcMac:str, dmac:str, srcPos:int, dstPos:int, hexData:str):
    data = srcMac+dmac+"0000"+Converter.deCounterToHex(len(Converter.hexToBin(hexData)))+\
           Converter.deCounterToHex(srcPos)+Converter.deCounterToHex(dstPos)+hexData
    return sock.socketWrite(Converter.hexToBin(data))

# funktion welchem dem routerboard zeit gibt die daten zu schreiben
# und antworten vom Routerboard verarbeitet welche von socketRead() kommen
def flashWait(sock, srcMac:str, dmac:str, srcPos:int, dstPos:int):
    while True:
        try:
            recvData = sock.socketRead(srcMac)
            recvData = recvData[40:]
            if ((sock.headsMac).decode() == dmac) and ((sock.headdMac).decode() == srcMac or (sock.headdMac).decode() == "000000000000"):
                lastData = recvData
                if (sock.headdPos == srcPos and sock.headsPos == dstPos):
                    return recvData
                else:
                    raise Exception("Position Error: Positions not matching")
            else:
                raise Exception("MAC Error: MACs not equal")
        except Exception as e:
            exc_type, exc_object, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, "-", fname, "on line", exc_tb.tb_lineno)
            break

def flashOffer(srcMac:str, dstMac:str, srcPos:int, dstPos:int):
    try:
        srcPos+=1
        command = ["O", "F", "F", "R", 10, 10]
        data = Converter.arrayToHex(command)
        flashWrite(sock, srcMac, dstMac, srcPos, dstPos, data)

        dstPos+=1
        resp = flashWait(sock, srcMac, dstMac, srcPos, dstPos)

        command = ["Y", "A", "C", "K", 10]
        okResp = Converter.arrayToHex(command)

        # check
        if (okResp == ((sock.socketRead(srcMac)).decode())[40:]):
            print("OFFR DONE")
            return srcPos, dstPos, None
        else:
            return srcPos, dstPos, Exception("Flash Error: Invalid Offer ACK")
    except Exception as e:
        exc_type, exc_object, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, "-", fname, "on line", exc_tb.tb_lineno)

def flashFormat(srcMac:str, dstMac:str, srcPos:int, dstPos:int):
    try:
        srcPos+=1
        data = ""
        flashWrite(sock, srcMac, dstMac, srcPos, dstPos, data)
        
        dstPos+=1
        resp = flashWait(sock, srcMac, dmac, srcPos, dstPos)
        command = ["S", "T", "R", "T"]
        okResp = Converter.arrayToHex(command)

        # check
        if (okResp == (sock.socketRead(srcMac)).decode()[40:]):
            print("FORMAT DONE")
            return srcPos, dstPos, None
        else:
            return srcPos, dstPos, Exception("Flash Error: Invalid Format Start return")
    except Exception as e:
        exc_type, exc_object, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, "-", fname, "on line", exc_tb.tb_lineno)

def flashSpacer(srcMac:str, dstMac:str, srcPos:int, dstPos:int):
    try:
        srcPos+=1
        command = ["R", "E", "T", "R"]
        data = ""
        flashWrite(sock, srcMac, dstMac, srcPos, dstPos, data)
        dstPos = dstPos+1
        resp = flashWait(sock, srcMac, dmac, srcPos, dstPos)
        okResp = Converter.arrayToHex(command)

        # check
        if (okResp == ((sock.socketRead(srcMac)).decode())[40:]):
            print("SPACER DONE")
            return srcPos, dstPos, None
        else:
            return srcPos, dstPos, Exception("Flash Error: Invalid Spacer Return")
    except Exception as e:
        exc_type, exc_object, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, "-", fname, "on line", exc_tb.tb_lineno)

def flashFileHeader(srcMac:str, dstMac:str, srcPos:int, dstPos:int, fw:str, fileName:str=None):
    if fileName == None:
        fileName = os.path.basename(fw)

    try:
        srcPos+=1
        command = ["F", "I", "L", "E", 10] + list(fileName) + [10] + list(str(os.stat(fw).st_size)) + [10]
        data = Converter.arrayToHex(command)
        flashWrite(sock, srcMac, dmac, srcPos, dstPos, data)

        dstPos+=1
        resp = flashWait(sock, srcMac, dmac, srcPos, dstPos)

        command = ["R", "E", "T", "R"]
        okResp = Converter.arrayToHex(command)

        # check
        if (okResp == ((sock.socketRead(srcMac)).decode())[40:]):
            print("FILE HEADER DONE")
            return srcPos, dstPos, None
        else:
            return srcPos, dstPos, Exception("Flash Error: Invalid File Header Return")
    except Exception as e:
        exc_type, exc_object, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, "-", fname, "on line", exc_tb.tb_lineno)

def flashFile(srcMac:str, dstMac:str, srcPos:int, dstPos:int, fw:str, maxBytes:int):
    filePos = 0
    maxPos = os.stat(fw).st_size
    with open(fw, "rb") as file:
      while True:
        srcPos+=1
        command = file.read(maxBytes)
        data = Converter.binToHex(command)
        flashWrite(sock, srcMac, dstMac, srcPos, dstPos, data.decode())

        dstPos+=1
        filePos = filePos + len(command)
        if (filePos >= maxPos):
            try:
                resp = flashWait(sock, srcMac, dmac, srcPos, dstPos)
                command = ["R", "E", "T", "R"]
                okResp = Converter.arrayToHex(command)

                # check
                if (okResp == ((sock.socketRead(srcMac)).decode())[40:]):
                    print("FILE DONE")
                    return srcPos, dstPos, None
                else:
                    return srcPos, dstPos, Exception("Flash Error: Invalid File Return")
            except Exception as e:
                exc_type, exc_object, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, "-", fname, "on line", exc_tb.tb_lineno)
                break
        else:
            # dieses sleep ist der hauptgrund wieso das file so lange zum
            # flashen braucht. je niedrieger desto schneller 
            # kann zu position errors durch timing issues fuehren
            sleep(35/10000)

def flashComplete(srcMac:str, dstMac:str, srcPos:int, dstPos:int):
    try:
        srcPos+=1
        command = ["F", "I", "L", "E", 10]
        data = Converter.arrayToHex(command)
        flashWrite(sock, srcMac, dmac, srcPos, dstPos, data)

        dstPos+=1
        resp = flashWait(sock, srcMac, dmac, srcPos, dstPos)

        command = ["W", "T", "R", "M"]
        okResp = Converter.arrayToHex(command)

        # check
        if (okResp == ((sock.socketRead(srcMac)).decode())[40:]):
            print("FLASH COMPLETED")
            return srcPos, dstPos, None
        else:
            return srcPos, dstPos, Exception("Flash Error: Invalid Terminator Return")
    except Exception as e:
        exc_type, exc_object, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, "-", fname, "on line", exc_tb.tb_lineno)

def flashReboot(srcMac:str, dstMac:str, srcPos:int, dstPos:int):
    try:
        srcPos+=1
        command = ["T", "E", "R", "M", 10] + list("Installation successful") + [10]
        data = Converter.arrayToHex(command)
        flashWrite(sock, srcMac, dmac, srcPos, dstPos, data)

        dstPos+=1
        return
    except Exception as e:
        exc_type, exc_object, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, "-", fname, "on line", exc_tb.tb_lineno)


# führt den flash prozess aus
def runflash(sock, srcMac:str, dstMac:str, fw:str, conf:str):
    maxBytes    = 1024

    try:
        srcPos = 0
        dstPos = 0

        srcPos, dstPos, e = flashOffer(srcMac, dstMac, srcPos, dstPos)
        srcPos, dstPos, e = flashFormat(srcMac, dstMac, srcPos, dstPos)
        srcPos, dstPos, e = flashSpacer(srcMac, dstMac, srcPos, dstPos)
        srcPos, dstPos, e = flashFileHeader(srcMac, dstMac, srcPos, dstPos, fw)
        srcPos, dstPos, e = flashFile(srcMac, dstMac, srcPos, dstPos, fw, maxBytes)
        
        srcPos, dstPos, e = flashSpacer(srcMac, dstMac, srcPos, dstPos)
        srcPos, dstPos, e = flashFileHeader(srcMac, dstMac, srcPos, dstPos, conf, "autorun.scr")
        srcPos, dstPos, e = flashFile(srcMac, dstMac, srcPos, dstPos, conf, maxBytes)
    
        srcPos, dstPos, e = flashSpacer(srcMac, dstMac, srcPos, dstPos)
        srcPos, dstPos, e = flashComplete(srcMac, dstMac, srcPos, dstPos)
        flashReboot(srcMac, dstMac, srcPos, dstPos)
        
    except Exception as e:
        exc_type, exc_object, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, "-", fname, "on line", exc_tb.tb_lineno)
    

# startpunkt des programmes
# check ob flash file und config übergeben wurden
if (len(sys.argv) != 3):
    print("Usage: flash.py /PATH/TO/ROUTEROS-FILE.npk /PATH/TO/CONFIG-FILE.rsc")
    sys.exit()

if (sys.argv[1].endswith('.npk')):
    fwPath = sys.argv[1]
else:
    print("Usage: flash.py /PATH/TO/ROUTEROS-FILE.npk /PATH/TO/CONFIG-FILE.rsc")
    sys.exit()

if (sys.argv[2].endswith(".rsc")):
    confPath = sys.argv[2]
else:
    print("Usage: flash.py /PATH/TO/ROUTEROS-FILE.npk /PATH/TO/CONFIG-FILE.rsc")
    sys.exit()

# check ob files gefunden werden
if not os.path.exists(fwPath):
    print("Firmware not found...")
    sys.exit(1)
elif not os.path.exists(confPath):
    print("Configuration not found...")
    sys.exit(1)

# ip und mac von dhcp/tftp server
ip, smac = get_ip_and_mac("eth0")
print("Server IP Address:", ip)
print("Server MAC Address:", smac)

# mac von routerboard wird automatisch gesucht
dmac = ""

# starte flash prozess
print("\nLooking for Devices...")
sock = socketConn()
dmac = getDeviceInfo(sock, smac)
print("\nStart flashing...")
runflash(sock, smac, dmac, fwPath, confPath)
