# lista de tuplos (nome do ficheiro, blocos) onde blocos = (id, hash)
# ex: [("file1", {(1, 1324123), (2, 1241234), (3, 4125342)}), ("file2", (...))]
Pombo = list[tuple[str, set[tuple[int, bytes]]]]
