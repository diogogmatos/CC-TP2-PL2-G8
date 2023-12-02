import queue

class ChunksToProcess:
    def __init__(self):
        self.queue: queue.Queue[bytes] = queue.Queue()

    def addChunk(self, data: bytes):
        self.queue.put(data)

    def getChunk(self):
        return self.queue.get()

    def isEmpty(self):
        return self.queue.empty()
