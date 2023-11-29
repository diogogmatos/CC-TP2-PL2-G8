import threading
import socket
import time

from src.protocols.UDPombo.UDPombo import UDPombo
from src.protocols.utils import UDP_PORT, TIMEOUT_TIME

class TimeOutChunk(threading.Thread):
    def __init__(self, chunk_nr: int, file_name: str, ip: str, udp_socket: socket.socket):
        super().__init__()
        self.chunk_nr = chunk_nr
        self.file_name = file_name
        self.addr = (ip, UDP_PORT)
        self.udp_socket = udp_socket
        self.interrupted = False
        self.limit = 5

    def interrupt(self):
        self.interrupted = True

    def send_chunk(self):
        self.udp_socket.sendto(UDPombo.createCall([self.chunk_nr], self.file_name), self.addr)

    def timeout_handler(self):
        if not self.interrupted and self.limit > 0:
            print("- timeout on chunk", self.chunk_nr)
            self.limit -= 1
            self.send_chunk()
            self.run()
        elif self.limit == 0:
            print("- transfer failed:", self.chunk_nr)

    def run(self):
        time.sleep(TIMEOUT_TIME)
        self.timeout_handler()
