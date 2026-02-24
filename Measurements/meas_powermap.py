#from threading import Timer
#import threading
import random
import time
import datetime

from core.gui_helper import *
from core.texts import *

from Measurements.devices.pm2100 import PM2100
import threading
import core.texts as txt
from core.utils import *
import numpy as np
import cv2 #Bind OpenCV
from scipy.ndimage import gaussian_filter

context = Context()

GO_TO_ZERO = 1
GO_TO_MAX  = 2

class MeasurePowerMap():

    def __init__(self):
        self.cross  = 999999
        self.cross2 = 999999

        self.pm_mode    =  0
        self.meas_chan  = -1
        self.meas_chan2 = -1

        self.meas_chart = None
        self.thread_proc = None

    def mode_sel_callback(self, sender, app_data, user_data):
        if dpg.get_value("pmap_mode") == PM_MODE_CHAN:
            context.pmap_procedures.is_prepared = False
            dpg.hide_item(self.meas_chart2)
            dpg.hide_item("pm_pm2")
            dpg.hide_item("pm_chan_dist")
            self.pm_mode = 0
        else:  # PM_MODE_FAWR
            context.pmap_procedures.is_prepared = False
            dpg.show_item(self.meas_chart2)
            dpg.show_item("pm_pm2")
            dpg.show_item("pm_chan_dist")
            self.pm_mode = 1

    def platform_sel_callback(self, sender, app_data, user_data):
        if dpg.get_value("pmap_platform") == LEFT:
            context.pmap_procedures.platform = LEFT_CHAN
            context.pmap_procedures.y_idx = context.z1_line_i
            context.pmap_procedures.x_idx = context.y1_line_i
            context.pmap_procedures.horiz_idx = context.x1_ang_i

        else:  # RIGHT platform
            context.pmap_procedures.platform = RIGHT_CHAN
            context.pmap_procedures.y_idx = context.z2_line_i
            context.pmap_procedures.x_idx = context.y2_line_i
            context.pmap_procedures.horiz_idx = context.x2_ang_i

        context.pmap_procedures.y_axis     = int(context.axis[context.pmap_procedures.y_idx]['idx'])
        context.pmap_procedures.x_axis     = int(context.axis[context.pmap_procedures.x_idx]['idx'])
        context.pmap_procedures.horiz_axis = int(context.axis[context.pmap_procedures.horiz_idx]['idx'])

    def plot_callback(self, sender, app_data, user_data):
            if self.pm_mode == 0:
                if context.zplatform.is_connected:
                    x, y = dpg.get_plot_mouse_pos()
                    context.logger.log_com(f"Перемещение Y -> {x} мкм ({int(x/Y_MKM_KOEF)} шагов) , y -> {y} мкм({int(y/Z_MKM_KOEF)}шагов)")
                    context.gui_hlp.showMessage(txt.PLATFORM_AIMING_MSG, txt.BREAK, DLG_CT_NO_CLOSE)
                    self.set_platform_pos(context.pmap_procedures.x_axis, context.pmap_procedures.y_axis, int(x/Y_MKM_KOEF), int(y/Y_MKM_KOEF))
                    context.gui_hlp.popup_close()
            else:
                self.cross = context.pmap_procedures.process_horiz_aiming(self.cross, 1)

    def plot_callback2(self, sender, app_data, user_data):
#        if context.zplatform.is_connected:
            x, y = dpg.get_plot_mouse_pos()
            if self.pm_mode == 1:
                self.cross2 = context.pmap_procedures.process_horiz_aiming(self.cross2, 2)

# Перемещение
    def set_platform_pos(self, x_axis, y_axis, x, y):
#        context.logger.log_com("shift x -> " + str(x) + ", y -> " + str(y))
        x = context.pmap_procedures.map_min_x+x
        y = context.pmap_procedures.map_min_y+y
        context.zplatform.move_to(y_axis, y)
        context.zplatform.move_to(x_axis, x)
        while context.zcontrollers.is_platforms_axis_busy():
            pass

    def measure_powermap_callback(self, sender, app_data, user_data):
        if ((not context.device_worker.is_pm2100_1_connected) and
            (not context.device_worker.is_pm2100_2_connected) and
            (not context.device_worker.is_pm2100_3_connected)):
            context.logger.log_warning(txt.PM_NOT_CONNECTED)
            return
        if not context.zplatform.is_connected:
            context.logger.log_warning(txt.PLATFORMS_NOT_CONNECTED)
            return

        if context.pmap_procedures.syncro_mode and  not context.device_worker.is_syncro_connected:
            context.logger.log_warning(txt.SYNCRONIZER_NOT_CONNECTED)
            return

        context.gui_hlp.showMessage(txt.PLATFORM_AIMING_MSG, txt.BREAK, DLG_CT_BREAK_PROC, prog_bar=True)
