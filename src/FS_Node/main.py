import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder
import threading
import hashlib  # para calcular o hash dos blocos

from typing import Dict  # to use typing for dictionaries

# TCPombo protocol payload
from src.types.Pombo import Pombo

# TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo
# UDPombo protocol
from src.protocols.UDPombo.UDPombo import UDPombo

from src.protocols.utils import TCP_PORT, UDP_PORT, CHUNK_SIZE, chunkify

# set node buffer size
BUFFER_SIZE = 1024

Chunks = Dict[int, bool]

# TODO:
# - fazer o node ser um servidor udp que atenda pedidos de outros nodes e informe o tracker de ficheiros recebidos


# establish connection with server
def connectServer(TCP_IP: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((TCP_IP, TCP_PORT))
    except socket.error as e:
        raise ValueError("Error connecting to server:", e)

    # connection established print
    print("  ww     ///")
    print(" ('>     <')")
    print(" (//)   (\\\\)")
    print("--oo-----oo--")
    print("TCPombo Connection with Server @",
          TCP_IP + ":" + str(TCP_PORT))

    return s


# calculate total number of chunks
def chunkNr(locations: Pombo):
    i = 0
    for (n, chunks) in locations:
        j = 0
        for (c, h) in chunks:
            if c > j:
                j = c
        if j > i:
            i = j
    return i


# handle the process of receiving a chunk
def receiveChunk(tcp_socket: socket.socket, file: str, chunk: int, data: bytes, expected_hash: bytes):
    # check if chunk is valid
    received_hash = hashlib.sha1(data).digest()
    if received_hash != expected_hash:
        return False

    # write chunk to file
    with open(file, "wb") as f:
        f.seek(chunk * CHUNK_SIZE)
        f.write(data)

    # inform tracker
    pombo: Pombo = list()
    pombo.append((file, set().add(chunk, expected_hash)))
    message = TCPombo.createChirp("", pombo)
    tcp_socket.send(message)

    return True


# handle transfer of specific chunks
def handleChunkTransfer(tcp_socket: socket.socket, file: str, location: tuple[str, set[tuple[int, bytes]]], availableChunks: Chunks, lock: threading.Lock):
    # TODO: mudar quando DNS for implementado

    # criar socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # fazer bind da socket ao node ao qual vamos pedir o ficheiro
    ip = location[0]
    s.bind((ip, UDP_PORT))

    # pedir e receber cada chunk, se este ainda não tiver sido recebido
    file_name = file
    for chunk in location[1]:
        lock.acquire()
        if not availableChunks[chunk[0]]:
            v = False
            # enquanto chunk recebido não for válido
            while not v:
                # send file request
                availableChunks[chunk[0]] = True
                lock.release()
                CALL = UDPombo.createCall(chunk[0], file_name)
                addr = tuple()
                addr = (ip, UDP_PORT)
                s.sendto(CALL, addr)

                print("sent call for chunk\n", UDPombo.toString(CALL))

                # receive response
                udpombo = UDPombo.receiveUDPombo(s)
                data = UDPombo.getData(udpombo)

                # verificar integridade do chunk, escrever para o ficheiro e informar o tracker
                v = receiveChunk(tcp_socket, file, chunk[0], data, chunk[1])
        else:
            lock.release()


# handle file transfer
def handleTransfer(tcp_socket: socket.socket, file: str, locations: Pombo):
    # create lock for availableChunks
    lock = threading.Lock()

    # create and initialize dictionary
    availableChunks: Chunks = dict()
    for i in range(0, chunkNr(locations)):
        availableChunks[i] = False

    # create thread array to store thread pointers and wait for them to end
    threads: list[threading.Thread] = list()

    # send threads to make the transfer
    for l in locations:
        t = threading.Thread(target=handleChunkTransfer,
                             args=(tcp_socket, file, l, availableChunks, lock))
        t.start()
        threads.append(t)

    # wait for threads to finish
    for t in threads:
        t.join()


# handle get command
def handleGet(s: socket.socket, file: str):
    # create message
    pombo: Pombo = [(file, set())]
    message = TCPombo.createCall("", pombo)
    s.send(message)

    # receive & handle response

    # receive message length
    data = s.recv(4)

    # if data was actually received, handle it
    if data:
        length = int.from_bytes(data, byteorder="big")
        l = 4

        # receive all the message, even if it's bigger than the buffer size
        while l < length:
            chunk = s.recv(BUFFER_SIZE)
            l += len(chunk)
            data += chunk

        # check if file was found
        locations = TCPombo.getPombo(data)
        if locations == []:
            print("File not found.")
            return

        # handle file transfer
        handleTransfer(s, file, TCPombo.getPombo(data))


def main():
    if len(sys.argv) < 3:
        return False

    # get command arguments
    folder = sys.argv[1]
    server_ip = sys.argv[2]

    # set server ip
    TCP_IP = server_ip

    # establish connection with server
    try:
        tcp_socket = connectServer(TCP_IP)
    except ValueError as e:
        print(e)
        return

    # TODO?: verificar se foram adicionados ficheiros ao folder de x em x tempo
    # (ficheiros adicionados manualmente à pasta e que não foram transferidos de outros nodes)
    # send available files in folder

    # Get a list of all the files and directories in the folder
    files = os.listdir(folder)
    # Filter the list to include only files
    files = [file for file in files if os.path.isfile(
        os.path.join(folder, file))]

    pombo: Pombo = []
    for file in files:
        with open(folder + "/" + file, 'rb') as f:
            f_bytes = f.read()
            pombo.append((file, chunkify(f_bytes)))
    # create message
    message = TCPombo.createChirp("", pombo)
    tcp_socket.send(message)

    # handle user input
    fail_msg: str = "Unknown command. Available commands:\n- get <filename>\n- exit"
    print()
    while True:
        command = input("> ")
        parameters = command.split(" ")
        if len(parameters) < 1 or len(parameters) > 2:
            print(fail_msg)
        elif parameters[0] == "exit":
            break
        elif parameters[0] == "get":
            file = parameters[1]
            handleGet(tcp_socket, file)
        else:
            print(fail_msg)

    # close connection
    tcp_socket.close()


main()
