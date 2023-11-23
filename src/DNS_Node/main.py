import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder
import signal  # to handle signals
import threading  # to handle multiple connections
from typing import Dict  # to use typing for dictionaries

# payload protocol
from src.types.Pombo import Pombo

# TCPombo protocol and UDPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo
from src.protocols.UDPombo.UDPombo import UDPombo


# DNS server configuration
UDP_PORT = 9090
# set buffer size
BUFFER_SIZE = 1024
# Caminho do arquivo de zona
zone_file_path = '/etc/bind/zones/example.com.zone'         # ou isto: /etc/resolv.conf         é link simbólico para /run/systemd/resolve/stub-resolv.conf


# Add a new domain name and IP address to the zone file
def handleChirp(addr: tuple[str, int], data: bytes, lock: threading.Lock):

    # get requested file / file blocks
    requestedFile = UDPombo.getData(data)[0]

    f_name = requestedFile[0] # Domain name to be added to the zone file
    new_ip = addr[0] # IP address to be associated with the domain name
    
    lock.acquire()
    try:
        # Leitura do conteúdo atual do arquivo de zona
        with open(zone_file_path, 'r') as zone_file:
            zone_content = zone_file.readlines()

        # Adição do novo nome associado ao IP
        new_record = f'{f_name}    IN    A    {new_ip}\n'
        zone_content.append(new_record)

        # Escrita do conteúdo modificado de volta ao arquivo de zona
        with open(zone_file_path, 'w') as zone_file:
            zone_file.writelines(zone_content)
    finally:
        lock.release()



# Returns the IP address associated with a domain name in the zone file
def handleCall(conn, data: bytes, lock: threading.Lock):
    # create message
    MESSAGE: Pombo 

    # get requested file / file blocks
    requestedFile = UDPombo.getData(data)[0]

    domain_name = requestedFile[0]

    lock.acquire()
    try:
        try:
            with open(zone_file_path, 'r') as file:
                for line in file:
                    # Ignore comments and empty lines
                    if line.strip() == '' or line.startswith(';'):
                        continue

                    # Split the line into parts
                    parts = line.split()

                    # Check if the line contains an A record for the specified domain
                    if len(parts) >= 5 and parts[0] == domain_name and parts[2] == 'IN' and parts[3] == 'A':
                        return parts[4]

            # If the loop completes without finding a match
            return f"No IP address found for {domain_name}"
        except FileNotFoundError:
            return f"Error: Zone file {zone_file_path} not found"
    finally:
        lock.release()

    # send message
    conn.send(UDPombo.createChirp("", MESSAGE))


# handle get command
def handleNode(conn, addr: tuple[str, int], data: bytes, lock: threading.Lock):
    # connection established print
    print("\nUDPombo Connection with Client @",
          addr[0] + ":" + str(addr[1]))

    # listen for messages from client
    run = True
    while run:
        # receive message length
        data = conn.recv(4)

        # if data was actually received, handle it
        if data:
            length = int.from_bytes(data, byteorder="big")
            l = 4

            # receive all the message, even if it's bigger than the buffer size
            while l < length:
                chunk = conn.recv(BUFFER_SIZE)
                l += len(chunk)
                data += chunk

            # print message
            print("\n" + UDPombo.toString(data))

            # if the message is a chirp, add the new domain name and IP address to the zone file
            if (UDPombo.isChirp(data)):
                handleChirp(addr, data, lock)
            # send the location of the requested file
            else:
                handleCall(conn, data, lock)
        # else, the client disconnected
        else:
            # disconnect print
            print("\nClient @", addr[0] + ":" +
                  str(addr[1]), "disconnected.")
            run = False

    # close connection
    conn.close()
    


def main():
    #if len(sys.argv) < 3:
    #    return False
    #
    # get command arguments
    #folder = sys.argv[1]
    #server_ip = sys.argv[2]

    # set server ip
    UDP_IP = "127.0.0.2"

    # create a lock object, used to lock access to availableFiles between threads
    lock = threading.Lock()

    # define a signal handler function
    def signal_handler(sig, frame):
        if (sig == 2):
            print("\b\b  \nReceived exit signal. Flying away...")
            sys.exit(0)

    # register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Create a UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the specified host and port
    s.bind((UDP_IP, UDP_PORT))
    # Listen until 5 connections limit
    s.listen(5)

    # dns server active print
    print("    (o)>")
    print("  -\\_/")
    print("    ll")
    print("DNS Server Active @ " + UDP_IP + ":" + str(UDP_PORT))
    print("Listening...")

    while 1:
        # accept connection
        conn, addr = s.accept()

        # start a new thread to handle the connection
        threading.Thread(target=handleNode, args=(
            conn, addr, lock)).start()

    # close connection
    s.close()


main()
