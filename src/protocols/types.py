# tuplo com o nome do ficheiro e o novo bloco
# ex: ("file1", 32)
PomboUpdate = tuple[str, int]

# lista de tuplos (nome do ficheiro, blocos) onde blocos = (id, hash)
# ex: [("file1", {(1, 1324123), (2, 1241234), (3, 4125342)}), ("file2", (...))]
PomboFiles = list[tuple[str, set[tuple[int, bytes]]]]

# tuplo com duas listas, uma com os nodes e os blocos que têm do ficheiro pedido,
# e outra com as hash's dos blocos do ficheiro pedido
# ex: ([("node1", {1, 2, 3}), ("node2", {2, 3, 4})], [hash1, hash2, hash3, hash4])
PomboLocations = tuple[list[tuple[str, set[int]]], set[bytes]]
