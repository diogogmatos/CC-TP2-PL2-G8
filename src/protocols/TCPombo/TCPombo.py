import pickle


class TCPombo:
    """
    ### TCPombo Protocol
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
    - data: used to carry messages between client and server
    """

    # handle bytes

    @staticmethod
    def __toBytes(data):
        d: bytes
        if (type(data) == str):
            d = data.encode()
        elif (type(data) == list):
            s = '|'.join(data)
            d = s.encode()
        else:
            raise ValueError("Data must be a list or a string.")

        return d

    @staticmethod
    def __fromBytes(data: bytes):
        s = data.decode()
        if (s.find('|') == -1):
            d = s
        else:
            d = s.split('|')
        return d

    # create protocol message

    @staticmethod
    def __createTCPombo(chirp: bool, data):
        # turn data into bytes
        d = TCPombo.__toBytes(data)

        # calculate length
        l = 5 + len(d)

        # create TCPombo
        tcpombo = bytearray()
        tcpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        tcpombo.append(chirp)  # chirp
        tcpombo.extend(d)  # data (in bytes)

        return tcpombo

    @staticmethod
    def createChirp(data):
        return bytes(TCPombo.__createTCPombo(True, data))

    @staticmethod
    def createCall(data):
        return bytes(TCPombo.__createTCPombo(False, data))

    # gets

    @staticmethod
    def getTCPombo(tcpombo: bytes):
        return bytearray(tcpombo)

    @staticmethod
    def getChirp(tcpombo: bytes):
        return bool(TCPombo.getTCPombo(tcpombo)[4])

    @staticmethod
    def getLength(tcpombo: bytes):
        return int.from_bytes(TCPombo.getTCPombo(tcpombo)[0:4], byteorder="big")

    @staticmethod
    def getData(tcpombo: bytes):
        return TCPombo.__fromBytes(TCPombo.getTCPombo(tcpombo)[5:])

    # to string
    @staticmethod
    def toString(tcpombo: bytes):
        r = ""
        if TCPombo.getChirp(tcpombo):
            r += "('> Chirp! "
        else:
            r += "('> Call! "
        r += "Here's a message with " + \
            str(TCPombo.getLength(tcpombo)) + " bytes!"
        r += "\nData: " + str(TCPombo.getData(tcpombo))
        return r
