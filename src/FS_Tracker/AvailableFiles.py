import threading

from typing import Dict
from src.protocols.types import PomboFiles, PomboLocations

Flock = Dict[str, Dict[str, set[int]]]
HashFlock = Dict[str, list[bytes]]

class AvailableFiles:
    def __init__(self):
        self.availableFiles: Flock = dict()
        self.fileHashes: HashFlock = dict()
        self.lock = threading.Lock()

    def addFileBlock(self, file: str, node: str, block: int):
        with self.lock:
            if file not in self.availableFiles:
                self.availableFiles[file] = dict()
            
            if node not in self.availableFiles[file]:
                self.availableFiles[file][node] = set()

            self.availableFiles[file][node].add(block)

    def addFile(self, node: str, pomboFiles: PomboFiles):
        with self.lock:
            for p in pomboFiles:

                blocks: set[int] = set()
                for i in range(p[1][0]):
                    blocks.add(i)

                if p[0] not in self.availableFiles:
                    self.availableFiles[p[0]] = dict()

                self.availableFiles[p[0]][node] = blocks
                self.fileHashes[p[0]] = p[1][1]

    def getFileLocations(self, file: str) -> PomboLocations:
        with self.lock:
            if file in self.availableFiles:
                locations = [(node, self.availableFiles[file][node]) for node in self.availableFiles[file]]
                hashes = self.fileHashes[file]
                return (locations, hashes)
            else:
                return ([], [])

    def removeNode(self, node: str):
        with self.lock:
            for file in self.availableFiles:
                if node in self.availableFiles[file]:
                    del self.availableFiles[file][node]
                    