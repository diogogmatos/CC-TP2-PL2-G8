import socket  # to send via tcp
import signal  # to handle signals
import sys  # to exit gracefully
import threading  # to

# import TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo

# TODO:
# - make the tracker actually receive and store information about what files each node has available
# - modularize the connection handling code

TCP_IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 9090
BUFFER_SIZE = 1024


def handleNode(conn, addr):
    # connection established print
    print("\nTCPombo Connection with Client @",
          addr[0] + ":" + str(addr[1]))

    # listen for messages from client
    run = True
    while run:
        # receive message
        data = conn.recv(4)
        length = int.from_bytes(data, byteorder="big")
        l = 4
        while l < length:  # exit the loop when all data has been received
            chunk = conn.recv(BUFFER_SIZE)
            l += len(chunk)
            data += chunk

        # if data was actually received
        if data:
            # check if client wants to disconnect
            if TCPombo.getData(data) == "quit":
                # disconnect print
                print("\nClient @", addr[0] + ":" +
                      str(addr[1]), "disconnected.")
                run = False
            else:
                # print data
                print()
                print(TCPombo.toString(data))

                # send response message
                response = "Hello " + str(addr[0]) + ":" + str(addr[1]) + "!"
                conn.send(TCPombo.createChirp(response))

    # close connection
    conn.close()


def main():
    # define a signal handler function
    def signal_handler(sig, frame):
        if (sig == 2):
            print("\b\b  \nReceived exit signal. Flying away...")
            sys.exit(0)

    # register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # listen for connections with the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(5)  # 5 = max number of connections

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
        threading.Thread(target=handleNode, args=(conn, addr)).start()


main()
