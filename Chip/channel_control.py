
from core.context import Context
import core.consts as const
import numpy as np

context = Context()

class Chanel_Controller:

    def __init__(self, num):
        self.position = [0, 0, 0, 0, 0, 0]
        self.num = num
        self.state = 0 # 0 - not aimed, 1 - aimed,
        self.measure = True
        arr = np.zeros(shape=[5, 5])
        self.aiming_data = [arr, arr, arr, arr, arr]

    def make_aimed(self, xl, yl, zl, xa, ya, za):
        self.position = [xl, yl, zl, xa, ya, za]
        self.state |= const.CHAN_IS_CHANGED | const.CHAN_IS_AIMED

    def make_unaimed(self):
        self.position = [0, 0, 0, 0, 0, 0]
        self.state &= ~const.CHAN_IS_AIMED
        self.state |= const.CHAN_IS_CHANGED

    def deinit(self):
        pass
