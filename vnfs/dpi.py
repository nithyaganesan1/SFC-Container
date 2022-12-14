from curses import flash
from pydoc import describe
from urllib.request import parse_keqv_list
from webbrowser import get
from scapy.all import *
import sys
import socket 
import json
import time

MY_CONTAINER_NAME = str(subprocess.check_output(['bash','-c', 'hostname']).decode("utf-8")).replace("\n","")
MY_IP = socket.gethostbyname(MY_CONTAINER_NAME)
SRC_PORT = 7000
CONTROLLER_IP = socket.gethostbyname("sdn")
FILTER = 'tcp and dst port 7000 and dst {0}'.format(MY_IP)

routingTable = {}

flagsMapping = {
    'F': '1',
    'S': '2',
    'R': '3',
    'P': '4',
    'A': '5',
    'U': '6',
    'E': '7',
    'C': '8',
}
notAllowed = ["hack", "virus", "urgent", "attention"]



def getNextAddress(sfcNo):
    global routingTable, MY_CONTAINER_NAME
    sfcPath = routingTable[sfcNo]

    DEST_IP, DEST_PORT = "0.0.0.0", 10000

    for i in range(len(sfcPath)):
        l = sfcPath[i]
        if MY_CONTAINER_NAME in l:
            DEST_IP, DEST_PORT = sfcPath[i+1][0], sfcPath[i+1][1]

    print(DEST_IP, DEST_PORT)
    return DEST_IP, DEST_PORT


def signatureMatching(data):
    global notAllowed
    for s in notAllowed:
        if s in data:
            return False

    return True


def handle_packet(packet):
    global SRC_PORT, flagsMapping, MY_IP
    t = time.time()
    print(bytes(packet[TCP].payload))

    # print(packet[IP].dst)

    if(signatureMatching(str(bytes(packet[TCP].payload)))):
        flag = str(packet[TCP].flags)

        DEST_IP, DEST_PORT = getNextAddress(flagsMapping[flag])
        pkt = IP(ttl = 64)
        pkt = pkt/TCP(sport=SRC_PORT, dport=DEST_PORT, flags = flag)/Raw(load=bytes(packet[TCP].payload))
        pkt.src = packet[IP].src  # original ip of client
        pkt.dst = DEST_IP
        # print("packet recieved - dpi : {0} secs".format(time.time() - t))
        print("packet recieved - DPI")
        send(pkt)


def getRoutingTable():
    global routingTable
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((CONTROLLER_IP, 4000))
    data = client.recv(4096)
    routingTable = json.loads(data.decode('utf-8'))

    # print(routingTable)


if __name__ =="__main__":
    getRoutingTable()
    sniff(prn=handle_packet, filter = FILTER)