from abc import ABCMeta, abstractmethod
from core.context import Context
from core.exceptions import ConnectionClassNotFoundError, ConnectionError

context = Context()

class AbstractDevice(metaclass=ABCMeta):
    connection = None
    connection_type = None
    dev_name = None
    dev_addr = None
    dev_type = None
    timeout = None
    status = 'init'
    chanels = 1
    
    def __init__(self):
        self.con_class = None

    def set_connection(self, connection_type):
        self.connection_type = connection_type

    def set_addr(self, addr):
        """ip address:port or com port or ip addrres for visa"""
        self.dev_addr = addr

    def set_baudrate(self, baudrate):
        """baudrate for com port """
        self.connection.set_baudrate(baudrate)


    def connect(self):
#        for con_class in context.connections_classes.values():
#            if con_class.connection_type == self.connection_type:
#                self.connection = con_class(self.dev_addr,self.timeout)
#                break
        self.connection = self.con_class(self.dev_addr, self.timeout)
            
        if not self.connection:
            return False #raise ConnectionClassNotFoundError(self.connection_type)
        
        try:
            self.connection.connect()
        except Exception:
            self.status = 'error'
            context.logger.log_error(f' failed to connect to {self.dev_addr}')
            return False
            
        self.status = 'idle'
        return True

    def close(self):
        self.connection.close()
        self.status = 'init'
#        context.logger.log_com(f'{self.dev_name} disconnected from {self.dev_addr}')

    def send(self, data):        
#        context.logger.log_com(f'{self.dev_name} on {self.dev_addr}\nsent: {data}')
        self.connection.send(data)

    def read(self):
        ans = self.connection.read()
#        context.logger.log_com(f'{self.dev_name} on {self.dev_addr}\nrecieved: {ans}')

    def read_len(self,len):
        ans = self.connection.read_len(len)
        return ans

    def io(self, data):
        ans = self.connection.io(data)
#        context.logger.log_com(f'{self.dev_name} on {self.dev_addr}\nsent: {data}\nrecieved: {ans}')
        return ans

    def io_raw(self, data):
        ans = self.connection.io_raw(data)
        return ans

    @abstractmethod
    def init(self):
        pass
    
    @property
    def labels(self):
        """labels for showing line names in plots"""
        if self.chanels > 1:
            return [f'{self.dev_name} {i}' for i in range(self.chanels)]
        
        return [self.dev_name, ] 
    
    @property
    def keys(self):
        if self.chanels > 1:
            return [f'{self.dev_name.lower()}_{i}' for i in range(self.chanels)]
        
        return [self.dev_name.lower(), ] 