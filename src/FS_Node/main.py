import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder
import threading
import hashlib  # para calcular o hash dos blocos

# to use typing for dictionaries
from typing import Dict
# TCPombo protocol payload
from src.protocols.TCPombo.types import PomboFiles, PomboLocations, PomboUpdate
# TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo
# UDPombo protocol
from src.protocols.UDPombo.UDPombo import UDPombo
# constants and utility functions
from src.protocols.utils import TCP_PORT, UDP_PORT, CHUNK_SIZE, chunkify

# TODO:
# - fazer o node ser um servidor udp que atenda pedidos de outros nodes e informe o tracker de ficheiros recebidos


# TRACKER RELATED


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


# EXECUTING A GET


# handle do processo de receber um chunk
def receiveChunk(tcp_socket: socket.socket, udp_socket: socket.socket, addr: tuple[str,int], folder: str, file_name: str, chunk_nr: int, expected_hash: bytes):
    valid = False
    limit = 5 # limite de tentativas até considerar transferência do chunk falhada
    
    # enquanto verificações não forem bem sucedidas
    while not valid and limit > 0:

        valid = True
        timeout = False
        
        # receber chunk
        try:
            udp_socket.settimeout(0.5)
            udpombo, addr = udp_socket.recvfrom(5000)
        except socket.timeout:
            timeout = True

        # verificar que não ocorreu timeout
        if not timeout:
            
            # verificar que foi recebida informação
            if udpombo:

                # verificar que o chunk é válido
                calculated_hash = hashlib.sha1(UDPombo.getChirpData(udpombo)[1]).digest()

                if calculated_hash == expected_hash:

                    # escrever chunk para ficheiro
                    with open(folder + "/" + file_name, 'r+b') as f:
                        f.seek(chunk_nr * CHUNK_SIZE)
                        f.write(UDPombo.getChirpData(udpombo)[1])
                        f.flush()
                        f.close()

                    # informar o tracker
                    pomboUpdate = (file_name, chunk_nr)
                    tcp_socket.send(TCPombo.createUpdateChirp("", pomboUpdate))

                # se o chunk não é válido, reenviar pedido
                else:
                    valid = False
                    limit -= 1
                    print("- chunk", chunk_nr, "is invalid")

            # se receber end of file, sair
            else:
                valid = False
                print("- end of file on chunk", chunk_nr)
                return False

        # se ocorrer timeout, reenviar pedido
        else:
            valid = False
            limit -= 1
            print("- timeout on chunk", chunk_nr)

        # reenviar pedido se condições assim o pedirem
        if not valid and limit > 0:
            udp_socket.sendto(UDPombo.createCall(chunk_nr, file_name), addr)

    if limit > 0:
        print("- transfer succeeded:", chunk_nr)
    else:
        print("- transfer failed:", chunk_nr)

    udp_socket.close()


# calcular nº total de chunks
def chunkNr(locations: PomboLocations):
    i = 0
    for (_, chunks) in locations[0]:
        j = 0
        for c in chunks:
            if c > j:
                j = c
        if j > i:
            i = j
    return i + 1


# efetuar a tansferência de chunks de um node específico
def handleChunkTransfer(tcp_socket: socket.socket, file: str, dest_ip: str, chunksToTransfer: list[int], hashes: list[bytes], folder: str):
    # array de threads
    threads: list[threading.Thread] = list()

    # pedir chunks do ficheiro
    for chunk in chunksToTransfer:

            # criar socket exclusiva ao chunk
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(('', 0))

            # enviar call para pedir chunk
            addr = (dest_ip, UDP_PORT)
            s.sendto(UDPombo.createCall(chunk, file), addr)
            
            # receber chunk pedido (paralelamente)
            t = threading.Thread(target=receiveChunk, args=(tcp_socket, s, addr, folder, file, chunk, hashes[chunk]))
            t.start()
            threads.append(t)

    # esperar que threads terminem
    for t in threads:
        t.join()


