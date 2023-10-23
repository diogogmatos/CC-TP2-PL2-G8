import sys  # to get argument input
import socket  # to send via tcp
import pickle  # to serialize objects into bytes

# import TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo


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

    # set message to send
    string = "Hello World!"
    m = TCPombo(True, False, len(string), string)
    # serialize message into bytes with pickle.dumps()
    MESSAGE = pickle.dumps(m)

    # establish tcp connection with server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))

    # connection established print
    print("  ww     ///")
    print(" ('>     <')")
    print(" (//)   (\\\\)")
    print("--oo-----oo--")
    print("TCPombo Connection with Server @", TCP_IP + ":" + str(TCP_PORT))

    # send message
    s.send(MESSAGE)

    # wait for / receive response
    data = s.recv(BUFFER_SIZE)

    # close connection
    s.close()

    # decode binary data with picke.loads()
    tcpombo: TCPombo = pickle.loads(data)

    # print data
    print(tcpombo)  # print protocol message
    print("Data:", tcpombo.getData())  # print transported data


main()
