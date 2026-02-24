import random

import dearpygui.dearpygui as dpg
from threading import Timer
import threading
import time

import core.texts as txt
from core.consts import *
from core.context import Context
from core.utils import *
import numpy as np
from math import sin
from Measurements.devices.pm2100 import PM2100
from core.gui_helper import *

#PM_2100   = "1250 – 1630 нм  от -80 до +10 дБм"
#Golight   = "1525 - 1565 нм  от  0 до  +10 дБм"

context = Context()

MEAS_TYPES = ["Один канал", "Все подключенные каналы", "Один канал отобразить на все"]
class MeasureSpectrumZero():

    def __init__(self):
        self.start_len  = 1525
        self.stop_len   = 1565
        self.step       = 0.01
        self.wave_len = 0
        self.can_run  = 0
        self.meas_type = 0
        self.pm_dev    = None
        self.pm_module = -1
        self.pm_chan = -1
        self.meas_chan = -1

    def show_spectrum_zero_page(self):
        dpg.configure_item("spectrum_zero", show = True)

    def prepare_spectrum_zero_page(self):
#        for i in range(2200,2300):
#            arr = np.array([(float(i), np.random.default_rng(i).random((60)))], context.spectrum_zero_dt)
#            context.spectrum_zero = np.append(context.spectrum_zero, arr)
        with dpg.window(tag="spectrum_zero", label="Измерения опорного уровня мощности", pos=(200, 30),
                        no_collapse=True, show=False):
            with dpg.group(horizontal=True):
                dpg.add_group(tag="spectrum_zero_legend")
                self.meas_chart = dpg.add_plot(label="Нулевой уровень", height=500, width=1000)
            dpg.add_spacer(height=10)
            dpg.add_text(default_value=f"               Измерение производится в диапазоне от {self.start_len}нм до "
                                       f"{self.stop_len}нм с шагом {self.step}нм")
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text(default_value="    Источник")
                    dpg.add_radio_button(label="", tag="zero_laser_type", items=["Golight OS-TL"],
                                         horizontal=True, default_value="Golight OS-TL")

                    dpg.add_text(default_value="    Тип измерения")
                    dpg.add_radio_button(label="", tag="zero_meas_type",
                                         items=MEAS_TYPES,
                                         horizontal=True, default_value=MEAS_TYPES[self.meas_type])
                dpg.add_spacer(width=25)
                with dpg.group():
                    dpg.add_text(default_value="    Выбор измерителя")
                    dpg.add_combo(tag="zero_device", items=[txt.DEV_NOT_FOUND], default_value=txt.DEV_NOT_FOUND,
                                  width=200, callback=self.select_pm)

                    dpg.add_text(default_value="    Канал измерителя")
                    dpg.add_combo(tag="zero_meas_chanel", items=["Нет"], default_value='Нет', width=200,
                                  callback=self.select_pm_chan)

            dpg.add_button(label="Провести измерение", callback=self.measure_zero_spectrum_callback,
                           user_data=False, width= 200, height=30)

            dpg.push_container_stack(self.meas_chart)
            # create x and y axes
            dpg.add_plot_axis(dpg.mvXAxis, label="Длина волны", tag="zero_x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Мощность, dBm", tag="zero_y_axis")
            # series belong to a y axis
            dpg.pop_container_stack() # pop chart context
        self.show_zero_chart()
        context.gui_hlp.show_channels_legend(legend_grp="spectrum_zero_legend", prefix="zero_legend", callback=self.legend_callback)

    def legend_callback(self, sender, app_data, user_data):
        val = dpg.get_value(sender)
        item = f"series_zero_tag{user_data}"
        if dpg.does_item_exist(item):
            dpg.configure_item(item, show=val)

    def measure_zero_spectrum_callback(self, sender, app_data, user_data):
        if not context.device_worker.is_pm2100_1_connected and not context.device_worker.is_pm2100_2_connected and \
                not context.device_worker.is_pm2100_3_connected:
            context.logger.log_warning(txt.PM_NOT_CONNECTED)
            return
        meas_type = dpg.get_value("zero_meas_type")
        if meas_type==MEAS_TYPES[0]:
            self.meas_type = 0
        elif meas_type==MEAS_TYPES[1]:
            self.meas_type = 1
        elif meas_type==MEAS_TYPES[2]:
            self.meas_type = 2

        pm_channel     = int(dpg.get_value("zero_meas_chanel"))
        self.pm_module = pm_channel // 4  # вычисляем модуль
        self.pm_chan   = pm_channel % 4   # вычисляем канал

        laser_type = dpg.get_value("zero_laser_type")

        if not context.device_worker.is_laser_golight_connected:
            context.logger.log_warning('Не подключен лазер Golight OS-TL')
            return

        context.gui_hlp.showMessage(txt.PLATFORM_MEASURING_MSG, txt.BREAK, DLG_CT_BREAK_PROC, prog_bar=True)
        self.thread_proc = threading.Thread(target=self.exec_zero_measure, args=[], daemon=True)
        self.thread_proc.start()

    def select_pm(self, sender, app_data, user_data):
        device = dpg.get_value('zero_device')
        chan_list = []
        if device==txt.POWER_METER_1:
            self.pm_dev = context.device_worker.pm2100_1_ctrl
            for i in range(0, 20):
                if context.act_chans[i]:
                    chan_list.append(str(i))
        elif device == txt.POWER_METER_2:
            self.pm_dev = context.device_worker.pm2100_2_ctrl
            for i in range(20, 40):
                if context.act_chans[i]:
                    chan_list.append(str(i-20))
        elif device == txt.POWER_METER_3:
            self.pm_dev = context.device_worker.pm2100_3_ctrl
            for i in range(40, 60):
                if context.act_chans[i]:
                    chan_list.append(str(i-40))
        if len(chan_list)==0:
            self.pm_dev = None
            chan_list = ['Нет']
        dpg.configure_item('zero_meas_chanel', items=chan_list)
        dpg.set_value('zero_meas_chanel', chan_list[0])

    def select_pm_chan(self, sender, app_data, user_data):
        chan = dpg.get_value('zero_meas_chanel')
        if not chan.isdigit():
            self.meas_chan = -1
        else:
            self.meas_chan = int(chan)
            if self.pm_dev == context.device_worker.pm2100_2_ctrl:
                self.meas_chan += 20
            elif self.pm_dev == context.device_worker.pm2100_3_ctrl:
                self.meas_chan += 40

    def exec_zero_measure(self):
        try:
            power = context.spectrum_laser_power

            self.wave_len = self.start_len
            context.is_meas_in_process = True

            conn_state = context.device_worker.laser_golight_ctrl.get_beam_state()
            context.device_worker.laser_golight_ctrl.turn_beam(1)
            context.device_worker.laser_golight_ctrl.set_power_dbm(power)
            context.device_worker.laser_golight_ctrl.set_wave_len(self.start_len)
            time.sleep(2)

            context.break_proc = False
            steps = (self.stop_len - self.start_len) / self.step
            context.gui_hlp.init_progress_bar(steps)
            wl_idx = 0
            while not context.break_proc and self.wave_len <= self.stop_len:
                context.gui_hlp.progress_bar_step()
                context.device_worker.laser_golight_ctrl.set_wave_len(self.wave_len)

                if context.device_worker.is_pm2100_1_connected:
                    context.device_worker.pm2100_1_ctrl.set_wave_len(self.wave_len, False)
                if context.device_worker.is_pm2100_2_connected:
                    context.device_worker.pm2100_2_ctrl.set_wave_len(self.wave_len, False)
                if context.device_worker.is_pm2100_3_connected:
                    context.device_worker.pm2100_3_ctrl.set_wave_len(self.wave_len, False)

                if len(context.spectrum_zero)>wl_idx:
                    context.spectrum_zero[wl_idx]['wl'] = float(self.wave_len)
                else: # добавляем в массив
                    arr = np.array([(float(self.wave_len), np.zeros(60))], context.spectrum_zero_dt)
                    context.spectrum_zero = np.append(context.spectrum_zero, arr)

                if self.meas_type == 0: # ---------------------------измерение одного канала
                    pm_values = self.pm_dev.get_power(self.pm_module)
                    val = pm_values[self.pm_chan]
