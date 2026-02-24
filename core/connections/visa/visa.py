import pyvisa as visa

from ..abstract import AbstractConnection

# TODO: add log
# TODO: add exceptions handling

class Visa(AbstractConnection):
    connection_type = 'visa'

    def __init__(self, ipaddr : str, dev_type='TCPIP') -> None:
        self.__devLine   = f"{dev_type}0::{ipaddr}::inst0::INSTR"
        self.__rm = visa.ResourceManager()
        self.__devDesc = None

    def connect(self):
        self.__devDesc = self.__rm.get_instrument(self.__devLine)
        self.connected = True

    def close(self):
        self.__devDesc.close()
        self.connected = False

    def send(self, data):
        self.__devDesc.write(data)

    def read(self, data):
        raise Exception('Not implemented')

    def io(self, data):
        ans = self.__devDesc.query(data)

        return ans

