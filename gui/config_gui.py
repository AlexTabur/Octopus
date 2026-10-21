import time

import dearpygui.dearpygui as dpg

import core.texts as txt
from Measurements.meas_powermap import select_pm
from core.gui_helper import check_edit_data, set_conn_states
from core.texts import *
from core.utils import *
from time import sleep
context = Context()


def init_config_page():
    def prepare_pm(num):
        placeholder = "  xxxx  "
        pm_shift = 20 * (num - 1)
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_spacer(height=5)
                dpg.add_text(default_value=txt.METER_IP_TITLE + str(num))
                dpg.add_spacer(height=5)
                context.editor_list.append(f"pm2100_ip{num}")
                dpg.add_input_text(tag=f"pm2100_ip{num}", default_value=f"192.168.1.16{num}", width=125, height=16)
                dpg.add_spacer(height=5)

                #                callback=self.pm_zero_callback, user_data=num)

            dpg.add_spacer(width=10)
            with dpg.table(header_row=False, resizable=False, borders_innerV=True, borders_outerH=True, width=700):
                for i in range(10):
                    dpg.add_table_column()
                with dpg.table_row():
                    for i in range(5):
                        with dpg.table_cell():
                            dpg.add_text(default_value=f"CH{i * 4}({i * 4 + pm_shift})")
                        with dpg.table_cell():
                            dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + pm_shift}")
                with dpg.table_row():
                    for i in range(5):
                        with dpg.table_cell():
                            dpg.add_text(default_value=f"CH{i * 4 + 1}({i * 4 + 1 + pm_shift})")
                        with dpg.table_cell():
                            dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 1 + pm_shift}")
                with dpg.table_row():
                    for i in range(5):
                        with dpg.table_cell():
                            dpg.add_text(default_value=f"CH{i * 4 + 2}({i * 4 + 2 + pm_shift})")
                        with dpg.table_cell():
                            dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 2 + pm_shift}")
                with dpg.table_row():
                    for i in range(5):
                        with dpg.table_cell():
                            dpg.add_text(default_value=f"CH{i * 4 + 3}({i * 4 + 3 + pm_shift})")
                        with dpg.table_cell():
                            dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 3 + pm_shift}")
            dpg.add_spacer(height=60)
            dpg.add_checkbox(label='Читать', callback=set_pm_read_online, user_data=num,
                             default_value=True)

    with dpg.group(horizontal=True):
        with dpg.group():
            prepare_pm(1)
            prepare_pm(2)
            prepare_pm(3)

            with dpg.group(horizontal=True):
                with dpg.group():
                    init_comports()
                    dpg.add_spacer(height=5)
                    dpg.add_text(default_value=txt.sync_TITLE)
                    dpg.add_text(default_value="COM порт")
                    dpg.add_combo(tag="sync_com", width=125, items=context.comports,
                                  callback=select_sync_com)
                dpg.add_spacer(width=10)

        dpg.add_spacer(width=10)
        init_comports()

        dpg.add_spacer(width=10)
        with dpg.group():
            dpg.add_text(default_value=txt.LASER_GOLIGHT_TITLE)

            context.editor_list.append("laser_golight_ip")
            dpg.add_input_text(tag="laser_golight_ip", default_value="192.168.1.164", width=125, height=16)
            dpg.add_text(default_value=txt.WAVE_LENGTH)
            context.editor_list.append("golight_wavelength")
            dpg.add_input_text(tag="golight_wavelength", default_value="1550.0", width=125, height=16,
                               callback=set_params_laser_golight_callback)
            dpg.add_text(default_value='1525~1570')

            dpg.add_text(default_value=txt.POWER_MW)
            #                with dpg.group(horizontal=True):
            context.editor_list.append("golight_power")
            dpg.add_input_text(tag="golight_power", default_value="9.0", width=125, height=16,
                               callback=set_params_laser_golight_callback)
            pw_range = '1~10 dBm'
            dpg.add_text(default_value=pw_range)

            dpg.add_spacer(height=5)
            dpg.add_button(label="Включить луч", callback=turn_laser_golight_callback, height=20, width=200,
                           tag="btn_laser_golight_beam_ctrl", user_data=1)
    dpg.add_spacer(height=50)


