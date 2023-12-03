import socket

from src.protocols.types import PomboFiles, PomboLocations, PomboUpdate

BUFFER_SIZE = 1024


class TCPombo:
    """
    ### TCPombo Protocol
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
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
                chunk = s.recv(min(BUFFER_SIZE, length - l))
                l += len(chunk)
                tcpombo += chunk

        return tcpombo

    # handle bytes

    # PomboFiles: [ ( "file1", ( 4, [hash1, hash2, hash3, hash4] ) ), ( "file2", ( 2, [hash1, hash2] ) ) ]
    # bytes: file1\04hash11hash2hash3hash4file2\02hash1hash2
    @staticmethod
    def __toBytesFiles(data: PomboFiles):
        # criar bytearray para guardar dados
        b_array: bytearray = bytearray()

        # adicionar ficheiros e seus blocos e hash's
        for f in data:

            # adicionar nome do ficheiro e \0 para separar nome de blocos
            b_array.extend((f[0] + "\0").encode())

            # adicionar nr de blocos
            b_array.extend(f[1][0].to_bytes(4, byteorder="big"))

            # adicionar hash's dos blocos
            for b_hash in f[1][1]:
                b_array.extend(b_hash)

        # converter bytearray para bytes
        b = bytes(b_array)

        return b

    
    # PomboLocations: ([("node1", {1, 2, 3}), ("node2", {2, 3, 4})], [hash1, hash2, hash3, hash4])
    # bytes: node1\0123\nnode2\0234\thash1hash2hash3hash4
    @staticmethod
    def __toBytesLocations(data: PomboLocations):
        # criar bytearray para guardar dados
        b_array: bytearray = bytearray()

        # adicionar nodes e os blocos que têm do ficheiro pedido
        i = 0
        node_nr = len(data[0])

        for n in data[0]:

            # adicionar nome do node e \0 para separar nome de blocos
            b_array.extend((n[0] + "\0").encode())

            # adicionar blocos
            for b in n[1]:
                b_array.extend(b.to_bytes(4, byteorder="big"))

            i += 1
            if i < node_nr:
                # adicionar \n para separar nodes
                b_array.extend("\n".encode())

        # adicionar \t para separar os nodes e blocos das hash's
        b_array.extend("\t".encode())

        # adicionar as hahs's dos blocos do ficheiro pedido
        for h in data[1]:
            b_array.extend(h)

        # converter bytearray para bytes
        b = bytes(b_array)

        return b

    @staticmethod
    def __toBytesUpdate(data: PomboUpdate):
        # criar bytearray para guardar dados
        b_array: bytearray = bytearray()

        # adicionar nome do ficheiro e \0 para separar nome do bloco
        b_array.extend((data[0] + "\0").encode())

        # adicionar bloco
        b_array.extend(data[1].to_bytes(4, byteorder="big"))

        # converter bytearray para bytes
        b = bytes(b_array)

        return b
    
    # PomboFiles: [ ( "file1", ( 4, [hash1, hash2, hash3, hash4] ) ), ( "file2", ( 2, [hash1, hash2] ) ) ]
    # bytes: file1\04hash11hash2hash3hash4file2\02hash1hash2
    @staticmethod
    def __fromBytesFiles(data: bytes) -> PomboFiles:
        # criar Pombo
        p: PomboFiles = list()

        b_array = bytearray(data)

        while len(b_array) > 0:

            f_name = ""
            b: str = b_array[0:1].decode()
            while b != "\0":
                f_name += b
                b_array = b_array[1:]
                b = b_array[0:1].decode()

            # nr blocos
            b_array = b_array[1:]
            nr_blocks = int.from_bytes(b_array[0:4], byteorder="big")

            # hash's dos blocos
            b_array = b_array[4:]
            hashes: list[bytes] = list()
            for i in range(nr_blocks):
                hashes.append(bytes(b_array[0:20]))
                b_array = b_array[20:]

            # adicionar ficheiro e seus blocos
            p.append((f_name, (nr_blocks, hashes)))

        return p

    # PomboLocations: ([("node1", {1, 2, 3}), ("node2", {2, 3, 4})], [hash1, hash2, hash3, hash4])
    # bytes: node1\0123\nnode2\0234\thash1hash2hash3hash4
    @staticmethod
    def __fromBytesLocations(data: bytes) -> PomboLocations:
        # criar Pombo
        p: PomboLocations = (list(), list())

        b_array = bytearray(data)
        sep = b_array[0:1].decode()

        # nodes e seus blocos
        while sep != "\t":

            n_name = ""
            b: str = b_array[0:1].decode()
            while b != "\0":
                n_name += b
                b_array = b_array[1:]
                b = b_array[0:1].decode()

            # avançar array (para passar o \0)
            b_array = b_array[1:]

            # blocos
            n_blocks: set[int] = set()

            sep = b_array[0:1].decode()

            while sep != "\t" and sep != "\n":

                # nr do bloco
                block_nr = int.from_bytes(b_array[0:4], byteorder="big")
                # adicionar bloco
                n_blocks.add(block_nr)
                # avançar array
                b_array = b_array[4:]

                # atualizar separador
                sep = b_array[0:1].decode()

            p[0].append((n_name, n_blocks))

            # avançar array (para passar o \n ou o \t)
            b_array = b_array[1:]

        # hash's dos blocos
        while len(b_array) > 0:
            # hash do bloco
            block_hash = bytes(b_array[0:20])
            # adicionar bloco
            p[1].append(block_hash)
            # avançar array
            b_array = b_array[20:]

        return p

    @staticmethod
    def __fromBytesUpdate(data: bytes) -> PomboUpdate:
        # criar PomboUpdate
        p: PomboUpdate

        b_array = bytearray(data)

        f_name = ""
        b: str = b_array[0:1].decode()
        while b != "\0":
            f_name += b
            b_array = b_array[1:]
            b = b_array[0:1].decode()

        b_array = b_array[1:]
        p = (f_name, int.from_bytes(b_array[0:4], byteorder="big"))

        return p

    # create protocol message

    @staticmethod
    def __createTCPombo(chirp: bool, update: bool, data: bytes):
        # calculate length
        # length + chirp + update + payload
        l = 4 + 1 + 1 + len(data)

        # create TCPombo
        tcpombo = bytearray()
        tcpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        tcpombo.append(chirp)  # chirp
        tcpombo.append(update) # update
        tcpombo.extend(data)  # payload

        return tcpombo

    @staticmethod
    def createUpdateChirp(data: PomboUpdate):
        return bytes(TCPombo.__createTCPombo(True, True, TCPombo.__toBytesUpdate(data)))

    @staticmethod
    def createFilesChirp(data: PomboFiles):
        return bytes(TCPombo.__createTCPombo(True, False, TCPombo.__toBytesFiles(data)))

    @staticmethod
    def createLocationsChirp(data: PomboLocations):
        return bytes(TCPombo.__createTCPombo(True, False, TCPombo.__toBytesLocations(data)))

    @staticmethod
    def createCall(data: str):
        return bytes(TCPombo.__createTCPombo(False, False, data.encode()))

    # gets

    @staticmethod
    def getLength(tcpombo: bytes):
        return int.from_bytes(bytearray(tcpombo)[0:4], byteorder="big")

    @staticmethod
    def isChirp(tcpombo: bytes):
        return bool(bytearray(tcpombo)[4])

    @staticmethod
    def isUpdate(tcpombo: bytes):
        return bool(bytearray(tcpombo)[5])

    @staticmethod
    def __getOverheadLen():
        # length + chirp + update
        return 4 + 1 + 1

    # gets do payload

    @staticmethod
    def getPomboCall(tcpombo: bytes) -> str:
        return bytearray(tcpombo)[TCPombo.__getOverheadLen():].decode()

    @staticmethod
    def getPomboUpdate(tcpombo: bytes) -> PomboUpdate:
        return TCPombo.__fromBytesUpdate(bytearray(tcpombo)[TCPombo.__getOverheadLen():])

    @staticmethod
    def getPomboFiles(tcpombo: bytes) -> PomboFiles:
        return TCPombo.__fromBytesFiles(bytearray(tcpombo)[TCPombo.__getOverheadLen():])

    @staticmethod
    def getPomboLocations(tcpombo: bytes) -> PomboLocations:
        return TCPombo.__fromBytesLocations(bytearray(tcpombo)[TCPombo.__getOverheadLen():])

    # toString

    # @staticmethod
    # def bytesListToString(l: list[bytes]) -> list[str]:
    #     r = list()
    #     for b in l:
    #         r.append(b.hex())
    #     return r

    @staticmethod
    def __reducePomboFiles(pombo: PomboFiles) -> list[tuple[str, set[int]]]:
        l: list[tuple[str, int]] = list()

        for f in pombo:
            l.append((f[0], f[1][0]))

        return l

    # TCPombo
    @staticmethod
    def toString(tcpombo: bytes, tracker: bool = False):
        r = ""

        if TCPombo.isChirp(tcpombo):

            r += "('> Chirp! "
            r += "Here's a message with " + \
                str(TCPombo.getLength(tcpombo)) + " bytes!"

            if TCPombo.isUpdate(tcpombo):
                info = TCPombo.getPomboUpdate(tcpombo)
                r += " I now have block " + \
                    str(info[1]) + " from " + info[0] + "."
            elif tracker:
                r += " The file you asked for is here:\n" + str(TCPombo.getPomboLocations(tcpombo)[0]) + "."
            else:
                r += " I have the following files:\n" + \
                    str(TCPombo.__reducePomboFiles(TCPombo.getPomboFiles(tcpombo))) + "."

        else:

            r += "('> Call! "
            r += "Here's a message with " + \
                str(TCPombo.getLength(tcpombo)) + " bytes!"
            r += " I'm asking for " + TCPombo.getPomboCall(tcpombo) + "."

        return r
