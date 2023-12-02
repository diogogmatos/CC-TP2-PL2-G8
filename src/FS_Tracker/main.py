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

# set tracker buffer size
BUFFER_SIZE = 1024

# type for the dictionary that stores the available files for each node
Flock = Dict[tuple[str, int], Dict[str, set[int]]]
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


# remove hashes from a PomboFiles
def removeHashes(p: PomboFiles) -> list[tuple[str, set[int]]]:
    l: list[tuple[str, set[int]]] = list()

    for f in p:

        blocks: set[int] = set()
        for (block_nr, _) in f[1]:
            blocks.add(block_nr)
        l.append((f[0], blocks))

    return l


# handle a chirp message
def handleChirp(node: str, availableFiles: Flock, fileHashes: HashFlock, data: bytes, lock: threading.Lock):    
    # update chirp, adds new block to file
    if TCPombo.isUpdate(data):

        update = TCPombo.getPomboUpdate(data)

        with lock:
            if update[0] not in availableFiles[node]:
                availableFiles[node][update[0]] = set()

            availableFiles[node][update[0]].add(update[1])

    # files chirp, adds the initial files of a node
    else:

        with lock:
            availableFiles[node] = dict()
            pomboFiles = TCPombo.getPomboFiles(data)

            for f in pomboFiles:

                blocks: set[int] = set()
                fileHashes[f[0]] = [b''] * len(f[1])

                for (block_nr, block_hash) in f[1]:

                    blocks.add(block_nr)
                    fileHashes[f[0]][block_nr] = block_hash

                availableFiles[node][f[0]] = blocks


# handle a call message
def handleCall(conn, availableFiles: Flock, fileHashes: HashFlock, data: bytes, lock: threading.Lock):
    # create message
    MESSAGE: PomboLocations = (list(), list())

    # get requested file / file blocks
    requestedFile = TCPombo.getPomboCall(data)

    # if the file exists
    if requestedFile in fileHashes:

        with lock:
            # get the locations of the requested file
            for node in availableFiles:
                for f_name, f_blocks in availableFiles[node].items():
                    if (f_name == requestedFile):
                        MESSAGE[0].append((node[0], f_blocks))

        # get the block hashes
        for h in fileHashes[requestedFile]:
            MESSAGE[1].append(h)

    # send message
    conn.send(TCPombo.createLocationsChirp(MESSAGE))


# handle a node being disconnected: remove it from availableFiles
def handleDisconnect(node: str, availableFiles: Flock, lock: threading.Lock):
    lock.acquire()
    try:
        if (node in availableFiles):
            del availableFiles[node]
    finally:
        lock.release()


# handle a connection with a node
def handleNode(conn: socket.socket, ip: str, availableFiles: Flock, fileHashes: HashFlock, lock: threading.Lock):
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
                handleChirp(hostname, availableFiles, fileHashes, data, lock)

            # send the location of the requested file
            else:
                handleCall(conn, availableFiles, fileHashes, data, lock)

        # else, the client disconnected
        else:
            # disconnect print
            print("\n" + hostname, "@", ip, "disconnected.")
            run = False

    # close connection
    conn.close()
    # remove node from availableFiles
    handleDisconnect(hostname, availableFiles, lock)


# main function
def main():
    # create dictionary to store the available files for each node
    availableFiles: Flock = dict()
    fileHashes: HashFlock = dict()

    # create a lock object, used to lock access to availableFiles between threads
    lock = threading.Lock()

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
            conn, addr[0], availableFiles, fileHashes, lock)).start()


main()
