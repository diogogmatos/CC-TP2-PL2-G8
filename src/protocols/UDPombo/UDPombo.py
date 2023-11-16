import time

class UDPombo:
    """
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
    - timestamp: used to calculate the RTT
    - file name: used to carry the name of the file
    - chunks: 
    - data: used to carry a chunk of a file
    """

    # create protocol message

    @staticmethod
    def __createUDPombo(chirp: bool, chunk: int, file: str, data: bytes):
        # calculate length
        # length + chirp + timestamp + chunk + file name length + file name + data
        l = 4 + 1 + 4 + 4 + 4 + len(file) + len(data)

        # create UDPombo
        udpombo = bytearray()
        udpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        udpombo.append(chirp) # chirp
        udpombo.extend(int(round(time.time() * 1000)).to_bytes(4, byteorder="big")) # timestamp
        udpombo.extend(chunk.to_bytes(4, byteorder="big")) # chunk
        udpombo.extend(len(file).to_bytes(4, byteorder="big")) # file name length
        udpombo.extend(file.encode()) # file name
        udpombo.extend(data)

        return udpombo

    @staticmethod
    def createChirp(chunk: int, file: str, data: bytes):
        return UDPombo.__createUDPombo(True, chunk, file, data)

    @staticmethod
    def createCall(chunk: int, file: str):
        return UDPombo.__createUDPombo(False, chunk, file, b'')

    # gets

    @staticmethod
    def getLength(data: bytes):
        return int.from_bytes(data[0:4], byteorder="big")

    @staticmethod
    def isChirp(data: bytes):
        return bool(bytearray(data)[4])

    @staticmethod
    def getTimestamp(data: bytes):
        return int.from_bytes(data[5:9], byteorder="big")
    
    @staticmethod
    def getChunk(data: bytes):
        return int.from_bytes(data[9:13], byteorder="big")
    
    @staticmethod
    def getFileNameLength(data: bytes):
        return int.from_bytes(data[13:17], byteorder="big")
    
    @staticmethod
    def getFileName(data: bytes):
        nameLength = UDPombo.getFileNameLength(data)
        return bytearray(data)[17:17+nameLength].decode()

    @staticmethod
    def getData(data: bytes):
        overhead = 17 + UDPombo.getFileNameLength(data)
        return data[overhead:]

    # to string
    @staticmethod
    def toString(udpombo: bytes):
        r = ""
        if UDPombo.isChirp(udpombo):
            r += "('> Chirp! "
        else:
            r += "('> Call! "
        r += "Here's a message from with " + \
            str(UDPombo.getLength(udpombo)) + " bytes!"
        return r
