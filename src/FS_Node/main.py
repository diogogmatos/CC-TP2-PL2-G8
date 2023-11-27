import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder
import threading
import hashlib  # para calcular o hash dos blocos
import signal

# dicionário que guarda os chunks que já foram pedidos
from src.FS_Node.AvailableChunks import AvailableChunks
# TCPombo protocol payload
from src.types.Pombo import PomboFiles, PomboLocations, PomboUpdate
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
# NOTA: não sabe que chunk vai receber ent n sabe que chunk pedir quando faz timeout
def receiveChunk(tcp_socket: socket.socket, udp_socket: socket.socket, addr: tuple[str,int], folder: str, file_name: str, chunk_nr: int, expected_hash: bytes):
    valid = False
    limit = 5

    # file_name: str
    # chunk_nr: int
    
    # enquanto verificações não forem bem sucedidas
    while not valid and limit > 0:

        valid = True
        
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
                print("calculated hash:", calculated_hash.hex())

                if calculated_hash == expected_hash:

                    # escrever chunk para ficheiro
                    with open(folder + "/" + file_name, 'r+b') as f:
                        f.seek(chunk_nr * CHUNK_SIZE)
                        f.write(UDPombo.getData(udpombo))
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

        if not valid and limit > 0:
            CALL = UDPombo.createCall(chunk_nr, file_name)
            udp_socket.sendto(CALL, addr)

    if limit > 0:
        print("- transfer succeeded:", chunk_nr)
    else:
        print("- transfer failed:", chunk_nr)


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
def handleChunkTransfer(tcp_socket: socket.socket, file: str, location: tuple[str, set[int]], hashes: list[bytes], availableChunks: AvailableChunks, folder: str):
    # criar socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # pedir chunks do ficheiro
    handledChunks: list[int] = list()
    for chunk in location[1]:

        # bloquear acesso
        availableChunks.lockAquire()

        # verificar que chunk ainda não foi tratado
        if not availableChunks.isChunkHandled(chunk):

            # marcar chunk como tratado
            availableChunks.handleChunk(chunk)

            # desbloquear acesso
            availableChunks.lockRelease()

            # adicionar chunk à lista de chunks visitados
            handledChunks.append(chunk)

            # enviar call para pedir chunk
            addr = (location[0], UDP_PORT)
            s.sendto(UDPombo.createCall(chunk, file), addr)

            # receber chunk pedido
            receiveChunk(tcp_socket, s, addr, folder, file, chunk, hashes[chunk])

    # receber respostas
    # for chunk in handledChunks:
    #     pass


# efetuar uma transferência
def handleTransfer(tcp_socket: socket.socket, file: str, locations: PomboLocations, folder: str):
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
    for l in locations[0]:
        t = threading.Thread(target=handleChunkTransfer,
                             args=(tcp_socket, file, l, locations[1], availableChunks, folder))
        t.start()
        threads.append(t)

    # aguardar que as threads terminem
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
        print("\n\nGet:", TCPombo.toString(data, True))

        # check if file was found
        locations = TCPombo.getPomboLocations(data)
        print("Locations:", TCPombo.bytesListToString(locations[1]))
        print()
        if locations[0] == []:
            print("File not found.")
            return

        # handle file transfer
        handleTransfer(s, file, locations, folder)


# SERVIDOR UDP


# servidor UDP: recebe calls e responde com chirps
def handleServer(folder: str):
    # criar socket udp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # fazer bind da socket à porta de escuta
    s.bind(('', UDP_PORT))

    # esperar, aceitar e responder a pedidos
    run = True
    while run:
        res_bytes: list[bytes] = []
        res_addr: list[tuple[str, int]] = []
        UDPombo.receiveUDPombo(s, res_bytes, res_addr)
        data = res_bytes[0]
        addr = res_addr[0]

        if not UDPombo.isChirp(data):  

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
                    print("chunk_data:", chunk_data)
                    f.close()

                # criar mensagem de resposta
                s.sendto(UDPombo.createChirp(chunk_nr, file, chunk_data), addr)

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
