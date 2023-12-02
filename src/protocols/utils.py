import hashlib  # para calcular o hash dos blocos
import math
import os

# tamanho dos chunks em bytes
CHUNK_SIZE = 2048
# set tracker port
TCP_PORT = 9090
# set udp server port
UDP_PORT = 9090
# set timeout time
TIMEOUT_TIME = 1.5
# set timeout limit
TIMEOUT_LIMIT = 10

# divide ficheiro em chunks e calcula as hashes respetivas
def chunkify(path: str) -> set[tuple[int, bytes]]:
        # criar estrutura para guardar informação dos blocos
        chunks: set[tuple[int, bytes]] = set()
        
        # obter número de blocos
        file_size = os.path.getsize(path)
        l = math.ceil(file_size / CHUNK_SIZE)

        # abrir o ficheiro
        with open(path, "rb") as f:

            i = 0
            while i < l:

                # ler o chunk correspondente
                f.seek(i * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)

                # adicionar informação (nr, hash)
                chunks.add((i, hashlib.sha1(chunk_data).digest()))
                i += 1

            # fechar o ficheiro
            f.close()
        
        return chunks
