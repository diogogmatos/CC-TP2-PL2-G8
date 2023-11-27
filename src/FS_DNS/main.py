import hashlib
import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder
import signal  # to handle signals
import threading  # to handle multiple connections
from typing import Dict  # to use typing for dictionaries
from collections import defaultdict # to use hashtable

#definir hashtable
dns_database = defaultdict(str)
# set buffer size
BUFFER_SIZE = 1024
# Caminho do arquivo de zona
# zone_file_path = '/etc/bind/zones/example.com.zone'         # ou isto: /etc/resolv.conf         é link simbólico para /run/systemd/resolve/stub-resolv.conf

# Returns the IP address associated with a domain name 
def handleCall(conn, name: str, lock: threading.Lock):
    lock.acquire()
    try:
        if name in dns_database:
            hashed_ip = dns_database[name]
            print(f"IP address for {name}: {hashed_ip}")
            conn.send(hashed_ip.encode('utf-8'))
        else:
            print(f"name is not registered: {name}")
    finally:
        lock.release()


# Add a new domain name and IP address 
def handleChirp(addr: tuple[str, int], name: str, lock: threading.Lock):
    lock.acquire
    try:
        # Calcular hash do IP (SHA-256)
        hashed_ip = hashlib.sha256(addr[0].encode('utf-8')).hexdigest()
        dns_database[name] = hashed_ip
        print(f"Registered: {name} -> {hashed_ip}")
    finally:
        lock.release()

# handle get command
def handleNode(conn, addr: tuple[str, int], data: bytes, lock: threading.Lock):
    # connection established print
    print("\nTCP Connection with Client @",
          addr[0] + ":" + str(addr[1]))

    # listen for messages from client
    run = True
    while run:
        # receive message length
        data = conn.recv(BUFFER_SIZE).decode('utf-8')

        # if data was actually received, handle it
        if data:
            command = data[0]
            name = data[1:]
            
            # Add a new domain name and IP address
            if command == '0':
                handleCall(conn, name, lock)
            # Returns the IP address associated with a domain name 
            elif command == '1':
                handleChirp(addr, name, lock)
            else:
                print("Invalid command")
        # else, the client disconnected
        else:
            # disconnect print
            print("\nClient @", addr[0] + ":" +
                  str(addr[1]), "disconnected.")
            run = False

    # close connection
    conn.close()
    


def main():
    TCP_IP = ''
    TCP_PORT = 9090
   
    # create a lock object, used to lock access to availableFiles between threads
    lock = threading.Lock()

    # define a signal handler function
    def signal_handler(sig, frame):
        if (sig == 2):
            print("\b\b  \nReceived exit signal. Flying away...")
            sys.exit(0)

    # register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Create a TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the specified host and port
    s.bind((TCP_IP, TCP_PORT))
    # Listen until 5 connections limit
    s.listen(5)

    # dns server active print
    print("    (o)>")
    print("  -\\_/")
    print("    ll")
    print("DNS Server Active @ " + s.getsockname()[0] + ":" + str(TCP_PORT))
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
