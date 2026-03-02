import struct

from core.connections.com.com import Com
from core.exceptions import ConnectionError

cmd_ping = 0x01
cmd_sync = 0x02


class Syncronizer:
    connection = None
    status = 'init'
    dev_name = 'Syncronizer'
    dev_type = 'Sync'
    port_num = None

    def __init__(self):
        # self.__helper = Helper()
        self.baudrate = 115200
        self.timeout = 2
        self.connection_type = 'com'
        self.state = 0
        self.logger = None

    def set_timeout(self, timeout):
        self.timeout = timeout

    def set_baudrate(self, baudrate):
        self.baudrate = baudrate

    def set_addr(self, port):
        self.port_num = port

    def connect(self):
        if self.port_num is None:
            self.port_num = "COM3"
        self.connection = Com(comport=self.port_num, timeout=self.timeout, baudrate=self.baudrate)
        if self.connection:
            self.connection.connect()
            return self.connection.connected
        else:
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.status = 'None'
            self.state |= 0x01

    def init(self):
        if not self.connection or not self.connection.connected:
            raise ConnectionError(f'Device {self.dev_name} is not connected')

        self.send_cmd(cmd_ping, 0, 0, 0, 0)
        cmd, p1, p2 = self.get_cmd()
        if cmd == cmd_ping:
            self.status = 'ready'
        self.state |= 0x01

    def make_sync(self, cnt, delay):
        #        if not self.connection or not self.connection.connected:
        #            raise ConnectionError(f'Device {self.dev_name} is not connected')
        # calculate frequency in THz
        try:
            self.send_cmd(cmd_sync, (cnt >> 8) & 0xFF, cnt & 0xFF, (delay >> 8) & 0xFF, delay & 0xFF)
            ans = self.connection.read_len(1)
        except Exception as e:
            self.disconnect()

    def send_cmd(self, cmd, param1, param2, param3, param4):
        # put to regs
        try:
            self.status = 'processing'
            bytes_ = struct.pack('!{0}B'.format(6), 0x55, cmd, param1, param2, param3, param4)

            self.connection.send(bytes_)
            self.status = 'ready'

        except Exception as e:
            self.disconnect()

    def get_cmd(self):
        try:
            self.status = 'processing'
            ans = self.connection.read_len(4)
            status = ans[0] == 0x55
            cmd = ans[1]
            param1 = ans[2]
            param2 = ans[3]
            self.status = 'ready'
            return cmd, param1, param2

        except Exception as e:
            self.disconnect()
