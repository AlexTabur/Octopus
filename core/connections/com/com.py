from serial import Serial
from ..abstract import AbstractConnection

# TODO: add log
# TODO: add exceptions handling

class Com(AbstractConnection):
    connection_type = 'com'
    dev_addr = None
    
    def __init__(self, comport, timeout=1, baudrate=9600):
        self.__comport = comport
        self.__port = None
        self.__timeout = timeout
        self.__baudrate = baudrate

    def set_baudrate(self, baudrate = 9600):
        self.__baudrate = baudrate
        if self.__port:
            self.__port.baudrate = self.__baudrate

    def connect(self):
        self.__port = Serial()
        self.__port.port = self.__comport
        self.__port.baudrate = self.__baudrate
        self.__port.timeout = self.__timeout
        self.__port.open()
        self.connected = True

    def close(self):
        try:
            self.__port.close()
        except:
            pass
        self.__port = None
        self.connected = False

    def send(self, data):
        self.__port.write(data)

    def read(self, data):
        try:
            line = self.__port.readline()

            return line
        except TimeoutError as e:
            pass

    def io(self, data):
        self.__port.write(data)
        try:
            line = self.__port.read(size=4)

            return line
        except TimeoutError as e:
            pass

    def read_len(self, len):
        try:
            line = self.__port.read(size=len)
            return line
        except TimeoutError as e:
            pass