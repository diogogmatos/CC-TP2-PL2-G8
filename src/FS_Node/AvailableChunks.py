from typing import Dict  # to use typing for dictionaries
import threading

class AvailableChunks:
    def __init__(self, chunkNr: int):
        self.chunks: Dict[int, bool] = dict()
        for i in range(0, chunkNr):
            self.chunks[i] = False
        self.lock = threading.Lock()

    def addAll(self, chunkNr: int, value: bool = False):
        self.lock.acquire()
        try:
            for i in range(0, chunkNr):
                self.chunks[i] = value
        finally:
            self.lock.release()

    def handleChunk(self, chunk: int):
        self.lock.acquire()
        try:
            self.chunks[chunk] = True
        finally:
            self.lock.release()

    def isChunkHandled(self, chunk: int):
        self.lock.acquire()
        try:
            return self.chunks[chunk]
        finally:
            self.lock.release()
