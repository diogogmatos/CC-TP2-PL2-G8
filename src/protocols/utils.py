import hashlib  # para calcular o hash dos blocos
import math

# tamanho dos chunks em bytes
CHUNK_SIZE = 2048
# set tracker port
TCP_PORT = 9090
# set udp server port
UDP_PORT = 9090
# set timeout time
TIMEOUT_TIME = 5
# set timeout limit
TIMEOUT_LIMIT = 5

# divide ficheiro em chunks e calcula as hashes respetivas
def chunkify(data: bytes) -> set[tuple[int, bytes]]:
        data_array = bytearray(data)

        # create chunks
        chunks: set[tuple[int, bytes]] = set()
        i = 0
        l = math.ceil(len(data) / CHUNK_SIZE)
        while i < l - 1:
            # (nr, hash)
            chunks.add((i, hashlib.sha1(bytes(data_array[0:CHUNK_SIZE])).digest()))
            data_array = data_array[CHUNK_SIZE:]
            i += 1

        chunks.add((i, hashlib.sha1(bytes(data_array[0:])).digest()))
        
        return chunks
