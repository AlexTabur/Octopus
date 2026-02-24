from threading import Timer
from threading import Thread
import dearpygui.dearpygui as dpg
import numpy as np
import os
import json
import zmotion
from core.consts import *

class Singleton(type):
    def __init__(self, name, bases, mmbs):
        super(Singleton, self).__init__(name, bases, mmbs)
        self._instance = super(Singleton, self).__call__()

    def __call__(self, *args, **kw):
        return self._instance

class Context(metaclass = Singleton):
    """ Class that contains all states of program"""
    x1_line_i = 0
    y1_line_i = 1
    z1_line_i = 2
    x1_ang_i = 3
    y1_ang_i = 4
    z1_ang_i = 5
    x2_line_i = 6
    y2_line_i = 7
    z2_line_i = 8
    x2_ang_i = 9
    y2_ang_i = 10
    z2_ang_i = 11
    y_table_i = 12

    def __init__(self):
            #print("initialization")
            self.logger = None
            self.gui_hlp = None
            self.spectrum_gui = None
            self.spectrum_zero_gui = None
            self.motionGUI = None
            self.chip_meas_ctrl = None
            self.positions = None
            self.chip_ctrl = None
            self.config_ctrl = None
            self.meas_powermap = None

            self.pmap_procedures = None
            self.editor_list = []

            self.tabBar = None # основной таб бар
            self.is_meas_in_process = False
            self.run_scan = False
            self.exit_mode = False

            self.current_wavelen = None
            self.current_power = None
            self.zcontrollers = None
            self.texture_reg = None

            self.main_width = 1470
            self.main_height = 800
            self.current_axis = -1 # переменная для отслеживания какой осью в непрерывном режиме мы управляем
            self.ctrl_mode = CTRL_MODE_CONT # выбор режима ручного управления
            self.step_value_platform  = 1000 # величина перемещения в шаговом режиме
            self.step_value_table     = 1000 # величина перемещения в шаговом режиме
            self.speed_value_platform = 10
            self.speed_value_table    = 10
            self.spectrum_report_path = "report.csv"

            self.ctrl_by_keyboard = False
            self.lock_left_side = False
            self.lock_right_side = False

            self.platforms_initialized = False
            self.clicked_on = 0  # потом удалить отсюда
            self.t: Timer = None
            self.platform_connect_thread = Thread()
            self.table_connect_thread = Thread()
            self.axis = np.array([
                ('X линейное',  'axis_x_L', int(AXIS_L_X),   0, 0, 0, 0, "x_p.png",  "x_m.png",   "t_l_x_p",  "t_l_x_m",   None, None, 1, 1, -1, 0),
                ('Y линейное',  'axis_y_L', int(AXIS_L_Y),   0, 0, 0, 0, "y_p.png",  "y_m.png",   "t_l_y_p",  "t_l_y_m",   None, None, 1, -1, 1, 0),
                ('Z линейное',  'axis_z_L', int(AXIS_L_Z),   0, 0, 0, 0, "z_p.png",  "z_m.png",   "t_l_z_p",  "t_l_z_m",   None, None, 1, 1, -1, 0),
                ('X вращение', 'axis_rx_L', int(AXIS_L_R_X), 0, 0, 0, 0, "x_cw.png", "x_ccw.png", "t_l_x_cw", "t_l_x_ccw", None, None, 1, -1, 1, 0),
                ('Y вращение', 'axis_ry_L', int(AXIS_L_R_Y), 0, 0, 0, 0, "y_cw.png", "y_ccw.png", "t_l_y_cw", "t_l_y_ccw", None, None, 1, 1, -1, 0),
                ('Z вращение', 'axis_rz_L', int(AXIS_L_R_Z), 0, 0, 0, 0, "z_cw.png", "z_ccw.png", "t_l_z_cw", "t_l_z_ccw", None, None, 1, -1, 1, 0),
                ('X линейное',  'axis_x_R', int(AXIS_R_X),   0, 0, 0, 0, "x_p.png",  "x_m.png",   "t_r_x_p",  "t_r_x_m",   None, None, 1, -1, 1, 1),
                ('Y линейное',  'axis_y_R', int(AXIS_R_Y),   0, 0, 0, 0, "y_p.png",  "y_m.png",   "t_r_y_p",  "t_r_y_m",   None, None, 1, -1, 1, 1),
                ('Z линейное',  'axis_z_R', int(AXIS_R_Z),   0, 0, 0, 0, "z_p.png",  "z_m.png",   "t_r_z_p",  "t_r_z_m",   None, None, 1, 1, -1, 1),
                ('X вращение', 'axis_rx_R', int(AXIS_R_R_X), 0, 0, 0, 0, "x_cw.png", "x_ccw.png", "t_r_x_cw", "t_r_x_ccw", None, None, 1, 1, -1, 1),
                ('Y вращение', 'axis_ry_R', int(AXIS_R_R_Y), 0, 0, 0, 0, "y_cw.png", "y_ccw.png", "t_r_y_cw", "t_r_y_ccw", None, None, 1, -1, 1, 1),
                ('Z вращение', 'axis_rz_R', int(AXIS_R_R_Z), 0, 0, 0, 0, "z_cw.png", "z_ccw.png", "t_r_z_cw", "t_r_z_ccw", None, None, 1, 1, -1, 1),
                ('Y стол',      'axis_y_T', int(AXIS_TABLE), 0, 0, 0, 0, "y_p.png",  "y_m.png",   "t_t_y_p",  "t_t_y_m",   None, None, 2, 1, -1, 2)],
                dtype=[('label', 'U10'), ('name', 'U10'), ('idx', int), ('acc', 'f4'),
                       ('dec', 'f4'), ('state', 'f4'), ('pos', 'f4'),('img_p', 'U10'), ('img_m', 'U10'),
                       ('txt_p', 'U10'), ('txt_m', 'U10'), ('img_d_p', dpg.mvBuffer), ('img_d_m', dpg.mvBuffer),
                       ('controler', int), ('dir_fw', int), ('dir_bw', int), ('side', int)
                       ])

            self.preset_dt  = np.dtype([('name', 'U20'),('pos', 'f4', (13,))])
            self.preset_left  = np.array([], self.preset_dt)
            self.preset_right = np.array([], self.preset_dt)
            self.preset_table = np.array([], self.preset_dt)
            self.preset_all   = np.array([], self.preset_dt)

            self.spectrum_zero_dt  = np.dtype([('wl', 'f4'),('pow', 'f4', (60,))])
            self.spectrum_zero  = np.array([], self.spectrum_zero_dt)

            self.break_proc = False
            self.current_proc = 0

            self.pm_modules1 = [0, 0, 0, 0, 0]
            self.pm_modules2 = [0, 0, 0, 0, 0]
            self.pm_modules3 = [0, 0, 0, 0, 0]

            self.auto_meas_pm1 = True#False
            self.auto_meas_pm2 = True#False
            self.auto_meas_pm3 = True#False

            self.active_pm_list = ["Нет"]

            self.act_chans = np.zeros(60)  # список активных каналов измерителей
            self.pm_values = [0]*60 # текущие значения от измерителей

            self.zplatform = zmotion.ZMCWrapper()
            self.ztable = zmotion.ZMCWrapper()

            self.call_count = -1
            self.call_function   = None
            self.function_params = None

            self.spectrum_laser_power = 9.5 # мощности лазера при измерении спектра (читается из ini-файла)

            self.comports = None
            self.plarforms_controller_ip = "192.168.1.11"
            self.table_controller_ip     = "192.168.1.12"

# Measurements
            self.single_meas_results = {}
            self.scan_meas_results = {}
            self.meas_chart = 0

            self.enabled_btn_theme = None
            self.disabled_btn_theme = None

# Chip measurements params
            self.chip_list = None
            self.chip_chans_left = 16
            self.chip_chans_right = 16
            self.chip_chans_dy = 127
            self.chips_dy = 2000

# Aiming params
            self.aim_steps = 3
            self.aim_y_width = [200, 50, 20, 10, 5]
            self.aim_z_count = [5, 5, 10, 5, 5]
            self.aim_z_step = [100, 30, 2, 2, 1]
            self.aim_x_speed = [120, 120, 120, 120, 100]