class ConfigCtrl:
    def __init__(self):
        self.upd_laser_time = 0
        self.upd_meter_time = 0
        self.chart = None
        self.chart_group = 0
        self.meas_mode = 1

    def loop(self):
        if context.device_worker.sync_ctrl.state & 1:
            context.device_worker.sync_ctrl.state &= 0xFE
            if context.device_worker.sync_ctrl.status == 'ready':
                set_conn_states("sync_ctrl_state", "sync_conn_btn", 1)
                context.device_worker.is_sync_connected = True
                context.logger.log_com("Синхронизатор подключен")
            else:
                set_conn_states("sync_ctrl_state", "sync_conn_btn", 0)
                context.device_worker.is_sync_connected = False

        if context.device_worker.laser_golight_ctrl.state & 1:
            context.device_worker.laser_golight_ctrl.state &= 0xFE
            if context.device_worker.laser_golight_ctrl.init():
                set_conn_states("laser_golight_ctrl_state", "laser_golight_conn_btn", 1)
                context.device_worker.is_laser_golight_connected = True
                context.logger.log_com("Источник подключен")
            else:
                set_conn_states("laser_golight_ctrl_state", "laser_golight_conn_btn", 0)
                context.device_worker.is_laser_golight_connected = False
                
        if context.device_worker.pm2100_1_ctrl.state & 1: 
            context.device_worker.pm2100_1_ctrl.state &= 0xFE
            if context.device_worker.pm2100_1_ctrl.init():
                set_conn_states("pm2100_ctrl_state1", "pm2100_conn_btn1", 1)
                context.device_worker.is_pm2100_1_connected = True
                config_pm_modules(context.device_worker.pm2100_1_ctrl.get_module_cnt(), 1)
                context.logger.log_com("Измеритель 1 подключен")
            else:
                set_conn_states("pm2100_ctrl_state1", "pm2100_conn_btn1", 0)
                context.device_worker.is_pm2100_1_connected = False
                config_pm_modules(['', '', '', '', ''], 1)
            
            config_pm_devices()

        if context.device_worker.pm2100_2_ctrl.state & 1:
            context.device_worker.pm2100_2_ctrl.state &= 0xFE
            if context.device_worker.pm2100_2_ctrl.init():
                set_conn_states("pm2100_ctrl_state2", "pm2100_conn_btn2", 1)
                context.device_worker.is_pm2100_2_connected = True
                config_pm_modules(context.device_worker.pm2100_2_ctrl.get_module_cnt(), 2)
                context.logger.log_com("Измеритель 2 подключен")
            else:
                set_conn_states("pm2100_ctrl_state2", "pm2100_conn_btn2", 0)
                context.device_worker.is_pm2100_2_connected = False
                config_pm_modules(['', '', '', '', ''], 2)
            
            config_pm_devices()

        if context.device_worker.pm2100_3_ctrl.state & 1:  
            context.device_worker.pm2100_3_ctrl.state &= 0xFE
            if context.device_worker.pm2100_3_ctrl.init():
                set_conn_states("pm2100_ctrl_state3", "pm2100_conn_btn3", 1)
                context.device_worker.is_pm2100_3_connected = True
                config_pm_modules(context.device_worker.pm2100_3_ctrl.get_module_cnt(), 3)
                context.logger.log_com("Измеритель 3 подключен")
            else:
                set_conn_states("pm2100_ctrl_state3", "pm2100_conn_btn3", 0)
                context.device_worker.is_pm2100_3_connected = False
                config_pm_modules(['', '', '', '', ''], 3)
            
            config_pm_devices()

        now = round(time.time() * 1000)
        if (now - self.upd_laser_time) > 1000:
            self.upd_laser_time = now

        now = round(time.time() * 1000)
        if (now - self.upd_meter_time) > 200:
            self.upd_meter_time = now

            if not context.is_meas_in_process:
                if context.device_worker.is_pm2100_1_connected and context.auto_meas_pm1:
                    for i, module in enumerate(context.pm_modules1):
                        if module:
                            power_arr = context.device_worker.pm2100_1_ctrl.get_power(i)
                            for j in range(4):
                                context.pm_values[0 + i * 4 + j] = power_arr[j]

                if context.device_worker.is_pm2100_2_connected and context.auto_meas_pm2:
                    for i, module in enumerate(context.pm_modules2):
                        if module:
                            power_arr = context.device_worker.pm2100_2_ctrl.get_power(i)
                            for j in range(4):
                                context.pm_values[20 + i * 4 + j] = power_arr[j]

                if context.device_worker.is_pm2100_3_connected and context.auto_meas_pm3:
                    for i, module in enumerate(context.pm_modules3):
                        if module:
                            power_arr = context.device_worker.pm2100_3_ctrl.get_power(i)
                            for j in range(4):
                                context.pm_values[40 + i * 4 + j] = power_arr[j]

            if context.device_worker.pm2100_1_ctrl.value_upd:
                context.device_worker.pm2100_1_ctrl.value_upd = False
                for i in range(0, 20):
                    
                    dpg.set_value(f"PM2100_ch{i}", f'{context.pm_values[i]}')
                    
                    if i == context.meas_powermap.meas_chan:
                        dpg.set_value("pmap_meas_power", f'{context.pm_values[i]}')
                    if i == context.meas_powermap.meas_chan2:
                        dpg.set_value("pmap_meas_power2", f'{context.pm_values[i]}')

            if context.device_worker.pm2100_2_ctrl.value_upd:
                context.device_worker.pm2100_2_ctrl.value_upd = False
                val1 = 0
                val2 = 0
                for i in range(20, 40):
                    
                    dpg.set_value(f"PM2100_ch{i}", f'{context.pm_values[i]}')

                    if i == context.meas_powermap.meas_chan:
                        val1 = context.pm_values[i]
                        dpg.set_value("pmap_meas_power", f'{val1}')
                    if i == context.meas_powermap.meas_chan2:
                        val2 = context.pm_values[i]
                        dpg.set_value("pmap_meas_power2", f'{val2}')
                    if i == context.chip_meas_ctrl.meas_chan:
                        dpg.set_value("chip_meas_power", f'{context.pm_values[i]}')
                dpg.set_value("pmap_meas_power_diff", f'{round(float(val1) - float(val2), 3)}')
                dpg.set_value("pmap_meas_power_avg", f'{round((float(val1) + float(val2))/2, 3)}')

            if context.device_worker.pm2100_3_ctrl.value_upd:
                context.device_worker.pm2100_3_ctrl.value_upd = False
                for i in range(40, 60):
                    
                    dpg.set_value(f"PM2100_ch{i}", f'{context.pm_values[i]}')
                    
                    if i == context.meas_powermap.meas_chan:
                        dpg.set_value("pmap_meas_power", f'{context.pm_values[i]}')
                    if i == context.meas_powermap.meas_chan2:
                        dpg.set_value("pmap_meas_power2", f'{context.pm_values[i]}')
                    if i == context.chip_meas_ctrl.meas_chan:
                        dpg.set_value("chip_meas_power", f'{context.pm_values[i]}')


