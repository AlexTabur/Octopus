from socket import socket, AF_INET, SOCK_STREAM

from core.exceptions import ConnectionError
from ..abstract import AbstractConnection

# TODO: add log
# TODO: add exceptions handling

class Socket(AbstractConnection):
    connection_type = 'socket'

    def __init__(self, addr, timeout=5, package_len=1024):
        self.__addr = addr
        self.__ip = None
        self.__port = None
        self.__timeout = timeout
        self.__package_len = package_len
        self.__sock = None

    def connect(self):
        self.__ip, self.__port = self.__addr.split(':')
        if not (self.__ip and self.__port):
            raise ConnectionError(f'ip or port not found in {self.__addr}')
        
        self.__sock = socket(AF_INET, SOCK_STREAM)
        self.__sock.settimeout(self.__timeout)
        res = self.__sock.connect_ex((self.__ip, int(self.__port)))
        self.connected = res == 0 #True

    def close(self):
        self.__sock.close()
        self.__sock = None
        self.connected = False

    def send(self, data):
        self.__sock.send(data.encode('utf-8'))

    def read(self, data):
        try:
            ans = self.__sock.recv(self.__package_len)
            return str(ans, "utf-8")
        except socket.timeout:
            pass

    def io(self, data):
        self.__sock.send(data.encode('utf-8'))
        try:
            ans = self.__sock.recv(self.__package_len)
            return ans
        except socket.timeout:
            pass

    def io_raw(self, data):
        self.__sock.send(data)
        try:
            ans = self.__sock.recv(self.__package_len)
            return ans
        except socket.timeout:
            pass
