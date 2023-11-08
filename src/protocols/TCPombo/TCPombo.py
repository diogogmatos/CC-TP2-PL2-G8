from src.types.Pombo import Pombo  # tipo do payload do protocolo TCPombo


class TCPombo:
    """
    ### TCPombo Protocol
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
    - data: used to carry messages between client and server
    """

    # handle bytes

    @staticmethod
    def __toBytes(data: Pombo):
        # criar bytearray para guardar dados
        d_array: bytearray = bytearray()

        # adicionar número de ficheiros do array
        file_length = len(data)
        d_array.extend(file_length.to_bytes(4, byteorder="big"))

        # adicionar ficheiros e seus blocos
        for f in data:
            # adicionar tamanho do nome do ficheiro
            f_name = f[0]
            d_array.extend(len(f_name).to_bytes(4, byteorder="big"))
            # adicionar nome do ficheiro
            d_array.extend(f_name.encode())

            # adicionar tamanho do array de blocos
            f_blocks = f[1]
            d_array.extend(len(f_blocks).to_bytes(4, byteorder="big"))
            # adicionar blocos
            for b in f_blocks:
                d_array.extend(b.to_bytes(4, byteorder="big"))

        # converter bytearray para bytes
        d = bytes(d_array)

        return d

    @staticmethod
    def __fromBytes(data: bytes) -> Pombo:
        # converter bytes para bytearray
        d_array: bytearray = bytearray(data)

        # ler número de ficheiros do array
        file_length = int.from_bytes(d_array[0:4], byteorder="big")

        # ler ficheiros e seus blocos
        d_array = d_array[4:]
        d: Pombo = list()
        for i in range(file_length):
            # ler tamanho do nome do ficheiro
            f_name_len = int.from_bytes(d_array[0:4], byteorder="big")

            # ler nome do ficheiro
            f_name = d_array[4:4 + f_name_len].decode()
            d_array = d_array[4 + f_name_len:]

            # ler tamanho do array de blocos
            f_blocks_length = int.from_bytes(d_array[0:4], byteorder="big")

            # ler blocos
            f_blocks = set()
            d_array = d_array[4:]
            for j in range(f_blocks_length):
                f_blocks.add(int.from_bytes(d_array[0:4], byteorder="big"))
                d_array = d_array[4:]

            # adicionar ficheiro e seus blocos
            d.append((f_name, f_blocks))

        return d

    # create protocol message

    @staticmethod
    def __createTCPombo(chirp: bool, data, name:str=""):
        # turn data into bytes
        d = TCPombo.__toBytes(data)

        # calculate length
        l = 9 + len(name) + len(d)

        # create TCPombo
        tcpombo = bytearray()
        tcpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        tcpombo.append(chirp)  # chirp
        tcpombo.extend(len(name).to_bytes(4, byteorder="big"))
        tcpombo.extend(name)
        tcpombo.extend(d)  # data (in bytes)

        return tcpombo

    @staticmethod
    def createChirp(data: Pombo):
        return bytes(TCPombo.__createTCPombo(True, data))

    @staticmethod
    def createCall(data: Pombo):
        return bytes(TCPombo.__createTCPombo(False, data))

    # gets

    @staticmethod
    def getTCPombo(tcpombo: bytes):
        return bytearray(tcpombo)

    @staticmethod
    def isChirp(tcpombo: bytes):
        return bool(TCPombo.getTCPombo(tcpombo)[4])

    @staticmethod
    def getName(tcpombo: bytes):
        length = int.from_bytes(TCPombo.getTCPombo(tcpombo)[5])
        return str(TCPombo.getTCPombo(tcpombo)[9:9+length])

    @staticmethod
    def getLength(tcpombo: bytes):
        return int.from_bytes(TCPombo.getTCPombo(tcpombo)[0:4], byteorder="big")

    @staticmethod
    def getData(tcpombo: bytes):
        nameLength = 9 + int.from_bytes(TCPombo.getTCPombo(tcpombo)[5])
        # retorna o payload do protocolo (tudo menos os primeiros (9 + nameLen) bytes)
        return TCPombo.__fromBytes(TCPombo.getTCPombo(tcpombo)[nameLength:])

    # to string
    @staticmethod
    def toString(tcpombo: bytes):
        r = ""
        if TCPombo.isChirp(tcpombo):
            r += "('> Chirp! "
        else:
            r += "('> Call! "
        r += "Here's a message with " + \
            str(TCPombo.getLength(tcpombo)) + " bytes!"
        r += "\nData: " + str(TCPombo.getData(tcpombo))
        return r