def config_pm_modules(modules, id_):
    if modules:
        for i, module in enumerate(modules):
            if module == 'CM1104' or module == 'CM1204':
                if id_ == 1:
                    context.pm_modules1[i] = 1
                    for chan in range(4):
                        context.act_chans[0 + i * 4 + chan] = 1
                elif id_ == 2:
                    context.pm_modules2[i] = 1
                    for chan in range(4):
                        context.act_chans[20 + i * 4 + chan] = 1
                elif id_ == 3:
                    context.pm_modules3[i] = 1
                    for chan in range(4):
                        context.act_chans[40 + i * 4 + chan] = 1
            else:
                if id_ == 1:
                    context.pm_modules1[i] = 0
                    for chan in range(4):
                        context.act_chans[0 + i * 4 + chan] = 0
                elif id_ == 2:
                    context.pm_modules2[i] = 0
                    for chan in range(4):
                        context.act_chans[20 + i * 4 + chan] = 0
                elif id_ == 3:
                    context.pm_modules3[i] = 0
                    for chan in range(4):
                        context.act_chans[40 + i * 4 + chan] = 0


def config_pm_devices():
    saved_pmap_dev = dpg.get_value('pmap_meas_chanel')
    saved_chip_dev = dpg.get_value('chip_meas_chanel')
    saved_zero_dev = dpg.get_value('zero_meas_chanel')
    context.active_pm_list = []
    if context.device_worker.is_pm2100_1_connected:
        context.active_pm_list.append(POWER_METER_1)
    if context.device_worker.is_pm2100_2_connected:
        context.active_pm_list.append(POWER_METER_2)
    if context.device_worker.is_pm2100_3_connected:
        context.active_pm_list.append(POWER_METER_3)
    if len(context.active_pm_list) == 0:
        context.active_pm_list = [DEV_NOT_FOUND]
        dpg.configure_item('pmap_meas_chanel', items=['Нет'])
        dpg.set_value('pmap_meas_chanel', 'Нет')
        dpg.configure_item('chip_meas_chanel', items=['Нет'])
        dpg.set_value('chip_meas_chanel', 'Нет')
        dpg.configure_item('zero_meas_chanel', items=['Нет'])
        dpg.set_value('zero_meas_chanel', 'Нет')

    dpg.configure_item('pmap_device', items=context.active_pm_list)
    dpg.configure_item('chip_device', items=context.active_pm_list)
    dpg.configure_item('zero_device', items=context.active_pm_list)
    if context.active_pm_list.__contains__(saved_pmap_dev):
        dpg.set_value('pmap_device', saved_pmap_dev)
    else:
        dpg.set_value('pmap_device', context.active_pm_list[0])
        select_pm(0, 0, 0)
    context.meas_powermap.select_pm_chan(0, 0, 0)

    if context.active_pm_list.__contains__(saved_chip_dev):
        dpg.set_value('chip_device', saved_chip_dev)
    else:
        dpg.set_value('chip_device', context.active_pm_list[0])
        select_pm(0, 0, 0)
    context.chip_meas_ctrl.select_pm_chan(0, 0, 0)

    if context.active_pm_list.__contains__(saved_zero_dev):
        dpg.set_value('zero_device', saved_zero_dev)
    else:
        dpg.set_value('zero_device', context.active_pm_list[0])
        select_pm(0, 0, 0)
    context.spectrum_zero_gui.select_pm_chan(0, 0, 0)


