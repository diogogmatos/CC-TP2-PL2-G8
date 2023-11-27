import socket

from src.types.Pombo import Pombo  # tipo do payload do protocolo TCPombo

BUFFER_SIZE = 1024

class TCPombo:
    """
    ### TCPombo Protocol
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
    - node name: used to carry the name of the node that sent the message
    - data: used to carry the payload of the message
    """

    @staticmethod
    def receiveTCPombo(s: socket.socket):
        # receive message length
        tcpombo = s.recv(4)

        # if data was actually received
        if tcpombo:
            length = int.from_bytes(tcpombo, byteorder="big")
            l = 4

            # receive all the message, even if it's bigger than the buffer size
            while l < length:
                chunk = s.recv(BUFFER_SIZE)
                l += len(chunk)
                tcpombo += chunk
        
        return tcpombo

    # handle bytes

    # Pombo: [('f1', {(0, b'hash1'), (1, b'hash2')}), ('f2', {(2, b'hash3'), (3, b'hash4')})]
    # bytes: f1\00hash11hash2\nf2\02hash33hash4

    # converter payload de Pombo para bytes
    @staticmethod
    def __toBytes(data: Pombo):
        # criar bytearray para guardar dados
        b_array: bytearray = bytearray()

        # adicionar ficheiros e seus blocos
        i = 0
        file_nr = len(data)
        for f in data:
            # adicionar nome do ficheiro e \0 para separar nome de blocos
            b_array.extend((f[0] + "\0").encode())

            # adicionar blocos
            for (b_id, b_hash) in f[1]:
                b_array.extend(b_id.to_bytes(4, byteorder="big"))
                b_array.extend(b_hash)

            i += 1
            if i < file_nr:
                # adicionar \n para separar ficheiros
                b_array.extend("\n".encode())

        # converter bytearray para bytes
        b = bytes(b_array)

        return b

    # converter payload de bytes para Pombo
    @staticmethod
    def __fromBytes(data: bytes) -> Pombo:
        # criar Pombo
        p: Pombo = list()

        b_array = bytearray(data)
        while len(b_array) > 0:
            f_name = ""
            b: str = b_array[0:1].decode()
            while b != "\0":
                f_name += b
                b_array = b_array[1:]
                b = b_array[0:1].decode()

            # blocos
            f_blocks: set[tuple[int, bytes]] = set()
            b_array = b_array[1:]
            while len(b_array) > 0 and b_array[0:1].decode() != "\n":
                # nr do bloco
                block_nr = int.from_bytes(b_array[0:4], byteorder="big")
                # hash do bloco
                block_hash = bytes(b_array[4:24])
                # adicionar bloco
                f_blocks.add((block_nr, block_hash))
                # avançar array
                b_array = b_array[24:]

            # adicionar ficheiro e seus blocos
            p.append((f_name, f_blocks))

            # avançar array (para passar o \n)
            if len(b_array) > 0:
                b_array = b_array[1:]

        return p

    # create protocol message

    @staticmethod
    def __createTCPombo(chirp: bool, node: str, data: Pombo):
        # turn data into bytes
        d = TCPombo.__toBytes(data)

        # calculate length
        # length + chirp + node name + \0 + payload
        l = 4 + 1 + len(node) + 1 + len(d)

        # create TCPombo
        tcpombo = bytearray()
        tcpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        tcpombo.append(chirp)  # chirp
        tcpombo.extend((node + "\0").encode())  # node name + \0
        tcpombo.extend(d)  # data (in bytes)

        return tcpombo

    @staticmethod
    def createChirp(node: str, data: Pombo):
        return bytes(TCPombo.__createTCPombo(True, node, data))

    @staticmethod
    def createCall(node: str, data: Pombo):
        return bytes(TCPombo.__createTCPombo(False, node, data))

    # gets

    @staticmethod
    def getLength(tcpombo: bytes):
        return int.from_bytes(bytearray(tcpombo)[0:4], byteorder="big")

    @staticmethod
    def isChirp(tcpombo: bytes):
        return bool(bytearray(tcpombo)[4])

    @staticmethod
    def getName(tcpombo: bytes):
        b_array = bytearray(tcpombo)[5:]

        f_name = ""
        b: str = b_array[0:1].decode()
        while b != "\0":
            f_name += b
            b_array = b_array[1:]
            b = b_array[0:1].decode()

        return f_name

    @staticmethod
    def getPombo(tcpombo: bytes) -> Pombo:
        # length + chirp + node name + \0
        overhead = 5 + len(TCPombo.getName(tcpombo)) + 1
        return TCPombo.__fromBytes(bytearray(tcpombo)[overhead:])

    # toString

    # Pombo
    @staticmethod
    def toStringPombo(pombo: Pombo):
        l = list()
        for f in pombo:
            s = set()
            for b in f[1]:
                s.add(b[0])
            l.append((f[0], s))
        return str(l)

    # TCPombo
    @staticmethod
    def toString(tcpombo: bytes):
        r = ""
        if TCPombo.isChirp(tcpombo):
            r += "('> Chirp! "
        else:
            r += "('> Call! "
        r += "Here's a message from " + \
            TCPombo.getName(tcpombo) + " with " + \
            str(TCPombo.getLength(tcpombo)) + " bytes!"
        r += "\nData: " + str(TCPombo.toStringPombo(TCPombo.getPombo(tcpombo)))
        return r
