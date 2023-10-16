from ..utils import ordinalSuffix

# TODO: make methods: createChirp(), createCall()


class TCPombo:
    # chirp: flag used to send a chirp, i.e. used to communicate information
    # call: flag used to send a call, i.e. used to request information
    # flock: flag used to identify a flock, i.e. to identify a piece of a message that was divided in smaller segments
    # pigeon: used to track the segments of a message in a flock, i.e. the segment number
    # length: used to carry the length of the segment in bytes
    # data: used to carry messages between client and server
    def __init__(self, chirp: bool, call: bool, flock: bool, pigeon: int, length: int, data):
        self.chirp = chirp
        self.call = call
        self.flock = flock
        self.pigeon = pigeon
        self.length = length
        self.data = data

    # get & set
    def isChirp(self):
        return self.chirp

    def isCall(self):
        return self.call

    def isFlock(self):
        return self.flock

    def getPigeon(self):
        return self.pigeon

    def getLength(self):
        return self.length

    def getData(self):
        return self.data

    # to string
    def __str__(self):
        r = ""
        if self.chirp:
            r += "('> Chirp! "
        if self.call:
            r += "('> Call! "
        if self.flock:
            r += "I'm the " + \
                ordinalSuffix(self.pigeon) + " member of a flock. "
        r += "Here's " + str(self.length) + " bytes of data!"
        return r