# определяем параметры стыковки
        pm_channel = dpg.get_value("pmap_meas_chanel")
        if pm_channel.isnumeric():
            pm_channel = int(pm_channel)
        pm_channel2 = dpg.get_value("pmap_meas_chanel2")
        if pm_channel2.isnumeric():
            pm_channel2 = int(pm_channel2)


#        self.pm_dev уже содержит измеритель с которым будет производится работа
        context.pmap_procedures.pm_module = pm_channel // 4  # вычисляем модуль
        context.pmap_procedures.pm_chan  = pm_channel % 4  # вычисляем канал

        context.pmap_procedures.pm_module2 = pm_channel2 // 4  # вычисляем модуль 2
        context.pmap_procedures.pm_chan2 = pm_channel2 % 4  # вычисляем канал 2

        context.pmap_procedures.y_count       = dpg.get_value("pmap_z_count")
        context.pmap_procedures.x_scale       = int(dpg.get_value("pmap_y_width")/Y_MKM_KOEF)
        context.pmap_procedures.delta         = int(dpg.get_value("pmap_delta")/Y_MKM_KOEF)
        context.pmap_procedures.chan_dist     = dpg.get_value("pmap_chans_dist")
        context.pmap_procedures.after_measure = GO_TO_ZERO

        if self.pm_mode == 0:
            if context.pmap_procedures.syncro_mode:
                self.thread_proc = threading.Thread(target=context.pmap_procedures.scan_manual_sync, args=[], daemon=True)
            else:
                self.thread_proc = threading.Thread(target=context.pmap_procedures.scan_manual, args=[], daemon=True)
        else:
            if context.pmap_procedures.syncro_mode:
                self.thread_proc = threading.Thread(target=context.pmap_procedures.correct_horizont, args=[], daemon=True)

#        self.thread_proc = threading.Thread(target=self.exec_measure, args=[], daemon=True)
        self.thread_proc.start()


    def prepare(self):
        context.pmap_procedures.is_prepared = True
        context.pmap_procedures.ser_data = np.zeros(shape=[context.pmap_procedures.x_scale, context.pmap_procedures.y_count])

        for y in range(0, context.pmap_procedures.y_count):
            for x in range(0, context.pmap_procedures.x_scale):
                #                context.pmap_procedures.ser_data[i][j] = 1 - ((i-25)*(j-25)/(25*25))
                context.pmap_procedures.ser_data[x][y] = (1 - ((y - context.pmap_procedures.y_count / 2) ** 2) / ((context.pmap_procedures.y_count ** 2) / 4)) * \
                                      (1 - ((x - context.pmap_procedures.x_scale / 2) ** 2) / ((context.pmap_procedures.x_scale ** 2) / 4))

        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            self.meas_chart = dpg.add_plot(label="Power map", height=500, width=600, no_menus=True, no_title=True,
                                           crosshairs=True)
            if not dpg.does_item_exist("widget handler"):
                with dpg.item_handler_registry(tag="widget handler"):
                    dpg.add_item_clicked_handler(button=0, callback=self.plot_callback)
            dpg.bind_item_handler_registry(self.meas_chart, "widget handler")
            dpg.push_container_stack(self.meas_chart)

            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")#, no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")#, no_tick_labels=True, no_tick_marks=True)

            context.pmap_procedures.prepArray(context.pmap_procedures.ser_data)
            context.pmap_procedures.draw_map(context.pmap_procedures.ser_data, 1, True, True)
            context.pmap_procedures.draw_scale()

            dpg.pop_container_stack()  # pop chart context
            with dpg.group():
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text(default_value="Платформа")
                        dpg.add_radio_button(tag="pmap_platform", items=[LEFT, RIGHT], horizontal=True,
                                             default_value=LEFT, callback=context.meas_powermap.platform_sel_callback)
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text(default_value="Режим измерения")
                        dpg.add_radio_button(tag="pmap_mode", items=[PM_MODE_CHAN, PM_MODE_FAWR], horizontal=True,
                                             default_value=LEFT, callback=self.mode_sel_callback)
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text(default_value="Выбор измерителя")
                        dpg.add_combo(tag="pmap_device", items=[DEV_NOT_FOUND], default_value=DEV_NOT_FOUND,
                                      width=200, callback=self.select_pm)
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text(default_value="Канал измерителя")
                        dpg.add_combo(tag="pmap_meas_chanel", items=["Нет"], default_value='Нет', width=100,
                                      callback=self.select_pm_chan)
                    with dpg.group(tag="pm_pm2", show=False):
                        dpg.add_text(default_value="Канал измерителя 2")
                        dpg.add_combo(tag="pmap_meas_chanel2", items=["Нет"], default_value='Нет', width=100,
                                      callback=self.select_pm_chan2)
                    dpg.add_text(tag="pmap_meas_power", default_value="")
                dpg.add_spacer(height=5)
                with dpg.group(tag="pm_chan_dist", horizontal=True, show=False):
                    with dpg.group():
                        dpg.add_text(default_value="Количество каналов между измеряемыми")
                        dpg.add_input_int(tag="pmap_chans_dist", width=100, default_value=47,
                                          min_value=0, max_value=200, min_clamped=True, max_clamped=True)
                dpg.add_spacer(height=5)
                dpg.add_checkbox(label='Измерения в синхронном режиме', callback=self.syncro_mode_callback, default_value=True)
                dpg.add_spacer(height=15)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text(default_value="Шагов по Z")
                        context.editor_list.append("pmap_z_count")
                        dpg.add_input_int(tag="pmap_z_count", width=100, default_value=context.pmap_procedures.y_count,
                                          min_value=2, max_value=500, min_clamped=True, max_clamped=True)

                    with dpg.group():
                        dpg.add_text(default_value="Величина шага Z, мкм")
