import hashlib  # para calcular o hash dos blocos

# tamanho dos chunks em bytes
CHUNK_SIZE = 1024
# set tracker port
TCP_PORT = 9090
# set udp server port
UDP_PORT = 9090

def chunkify(data: bytes) -> set[tuple[int, bytes]]:
        data_array = bytearray(data)

        # create chunks
        chunks: set[tuple[int, bytes]] = set()
        i = 0
        while i <= (len(data) // CHUNK_SIZE):
            # (nr, hash)
            chunks.add((i, hashlib.sha1(data_array[0:CHUNK_SIZE]).digest()))
            data_array = data_array[CHUNK_SIZE:]
            i += 1

        # deal with remaining bytes
        if len(data_array) > 0:
            chunks.add((i, hashlib.sha1(data_array).digest()))

        return chunks
