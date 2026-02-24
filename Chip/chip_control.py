
import dearpygui.dearpygui as dpg
import numpy as np
from core.context import Context
from Chip.channel_control import Chanel_Controller
from core.consts import *

context = Context()

class Chip_Controller:

    def __init__(self):
        self.left_channels = []
        self.right_channels = []
        self.active_chan_left = -1
        self.active_chan_right = -1
        self.stateL = 0
        self.stateR = 0

    def set_active_chan(self, num, left):
        if left:
            self.active_chan_left = num
        else:
            self.active_chan_right = num

    def add_channel(self, num, left):
        if left:
            if(num >= len(self.left_channels)):
                self.left_channels.append(Chanel_Controller(num))
                idx = len(self.left_channels)-1
            else:
                idx = num
            return idx
        else:
            if(num >= len(self.right_channels)):
                self.right_channels.append(Chanel_Controller(num))
                idx = len(self.right_channels)-1
            else:
                idx = num
            return idx

    def set_chan_measure(self, num, measure, left):
        if left:
            self.left_channels[num].measure = measure
        else:
            self.right_channels[num].measure = measure

    def get_chan_measure(self, num, left):
        if left:
            return self.left_channels[num].measure
        else:
            return self.right_channels[num].measure

context.chip_ctrl = Chip_Controller()
