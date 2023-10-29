import pickle

from ..utils import ordinalSuffix

# TODO: make methods: createChirp(), createCall()


class TCPombo:
    """
    ### TCPombo Protocol
    - chirp: flag used to send a chirp, i.e. used to communicate information
    - call: flag used to send a call, i.e. used to request information
    - flock (old): flag used to identify a flock, i.e. to identify a piece of a message that was divided in smaller segments
    - pigeon(old): used to track the segments of a message in a flock, i.e. the segment number
    - length: used to carry the length of the segment in bytes
    - data: used to carry messages between client and server
    """

    def __init__(self, chirp: bool, kiss:bool, length: int, data: bytes):
        self.chirp = chirp
        self.kiss = kiss
        self.length = length
        self.data = data

   # create a chirp or call

    @staticmethod
    def createChirp(data, kiss:bool):
        d: bytes = pickle.dumps(data)  # serialize data into bytes
        return TCPombo(True, kiss, len(d), d)

    @staticmethod
    def createCall(data):
        d: bytes = pickle.dumps(data)  # serialize data into bytes
        return TCPombo(False, False, len(d), d)

    # get's & set's

    def isChirp(self):
        return self.chirp

    def getLength(self):
        return self.length

    def getData(self):
        # deserialize data from bytes and return
        return pickle.loads(self.data)

    # to string
    def __str__(self):
        r = ""
        if self.chirp:
            r += "('> Chirp! "
        else:
            r += "('> Call! "
        r += "Here's " + str(self.length) + " bytes of data!"
        return r