def turn_laser_golight_callback(sender, app_data, user_data):
    if context.device_worker.is_laser_golight_connected:
        context.device_worker.turn_laser_golight(user_data)
        power = float(dpg.get_value("golight_power"))
        context.device_worker.laser_golight_ctrl.set_power_dbm(float(power))
        wave_len = dpg.get_value("golight_wavelength")
        context.device_worker.laser_golight_ctrl.set_wave_len(float(wave_len))
        if context.device_worker.laser_golight_ctrl.get_beam_state():
            dpg.set_item_user_data("btn_laser_golight_beam_ctrl", 0)
            dpg.configure_item("btn_laser_golight_beam_ctrl", label=txt.BEAM_OFF)
        else:
            dpg.set_item_user_data("btn_laser_golight_beam_ctrl", 1)
            dpg.configure_item("btn_laser_golight_beam_ctrl", label=txt.BEAM_ON)


def set_params_laser_golight_callback(sender, app_data, user_data):
    check_edit_data("golight_wavelength", float, 1570, 1525)
    check_edit_data("golight_power", float, 10, 1)
    if context.device_worker.is_laser_golight_connected:
        power = float(dpg.get_value("golight_power"))
        context.device_worker.laser_golight_ctrl.set_power_dbm(float(power))
        wave_len = dpg.get_value("golight_wavelength")
        context.device_worker.laser_golight_ctrl.set_wave_len(float(wave_len))


def select_sync_com(sender, app_data, user_data):
    param = dpg.get_value("sync_com")
    context.device_worker.sync_ctrl.set_addr(param)


def connect_pm2100_device3(sender, app_data, user_data):
    if user_data == 0:
        context.device_worker.connectPM2100(3)
    elif user_data == 1:
        context.device_worker.disconnectPM2100(3)


def connect_pm2100_device2(sender, app_data, user_data):
    if user_data == 0:
        context.device_worker.connectPM2100(2)
    elif user_data == 1:
        context.device_worker.disconnectPM2100(2)


def connect_pm2100_device1(sender, app_data, user_data):
    if user_data == 0:
        context.device_worker.connectPM2100(1)
    elif user_data == 1:
        context.device_worker.disconnectPM2100(1)


def connect_sync_device(sender, app_data, user_data):
    if user_data == 0:
        context.device_worker.connect_sync()
    elif user_data == 1:
        context.device_worker.disconnect_sync()


def connect_laser_golight_device(sender, app_data, user_data):
    if user_data == 0:
        context.device_worker.connectGolightLaser()
    elif user_data == 1:
        context.device_worker.disconnectGolightLaser()


def init_comports():
    context.comports = get_comports_list()


def set_pm_read_online(sender, app_data, user_data):
    if user_data == 1:
        context.auto_meas_pm1 = dpg.get_value(sender)
    elif user_data == 2:
        context.auto_meas_pm2 = dpg.get_value(sender)
    elif user_data == 3:
        context.auto_meas_pm3 = dpg.get_value(sender)


