
from threading import Thread

from core.context import Context
import dearpygui.dearpygui as dpg
import Measurements.devices.pm2100      as pm2100
import Measurements.devices.golight_tl  as golight
import Measurements.devices.syncronizer as syncronizer
from core.consts import *
from core.utils import *

context = Context()

class DeviceWorker():

    def __init__(self):
        self.is_laser_golight_connected = False
        self.is_pm2100_1_connected = False
        self.is_pm2100_2_connected = False
        self.is_pm2100_3_connected = False
        self.is_syncro_connected   = False

        self.laser_golight_ctrl = golight.GolightTL()
        self.syncroniser_ctrl = syncronizer.Syncronizer()
        self.pm2100_1_ctrl = pm2100.PM2100(1)
        self.pm2100_2_ctrl = pm2100.PM2100(2)
        self.pm2100_3_ctrl = pm2100.PM2100(3)
        self.laserGolight_connect_thread = Thread()
        self.syncronizer_connect_thread = Thread()
        self.meas_connect_thread1 = Thread()
        self.meas_connect_thread2 = Thread()
        self.meas_connect_thread3 = Thread()

    def connectGolightLaser(self):
        if (not self.laserGolight_connect_thread.is_alive()) and (not self.is_laser_golight_connected):
            self.laser_golight_ctrl.set_timeout(2)
            param = dpg.get_value("laser_golight_ip") + ":8888"
            self.laser_golight_ctrl.set_addr(param)
            if self.laser_golight_ctrl.connect():
                context.gui_hlp.set_conn_states("laser_golight_ctrl_state", "laser_golight_conn_btn", 2)
                self.laserGolight_connect_thread = Thread(target=self.laser_golight_ctrl.init, args=[], daemon=True)
                self.laserGolight_connect_thread.start()

    def connectSyncronizer(self):
        if (not self.syncronizer_connect_thread.is_alive()) and (not self.is_syncro_connected):
#            self.syncroniser_ctrl.set_timeout(2)
            if self.syncroniser_ctrl.connect():
                context.gui_hlp.set_conn_states("syncronizer_ctrl_state", "syncronizer_conn_btn", 2)
                self.syncronizer_connect_thread = Thread(target=self.syncroniser_ctrl.init, args=[], daemon=True)
                self.syncronizer_connect_thread.start()

    def connectPM2100(self, id):
            if id == 1:
                if not self.is_pm2100_1_connected and not self.meas_connect_thread1.is_alive():
                    context.gui_hlp.set_conn_states("pm2100_ctrl_state1", "pm2100_conn_btn1", 2)  # set connecting state
                    param = dpg.get_value("pm2100_ip1") + ":5000"
                    self.pm2100_1_ctrl.set_addr(param)
                    self.pm2100_1_ctrl.set_timeout(4)
                    self.meas_connect_thread1 = Thread(target=self.pm2100_1_ctrl.connect, args=[], daemon=True)
                    self.meas_connect_thread1.start()
            elif id == 2:
                if not self.is_pm2100_2_connected and not self.meas_connect_thread2.is_alive():
                    context.gui_hlp.set_conn_states("pm2100_ctrl_state2", "pm2100_conn_btn2", 2)  # set connecting state
                    param = dpg.get_value("pm2100_ip2") + ":5000"
                    context.device_worker.pm2100_2_ctrl.set_addr(param)
                    self.pm2100_2_ctrl.set_timeout(4)
                    self.meas_connect_thread2 = Thread(target=self.pm2100_2_ctrl.connect, args=[], daemon=True)
                    self.meas_connect_thread2.start()
            elif id == 3:
                if not self.is_pm2100_3_connected and not self.meas_connect_thread3.is_alive():
                    context.gui_hlp.set_conn_states("pm2100_ctrl_state3", "pm2100_conn_btn3", 2)  # set connecting state
                    param = dpg.get_value("pm2100_ip3") + ":5000"
                    context.device_worker.pm2100_3_ctrl.set_addr(param)
                    self.pm2100_3_ctrl.set_timeout(4)
                    self.meas_connect_thread3 = Thread(target=self.pm2100_3_ctrl.connect, args=[], daemon=True)
                    self.meas_connect_thread3.start()

    def disconnectSyncronizer(self):
        if self.is_syncro_connected:
            self.syncroniser_ctrl.disconnect()
            self.is_syncro_connected = False
            context.gui_hlp.set_conn_states("syncronizer_ctrl_state", "syncronizer_conn_btn", 0)

    def disconnectGolightLaser(self):
        if self.is_laser_golight_connected:
            self.laser_golight_ctrl.close()
            self.is_laser_golight_connected = False
            context.gui_hlp.set_conn_states("laser_golight_ctrl_state", "laser_golight_conn_btn", 0)

    def disconnectPM2100(self, id):
        if id == 1:
            if self.is_pm2100_1_connected:
                self.pm2100_1_ctrl.close()
                self.is_pm2100_1_connected = False
                context.device_worker.pm2100_1_ctrl.state |= 0x01
                context.gui_hlp.set_conn_states("pm2100_ctrl_state1", "pm2100_conn_btn1", 0)
        elif id == 2:
            if self.is_pm2100_2_connected:
                self.pm2100_2_ctrl.close()
                self.is_pm2100_2_connected = False
                context.device_worker.pm2100_2_ctrl.state |= 0x01
                context.gui_hlp.set_conn_states("pm2100_ctrl_state2", "pm2100_conn_btn2", 0)
        elif id == 3:
            if self.is_pm2100_3_connected:
                self.pm2100_3_ctrl.close()
                self.is_pm2100_3_connected = False
                context.device_worker.pm2100_3_ctrl.state |= 0x01
                context.gui_hlp.set_conn_states("pm2100_ctrl_state3", "pm2100_conn_btn3", 0)

    def turn_laser_golight(self, on):
        return self.laser_golight_ctrl.turn_beam(on)

context.device_worker = DeviceWorker()
