import math
import re
import configparser

import serial.tools.list_ports
import dearpygui.dearpygui as dpg
from core.context import Context
from core.consts import *
import numpy as np
from pathlib import Path

# import serial
context = Context()


def get_comports_list():
    return [port.name for port in serial.tools.list_ports.comports()]


def mW_to_dBm(mW):
    return 10 * math.log10(mW)


def dBm_to_mW(dBm):
    return 10 ** (dBm / 10)


def ghz_to_nm(freq):
    return 299792458 / freq


def nm_to_ghz(wavelen):
    return 299792458 / wavelen


def get_pm_devices():
    return [dev_dict['instance'] for dev_dict in context.devices if dev_dict['type'] == 'power_meter']


def load_prameters():
    def get_int_param(section, option, default):
        if config.has_option(section, option):
            return config.getint(section, option)
        else:
            return default

    def get_str_param(section, option, default):
        if config.has_option(section, option):
            return config.get(section, option)
        else:
            return default

    config = configparser.ConfigParser()
    config.read(r'Config\settings.ini', encoding="windows-1252")

    context.speed_value_platform = get_int_param('CONFIGURATION', 'platforms_speed', 1000)
    context.step_value_platform = get_int_param('CONFIGURATION', 'platforms_step', 10)
    context.speed_value_table = get_int_param('CONFIGURATION', 'table_speed', 1000)
    context.step_value_table = get_int_param('CONFIGURATION', 'table_step', 10)

    context.spectrum_report_path = get_str_param('CONFIGURATION', 'spectrum_report', "report.csv")

    context.spectrum_laser_power = get_int_param('CONFIGURATION', 'spectrum_laser_power', 10)

    config.read(r'Config\chip_params.ini', encoding="utf-8-sig")

    if config.has_option('COMMON', 'chip_list'):
        context.chip_list = config.get('COMMON', 'chip_list').split(',')
    else:
        context.chip_list = ['None']


def save_prameters():
    config = configparser.ConfigParser()
    config.read(r'Config\settings.ini', encoding="windows-1252")
    if not config.has_section('CONFIGURATION'):
        config.add_section('CONFIGURATION')
    if not config.has_section('POSITIONING'):
        config.add_section('POSITIONING')
    config.set('CONFIGURATION', 'platforms_speed', str(context.speed_value_platform))
    config.set('CONFIGURATION', 'platforms_step', str(context.step_value_platform))
    config.set('CONFIGURATION', 'table_speed', str(context.speed_value_table))
    config.set('CONFIGURATION', 'table_step', str(context.step_value_table))
    config.set('CONFIGURATION', 'spectrum_report', str(context.spectrum_report_path))

    with open(r'Config\settings.ini', mode='w', encoding="windows-1252") as configfile:  # save
        config.write(configfile)


def save_presets():
    np.save(r'Config\presets_left.npy', context.preset_left)
    np.save(r'Config\presets_right.npy', context.preset_right)
    np.save(r'Config\presets_table.npy', context.preset_table)
    np.save(r'Config\presets.npy', context.preset_all)


def load_presets():
    context.preset_left = np.load(r'Config\presets_left.npy', allow_pickle=True)
    context.preset_right = np.load(r'Config\presets_right.npy', allow_pickle=True)
    context.preset_table = np.load(r'Config\presets_table.npy', allow_pickle=True)
    context.preset_all = np.load(r'Config\presets.npy', allow_pickle=True)
    my_file = Path(r"Config\spectrum_zero.npy")
    if my_file.is_file():
        context.spectrum_zero = np.load(r'Config\spectrum_zero.npy', allow_pickle=True)


def load_chip_params(chip_name):
    def get_int_param(section, option, default):
        if config.has_option(section, option):
            return config.getint(section, option)
        else:
            return default

    config = configparser.ConfigParser()
    config.read(r'Config\chip_params.ini', encoding="utf-8-sig")

    context.chip_chans_left = get_int_param(chip_name, 'channels_left', 16)
    context.chip_chans_right = get_int_param(chip_name, 'channels_right', 16)
    context.chip_chans_dy = get_int_param(chip_name, 'channels_dy', 127)
    context.chips_dy = get_int_param(chip_name, 'chips_dy', 20000)


def text_to_float(text):
    val = re.sub('[^0-9.,-]', '', text)
    val = re.sub(',', '.', val)
    if val == '' or val == '.' or val == '-':
        val = '0'
    dotctn = 0
    ret = ''
    for i, c in enumerate(val):
        if c == '.':
            if dotctn:
                continue
            else:
                dotctn += 1
        if c == '-' and i > 0:
            continue
        ret += c
    return float(ret)


def text_to_int(text):
    val = re.sub('-[^0-9]', '', text)
    if val == '':
        val = '0'
    ret = ''
    for i, c in enumerate(val):
        if c == '-' and i > 0:
            continue
        ret += c

    return int(ret)


def calc_aiming_window(width, height):
    #    context.aim_y_width  = [0, 0, 0, 0, 0]
    #    context.aim_z_step = [0, 0, 0, 0, 0]
    min_y_step = 5
    context.aim_steps = 0
    while True:
        context.aim_steps += 1
        context.aim_x_speed[context.aim_steps - 1] = 150
        if (height // 5) > 200:  # ширина зоны еще больше 200
            context.aim_z_count[context.aim_steps - 1] = height // 200
            context.aim_z_step[context.aim_steps - 1] = 200
        else:  # ширина зоны уже меньше 200
            context.aim_z_count[context.aim_steps - 1] = 5
            context.aim_z_step[context.aim_steps - 1] = height // 5
        if context.aim_z_step[context.aim_steps - 1] < min_y_step:  # ширина уже меньше минимальной
            context.aim_z_step[context.aim_steps - 1] = min_y_step
        if context.aim_steps == 1:  # если это первый шаг, то ширину по X оставляем как есть
            context.aim_y_width[context.aim_steps - 1] = width
        else:  # на последующих шагах делаем ее равной общей ширине зоны сканирования по Y
            context.aim_y_width[context.aim_steps - 1] = context.aim_z_step[context.aim_steps - 1] * \
                                                         context.aim_z_count[context.aim_steps - 1]
        if context.aim_z_step[context.aim_steps - 1] <= min_y_step:
            break
        height = context.aim_z_step[context.aim_steps - 1] * 3 // 2  # уменьшаем изначальную общую всоту зоны на 1/3

    context.aim_x_speed[context.aim_steps - 1] = 100
