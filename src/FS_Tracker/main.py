import socket  # to send via tcp
import pickle  # to serialize objects into bytes
import signal  # to handle signals
import sys  # to exit gracefully
import threading  # to

# import TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo

# TODO:
# - make the tracker actually receive and store information about what files each node has available
# - modularize the connection handling code


def handleNode(inicialConn, inicialClientAddr, BUFFER_SIZE, TCP_IP):
    # create new socket to communicate with client
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, 0))
    _, newPort = s.getsockname()

    # send new port to client

    inicialConn.send(pickle.dumps(TCPombo.createChirp(newPort, True)))

    # close connection
    inicialConn.close()

    # wait for client to connect to new port
    s.listen(1)  # only 1 client can connect to this socket

    # accept connection
    conn, addr = s.accept()

    # connection established print
    print("\nTCPombo Connection on Port", newPort, "with Client @",
          addr[0] + ":" + str(addr[1]))

    # listen for messages from client
    run = True
    while run:
        # receive message
        data = conn.recv(BUFFER_SIZE)

        # if data was actually received
        if data:
            # decode binary data with pickle.loads()
            tcpombo: TCPombo = pickle.loads(data)

            # check if client wants to disconnect
            if tcpombo.getData() == "quit":
                # disconnect print
                print("\nClient @", addr[0] + ":" +
                      str(addr[1]), "disconnected.")
                run = False
            else:
                # print data
                print()
                print("(" + addr[0] + "):", tcpombo)  # print protocol message
                print("Data:", tcpombo.getData())  # print transported data

                # send response message
                response = "Hello " + str(addr[0]) + ":" + str(addr[1]) + "!"
                conn.send(pickle.dumps(TCPombo.createChirp(response)))

    # close connection
    conn.close()
    # close socket
    s.close()


def main():
    # define a signal handler function
    def signal_handler(sig, frame):
        if (sig == 2):
            print("\b\b  \nReceived exit signal. Flying away...")
            sys.exit(0)

    # register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # set server ip
    TCP_IP = socket.gethostbyname(socket.gethostname())
    TCP_PORT = 9090

    # set buffer size
    BUFFER_SIZE = 1024

    # listen for connections with the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(5)  # 5 = max number of pending connections

    # server active print
    print("  ww")
    print(" ('>")
    print(" (//)")
    print("--oo---------")
    print("Server Active @ " + TCP_IP + ":" + str(TCP_PORT))
    print("Listening for chirps and calls...")

    # wait & accept incoming connections
    while 1:
        # accept connection
        conn, addr = s.accept()

        # start a new thread to handle the connection
        threading.Thread(target=handleNode, args=(
            conn, addr, BUFFER_SIZE, TCP_IP)).start()


main()
