import pandas as pd
import socket
import struct


class PM:
    def __init__(self, s, num):
        self.s = s
        self.num = num

    def write(self, command):
        self.s.send(f'{command}\r\n'.encode())

    def decode(self, num):
        return self.s.recv(num).strip().decode('utf-8')

    def errors(self):
        self.write('ERR?')
        errors = self.decode(100)
        while errors[0] != '0':
            print(errors)
            self.write('ERR?')
            errors = self.decode(100)

    def run_sweep(self):
        self.write('MEAS')

    def set_avg(self, val):
        self.write(f'AVG {val}')

    def stat(self):
        self.write('STAT?')
        return self.decode(100)

    def read_sweep(self, module, channel):
        self.write(f'LOGG? {module},{channel}')
        response = self.s.recv(1000)
        hashtag = response[0].decode("ASCII")
        digits = int(response[1].decode("ASCII"))
        num = int(response[2:2 + digits].decode("ASCII"))
        print(hashtag, digits, num)
        return pd.DataFrame(struct.unpack("<" + "f" * num, response[2 + digits:2 + digits + num]),
                            columns=[f'CH{module * 4 + channel}'])

    def set_wavelength(self, wv):
        self.write(f'WAV {wv}')

    def stop(self):
        self.write('STOP')

    def read_one(self, module, channel):
        self.write(f'READ? {module}')
        return float(self.decode(1024).split(',')[channel])

    def read(self, num):
        self.write(f'READ? {num}')
        df = pd.DataFrame(self.decode(1024).split(','))
        df[0] = df[0].astype(float)
        df = df.transpose()
        df.columns = [f'CH{num * 4 + 1 + j + self.num * 20}' for j in range(4)]
        return df

    def get_ip(self):
        self.write("IP?")
        return self.decode(100)

    def set_ip(self, ip_str):
        self.write("IP " + ip_str)
        # return self.read(9)

    def disconnect(self):
        self.s.close()


s = socket.socket()
s.settimeout(2)
s.connect(("192.168.1.121", 5000))
a = PM(s, 0)
print(a.set_ip("192.168.1.161"))
