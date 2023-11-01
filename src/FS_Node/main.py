import sys  # to get argument input
import socket  # to send via tcp



# import TCPombo protocol
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

    # set message to send
    listFiles = list()  # TODO: get files from folder
    listFiles.append("file1")
    listFiles.append("file2")

    # create message
    MESSAGE = TCPombo.createChirp(listFiles)

    # send message
    s.send(MESSAGE)

    # wait for / receive response
    tcpombo = s.recv(BUFFER_SIZE)

    # close connection
    s.send((TCPombo.createChirp("quit")))
    s.close()

    # print data
    print(TCPombo.toString(tcpombo))

main()
