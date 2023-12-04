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

    def newNode(self, node:str):
        with self.lock:
            if node not in self.dict:
                self.dict[node] = (0, 0, 0)

    def addLostTransfer(self, node: str):
        with self.lock:
            if node not in self.dict:
                self.dict[node] = (0, 0, 0)
            self.dict[node] = (self.dict[node][0], self.dict[node][1], self.dict[node][2] + 1)

    # devolve o RTT médio de um nó
    def getAverageTransferTime(self, node: str):
        with self.lock:
            # Acho que isto não é preciso, pior das hipóteses volta a colocar
            # if node not in self.dict:
            #     self.dict[node] = (0, 0, 0)
            if self.dict[node][0] == 0:
                return 0
            return self.dict[node][1] / self.dict[node][0]
        
    # devolve o ratio de transferências bem sucedidas (0-1) de um nó
    def getSuccessRate(self, node: str):
        with self.lock:
            if node not in self.dict:
                self.dict[node] = (0, 0, 0)
            if self.dict[node][0] == 0:
                return 0
            return 1 - (self.dict[node][2] / (self.dict[node][0] + self.dict[node][2]))
        
    def __str__(self) -> str:
        s = ""
        for node in self.dict:
            s += f"{node}:\n"
            s += f"\tAverage transfer time (ms): {self.getAverageTransferTime(node)}\n"
            s += f"\tSucceeded ratio (%): {self.getSuccessRate(node) * 100}\n"
            s += f"\tTotal transfers: {self.dict[node][0]}\n"
            s += f"\tTotal transfer time (ms): {self.dict[node][1]}\n"
            s += f"\tTotal lost transfers: {self.dict[node][2]}\n"
        return s
