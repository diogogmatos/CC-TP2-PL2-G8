import socket  # to send via tcp
import pickle  # to serialize objects into bytes
import signal  # to handle signals
import sys  # to exit gracefully

# import TCPombo protocol
from src.protocols.TCPombo.TCPombo import TCPombo

# TODO: usar sinais para encerrar "graciosamente" o servidor


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
    s.listen(1)

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

        # connection established print
        print("\nTCPombo Connection with Client @",
              addr[0] + ":" + str(addr[1]))

        # receive message
        data = conn.recv(BUFFER_SIZE)

        # if data was actually received
        if data:
            # decode binary data with pickle.loads()
            tcpombo: TCPombo = pickle.loads(data)

            # print data
            print(tcpombo)  # print protocol message
            print("Data:", tcpombo.getData())  # print transported data

            # send response message
            response = "Hello " + str(addr[0]) + ":" + str(addr[1]) + "!"
            conn.send(pickle.dumps(
                TCPombo(True, False, len(response), response)))

        # close connection (unreachable for now)
        conn.close()


main()
