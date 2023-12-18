import time

BUFFER_SIZE = 1024

class UDPombo:
    """
    - length: used to carry the length of the segment in bytes
    - chirp: flag used to send a chirp or a call, i.e. used to communicate information or request information
    - timestamp: used to calculate the RTT
    - file name: used to carry the name of the file
    - data: used to carry the payload of the message
    """

    # handle bytes

    @staticmethod
    def __toBytesCall(chunks: list[int]):
        num_bits = max(chunks) + 1

        # calculate the number of bytes needed
        num_bytes = (num_bits + 7) // 8

        # create a bytearray with the required number of bytes
        b_array = bytearray(num_bytes)

        # set the corresponding bits to 1
        for c in chunks:
            byte_index = c // 8
            bit_offset = c % 8
            b_array[byte_index] |= 1 << (7 - bit_offset)

        return bytes(b_array)
    
    @staticmethod
    def __fromBytesCall(data: bytes) -> list[int]:
        b_array = bytearray(data)

        bits = ''.join(format(byte, '08b') for byte in b_array)

        chunks = []
        for i, bit in enumerate(bits):
            if bit == '1':
                chunks.append(i)

        return chunks
    
    @staticmethod
    def __toBytesChirp(chunk: int, data: bytes):
        b_array = bytearray()

        b_array.extend(chunk.to_bytes(4, byteorder="big"))
        b_array.extend(data)

        return bytes(b_array)
    
    @staticmethod
    def __fromBytesChirp(data: bytes) -> tuple[int, bytes]:
        return (int.from_bytes(data[0:4], byteorder="big"), data[4:])

    # create protocol message

    @staticmethod
    def __createUDPombo(chirp: bool, file: str, time: int, data: bytes):
        # calculate length
        # length + chirp + timestamp + file name + \0 + data
        l = 4 + 1 + 8 + len(file) + 1 + len(data)

        # create UDPombo
        udpombo = bytearray()
        udpombo.extend(l.to_bytes(4, byteorder="big"))  # length
        udpombo.append(chirp)  # chirp
        udpombo.extend(time.to_bytes(8, byteorder="big"))  # timestamp (long)
        udpombo.extend((file + "\0").encode())  # file name + \0
        udpombo.extend(data)

        return udpombo

    @staticmethod
    def createChirp(chunk: int, file: str, time: int, data: bytes):
        return bytes(UDPombo.__createUDPombo(True, file, time, UDPombo.__toBytesChirp(chunk, data)))

    @staticmethod
    def createCall(chunks: list[int], file: str):
        return bytes(UDPombo.__createUDPombo(False, file, round(time.time() * 1000), UDPombo.__toBytesCall(chunks)))

    # gets

    @staticmethod
    def getLength(data: bytes):
        return int.from_bytes(data[0:4], byteorder="big")

    @staticmethod
    def isChirp(data: bytes):
        return bool(bytearray(data)[4])

    @staticmethod
    def getTimestamp(data: bytes):
        return int.from_bytes(data[5:13], byteorder="big")

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
    def getCallData(data: bytes) -> list[int]:
        overhead = 13 + len(UDPombo.getFileName(data)) + 1
        return UDPombo.__fromBytesCall(data[overhead:])
    
    @staticmethod
    def getChirpData(data: bytes) -> tuple[int, bytes]:
        overhead = 13 + len(UDPombo.getFileName(data)) + 1
        return UDPombo.__fromBytesChirp(data[overhead:])

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
            r += "carrying chunk number " + str(UDPombo.getChirpData(udpombo)[0])
        else:
            r += "asking for the chunks " + str(UDPombo.getCallData(udpombo))
        r += " of " + UDPombo.getFileName(udpombo) + "."
        return r
