import socket  # to send via tcp
import signal  # to handle signals
import sys  # to exit gracefully
import threading  # to handle multiple connections
from typing import Dict  # to use typing for dictionaries

# TCPombo protocol payload
from src.types.Pombo import Pombo

# import TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo

# TODO:
# - make the tracker actually receive and store information about what files each node has available
# - modularize the connection handling code

TCP_IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 9090
BUFFER_SIZE = 1024

Flock = Dict[tuple[str, int], Pombo]


def joinPombos(p1: Pombo, p2: Pombo) -> Pombo:
    p: Pombo = list()
    seen_first_elements = set()

    for f1 in p1:
        f_name = f1[0]
        blocks1 = f1[1]
        if f_name not in seen_first_elements:
            seen_first_elements.add(f_name)
            for f2 in p2:
                if (f1[0] == f2[0]):
                    blocks2 = f2[1]
                    p.append((f_name, blocks1.union(blocks2)))
                    break
            else:
                p.append(f1)

    # append remaining tuples from p2
    for f2 in p2:
        if f2[0] not in seen_first_elements:
            p.append(f2)

    return p


def handleNode(conn, addr, availableFiles: Flock):
    # connection established print
    print("\nTCPombo Connection with Client @",
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
            print()
            print(TCPombo.toString(data))

            # if the message is a chirp, store the available files
            if (TCPombo.isChirp(data)):
                if (addr not in availableFiles):
                    availableFiles[addr] = TCPombo.getData(data)
                else:
                    availableFiles[addr] = joinPombos(
                        availableFiles[addr], TCPombo.getData(data))

            # else if the message is a call, send the location of the requested file
            else:
                # create message
                MESSAGE: Pombo = list()

                # get requested file / file blocks
                requestedFile = TCPombo.getData(data)[0]

                f_name = requestedFile[0]
                f_blocks = requestedFile[1]

                # if client requested specific file blocks
                if len(f_blocks) > 0:
                    # send the locations of the requested file blocks
                    for node in availableFiles:
                        for file in availableFiles[node]:
                            if (file[0] == f_name):
                                s: set[int] = set()
                                for block in file[1]:
                                    if block in f_blocks:
                                        s.add(block)
                                if len(s) > 0:
                                    MESSAGE.append((node[0], s))

                # if client requested the whole file
                else:
                    # send the locations of the requested file
                    for node in availableFiles:
                        for file in availableFiles[node]:
                            if (file[0] == f_name):
                                MESSAGE.append((node[0], file[1]))

                # send message
                conn.send(TCPombo.createChirp(MESSAGE))

        # else, the client disconnected
        else:
            # disconnect print
            print("\nClient @", addr[0] + ":" +
                  str(addr[1]), "disconnected.")
            run = False

    # close connection
    conn.close()


def main():
    # create dictionary to store the available files for each node
    availableFiles: Flock = dict()

    # define a signal handler function
    def signal_handler(sig, frame):
        if (sig == 2):
            print("\b\b  \nReceived exit signal. Flying away...")
            sys.exit(0)

    # register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # listen for connections with the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(5)  # 5 = max number of connections

    # server active print
    print("  ww")
    print(" ('>")
    print(" (//)")
    print("--oo---------")
    print("Server Active @ " + TCP_IP + ":" + str(TCP_PORT))
    print("Listening for chirps and calls...")

    # wait & accept incoming connections
    while 1:
        # accept connection
        conn, addr = s.accept()

        # start a new thread to handle the connection
        threading.Thread(target=handleNode, args=(
            conn, addr, availableFiles)).start()


main()
