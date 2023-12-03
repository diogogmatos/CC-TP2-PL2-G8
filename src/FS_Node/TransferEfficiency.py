import threading
from typing import Dict

class TransferEfficiency:
    def __init__(self):
        self.lock = threading.Lock()
        # key: node name, value: (total nr of transfers, sum of transfer times, nr of lost transfers)
        self.dict: Dict[str, tuple[int, int, int]] = dict()

    def addTransfer(self, node: str, time: int):
        with self.lock:
            if node not in self.dict:
                self.dict[node] = (0, 0, 0)
            self.dict[node] = (self.dict[node][0] + 1, self.dict[node][1] + time, self.dict[node][2])

    def addLostTransfer(self, node: str):
        with self.lock:
            if node not in self.dict:
                self.dict[node] = (0, 0, 0)
            self.dict[node] = (self.dict[node][0] + 1, self.dict[node][1], self.dict[node][2] + 1)

    # devolve o RTT médio de um nó
    def getAverageTransferTime(self, node: str):
        with self.lock:
            if node not in self.dict:
                self.dict[node] = (0, 0, 0)
            if self.dict[node][0] == 0:
                return 0
            return self.dict[node][1] / self.dict[node][0]
        
    # devolve o ratio de transferências bem sucedidas (0-1) de um nó
    def getSucceededRatio(self, node: str):
        with self.lock:
            if node not in self.dict:
                self.dict[node] = (0, 0, 0)
            if self.dict[node][0] == 0:
                return 0
            return 1 - (self.dict[node][2] / self.dict[node][0])
