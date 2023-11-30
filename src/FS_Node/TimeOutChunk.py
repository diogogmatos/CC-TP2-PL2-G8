import threading
import socket

from src.protocols.UDPombo.UDPombo import UDPombo
from src.protocols.utils import UDP_PORT, TIMEOUT_TIME

class TimeOutChunk(threading.Thread):
    def __init__(self, chunk_nr: int, file_name: str, ip: str, udp_socket: socket.socket):
        super().__init__()
        self.chunk_nr = chunk_nr
        self.file_name = file_name
        self.addr = (ip, UDP_PORT)
        self.udp_socket = udp_socket
        self.interrupt_event = threading.Event()
        self.limit = 5

    def interrupt(self):
        print("INTERRUPTED TIMEOUT")
        self.interrupt_event.set()

    def send_chunk(self):
        self.udp_socket.sendto(UDPombo.createCall([self.chunk_nr], self.file_name), self.addr)

    def timeout_handler(self):
        print("- timeout on chunk", self.chunk_nr)
        self.limit -= 1
        self.send_chunk()
        self.run()

    def run(self):
        try:
            if not self.interrupt_event.wait(timeout=TIMEOUT_TIME):
                print("PROCEEDED WITH TIMEOUT")
                self.timeout_handler()
        finally:
            print("EXITED TIMEOUT")
            self.udp_socket.close()
