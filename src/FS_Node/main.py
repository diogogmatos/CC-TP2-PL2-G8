import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder
import threading
import hashlib  # para calcular o hash dos blocos
import time
import select

# dns functions
import src.dns as dns
# to use typing for dictionaries
from typing import Dict
# TCPombo protocol payload
from src.protocols.types import PomboFiles, PomboLocations, PomboUpdate
# TCPombo protocol
from src.protocols.TCPombo import TCPombo
# UDPombo protocol
from src.protocols.UDPombo import UDPombo
# constants and utility functions
from src.protocols.utils import TCP_PORT, UDP_PORT, CHUNK_SIZE, chunkify, getNodeFromChunk
# data structure to store chunks to receive
from src.FS_Node.ChunksToReceive import ChunksToReceive
# data structure to store chunks to process
from src.FS_Node.ChunksToProcess import ChunksToProcess
# data structure to store transfer efficiency data
from src.FS_Node.TransferEfficiency import TransferEfficiency


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


def processReceivedChunk(chunksToProcess: ChunksToProcess, chunksToReceive: ChunksToReceive, folder: str, file_name: str, tcp_socket: socket.socket):
    while not (chunksToProcess.isEmpty() and chunksToReceive.isEmpty()):

        # pegar num chunk da fila de chunks a processar
        udpombo = chunksToProcess.getChunk()

        # verificar que foi recebida informação
        if udpombo:

            # obter payload (chunk_nr, bytes)
            data = UDPombo.getChirpData(udpombo)

            # obter informação do chunk
            info = chunksToReceive.getChunk(data[0])

            # verificar que o chunk é válido
            calculated_hash = hashlib.sha1(data[1]).digest()

            if info != None:
                # se o chunk é válido
                if calculated_hash == info[0]:

                    # remover chunk da fila de chunks a receber e parar o seu timeout
                    chunksToReceive.removeChunk(data[0])

                    # escrever chunk para ficheiro
                    with open(folder + "/" + file_name, 'r+b') as f:
                        f.seek(data[0] * CHUNK_SIZE)
                        f.write(data[1])
                        f.flush()
                        f.close()

                    # informar o tracker
                    pomboUpdate = (file_name, data[0])
                    tcp_socket.send(TCPombo.createUpdateChirp(pomboUpdate))

                    # mensagem de sucesso
                    print("- transfer succeeded:", data[0])
                else:
                    print("- invalid chunk:", data[0])


def receiveChunks(s: socket.socket, chunksToProcess: ChunksToProcess, divisionOfChunks: Dict[str, list[int]], transferEfficiency: TransferEfficiency, stop_event: threading.Event):
    while not stop_event.is_set():
        ready = select.select([s], [], [], 0.1)
        if ready[0]:
            udpombo, _ = s.recvfrom(20000)
            transferEfficiency.addTransfer(getNodeFromChunk(UDPombo.getChirpData(udpombo)[0], divisionOfChunks), round(time.time() * 1000) - UDPombo.getTimestamp(udpombo))
            chunksToProcess.addChunk(udpombo)


def transferSingleChunk(s: socket.socket, tcp_socket: socket.socket, node_name: str, folder: str, file_name: str, chunk: int, hashes: list[bytes], transferEfficiency: TransferEfficiency):
    # inicializar estrutura de dados para chunks a processar
    chunksToProcess = ChunksToProcess()

    # receber chunk
    stop = threading.Event()
    r = threading.Thread(target=receiveChunks, args=(s, chunksToProcess, {node_name: [chunk]}, transferEfficiency, stop))
    r.start()

    # obter ip do node
    dest_ip = dns.getHostByName(node_name)

    # enviar call a pedir chunk
    addr = (dest_ip, UDP_PORT)
    s.sendto(UDPombo.createCall([chunk], file_name), addr)

    print("- sent call for chunk:", node_name, "@", dest_ip)

    # inicializar estrutura de dados para chunks a receber e o timeout de cada chunk
    chunksToReceive = ChunksToReceive(file_name, [chunk], hashes, s, transferEfficiency, {node_name: [chunk]})

    # processar chunk
    processReceivedChunk(chunksToProcess, chunksToReceive, folder, file_name, tcp_socket)

    # cleanup
    stop.set()
    r.join()
    chunksToReceive.destroy()


