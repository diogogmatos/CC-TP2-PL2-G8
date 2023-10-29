import sys  # to get argument input
import socket  # to send via tcp
import pickle  # to serialize objects into bytes

# import TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo

# TODO:
# - fazer o node informar o tracker sobre os ficheiros que tem disponível, inicialmente e à medida que vai recebendo novos
# - fazer o node ser um servidor udp


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

    # establishing connection print
    print("Establishing TCPombo Connection with Server @",
          TCP_IP + ":" + str(TCP_PORT) + "...")

    # establish inicial tcp connection with server
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s1.connect((TCP_IP, TCP_PORT))
    except socket.error as e:
        print("Error connecting to server:", e)
        return

    # receive dedicated port to connect to from server
    data = s1.recv(BUFFER_SIZE)
    dedicatedPort: socket._RetAddress = pickle.loads(data).getData()

    # close inicial connection
    s1.close()

    # establish dedicated tcp connection with server
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s2.connect((TCP_IP, dedicatedPort))
    except socket.error as e:
        print("Error connecting to server on port", dedicatedPort, ":", e)
        return

    # connection established print
    print("\n  ww     ///")
    print(" ('>     <')")
    print(" (//)   (\\\\)")
    print("--oo-----oo--")
    print("TCPombo Connection with Server @",
          TCP_IP + ":" + str(dedicatedPort))

    # set message to send
    string = "Hello World!"
    m = TCPombo.createChirp(string)
    # serialize message into bytes with pickle.dumps()
    MESSAGE = pickle.dumps(m)

    # send message
    s2.send(MESSAGE)

    # wait for / receive response
    data = s2.recv(BUFFER_SIZE)

    # close connection
    # s2.send(pickle.dumps(TCPombo.createChirp("quit")))
    # s2.close()

    # decode binary data with picke.loads()
    tcpombo: TCPombo = pickle.loads(data)

    # print data
    print(tcpombo)  # print protocol message
    print("Data:", tcpombo.getData())  # print transported data

    while 1:
        pass


main()
