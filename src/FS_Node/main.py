import sys  # to get argument input
import socket  # to send via tcp
import os  # to get files in folder

# TCPombo protocol payload
from src.types.Pombo import Pombo

# TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo

# set server port
TCP_PORT = 9090
# set buffer size
BUFFER_SIZE = 1024

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


# handle file transfer
def handleTransfer(s: socket.socket, locations: Pombo):
    print(TCPombo.toStringPombo(locations))


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
        handleTransfer(s, TCPombo.getPombo(data))


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
        s = connectServer(TCP_IP)
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
            pombo.append((file, TCPombo.chunkify(f_bytes)))
    # create message
    message = TCPombo.createChirp("", pombo)
    s.send(message)

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
            handleGet(s, file)
        else:
            print(fail_msg)

    # close connection
    s.close()


main()
