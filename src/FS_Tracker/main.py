import socket  # to send via tcp
import signal  # to handle signals
import sys  # to exit gracefully
import threading  # to handle multiple connections
from typing import Dict  # to use typing for dictionaries

# dns functions
import src.dns as dns
# TCPombo protocol payload type
from src.protocols.types import PomboLocations, PomboFiles
# import TCPombo protocol
from src.protocols.TCPombo import TCPombo
# import TCP_PORT
from src.protocols.utils import TCP_PORT
from src.FS_Tracker.AvailableFiles import AvailableFiles

# set tracker buffer size
BUFFER_SIZE = 1024

# type for the dictionary that stores the available files for each node
# {file_name, {node_name, {block1, block2, block3} } }
Flock = Dict[str, Dict[str, set[int]]]
HashFlock = Dict[str, list[bytes]]


# join two file lists
def joinFileLists(l1: list[tuple[str, set[int]]], l2: list[tuple[str, set[int]]]) -> list[tuple[str, set[int]]]:
    l: list[tuple[str, set[int]]] = list()
    seen_files = set()

    for f1 in l1:
        f_name = f1[0]
        blocks1 = f1[1]
        if f_name not in seen_files:
            seen_files.add(f_name)
            for f2 in l2:
                if (f1[0] == f2[0]):
                    blocks2 = f2[1]
                    l.append((f_name, blocks1.union(blocks2)))
                    break
            else:
                l.append(f1)

    # append remaining tuples from p2
    for f2 in l2:
        if f2[0] not in seen_files:
            l.append(f2)

    return l


# handle a chirp message
def handleChirp(node: str, availableFiles: AvailableFiles, data: bytes):
    # update chirp, adds new block to file
    if TCPombo.isUpdate(data):
        update = TCPombo.getPomboUpdate(data)
        availableFiles.addFileBlock(update[0], node, update[1])

    # files chirp, adds the initial files of a node
    else:
        pomboFiles = TCPombo.getPomboFiles(data)
        availableFiles.addFile(node, pomboFiles)


# handle a call message
def handleCall(conn, availableFiles: AvailableFiles, data: bytes):
    # get requested file / file blocks
    requestedFile = TCPombo.getPomboCall(data)

    # create message
    MESSAGE: PomboLocations = availableFiles.getFileLocations(requestedFile)

    # send message
    conn.send(TCPombo.createLocationsChirp(MESSAGE))


# handle a node being disconnected: remove it from availableFiles
def handleDisconnect(node: str, availableFiles: AvailableFiles):
    if (node in availableFiles):
        availableFiles.removeNode(node)


# handle a connection with a node
def handleNode(conn: socket.socket, ip: str, availableFiles: AvailableFiles):
    hostname = dns.getHostByAddr(ip)

    # connection established print
    print("\nTCPombo Connection with", hostname, "@", ip)

    # listen for messages from client
    run = True
    while run:
        # receive message
        data = TCPombo.receiveTCPombo(conn)

        # if data was actually received, handle it
        if data:

            # print message
            print("\n" + TCPombo.toString(data))

            # store the available files
            if (TCPombo.isChirp(data)):
                handleChirp(hostname, availableFiles, data)

            # send the location of the requested file
            else:
                handleCall(conn, availableFiles, data)

        # else, the client disconnected
        else:
            # disconnect print
            print("\n" + hostname, "@", ip, "disconnected.")
            run = False

    # close connection
    conn.close()
    # remove node from availableFiles
    handleDisconnect(hostname, availableFiles)


# main function
def main():
    # create dictionary to store the available files for each node
    availableFiles: AvailableFiles = AvailableFiles()

    # define a signal handler function
    def signal_handler(sig, frame):
        if (sig == 2):
            print("\b\b  \nReceived exit signal. Flying away...")
            sys.exit(0)

    # register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # listen for connections with the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', TCP_PORT))
    s.listen(5)  # 5 = max number of connections

    # server active print
    print("  ww")
    print(" ('>")
    print(" (//)")
    print("--oo---------")
    print("Server Active @ " + s.getsockname()[0] + ":" + str(TCP_PORT))
    print("Listening for chirps and calls...")

    # wait & accept incoming connections
    while 1:
        # accept connection
        conn, addr = s.accept()

        # start a new thread to handle the connection
        threading.Thread(target=handleNode, args=(
            conn, addr[0], availableFiles)).start()


main()
