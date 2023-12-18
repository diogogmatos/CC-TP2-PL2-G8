import threading
import socket

from src.FS_Node.TimeOutChunk import TimeOutChunk
from typing import Dict
from src.FS_Node.TransferEfficiency import TransferEfficiency
from src.protocols.utils import getNodeFromChunk

class ChunksToReceive:
    def __init__(self, file_name: str, chunks: list[int], hashes: list[bytes], udp_socket: socket.socket, transferEfficiency: TransferEfficiency, divisionOfChunks: Dict[str, list[int]]):
        self.lock = threading.Lock()
        self.dictionary: Dict[int, tuple[bytes, TimeOutChunk]] = {}
        self.transferEfficiency = transferEfficiency
        for c in chunks:
            node_name = getNodeFromChunk(c, divisionOfChunks)
            timeout = TimeOutChunk(node_name, c, file_name, udp_socket, transferEfficiency)
            self.dictionary[c] = (hashes[c], timeout)
            timeout.start()

    def startTimeouts(self):
        with self.lock:
            for chunk in self.dictionary.values():
                chunk[1].start()

    def getChunk(self, chunk_nr: int):
        with self.lock:
            return self.dictionary.get(chunk_nr)

    def removeChunk(self, chunk_nr: int):
        with self.lock:
            # interromper o timeout
            self.dictionary[chunk_nr][1].interrupt()
            # remover o chunk do dicionário
            del self.dictionary[chunk_nr]

    def isEmpty(self):
        with self.lock:
            return len(self.dictionary) == 0
        
    def destroy(self):
        with self.lock:
            for chunk in self.dictionary.values():
                chunk[1].interrupt()
            self.dictionary.clear()
