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


# procurar a hash de um chunk
def searchChunkHash(chunk_nr: int, chunks: set[tuple[int, bytes]]):
    for c, h in chunks:
        if c == chunk_nr:
            return h


# handle do processo de receber um chunk
# NOTA: não sabe que chunk vai receber ent n sabe que chunk pedir quando faz timeout
def receiveChunk(tcp_socket: socket.socket, udp_socket: socket.socket, addr: tuple[str,int], chunks: set[tuple[int, bytes]], folder: str, file_name: str, chunk_nr: int):
    valid = False
    limit = 5

    # file_name: str
    # chunk_nr: int
    
    # enquanto verificações não forem bem sucedidas
    while not valid and limit > 0:
        
        # receber chunk
        res: list[bytes] = []  # variável para guardar o resultado da thread
        t = threading.Thread(target=UDPombo.receiveUDPombo,
                            args=(udp_socket, res, None))
        t.start()
        t.join(timeout=0.5) # timeout de 500ms

        # verificar que não ocorreu timeout
        if not t.is_alive():

            udpombo = res[0]
            
            # verificar que foi recebida informação
            if udpombo:

                # obter informações do pacote recebido
                # file_name = UDPombo.getFileName(udpombo)
                # chunk_nr = UDPombo.getChunk(udpombo)

                # verificar que o chunk é válido
                calculated_hash = hashlib.sha1(UDPombo.getData(udpombo)).digest()
                expected_hash = searchChunkHash(chunk_nr, chunks)

                if calculated_hash == expected_hash:

                    # escrever chunk para ficheiro
                    with open(folder + "/" + file_name, 'r+b') as f:
                        f.seek(chunk_nr * CHUNK_SIZE)
                        f.write(UDPombo.getData(udpombo))
                        f.flush()
                        f.close()

                    # informar o tracker
                    pombo: Pombo = list()
                    pombo_chunks: set[tuple[int, bytes]] = {(chunk_nr, expected_hash)}
                    pombo.append((file_name, pombo_chunks))
                    message = TCPombo.createChirp("", pombo)
                    tcp_socket.send(message)

                    valid = True

                # se o chunk não é válido, reenviar pedido
                else:
                    limit -= 1
                    print("- chunk", chunk_nr, "is invalid")

                valid = True

            # se receber end of file, sair
            else:
                print("- end of file on chunk", chunk_nr)
                return False

            valid = True

        # se ocorrer timeout, reenviar pedido
        else:
            limit -= 1
            print("- timeout on chunk", chunk_nr)

        if not valid and limit > 0:
            CALL = UDPombo.createCall(chunk_nr, file_name)
            udp_socket.sendto(CALL, addr)

    if limit > 0:
        print("- transfer succeeded:", chunk_nr)
    else:
        print("- transfer failed:", chunk_nr)


# calcular nº total de chunks
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


# efetuar a tansferência de chunks de um node específico
def handleChunkTransfer(tcp_socket: socket.socket, file: str, location: tuple[str, set[tuple[int, bytes]]], availableChunks: AvailableChunks, folder: str):
    # criar socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # pedir chunks do ficheiro
    handledChunks: list[int] = list()
    for chunk in location[1]:

        # bloquear acesso
        availableChunks.lockAquire()

        # verificar que chunk ainda não foi tratado
        if not availableChunks.isChunkHandled(chunk[0]):

            # marcar chunk como tratado
            availableChunks.handleChunk(chunk[0])

            # desbloquear acesso
            availableChunks.lockRelease()

            # adicionar chunk à lista de chunks visitados
            handledChunks.append(chunk[0])

            # enviar call para pedir chunk
            CALL = UDPombo.createCall(chunk[0], file)
            addr = tuple()
            addr = (location[0], UDP_PORT)
            s.sendto(CALL, addr)

            # receber chunk pedido
            receiveChunk(tcp_socket, s, addr, location[1], folder, file, chunk[0])

    # receber respostas
    # for chunk in handledChunks:
    #     pass


# efetuar uma transferência
def handleTransfer(tcp_socket: socket.socket, file: str, locations: Pombo, folder: str):
    availableChunks = AvailableChunks(chunkNr(locations))

    # criar o ficheiro e alocar o tamanho correto
    with open(folder + "/" + file, 'wb') as f:
        f.seek(availableChunks.getSize()-1)
        f.write(b'\0')
        f.flush()
        f.close()

    # criar array de threads de modo a esperar pelas mesmas
    threads: list[threading.Thread] = list()

    # criar threads para efetuar a transferência de chunks
    for l in locations:
        t = threading.Thread(target=handleChunkTransfer,
                             args=(tcp_socket, file, l, availableChunks, folder))
        t.start()
        threads.append(t)

    # aguardar que as threads terminem
    for t in threads:
        t.join()


# efetuar o comando "get"
def handleGet(s: socket.socket, file: str, folder: str):
    # ask tracker for file locations
    pombo: Pombo = [(file, set())]
    message = TCPombo.createCall("", pombo)
    s.send(message)

    # receive response
    data = TCPombo.receiveTCPombo(s)
    print("\n\nGet:", TCPombo.toString(data))

    if (data):
        # check if file was found
        locations = TCPombo.getPombo(data)
        if locations == []:
            print("File not found.")
            return

        # handle file transfer
        handleTransfer(s, file, TCPombo.getPombo(data), folder)


# SERVIDOR UDP


# servidor UDP: recebe calls e responde com chirps
def handleServer(folder: str):
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

        print("\n\nServer:", UDPombo.toString(data))

        # se data não for vazio ou end of file
        if data:
            # obter informações do pedido
            file = UDPombo.getFileName(data)
            chunk_nr = UDPombo.getChunk(data)

            # obter o chunk do ficheiro pedido
            with open(folder + "/" + file, "rb") as f:
                f.seek(chunk_nr * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)

            # criar mensagem de resposta
            message = UDPombo.createChirp(chunk_nr, file, chunk_data)
            s.sendto(message, addr)


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

    # close connection
    tcp_socket.close()
    # stop server
    t.join(timeout=0.1)


main()
