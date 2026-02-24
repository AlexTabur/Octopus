import logging
import struct
import time

from Measurements.devices.abstract import AbstractDevice
from core.context import Context
from core.exceptions import ConnectionError
from core.connections.socket.socket import Socket

PM_MODE_CONST1  = 0
PM_MODE_SWEEP1  = 1
PM_MODE_CONST2  = 2
PM_MODE_SWEEP2  = 3
PM_MODE_FREERUN = 4

class PM2100(AbstractDevice):

    dev_name = 'PM2100'
    dev_type = 'power_meter'
#    chanels = 4
    value_upd = False

    def __init__(self, module_num):
        super().__init__()
        self.baudrate = None
        self.connection_type = 'socket'
        self.con_class = Socket
        self.state = 0
        self.module_num = module_num

    def set_timeout(self, timeout):
        self.timeout = timeout

    def init(self):
        if not self.connection or not self.connection.connected:
            return False
        try:
            self.status = 'processing'

            cmd = '*IDN?'
            ans = self.io(f'{cmd}\r\n')

            self.send('AVG 0.5\r\n')
            self.status = 'ready'
        except Exception as e:
            return False
        return True

    def set_wave_len(self, wave_len, check):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')
            self.status = 'processing'

            cmd = f'WAV {wave_len}'
            ans = self.send(f'{cmd}\r\n')

            if check:
                for i in range(100):
                    ans = self.io('WAV?\r\n').decode()
                    if str(wave_len) in ans:
                        break
        except Exception as e:
            self.disconnect()
        self.status = 'ready'

    def get_power(self, chan=0):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')
            self.status = 'processing'
            cmd = f'READ? {chan}'
            ans = self.io(f'{cmd}\r\n')
            self.status = 'ready'
            self.value_upd = True
            res = ans.decode().strip().split(',')
            if len(res)==4:
                return res
            else:
                self.disconnect()
                return [0, 0, 0, 0]
        except Exception as e:
            self.disconnect()
            return [0,0,0,0]

    def get_module_cnt(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            ans = self.io('MNUM?\r\n')
            self.status = 'ready'
            self.value_upd = True
            return ans.decode().strip().split(',')
        except Exception as e:
            self.disconnect()

#  0 = “CONST1” => Constant Wavelength, No Auto Gain
#  1 = “SWEEP1” => Sweep Wavelength, No Auto Gain
#  2 = “CONST2” => Constant Wavelength, Auto Gain
#  3 = “SWEEP2” => Sweep Wavelength, Auto Gain
#  4 = “FREERUN” => Constant Wavelength, No Auto Gain, First
    def set_work_mode(self, wmode, check):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')
            self.status = 'processing'
            if wmode == 0:
                mode = "CONST1"
            elif wmode == 1:
                mode = "SWEEP1"
            elif wmode == 2:
                mode = "CONST2"
            elif wmode == 3:
                mode = "SWEEP2"
            elif wmode == 4:
                mode = "FREERUN"
            cmd = f'WMOD {mode}'
            ans = self.send(f'{cmd}\r\n')
            if check:
                for i in range(100):
                    ans = self.io('WMOD?\r\n').decode()
                    if str(wmode) in ans:
                        break
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

# Set the wavelength range of Sweep Wavelength measuring mode (1250 ~ 1630)
    def set_sweep_range(self, bg, end, step):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')
            self.status = 'processing'
            cmd = f'WSET {bg},{end},{step}'
            ans = self.send(f'{cmd}\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    # Set the wavelength Sweep Speed (0.001 ~ 10) nm/sec
    def set_sweep_speed(self, sweep_speed):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')
            self.status = 'processing'
            cmd = f'SPE {sweep_speed}'
            ans = self.send(f'{cmd}\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    # Set Gain stage for CONST1, SWEEP1 and FREERUN measuring mode (1, 2, 3, 4, 5)
    def set_gain(self, gain,  check):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'LEV {gain}'
            ans = self.send(f'{cmd}\r\n')
            if check:
                for i in range(100):
                    ans = self.io('LEV?\r\n').decode()
                    if str(gain) in ans:
                        break;

            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    # Set trigger 0 - Internal. 1 - External
    def set_triggeer(self, trig,  check):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'TRIG {trig}'
            ans = self.send(f'{cmd}\r\n')
            if check:
                for i in range(100):
                    ans = self.io('TRIG?\r\n').decode()
                    if str(trig) in ans:
                        break;

            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    def get_gain(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            ans = self.io(f'LEV?\r\n')
            self.status = 'ready'
            return ans
        except Exception as e:
            self.disconnect()

    # Set the averaging time for CONST1, CONST2, FREERUN Mode and READ? Command (0.01 ~ 10000.00) ms
    def set_avg_time(self, avg): # Default value = 5 ms
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'AVG {avg}'
            ans = self.send(f'{cmd}\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    # Set measuring time in CONT1, CONT2, FREERUN measuring mode.
    def set_meas_cnt(self, time):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'LOGN {time}'
            ans = self.send(f'{cmd}\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    # Starting to eliminate the electrical DC offset. Before measuring
    # optical power, run “ZERO”. Please be careful not to incident light into
    # optical connector. This command action takes about 2.5sec so
    # please run other commands at least 2.5 sec later.
    def run_zero(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            ans = self.send('ZERO\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    # Determine Automatic Set of Gain when using READ? Command.
    # In case of manual set, LEV command is used.
    def set_auto(self, en):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'AUTO {en}'
            ans = self.send(f'{cmd}\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    def get_auto(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            ans = self.io(f'AUTO?\r\n')
            self.status = 'ready'
            return ans
        except Exception as e:
            self.disconnect()

    def run_meas(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'MEAS'
            ans = self.send(f'{cmd}\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    def stop_meas(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'STOP'
            ans = self.send(f'{cmd}\r\n')
            self.status = 'ready'
        except Exception as e:
            self.disconnect()

    def get_meas_state(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'STAT?'
            ans = self.io(f'{cmd}\r\n')
            self.status = 'ready'
            return ans.decode().strip().split(',')
        except Exception as e:
            self.disconnect()

    def get_err(self):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            cmd = f'ERR?'
            ans = self.io(f'{cmd}\r\n')
            self.status = 'ready'
            return ans
        except Exception as e:
            self.disconnect()

    def get_meas_data(self, module, chan):
        try:
            if not self.connection or not self.connection.connected:
                raise ConnectionError(f'Device {self.dev_name} is not connected')

            self.status = 'processing'
            ans = self.io(f'LOGG? {module},{chan}\r\n')
 #           print("ans=",ans)
            list1 = list()
            length = ans[2:]
            length = int(length)
            header = ans[:1]
            if(len(ans) == 0) or (header != b'#'):
                return list1

#            print("ans_len=",length)
            while(length>0):
                data = self.io('')
                chunked_list = list()
                chunk_size = 4

                for i in range(0, len(data), chunk_size):
                    chunked_list.append(data[i:i + chunk_size])
                    arr = chunked_list[len(chunked_list) - 1]
                    barr = bytes(reversed(arr))
                    lennn = len(barr)
                    if lennn == 4:
                        ff = struct.unpack('!f', barr)
                        list1.append(ff[0])

                length -= len(data)
#            print(list1)

            self.status = 'ready'
            return list1
        except Exception as e:
#            return list1
            self.disconnect()

    def connect(self):
        AbstractDevice.connect(self)
        self.state |= 0x01

    def disconnect(self):
        if self.connection and self.connection.connected:
            AbstractDevice.close(self)
        self.state |= 0x01

    def startConst2(self, wave_len, avg, count):
        self.set_work_mode(2, False)
        time.sleep(0.1)
        self.set_wave_len(wave_len, False)
        time.sleep(0.1)
        self.set_triggeer(1, False)
        time.sleep(0.1)
        self.set_avg_time(avg)
        time.sleep(0.1)
        self.set_meas_cnt(count)
        time.sleep(0.1)
        self.run_meas()

    def startSweep2(self, start_wl, stop_wl, step_wl, speed):
        self.set_work_mode(3, False)
        self.set_sweep_range(start_wl,stop_wl,step_wl)
        self.set_sweep_speed(speed)
        self.run_meas()