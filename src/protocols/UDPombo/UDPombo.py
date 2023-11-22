import time


class UDPombo:
    """
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
    - timestamp: used to calculate the RTT
    - chunk: used to carry the chunk number
    - file name: used to carry the name of the file
    - data: used to carry a chunk of a file (for chirps)
    """

    # create protocol message

    @staticmethod
    def __createUDPombo(chirp: bool, chunk: int, file: str, data: bytes, timeStamp=0):
        # calculate length
        # length + chirp + timestamp + chunk + file name + \0 + data
        l = 4 + 1 + 8 + 4 + len(file) + 1 + len(data)

        # create UDPombo
        udpombo = bytearray()
        udpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        udpombo.append(chirp)  # chirp

        if timeStamp == 0:
            udpombo.extend(int(round(time.time() * 1000)
                               ).to_bytes(8, byteorder="big"))  # timestamp (long)
        else:
             udpombo.extend(timeStamp.to_bytes(8,byteorder='big'))
        
        udpombo.extend(chunk.to_bytes(4, byteorder="big"))  # chunk
        udpombo.extend((file + "\0").encode())  # file name + \0
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
    def getFileName(data: bytes):
        b_array = bytearray(data)[13:]

        f_name = ""
        b: str = b_array[0:1].decode()
        while b != "\0":
            f_name += b
            b_array = b_array[1:]
            b = b_array[0:1].decode()

        return f_name

    @staticmethod
    def getData(data: bytes):
        overhead = 13 + len(UDPombo.getFileName(data)) + 1
        return data[overhead:]

    # to string
    @staticmethod
    def toString(udpombo: bytes):
        r = ""
        if UDPombo.isChirp(udpombo):
            r += "('> Chirp! "
        else:
            r += "('> Call! "
        r += "Here's a message with " + \
            str(UDPombo.getLength(udpombo)) + " bytes! I'm "
        if UDPombo.isChirp(udpombo):
            r += "carrying"
        else:
            r += "asking for"
        r += " chunk number " + str(UDPombo.getChunk(udpombo)) + " of " + UDPombo.getFileName(udpombo) + "."
        return r
