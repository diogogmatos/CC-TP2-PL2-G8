import threading
import socket

from src.FS_Node.TimeOutChunk import TimeOutChunk

from typing import Dict

class ChunksToReceive:
    def __init__(self, file: str, chunks: list[int], hashes: list[bytes], ip: str, udp_socket: socket.socket):
        self.lock = threading.Lock()
        self.dictionary: Dict[int, tuple[bytes, TimeOutChunk]] = {}
        for c in chunks:
            timeout = TimeOutChunk(c, file, ip, udp_socket)
            timeout.start()
            self.dictionary[c] = (hashes[c], timeout)

    def getChunk(self, chunk_nr: int):
        return self.dictionary.get(chunk_nr)

    def removeChunk(self, chunk_nr: int):
        del self.dictionary[chunk_nr]

    def isEmpty(self):
        return len(self.dictionary) == 0
