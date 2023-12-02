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
            self.dictionary[c] = (hashes[c], timeout)
            timeout.start()

    def getChunk(self, chunk_nr: int):
        with self.lock:
            return self.dictionary.get(chunk_nr)

    def removeChunk(self, chunk_nr: int):
        with self.lock:
            self.dictionary[chunk_nr][1].interrupt()
            del self.dictionary[chunk_nr]

    def isEmpty(self):
        with self.lock:
            return len(self.dictionary) == 0
        
    def destroy(self):
        with self.lock:
            for chunk in self.dictionary.values():
                chunk[1].interrupt()
            self.dictionary.clear()