def pm_zero_callback(sender, app_data, user_data):
    if user_data == 1:
        if context.device_worker.is_pm2100_1_connected:
            context.logger.log_com("Обнуление измерителя 1")
            context.is_meas_in_process = 1
            context.device_worker.pm2100_1_ctrl.run_zero()
            sleep(3)
            context.is_meas_in_process = 0
    elif user_data == 2:
        if context.device_worker.is_pm2100_2_connected:
            context.logger.log_com("Обнуление измерителя 2")
            context.is_meas_in_process = 1
            context.device_worker.pm2100_2_ctrl.run_zero()
            sleep(3)
            context.is_meas_in_process = 0
    elif user_data == 3:
        if context.device_worker.is_pm2100_2_connected:
            context.logger.log_com("Обнуление измерителя 3")
            context.is_meas_in_process = 1
            context.device_worker.pm2100_3_ctrl.run_zero()
            sleep(3)
            context.is_meas_in_process = 0


context.config_ctrl = ConfigCtrl()

"""with dpg.group(horizontal=True):
    with dpg.group():
        dpg.add_spacer(height=5)
        dpg.add_text(default_value=txt.METER_IP_TITLE + '1')
        dpg.add_spacer(height=5)
        context.editor_list.append("pm2100_ip1")
        dpg.add_input_text(tag="pm2100_ip1", default_value="192.168.1.161", width=125, height=16)
        dpg.add_spacer(height=5)
        dpg.add_button(label="Обнулить", width=150, height=20,
                       callback=self.pm_zero_callback, user_data=1)

    dpg.add_spacer(width=10)
    with dpg.table(header_row=False, resizable=False, borders_innerV=True, borders_outerH=True, width=700):
        for i in range(10):
            dpg.add_table_column()
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4}({i * 4})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 1}({i * 4 + 1})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 1}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 2}({i * 4 + 2})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 2}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 3}({i * 4 + 3})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 3}")
    dpg.add_spacer(height=60)
with dpg.group(horizontal=True):
    with dpg.group():
        dpg.add_spacer(height=5)
        dpg.add_text(default_value=txt.METER_IP_TITLE + '2')
        dpg.add_spacer(height=5)
        context.editor_list.append("pm2100_ip2")
        dpg.add_input_text(tag="pm2100_ip2", default_value="192.168.1.162", width=125, height=16)
        dpg.add_spacer(height=5)
        dpg.add_button(label="Обнулить", width=150, height=20,
                       callback=self.pm_zero_callback, user_data=2)
    dpg.add_spacer(width=10)
    with dpg.table(header_row=False, resizable=False, borders_innerV=True, borders_outerH=True, width=700):
        for i in range(10):
            dpg.add_table_column()
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4}({i * 4 + 20})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 20}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 1}({i * 4 + 1 + 20})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 1 + 20}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 2}({i * 4 + 2 + 20})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 2 + 20}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 3}({i * 4 + 3 + 20})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 3 + 20}")

    dpg.add_spacer(height=60)
with dpg.group(horizontal=True):
    with dpg.group():
        dpg.add_spacer(height=5)
        dpg.add_text(default_value=txt.METER_IP_TITLE + '3')
        dpg.add_spacer(height=5)
        context.editor_list.append("pm2100_ip3")
        dpg.add_input_text(tag="pm2100_ip3", default_value="192.168.1.163", width=125, height=16)
        dpg.add_spacer(height=5)
        dpg.add_button(label="Обнулить", width=150, height=20,
                       callback=self.pm_zero_callback, user_data=3)
    dpg.add_spacer(width=10)
    with dpg.table(header_row=False, resizable=False, borders_innerV=True, borders_outerH=True, width=700):
        for i in range(10):
            dpg.add_table_column()
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4}({i * 4 + 40})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 40}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 1}({i * 4 + 1 + 40})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 1 + 40}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 2}({i * 4 + 2 + 40})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 2 + 40}")
        with dpg.table_row():
            for i in range(5):
                with dpg.table_cell():
                    dpg.add_text(default_value=f"CH{i * 4 + 3}({i * 4 + 3 + 40})")
                with dpg.table_cell():
                    dpg.add_text(default_value=placeholder, tag=f"PM2100_ch{i * 4 + 3 + 40}")
"""
