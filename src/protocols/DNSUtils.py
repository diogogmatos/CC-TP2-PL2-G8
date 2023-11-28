import socket 

DNS_IP = '10.4.4.2'

class DNSUtils:
    @staticmethod
    def setDomain(name):
        name = '0' + name
        socketDns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            socketDns.connect((DNS_IP, 8080))
        except socket.error as e:
            raise ValueError("Error connecting to server:", e)
        
        socketDns.send(name.encode('utf-8'))

    @staticmethod
    def getIp(name):
        name = '1' + name
        socketDns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            socketDns.connect((DNS_IP, 8080))
        except socket.error as e:
            raise ValueError("Error connecting to server:", e)
        
        socketDns.send(name.encode('utf-8'))
        addr = socketDns.recv(1024).decode('utf-8')
        print(addr)
        return addr