# calcular divisão de chunks por nodes
def calculateDivisionOfChunks(udp_socket: socket.socket, tcp_socket: socket.socket, file: str, folder: str, locations: PomboLocations, transferEfficiency: TransferEfficiency, total_chunks: int):
    divisionOfChunks: Dict[str, list[int]] = {node: [] for node, _ in locations[0]}
    received_nr = 0

    for node, _ in locations[0]:
        transferEfficiency.newNode(node)

    # se só um node tiver o ficheiro
    if len(locations[0]) == 1:

        for node, _ in locations[0]:
            divisionOfChunks[node] = list(range(total_chunks))
        
        return (divisionOfChunks, received_nr)
    
    for i in range(total_chunks):
        usable: set[str] = []
        for node, node_set in locations[0]:
            if node not in divisionOfChunks:
                divisionOfChunks[node] = []
            if transferEfficiency.getAverageTransferTime(node) == 0:
                transferSingleChunk(udp_socket, tcp_socket, node, folder, file, i, locations[1], transferEfficiency)
                received_nr += 1
                usable = []
                break
            if i in node_set:
                usable.append(node)

        if len(usable) == 0:
            continue
        elif len(usable) == 1:
            divisionOfChunks[usable[0]].append(i)
            continue

        better = usable[0]
        for n in range(len(usable) - 1):
            transferAverageA = transferEfficiency.getAverageTransferTime(better)
            transferAverageB = transferEfficiency.getAverageTransferTime(usable[n+1])
            transferRTTA = transferEfficiency.getSuccessRate(better)
            transferRTTB = transferEfficiency.getSuccessRate(usable[n+1])
            mediaA = transferAverageA + ((1-transferRTTA)*transferAverageA)
            mediaB =  transferAverageB +(transferAverageB *(1- transferRTTB))
            lenA = len(divisionOfChunks[better])
            lenB = len(divisionOfChunks[usable[n+1]])
            if mediaA < mediaB:
                value = mediaB / mediaA
            else:
                value = mediaA / mediaB
            if lenA == 0:
                better = better
            elif lenB == 0:
                better = usable[n+1]
            elif mediaA < mediaB and lenA < lenB:
                better = better
            elif mediaA > mediaB and lenA > lenB:
                better = usable[n+1]
            elif mediaA < mediaB:
                if abs((lenA+1) / (lenB) - value) < abs((lenA) / (lenB+1) - value):
                    better = better
                else:
                    better = usable[n+1]
            else:
                if abs((lenB+1) / (lenA) - value) < abs((lenB) / (len(divisionOfChunks[better])+1) - value):
                    better = usable[n+1]
                else:
                    better = better
        divisionOfChunks[better].append(i)
    
    return (divisionOfChunks, received_nr)


# efetuar uma transferência
def handleTransfer(tcp_socket: socket.socket, file_name: str, locations: PomboLocations, folder: str, transferEfficiency: TransferEfficiency):
    # criar socket udp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))

    # criar o ficheiro
    with open(folder + "/" + file_name, 'wb') as f:
        f.write(b'\0')
        f.flush()
        f.close()

    # calcular nº total de chunks
    total_chunks = chunkNr(locations)

    # calcular divisão de chunks por nodes
    print("- calculating division of chunks...")
    divisionOfChunks, received_chunks_nr = calculateDivisionOfChunks(s, tcp_socket, file_name, folder, locations, transferEfficiency, total_chunks)
    print("- done!")

    # inicializar estrutura de dados para chunks a processar
    chunksToProcess = ChunksToProcess()

    # receber chunks em paralelo
    stop = threading.Event()
    r = threading.Thread(target=receiveChunks, args=(s, chunksToProcess, divisionOfChunks, transferEfficiency, stop))
    r.start()

    # pedir chunks aos nodes, de acordo com a divisão calculada
    for node_name, chunksToTransfer in divisionOfChunks.items():
        if chunksToTransfer != []:
            # obter ip do node
            dest_ip = dns.getHostByName(node_name)

            # enviar call a pedir chunks
            addr = (dest_ip, UDP_PORT)
            s.sendto(UDPombo.createCall(chunksToTransfer, file_name), addr)

            print("- sent call for chunks:", node_name, "@", dest_ip)

    # inicializar estrutura de dados para chunks a receber e o timeout de cada chunk
    chunksToReceive = ChunksToReceive(file_name, list(range(received_chunks_nr, total_chunks)), locations[1], s, transferEfficiency, divisionOfChunks)

    # processar chunks
    processReceivedChunk(chunksToProcess, chunksToReceive, folder, file_name, tcp_socket)

    # cleanup
    stop.set()
    r.join()
    chunksToReceive.destroy()
    s.close()

    # mensagem de sucesso
    print("- transfer succeeded:", file_name)
    # print("Division of Chunks: ",divisionOfChunks)


# efetuar o comando "get"
def handleGet(s: socket.socket, file: str, folder: str, transferEfficiency: TransferEfficiency):
    # check if the file already exists
    if os.path.isfile(folder + "/" + file):
        print("\nFile already exists.")
        return
        
    # ask tracker for file locations
    s.send(TCPombo.createCall(file))

    # receive response
    data = TCPombo.receiveTCPombo(s)

    if data:

        # check if file was found
        locations = TCPombo.getPomboLocations(data)

        if locations[0] == []:
            print("\nFile not found.")
            return

        # print response
        print("\nGet:", TCPombo.toString(data, True))

        # handle file transfer
        handleTransfer(s, file, locations, folder, transferEfficiency)


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

            print("- sent chunk", chunk_nr)


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
        data, addr = s.recvfrom(20000)

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
        # obtain file information
        chunks = chunkify(folder + "/" + file)
        # add file information to pombo
        pombo.append((file, chunks))

    # send message to tracker (inform about initial files in folder)
    tcp_socket.send(TCPombo.createFilesChirp(pombo))

    # create transfer efficiency data structure
    transferEfficiency = TransferEfficiency()

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
            handleGet(tcp_socket, file, folder, transferEfficiency)

        elif parameters[0] == "stats":
            print(transferEfficiency)
        
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
