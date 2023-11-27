import threading
from typing import Dict

class AvailableChunks:
    def __init__(self, chunkNr: int):
        self.chunks: Dict[int, bool] = {i: False for i in range(chunkNr)}
        self.lock = threading.RLock()

    def addAll(self, chunkNr: int, value: bool = False):
        with self.lock:
            for i in range(chunkNr):
                self.chunks[i] = value

    def handleChunk(self, chunk: int):
        self.chunks[chunk] = True

    def isChunkHandled(self, chunk: int):
        return self.chunks[chunk]

    def getSize(self):
        with self.lock:
            return len(self.chunks.keys())
        
    def lockAquire(self):
        self.lock.acquire()

    def lockRelease(self):
        self.lock.release()
