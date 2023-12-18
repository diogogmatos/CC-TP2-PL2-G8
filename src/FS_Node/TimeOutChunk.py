import threading
import socket

from src.protocols.UDPombo import UDPombo
from src.protocols.utils import UDP_PORT, TIMEOUT_TIME, TIMEOUT_LIMIT
from src.FS_Node.TransferEfficiency import TransferEfficiency
from src import dns

class TimeOutChunk(threading.Thread):
    def __init__(self, node_name: str, chunk_nr: int, file_name: str, udp_socket: socket.socket, transferEfficiency: TransferEfficiency):
        super().__init__()
        self.node_name = node_name
        self.chunk_nr = chunk_nr
        self.file_name = file_name
        self.udp_socket = udp_socket
        self.transferEfficiency = transferEfficiency
        self.interrupt_event = threading.Event()
        self.time = TIMEOUT_TIME
        self.limit = TIMEOUT_LIMIT

    def interrupt(self):
        self.interrupt_event.set()

    def send_chunk(self):
        self.udp_socket.sendto(UDPombo.createCall([self.chunk_nr], self.file_name), (dns.getHostByName(self.node_name), UDP_PORT))

    def timeout_handler(self):
        print("- timeout on chunk", self.chunk_nr)
        self.limit -= 1 # decremento do limite de timeouts
        self.transferEfficiency.addLostTransfer(self.node_name) # incremento do número de timeouts
        self.send_chunk() # reenvio do chunk
        self.run() # reinício do timeout

    def run(self):
        if not self.interrupt_event.wait(timeout=self.time):
            if self.limit > 0:
                self.timeout_handler()
