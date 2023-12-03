import socket

def getHostByName(name: str):
    print(socket.gethostbyname(name + ".local"))
    return socket.gethostbyname(name + ".local")

def getHostByAddr(ip: str):
    print(socket.gethostbyaddr(ip))
    return socket.gethostbyaddr(ip)[0].split(".")[0]
