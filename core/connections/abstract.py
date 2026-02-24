from abc import ABCMeta, abstractmethod

class AbstractConnection(metaclass=ABCMeta):

    connected = False
    # com, socket, usb or visa
    connection_type = None

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def read(self, data):
        pass

    @abstractmethod
    def io(self, data):
        pass