#                        with dpg.group(horizontal=True):
                        context.editor_list.append("pmap_delta")
                        delta_um = context.pmap_procedures.delta * Z_MKM_KOEF
                        dpg.add_input_float(tag="pmap_delta", width=100, default_value=delta_um, step=Y_MKM_KOEF,
                                            callback=self.recalc_um, min_value=0.2, max_value=100,
                                            min_clamped=True, max_clamped=True)
                        dpg.add_text(default_value=f"{context.pmap_procedures.delta} шагов", tag="delta_steps")

                dpg.add_spacer(height=25)
                dpg.add_text(default_value="Ширина области Y, мкм")
                with dpg.group(horizontal=True):
                    context.editor_list.append("pmap_y_width")
                    x_scale_um =  context.pmap_procedures.x_scale * Y_MKM_KOEF
                    dpg.add_input_int(tag="pmap_y_width", width=100, default_value=x_scale_um, step=Y_MKM_KOEF,
                                      callback=self.recalc_um, min_value=10, max_value=5000,
                                      min_clamped=True, max_clamped=True)
                    dpg.add_text(default_value=f"мкм = {context.pmap_procedures.x_scale} шагов", tag="xscale_steps")

                dpg.add_spacer(height=10)
                dpg.add_button(label="Провести измерение", width=200, height=30,
                               callback=self.measure_powermap_callback)
