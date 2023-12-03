import socket

def getHostByName(name: str):
    return socket.gethostbyname(name + ".local")

def getHostByAddr(ip: str):
    return socket.gethostbyaddr(ip)[0].split(".")[0]