#                    for j in range(60):
 #                       if j == self.meas_chan:
                    context.pm_values[self.meas_chan] = val
                    context.spectrum_zero[wl_idx]['pow'][self.meas_chan] = float(val)

                elif self.meas_type == 1: # -------------------------измерение всех каналов
                    if context.device_worker.is_pm2100_1_connected:
                        for i, module in enumerate(context.pm_modules1):
                            if module:
                                power_arr = context.device_worker.pm2100_1_ctrl.get_power(i)
                                for j in range(4):
                                    chan_idx = 0 + i * 4 + j
                                    context.pm_values[chan_idx] = power_arr[j]
                                    context.spectrum_zero[wl_idx]['pow'][chan_idx] = float(power_arr[j])

                    if context.device_worker.is_pm2100_2_connected:
                        for i, module in enumerate(context.pm_modules2):
                            if module:
                                power_arr = context.device_worker.pm2100_2_ctrl.get_power(i)
                                for j in range(4):
                                    chan_idx = 20 + i * 4 + j
                                    context.pm_values[chan_idx] = power_arr[j]
                                    context.spectrum_zero[wl_idx]['pow'][chan_idx] = float(power_arr[j])

                    if context.device_worker.is_pm2100_3_connected:
                        for i, module in enumerate(context.pm_modules3):
                            if module:
                                power_arr = context.device_worker.pm2100_3_ctrl.get_power(i)
                                for j in range(4):
                                    chan_idx = 40 + i * 4 + j
                                    context.pm_values[chan_idx] = power_arr[j]
                                    context.spectrum_zero[wl_idx]['pow'][chan_idx] = float(power_arr[j])
                else: # -----------------------------------измерение одного канала и копирование на все
                    pm_values = self.pm_dev.get_power(self.pm_module)
                    val = pm_values[self.pm_chan]
                    for j in range(60):
                        context.pm_values[j] = val
                        context.spectrum_zero[wl_idx]['pow'][j] = float(val)

                self.wave_len += self.step
                wl_idx += 1

            self.show_zero_chart()

            if context.break_proc == False:
                np.save('Config\spectrum_zero.npy', context.spectrum_zero)

        finally:
            context.is_meas_in_process = False
            context.gui_hlp.popup_close()

    def show_zero_chart(self):
        arr_len = len(context.spectrum_zero)#int((self.stop_len-self.start_len) / self.step)+1
        ser_data_x = np.zeros(arr_len)
        ser_data_y = np.zeros((60, arr_len))
        for wl in range(arr_len):
            ser_data_x[wl] = context.spectrum_zero[wl]["wl"]
            for chan_idx in range(60):
                ser_data_y[chan_idx][wl] = context.spectrum_zero[wl]["pow"][chan_idx]

        for chan_idx in range(60):
            dpg.delete_item(f"series_zero_tag{chan_idx}")
            chan_name = f"CH{chan_idx}"
            dpg.add_line_series(ser_data_x, ser_data_y[chan_idx],
                                label=chan_name, parent="zero_y_axis", tag=f"series_zero_tag{chan_idx}")

context.spectrum_zero_gui = MeasureSpectrumZero()
