import threading
import socket

from src.FS_Node.TimeOutChunk import TimeOutChunk

from typing import Dict

from src.FS_Node.TransferEfficiency import TransferEfficiency

class ChunksToReceive:
    def __init__(self, node_name: str, file: str, chunks: list[int], hashes: list[bytes], ip: str, udp_socket: socket.socket, transferEfficiency: TransferEfficiency):
        self.lock = threading.Lock()
        self.dictionary: Dict[int, tuple[bytes, TimeOutChunk]] = {}
        self.transferEfficiency = transferEfficiency
        self.node_name = node_name
        for c in chunks:
            timeout = TimeOutChunk(node_name, c, file, ip, udp_socket, transferEfficiency)
            self.dictionary[c] = (hashes[c], timeout)
            timeout.start()

    def getChunk(self, chunk_nr: int):
        with self.lock:
            return self.dictionary.get(chunk_nr)

    def removeChunk(self, chunk_nr: int, time: int):
        with self.lock:
            # interromper o timeout
            self.dictionary[chunk_nr][1].interrupt()
            # remover o chunk do dicionário
            del self.dictionary[chunk_nr]
            # adicionar o tempo de transferência ao transferEfficiency
            self.transferEfficiency.addTransfer(self.node_name, time)

    def isEmpty(self):
        with self.lock:
            return len(self.dictionary) == 0
        
    def destroy(self):
        with self.lock:
            for chunk in self.dictionary.values():
                chunk[1].interrupt()
            self.dictionary.clear()