#                dpg.add_spacer(height=10)
#                dpg.add_button(label="Start Meas", width=200, height=30,
#                               callback=self.make_sync_dbg_start_meas)
#                dpg.add_spacer(height=10)
#                dpg.add_button(label="Make Sync", width=200, height=30,
#                               callback=self.make_sync_dbg_sync)
#                dpg.add_spacer(height=10)
#                dpg.add_button(label="Get Meas", width=200, height=30,
#                               callback=self.make_sync_dbg_get_meas)
#                dpg.add_spacer(height=10)
#                dpg.add_button(label="Get Meas state", width=200, height=30,
#                               callback=self.make_sync_dbg_get_meas_state)
#                dpg.add_spacer(height=10)
#                dpg.add_button(label="Get Error", width=200, height=30,
#                               callback=self.make_sync_dbg_get_err)
#                dpg.add_spacer(height=10)
#                dpg.add_button(label="Stop Meas", width=200, height=30,
#                               callback=self.make_sync_dbg_stop_meas)
            self.meas_chart2 = dpg.add_plot(label="Power map", height=500, width=500, no_menus=True, no_title=True,
                                            show=False, crosshairs=True)
            if not dpg.does_item_exist("chart2_widget_handler"):
                with dpg.item_handler_registry(tag="chart2_widget_handler"):
                    dpg.add_item_clicked_handler(button=0, callback=self.plot_callback2)
            dpg.bind_item_handler_registry(self.meas_chart2, "chart2_widget_handler")

    def make_sync_dbg_start_meas(self, sender, app_data, user_data):
        if context.device_worker.is_pm2100_1_connected:
            context.device_worker.pm2100_1_ctrl.startConst2(1535, 0.01, 10000)

    def make_sync_dbg_stop_meas(self, sender, app_data, user_data):
        if context.device_worker.is_pm2100_1_connected:
            context.device_worker.pm2100_1_ctrl.stop_meas()
            context.device_worker.pm2100_1_ctrl.set_work_mode(4, False)

    def make_sync_dbg_get_meas_state(self, sender, app_data, user_data):
        if context.device_worker.is_pm2100_1_connected:
            res1, res2, = context.device_worker.pm2100_1_ctrl.get_meas_state()
            print("res1=", res1)
            print("res2=", res2)

    def make_sync_dbg_get_meas(self, sender, app_data, user_data):
        if context.device_worker.is_pm2100_1_connected:
            res = context.device_worker.pm2100_1_ctrl.get_meas_data(0, 1)
            print("meas=", res)

    def make_sync_dbg_get_err(self, sender, app_data, user_data):
        if context.device_worker.is_pm2100_1_connected:
            res = context.device_worker.pm2100_1_ctrl.get_err()
            print("err=", res)

    def make_sync_dbg_sync(self, sender, app_data, user_data):
        if context.device_worker.is_syncro_connected:
            context.device_worker.syncroniser_ctrl.make_sync(10000, 1000);

    def select_pm(self, sender, app_data, user_data):
        device = dpg.get_value('pmap_device')
        chan_list = []
        if device == POWER_METER_1:
            context.pmap_procedures.pm_dev = context.device_worker.pm2100_1_ctrl
            for i in range(0, 20):
                if context.act_chans[i]:
                    chan_list.append(str(i))
        elif device == POWER_METER_2:
            context.pmap_procedures.pm_dev = context.device_worker.pm2100_2_ctrl
            for i in range(20, 40):
                if context.act_chans[i]:
                    chan_list.append(str(i-20))
        elif device == POWER_METER_3:
            context.pmap_procedures.pm_dev = context.device_worker.pm2100_3_ctrl
            for i in range(40, 60):
                if context.act_chans[i]:
                    chan_list.append(str(i-40))
        if len(chan_list)==0:
            context.pmap_procedures.pm_dev = None
            chan_list = ['Нет']
            dpg.configure_item('pmap_meas_chanel', items=chan_list)
            dpg.configure_item('pmap_meas_chanel2', items=chan_list)
            dpg.set_value('pmap_meas_chanel', chan_list[0])
            dpg.set_value('pmap_meas_chanel2', chan_list[0])
        else:
            dpg.configure_item('pmap_meas_chanel', items=chan_list)
            dpg.configure_item('pmap_meas_chanel2', items=chan_list)
            dpg.set_value('pmap_meas_chanel', chan_list[0])
            dpg.set_value('pmap_meas_chanel2', chan_list[1])

    def syncro_mode_callback(self, sender, app_data, user_data):
        if dpg.get_value(sender):
            context.pmap_procedures.syncro_mode = True
        else:
            context.pmap_procedures.syncro_mode = False

    def select_pm_chan(self, sender, app_data, user_data):
        chan = dpg.get_value('pmap_meas_chanel')
        if not chan.isdigit():
            dpg.set_value("pmap_meas_power", "***")
        else:
            self.meas_chan = int(chan)
            if context.pmap_procedures.pm_dev == context.device_worker.pm2100_2_ctrl:
                self.meas_chan += 20
            elif context.pmap_procedures.pm_dev == context.device_worker.pm2100_3_ctrl:
                self.meas_chan += 40

    def select_pm_chan2(self, sender, app_data, user_data):
        chan = dpg.get_value('pmap_meas_chanel2')
        if chan.isdigit():
            self.meas_chan2 = int(chan)
            if context.pmap_procedures.pm_dev == context.device_worker.pm2100_2_ctrl:
                self.meas_chan2 += 20
            elif context.pmap_procedures.pm_dev == context.device_worker.pm2100_3_ctrl:
                self.meas_chan2 += 40

    def recalc_um(self):
        delta = int(dpg.get_value("pmap_delta")/Y_MKM_KOEF)
        x_scale = int(dpg.get_value("pmap_y_width")/Y_MKM_KOEF)
        dpg.set_value("pmap_delta", delta*Y_MKM_KOEF)
        dpg.set_value("delta_steps", f"{delta} шагов")
        dpg.set_value("xscale_steps", f"{x_scale} шагов")

    def powermap_loop(self):
        #context.current_proc
        if dpg.get_value(context.tabBar) != TAB_POWERMAP_ID:
            return
        if self.pm_mode == 0:
            self.cross = context.pmap_procedures.process_crosshair(self.cross)

context.meas_powermap = MeasurePowerMap()
