import sys  # to get argument input
import socket  # to send via tcp
import time

# TCPombo protocol payload
from src.types.Pombo import Pombo

# TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo

# TODO:
# - fazer o node informar o tracker sobre os ficheiros que tem disponível, inicialmente e à medida que vai recebendo novos
# - fazer o node ser um servidor udp


# establish connection with server
def connectServer(TCP_IP: str, TCP_PORT: int, BUFFER_SIZE: int):
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


def main():
    if len(sys.argv) < 3:
        return False

    # get command arguments
    folder = sys.argv[1]
    server_ip = sys.argv[2]

    # set server ip
    TCP_IP = server_ip
    TCP_PORT = 9090

    # set buffer size
    BUFFER_SIZE = 1024

    # establish connection with server
    try:
        s = connectServer(TCP_IP, TCP_PORT, BUFFER_SIZE)
    except ValueError as e:
        print(e)
        return

    # FOR TESTING ONLY:

    # set message to send
    pombo1: Pombo = [("file3", {1, 2, 3}), ("file4", {4, 5, 6})]

    # create message
    MESSAGE1 = TCPombo.createChirp(pombo1)

    # send message
    s.send(MESSAGE1)

    time.sleep(2)

    pombo2: Pombo = [("file5", {4, 5, 6}), ("file6", {1, 2, 3})]
    MESSAGE2 = TCPombo.createChirp(pombo2)
    s.send(MESSAGE2)

    time.sleep(2)

    pombo3: Pombo = [("file3", set())]
    MESSAGE3 = TCPombo.createCall(pombo3)
    s.send(MESSAGE3)

    tcpombo_response = s.recv(BUFFER_SIZE)

    print(TCPombo.toString(tcpombo_response))

    # END OF TEST

    # close connection
    s.close()


main()
