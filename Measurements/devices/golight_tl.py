import struct

from Measurements.devices.abstract import AbstractDevice
from core.connections.socket.socket import Socket2
from core.exceptions import ConnectionError_


def checksum(a):
    summ = 0
    for i in a:
        summ += i
    summ %= 256
    return summ.to_bytes()


def command(h):
    res = bytearray.fromhex(h)
    res += checksum(res)
    return res


class GolightTL(AbstractDevice):
    dev_name = 'GolightTl'
    dev_type = 'power_meter'

    def __init__(self):
        super().__init__()
        self.baudrate = None
        self.connection_type = 'socket'
        self.con_class = Socket2
        self.state = 0
        self.last_power = 0
        self.last_wl = 0
        self.last_beam_state = 0
        self.reg1 = 0
        self.reg2 = 0
        self.reg3 = 0

    def set_timeout(self, timeout):
        self.timeout = timeout

    def init(self):
        if not self.connection or not self.connection.connected:
            return False

        try:
            self.status = 'processing'
            #            cmd_arr = [0xAA, 0x02, 0x78, 0x24]
            cmd = prep_array([0x78])
            ans = self.io_raw(cmd)

            res = struct.unpack('!{0}B'.format(len(ans)), ans)
            if res != [0xAA, 0x02, 0x45, 0xF1]:
                self.status = 'ready'
        except Exception as e:
            print(e)
            return False
        return True

    def turn_beam(self, on):
        if not self.connection or not self.connection.connected:
            raise ConnectionError_(f'Device {self.dev_name} is not connected')
        self.status = 'processing'
        if on:
            self.last_beam_state = 1
            cmd = prep_array([0x45, 0x01])
        else:
            self.last_beam_state = 0
            cmd = prep_array([0x45, 0x00])
        self.io_raw(cmd)
        self.status = 'ready'

    def get_beam_state(self):
        if not self.connection or not self.connection.connected:
            raise ConnectionError_(f'Device {self.dev_name} is not connected')
        self.status = 'processing'
        cmd = prep_array([0x65])
        ans = self.io_raw(cmd)
        self.status = 'ready'
        return ans[3]

    def set_power_dbm(self, power):
        if not self.connection or not self.connection.connected:
            raise ConnectionError_(f'Device {self.dev_name} is not connected')
        self.status = 'processing'
        self.last_power = power
        iLow, iHigh = struct.unpack('<HH', struct.pack('f', power))
        cmd = prep_array([0x50, iLow & 0xFF, (iLow >> 8) & 0xFF, iHigh & 0xFF, (iHigh >> 8) & 0xFF])
        self.io_raw(cmd)
        self.status = 'ready'

    def set_wave_len(self, wave_len):
        if not self.connection or not self.connection.connected:
            raise ConnectionError_(f'Device {self.dev_name} is not connected')
        self.status = 'processing'
        self.last_wl = wave_len
        wl = int(wave_len * 1000)
        cmd = prep_array([0x57, wl & 0xFF, (wl >> 8) & 0xFF, (wl >> 16) & 0xFF, (wl >> 24) & 0xFF])
        self.io_raw(cmd)
        self.status = 'ready'

    def start_scan(self, start, cutoff, interval):
        if not self.connection or not self.connection.connected:
            raise ConnectionError_(f'Device {self.dev_name} is not connected')
        self.status = 'processing'
        a = struct.pack('<IIH', start, cutoff, interval)
        self.io_raw(command("aa0c42" + a.hex()))
        self.status = 'ready'

    def connect(self):
        AbstractDevice.connect(self)
        self.state |= 0x01

    def store_state(self):
        self.reg1 = self.last_wl
        self.reg2 = self.last_power
        self.reg3 = self.last_beam_state

    def restore_state(self):
        self.set_wave_len(self.reg1)
        self.set_power_dbm(self.reg2)
        self.turn_beam(self.reg3)


def prep_array(data_arr):
    data_arr = [0xAA, len(data_arr) + 1] + data_arr
    crc = 0
    for i in range(len(data_arr)):
        crc += data_arr[i]
    data_arr.append(crc & 0xFF)
    cmd = struct.pack('!{0}B'.format(len(data_arr)), *data_arr)
    return cmd
