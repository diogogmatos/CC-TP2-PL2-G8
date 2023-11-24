import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder
import threading
import hashlib  # para calcular o hash dos blocos

# dicionário que guarda os chunks que já foram pedidos
from src.FS_Node.AvailableChunks import AvailableChunks
# TCPombo protocol payload
from src.types.Pombo import Pombo
# TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo
# UDPombo protocol
from src.protocols.UDPombo.UDPombo import UDPombo
# constants and utility functions
from src.protocols.utils import TCP_PORT, UDP_PORT, CHUNK_SIZE, chunkify

# set node buffer size
BUFFER_SIZE = 1024

# TODO:
# - fazer o node ser um servidor udp que atenda pedidos de outros nodes e informe o tracker de ficheiros recebidos


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
    return i + 1


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


# handle do processo de receber um chunk
def receiveChunk(tcp_socket: socket.socket, udp_socket: socket.socket, file: str, chunk: int, expected_hash: bytes, ip: str):
    # receber chunk
    res: list[bytes] = []  # variável para guardar o resultado da thread
    t = threading.Thread(target=UDPombo.receiveUDPombo,
                         args=(udp_socket, res))
    t.start()
    t.join(timeout=0.5)

    # se occorrer timeout, reenviar pedido
    if t.is_alive():
        print("- timeout on chunk", chunk)
        return False

    data = res[0]

    # se receber end of file, reenviar pedido
    if not data:
        return False

    # verificar que o chunk é válido
    received_hash = hashlib.sha1(data).digest()
    if received_hash != expected_hash:
        print("- chunk", chunk, "is invalid")
        return False

    # escrever chunk para ficheiro
    with open(file, "wb") as f:
        f.seek(chunk * CHUNK_SIZE)
        f.write(data)

    # informar o tracker
    pombo: Pombo = list()
    pombo.append((file, set().add(chunk, expected_hash)))
    message = TCPombo.createChirp("", pombo)
    tcp_socket.send(message)

    return True


# handle transfer of specific chunks
def handleChunkTransfer(tcp_socket: socket.socket, file: str, location: tuple[str, set[tuple[int, bytes]]], availableChunks: AvailableChunks):
    # criar socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # fazer bind da socket ao node ao qual vamos pedir o ficheiro
    ip = location[0]
    s.bind((ip, UDP_PORT))

    # pedir cada chunk, se este ainda não tiver sido pedido
    for chunk in location[1]:
        if not availableChunks.isChunkHandled(chunk[0]):
            # marcar chunk como pedido
            availableChunks.handleChunk(chunk[0])
            # enviar call para pedir chunk
            CALL = UDPombo.createCall(chunk[0], file)
            addr = tuple()
            addr = (ip, UDP_PORT)
            s.sendto(CALL, addr)

            print("- sent call for chunk", chunk[0], "of file", file, "to", ip)

    # receber respostas
    for chunk in location[1]:
        while not receiveChunk(tcp_socket, s, file, chunk[0], chunk[1], ip):
            CALL = UDPombo.createCall(chunk[0], file)
            addr = tuple()
            addr = (ip, UDP_PORT)
            s.sendto(CALL, addr)

            print("- sent call for chunk", chunk[0], "of file", file, "to", ip)


# handle file transfer
def handleTransfer(tcp_socket: socket.socket, file: str, locations: Pombo):
    availableChunks = AvailableChunks(chunkNr(locations))

    # create thread array to store thread pointers and wait for them to end
    threads: list[threading.Thread] = list()

    # send threads to make the transfer
    for l in locations:
        t = threading.Thread(target=handleChunkTransfer,
                             args=(tcp_socket, file, l, availableChunks))
        t.start()
        threads.append(t)

    # wait for threads to finish
    for t in threads:
        t.join()


# handle get command
def handleGet(s: socket.socket, file: str):
    # ask tracker for file locations
    pombo: Pombo = [(file, set())]
    message = TCPombo.createCall("", pombo)
    s.send(message)

    # receive response
    data = TCPombo.receiveTCPombo(s)
    print(TCPombo.toString(data))

    if (data):
        # check if file was found
        locations = TCPombo.getPombo(data)
        if locations == []:
            print("File not found.")
            return

        # handle file transfer
        handleTransfer(s, file, TCPombo.getPombo(data))


# handle do servidor UDP: recebe calls e responde com chirps
def handleServer():
    # criar socket udp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # fazer bind da socket à porta de escuta
    s.bind(('', UDP_PORT))

    # esperar, aceitar e responder a pedidos
    while True:
        res_bytes: list[bytes] = []
        res_addr: list[tuple[str, int]] = []
        UDPombo.receiveUDPombo(s, res_bytes, res_addr)
        data = res_bytes[0]
        addr = res_addr[0]

        # se data não for vazio ou end of file
        if data:
            # obter informações do pedido
            file = UDPombo.getFileName(data)
            chunk_nr = UDPombo.getChunk(data)

            # obter o chunk do ficheiro pedido
            with open(file, "rb") as f:
                f.seek(chunk_nr * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)

            # criar mensagem de resposta
            message = UDPombo.createChirp(chunk_nr, file, chunk_data)
            s.sendto(message, addr)


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

    # send available files in folder and initialize availableChunks

    # get a list of all the files and directories in the folder
    files = os.listdir(folder)

    # filter the list to include only files (exclude folders)
    files = [file for file in files if os.path.isfile(
        os.path.join(folder, file))]

    pombo: Pombo = []
    for file in files:
        with open(folder + "/" + file, 'rb') as f:
            # obtain file information
            f_bytes = f.read()
            chunks = chunkify(f_bytes)
            # add file information to pombo
            pombo.append((file, chunks))

    # create message
    message = TCPombo.createChirp("", pombo)
    # send message to tracker (inform about initial files in folder)
    tcp_socket.send(message)

    # handle server
    t = threading.Thread(target=handleServer)
    t.start()

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
    # stop server
    t.join(timeout=0.1)


main()