# calcular divisão de chunks por nodes
def calculateDivisionOfChunks(locations: PomboLocations) -> Dict[str, list[int]]:
    divisionOfChunks: Dict[str, list[int]] = {node: [] for node, _ in locations[0]}

    # calcular nº total de chunks
    totalChunks = chunkNr(locations)

    assigned_numbers = set()

    for _ in range(totalChunks):
        for node, node_set in locations[0]:
            if node not in divisionOfChunks:
                divisionOfChunks[node] = []

            available_numbers = node_set - set(divisionOfChunks[node]) - assigned_numbers

            if available_numbers:
                number = min(available_numbers)
                divisionOfChunks[node].append(number)
                assigned_numbers.add(number)
                break
    
    return divisionOfChunks


# efetuar uma transferência
def handleTransfer(tcp_socket: socket.socket, file: str, locations: PomboLocations, folder: str):
    # criar o ficheiro e alocar o tamanho correto
    with open(folder + "/" + file, 'wb') as f:
        f.write(b'\0')
        f.flush()
        f.close()

    threads = list()

    divisionOfChunks = calculateDivisionOfChunks(locations)

    # criar threads para efetuar a transferência de chunks
    for node, chunksToTransfer in divisionOfChunks.items():
        t = threading.Thread(target=handleChunkTransfer,
                             args=(tcp_socket, file, node, chunksToTransfer, locations[1], folder))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# efetuar o comando "get"
def handleGet(s: socket.socket, file: str, folder: str):
    # ask tracker for file locations
    s.send(TCPombo.createCall("", file))

    # receive response
    data = TCPombo.receiveTCPombo(s)

    if data:

        # print response
        print("\nGet:", TCPombo.toString(data, True))

        # check if file was found
        locations = TCPombo.getPomboLocations(data)

        if locations[0] == []:
            print("\nFile not found.")
            return

        # handle file transfer
        handleTransfer(s, file, locations, folder)


# SERVIDOR UDP


# receber e responder a um pedido de ficheiro
def handleCall(udp_socket: socket.socket, addr: tuple[str, int], folder: str, udpombo: bytes):
    print("\nServer:", UDPombo.toString(udpombo))

    # se udpombo não for vazio ou end of file
    if udpombo:
        # obter informações do pedido
        file = UDPombo.getFileName(udpombo)
        chunks = UDPombo.getCallData(udpombo)

        # enviar chunks pedidos
        for chunk_nr in chunks:

            # obter o chunk do ficheiro pedido
            with open(folder + "/" + file, "rb") as f:
                f.seek(chunk_nr * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)
                f.close()

            # criar mensagem de resposta
            udp_socket.sendto(UDPombo.createChirp(chunk_nr, file, chunk_data), addr)


# servidor UDP: recebe calls e responde com chirps
def handleServer(folder: str):
    # criar socket udp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # fazer bind da socket à porta de escuta
    s.bind(('', UDP_PORT))

    # esperar, aceitar e responder a pedidos
    run = True
    while run:

        # receber pedido por UDPombo (bloqueante)   
        data, addr = s.recvfrom(5000)

        if not UDPombo.isChirp(data):

            # lidar com um pedido paralelamente
            threading.Thread(target=handleCall, args=(s, addr, folder, data)).start()

        # received exit signal (empty chirp)
        else:
            run = False

    # cleanup
    s.close


# MAIN


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

    pombo: PomboFiles = []
    for file in files:

        with open(folder + "/" + file, 'rb') as f:

            # obtain file information
            f_bytes = f.read()
            chunks = chunkify(f_bytes)
            # add file information to pombo
            pombo.append((file, chunks))
            # close file
            f.close()

    # send message to tracker (inform about initial files in folder)
    tcp_socket.send(TCPombo.createFilesChirp("", pombo))

    # handle server
    t = threading.Thread(target=handleServer, args=(folder,))
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
            handleGet(tcp_socket, file, folder)
        
        else:
            print(fail_msg)

    # cleanup
    print("\nReceived exit signal. Flying away...")
    # exit signal for udp server
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(UDPombo.createChirp(0, "", b''), ('', UDP_PORT))
    # close connection
    tcp_socket.close()
    # stop server
    t.join()


main()
