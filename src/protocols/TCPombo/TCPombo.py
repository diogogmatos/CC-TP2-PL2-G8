from src.types.Pombo import Pombo  # tipo do payload do protocolo TCPombo
import hashlib  # para calcular o hash dos blocos

CHUNK_SIZE = 1024  # tamanho dos chunks em bytes


class TCPombo:
    """
    ### TCPombo Protocol
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
    - data: used to carry messages between client and server
    """

    # handle file chunks

    # obter o conjunto de blocos de um ficheiro e a hash de cada um
    @staticmethod
    def chunkify(data: bytes) -> set[tuple[int, bytes]]:
        data_array = bytearray(data)

        # create chunks
        chunks: set[tuple[int, bytes]] = set()
        i = 0
        while i <= (len(data) // CHUNK_SIZE):
            # (id, hash)
            chunks.add((i, hashlib.sha1(data_array[0:CHUNK_SIZE]).digest()))
            data_array = data_array[CHUNK_SIZE:]
            i += 1

        # deal with remaining bytes
        if len(data_array) > 0:
            chunks.add((i, hashlib.sha1(data_array).digest()))

        return chunks

    # handle bytes

    # convert payload data from Pombo to bytes
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

            # adicionar tamanho do set de blocos
            f_blocks = f[1]
            d_array.extend(len(f_blocks).to_bytes(4, byteorder="big"))
            # adicionar blocos
            for (b_id, b_hash) in f_blocks:
                d_array.extend(b_id.to_bytes(4, byteorder="big"))
                d_array.extend(b_hash)

        # converter bytearray para bytes
        d = bytes(d_array)

        return d

    # convert the payload data from bytes to Pombo
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
            f_blocks: set[tuple[int, bytes]] = set()
            d_array = d_array[4:]
            for j in range(f_blocks_length):
                # (id, hash)
                f_blocks.add(
                    (int.from_bytes(d_array[0:4], byteorder="big"), bytes(d_array[4:24])))
                # avancar para o proximo bloco (tuplo[int,bytes])
                d_array = d_array[24:]

            # adicionar ficheiro e seus blocos
            d.append((f_name, f_blocks))

        return d

    # create protocol message

    @staticmethod
    def __createTCPombo(chirp: bool, name: str, data: Pombo):
        # turn data into bytes
        d = TCPombo.__toBytes(data)

        # calculate length
        # length, chirp, name length, name, payload
        l = 4 + 1 + 4 + len(name) + len(d)

        # create TCPombo
        tcpombo = bytearray()
        tcpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        tcpombo.append(chirp)  # chirp
        tcpombo.extend(len(name).to_bytes(4, byteorder="big"))  # name length
        tcpombo.extend(name.encode())  # name
        tcpombo.extend(d)  # data (in bytes)

        return tcpombo

    @staticmethod
    def createChirp(name: str, data: Pombo):
        return bytes(TCPombo.__createTCPombo(True, name, data))

    @staticmethod
    def createCall(name: str, data: Pombo):
        return bytes(TCPombo.__createTCPombo(False, name, data))

    # gets

    @staticmethod
    def getTCPombo(tcpombo: bytes):
        return bytearray(tcpombo)

    @staticmethod
    def isChirp(tcpombo: bytes):
        return bool(TCPombo.getTCPombo(tcpombo)[4])

    @staticmethod
    def getNameLength(tcpombo: bytes):
        return int.from_bytes(TCPombo.getTCPombo(tcpombo)[5:4])

    @staticmethod
    def getName(tcpombo: bytes):
        nameLength = TCPombo.getNameLength(tcpombo)
        return TCPombo.getTCPombo(tcpombo)[9:9+nameLength].decode()

    @staticmethod
    def getLength(tcpombo: bytes):
        return int.from_bytes(TCPombo.getTCPombo(tcpombo)[0:4], byteorder="big")

    # retorna o payload do protocolo (tudo menos os bytes referentes ao cabeçalho)
    @staticmethod
    def getData(tcpombo: bytes):
        overhead = 9 + TCPombo.getNameLength(tcpombo)
        return TCPombo.__fromBytes(TCPombo.getTCPombo(tcpombo)[overhead:])

    # to string
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
        r += "\nData: " + str(TCPombo.toStringPombo(TCPombo.getData(tcpombo)))
        return r

    # Pombo to string
    @staticmethod
    def toStringPombo(pombo: Pombo):
        l = list()
        for f in pombo:
            s = set()
            for b in f[1]:
                s.add(b[0])
            l.append((f[0], s))
        return str(l)
