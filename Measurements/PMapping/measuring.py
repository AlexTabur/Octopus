import random
import time

from core.gui_helper import *
from core.texts import *

import Measurements.devices.pm2100 as pm2100
import threading
import math
import core.texts as txt
from core.utils import *
import numpy as np
import cv2 #Bind OpenCV
from scipy.ndimage import gaussian_filter

context = Context()

GO_TO_ZERO = 1
GO_TO_MAX  = 2

class PMapMeasureProcedures():

    def __init__(self):
        # параметры движения
        self.accT = 0 # время ускорения
        self.accS = 0 # путь ускорения
        self.moveT = 0 # время на уст.скорости
        self.moveS = 0 # путь на уст.скорости
        self.decT = 0 # время замедления
        self.decS = 0 # путь замеления

        self.syncro_mode = True

        self.max_val = 0
        self.min_val = 0
        self.diap = 0

        self.pm_dev = None
        self.pm_module  = -1
        self.pm_module2 = -1
        self.pm_chan  = -1
        self.pm_chan2 = -1

        self.y_count = 5
        self.delta = 20
        self.x_scale = 100

        self.zero_pos_x = -1
        self.zero_pos_y = -1
        self.is_prepared = False

        self.x_pos = 0
        self.y_pos = 0

        self.map_min_x = 0
        self.map_max_x = 0
        self.map_min_y = 0
        self.map_max_y = 0
        #self.map_side  = 0

        self.map_side = LEFT_CHAN

        self.ser_data  = np.zeros(shape=[self.x_scale, self.y_count])
        self.ser_data2 = np.zeros(shape=[self.x_scale, self.y_count])
        self.ser_data_res = [0, 0, 0, 0, 0]

        self.after_measure = GO_TO_ZERO

#       параметры выбранной платформы
        self.platform = LEFT_CHAN
        self.x_idx = context.y1_line_i
        self.y_idx = context.z1_line_i
        self.horiz_idx = context.x1_ang_i
        self.x_axis = int(context.axis[self.x_idx]['idx'])
        self.y_axis = int(context.axis[self.y_idx]['idx'])
        self.horiz_axis = int(context.axis[self.horiz_idx]['idx'])

        # параметры процесса выравнивания
        self.horiz1_y   = -1
        self.horiz2_y   = -1
        self.chan_dist  =  0

    def draw_scale(self):
        leg_count = 15
        sideX = 1
        sideY = self.delta*self.y_count / leg_count
        for y in range(0, leg_count):
            legend_width = self.x_scale / 4
            #red = (int(self.min_val+y*self.diap/self.z_count) >> 32) & 0xFF
            red = int(y/leg_count*0xFF)
            color = (red, 0, 0)
            x0 = self.x_scale * sideX
            x1 = self.x_scale * sideX + legend_width
            y0 = y * sideY
            y1 = y * sideY + sideY
            x0 *= X_MKM_KOEF
            x1 *= X_MKM_KOEF
            y0 *= Y_MKM_KOEF
            y1 *= Y_MKM_KOEF
            dpg.draw_quad((x0, y0), (x0, y1), (x1, y1), (x1, y0), thickness=0.05,
                          fill=color, color=(10, 10, 10))
            value = "{:5.2f}".format(self.min_val+y*self.diap/leg_count)
            dpg.draw_text(pos=(x0, y1), text=value, color=(200, 200, 200), size=self.x_scale*X_MKM_KOEF/20)

    def prepArray(self, arr):
        # вычисления диапазона измеренных значений
        self.max_val = -100000
        self.min_val = 100000
        x_cnt =  arr.shape[0]
        y_cnt =  arr.shape[1]

        for x in range(0, x_cnt):
            for y in range(0, y_cnt):
                if arr[x][y] != 0:
                    if arr[x][y]<self.min_val:
                        self.min_val = arr[x][y]
                    if arr[x][y]>self.max_val:
                        self.max_val = arr[x][y]

        self.diap = self.max_val - self.min_val

        if self.diap==0:
            context.logger.log("Не обнаружено различающихся значений")
            return False
        # преобразовать результаты измерения в цвет
        for x in range(0, self.x_scale):
            for y in range(0, self.y_count):
                if arr[x][y]==0:
                    arr[x][y] = self.min_val
                color = int(0xFF*(arr[x][y] - self.min_val)/self.diap)
                arr[x][y] = color
        arr[:] = arr
        return True

    def draw_map(self, arr, num, draw, scale_place): # scale_place - оставить место для шкалы легенды?
        sideX = 1
        sideY = self.delta
        truncate = 2
        if draw:
            for y in range(0, self.y_count):
                for x in range(0, self.x_scale):
                    #                   self.ser_data[i][j] = 1 - ((i-25)*(j-25)/(25*25))
                    #                   dpg.draw_quad((-2, -2), (-2, 2), (2, 2), (2, -2), label="qwe", thickness=0.1)
                    red = int(arr[x][y]) & 0xFF
                    color = (red, 0, 0)
                    x0 = x * sideX
                    x1 = x * sideX + sideX
                    y0 = y * sideY
                    y1 = y * sideY + sideY
                    x0 *= X_MKM_KOEF
                    x1 *= X_MKM_KOEF
                    y0 *= Y_MKM_KOEF
                    y1 *= Y_MKM_KOEF

                    dpg.draw_quad((x0, y0), (x0, y1), (x1, y1), (x1, y0), thickness=0.05,
                                  fill=color, color=color)
        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(arr)
        # круг на максимальном пикселе
        if draw:
            dpg.draw_circle(center=(maxLoc[1]*X_MKM_KOEF,maxLoc[0]*sideY*Y_MKM_KOEF), radius=self.x_scale*X_MKM_KOEF/50, thickness=0.05, color=(255, 255, 255))
            dpg.set_axis_limits(f"pm_y_axis{num}", 0, self.y_count * self.delta * Y_MKM_KOEF)
            if scale_place:
                dpg.set_axis_limits(f"pm_x_axis{num}", 0, (self.x_scale + self.x_scale / 4) * X_MKM_KOEF)
            else:
                dpg.set_axis_limits(f"pm_x_axis{num}", 0, (self.x_scale) * X_MKM_KOEF)
        return maxLoc

# стыковка(измерение) из диалога с графиком
    def scan_manual(self):
        x_speed = 0
        x_acc = 0
        x_dec = 0
        self.map_side = self.platform
        context.is_meas_in_process = True
        try:
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.zeros(shape=[self.x_scale+1, self.y_count])

    # сохранили изходные позиции
            self.zero_pos_x = context.zplatform.get_pos(self.x_axis)
            self.zero_pos_y = context.zplatform.get_pos(self.y_axis)

    # устанавливаем скорость для сканирования
            res, x_acc = context.zplatform.get_accel(self.x_axis)
            res, x_dec = context.zplatform.get_decel(self.x_axis)
            res, x_speed = context.zplatform.get_speed(self.x_axis)
            context.zplatform.set_accel(self.x_axis, 25000)
            context.zplatform.set_decel(self.x_axis, 25000)
            context.zplatform.set_speed(self.x_axis, 100)

            # Откатились в угол сканируемой области
    # X - Width/2
            context.zplatform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
    # Y - Width/2
            context.zplatform.move(self.x_axis, (-1 * self.x_scale / 2) + 1)

            while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc: # прерывание по кнопке
                return

            self.map_min_x = context.zplatform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.zplatform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count*self.delta
    # сохранили начальные позиции для сканирования
            self.init_pos_x = context.zplatform.get_pos(self.x_axis)

    # Start scan
            start = time.time()
            x_sign = 1

            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()
                x_pos = 0
    # идем в край -->
                context.zplatform.move(self.x_axis, x_sign * self.x_scale)
                y_pos = y #int(context.zplatform.get_pos(self.y_axis) - init_pos_y)

                while True:
                    pm_values = self.pm_dev.get_power(self.pm_module)
                    x_pos = int(context.zplatform.get_pos(self.x_axis) - self.init_pos_x)
                    self.ser_data[x_pos][y_pos] = float(pm_values[self.pm_chan])

                    if (not context.zcontrollers.is_platforms_axis_busy()) or context.break_proc: # доехалм до конца
                        x_sign *= -1  # разворачиваем напровление по Z
                    # шаг вниз
                        context.zplatform.move(self.y_axis, self.delta)
                        while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                            pass
                        break # выходим из цикла на следующий

            end = time.time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:  # было прерывание по кнопке
                return

            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")#, no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")#, no_tick_labels=True, no_tick_marks=True)

            res = self.prepArray(self.ser_data)
            if res:
                maxLoc = self.draw_map(self.ser_data, 1, True, True)
                self.draw_scale()

            dpg.pop_container_stack()  # pop chart context

        finally:
            context.zplatform.set_speed(self.x_axis, x_speed)
            context.zplatform.set_accel(self.x_axis, x_acc)
            context.zplatform.set_decel(self.x_axis, x_dec)

            if self.after_measure == GO_TO_ZERO: # Переход обратно в центр
                context.zplatform.move_to(self.x_axis, self.zero_pos_x)
                context.zplatform.move_to(self.y_axis, self.zero_pos_y)

            while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                pass

            if context.break_proc: # прерывание по кнопке
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            context.gui_hlp.popup_close()

# стыковка без диалога и графика
    def scan_auto(self,y_count,y_delta,x_scale,device,module,chan,after_measure,scan_x_speed):
        self.y_count = y_count # количество шагов по Y(Z)
        self.delta = y_delta # размер шага по Y(Z)
        self.x_scale = x_scale # длина сканирования по X(Y)
        self.after_measure = after_measure
        x_speed = 0
        x_acc = 0
        x_dec = 0
        res = False
        try:
            self.ser_data = np.zeros(shape=[self.x_scale+1, self.y_count])

            # сохранили изходные позиции
            self.zero_pos_x = context.zplatform.get_pos(self.x_axis)
            self.zero_pos_y = context.zplatform.get_pos(self.y_axis)

            # устанавливаем скорость для сканирования
            res, x_acc = context.zplatform.get_accel(self.x_axis)
            res, x_dec = context.zplatform.get_decel(self.x_axis)
            res, x_speed = context.zplatform.get_speed(self.x_axis)
            context.zplatform.set_accel(self.x_axis, 20000)
            context.zplatform.set_decel(self.x_axis, 20000)
            context.zplatform.set_speed(self.x_axis, 1000) # для перехода в угол области ставим скорость быстрее рабочей

            # Откатились в угол сканируемой области
            # X - Width/2
            context.zplatform.move(self.y_axis, -1 * self.delta * self.y_count / 2)
            # Y - Width/2
            context.zplatform.move(self.x_axis, -1 * self.x_scale / 2)

            while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):
                pass

            self.map_min_x = context.zplatform.get_pos(self.x_axis)
            self.map_min_y = context.zplatform.get_pos(self.y_axis)
            context.zplatform.set_speed(self.x_axis, scan_x_speed)

            if context.break_proc:  # прерывание по кнопке
                return
            # сохранили начальные позиции для сканирования
            self.init_pos_x = context.zplatform.get_pos(self.x_axis)

            # Start scan
            start = time.time()
            x_sign = 1

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()
                x_pos = 0
                # идем в край -->
                context.zplatform.move(self.x_axis, x_sign * self.x_scale)
                y_pos = y  # int(context.zplatform.get_pos(self.y_axis) - init_pos_y)

                while True:
                    pm_values = device.get_power(module)
                    x_pos = int(context.zplatform.get_pos(self.x_axis) - self.init_pos_x)
                    self.ser_data[x_pos][y_pos] = float(pm_values[chan])

                    if (not context.zcontrollers.is_platforms_axis_busy()) or context.break_proc:  # доехалм до конца
                        x_sign *= -1  # разворачиваем напровление по X
                        # шаг вниз
                        context.zplatform.move(self.y_axis, self.delta)
                        while context.zcontrollers.is_platforms_axis_busy() and \
                                (not context.break_proc):  # ждем установки позиции
                            pass
                        break  # выходим из цикла на следующий

            end = time.time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:  # было прерывание по кнопке
                return

            res = self.prepArray(self.ser_data)
            maxLoc = self.draw_map(context.pmap_procedures.ser_data,1,False, True)

            if res and self.after_measure == GO_TO_MAX:  # Переход в позицию с максимальной мощностью излучения
                x = maxLoc[1]
                y = maxLoc[0]*self.delta
                self.set_platform_pos(self.x_axis, self.y_axis, int(x), int(y))
            else:
                context.zplatform.move_to(self.x_axis, self.zero_pos_x)
                context.zplatform.move_to(self.y_axis, self.zero_pos_y)

            while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                pass

        finally:
            context.zplatform.set_speed(self.x_axis, x_speed)
            context.zplatform.set_accel(self.x_axis, x_acc)
            context.zplatform.set_decel(self.x_axis, x_dec)

            context.current_proc = 0
            return res

    def aiming(self, left, chan_num, aim_steps, aim_x_width, aim_y_count, aim_y_step, device, module, meas_chan, scan_x_speed):
        try:
            context.is_meas_in_process = True
            if left:
                self.platform = LEFT_CHAN
                self.y_idx = context.z1_line_i
                self.x_idx = context.y1_line_i
            else: # RIGHT platform
                self.platform = RIGHT_CHAN
                self.y_idx = context.z2_line_i
                self.x_idx = context.y2_line_i

            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.x_axis = int(context.axis[self.x_idx]['idx'])

            context.current_proc = 3
            context.break_proc = False

            steps = 0
            for i in range(aim_steps):
                steps += aim_y_count[i]
            context.gui_hlp.init_progress_bar(steps)

            res = True
            for i in range(aim_steps):
                res = self.exec_measure(aim_y_count[i], aim_y_step[i], aim_x_width[i], device, module, meas_chan, GO_TO_MAX, scan_x_speed[i])

                if context.break_proc:  # прерывание по кнопке
                    context.logger.log(txt.PROCESS_IS_BRAKED)
                    return
                elif res:
                    if left:
                        context.chip_ctrl.left_channels[chan_num].aiming_data[i] = self.ser_data[:]
                    else:  # RIGHT platform
                        context.chip_ctrl.right_channels[chan_num].aiming_data[i] = self.ser_data[:]
                else:
                    context.logger.log('Измерение остановлено')
                    return

            if res:
                # сохраняем данные стыковки
                if left:
                    xl = context.zplatform.get_pos(context.x1_line_i)
                    yl = context.zplatform.get_pos(context.y1_line_i)
                    zl = context.zplatform.get_pos(context.z1_line_i)
                    xa = context.zplatform.get_pos(context.x1_ang_i)
                    ya = context.zplatform.get_pos(context.y1_ang_i)
                    za = context.zplatform.get_pos(context.z1_ang_i)
                    context.chip_ctrl.left_channels[chan_num].make_aimed(xl, yl, zl, xa, ya, za)
                    context.gui_hlp.show_chart_hint(context.chip_ctrl.left_channels[chan_num].aiming_data, aim_steps)
                else: # RIGHT platform
                    xl = context.zplatform.get_pos(context.x2_line_i)
                    yl = context.zplatform.get_pos(context.y2_line_i)
                    zl = context.zplatform.get_pos(context.z2_line_i)
                    xa = context.zplatform.get_pos(context.x2_ang_i)
                    ya = context.zplatform.get_pos(context.y2_ang_i)
                    za = context.zplatform.get_pos(context.z2_ang_i)
                    context.chip_ctrl.right_channels[chan_num].make_aimed(xl, yl, zl, xa, ya, za)
                    context.gui_hlp.show_chart_hint(context.chip_ctrl.right_channels[chan_num].aiming_data, aim_steps)
        finally:
            context.is_meas_in_process = False
            context.gui_hlp.popup_close()

    def process_crosshair(self,cross):
        if not self.is_prepared: # карта еще не создана
            return 99999999
        if self.map_side == LEFT_CHAN:
            x_pos = context.axis[context.y1_line_i]['pos']
            y_pos = context.axis[context.z1_line_i]['pos']
        else:
            x_pos = context.axis[context.y2_line_i]['pos']
            y_pos = context.axis[context.z2_line_i]['pos']

        if x_pos > self.map_min_x and x_pos < self.map_max_x and y_pos > self.map_min_y and y_pos < self.map_max_y and \
                (x_pos != self.x_pos or y_pos != self.y_pos):
            self.x_pos = x_pos
            self.y_pos = y_pos
            if dpg.does_item_exist(cross):
                dpg.delete_item(cross)
            dpg.push_container_stack(context.meas_powermap.meas_chart)
            x = self.x_scale * (x_pos - self.map_min_x) / (self.map_max_x - self.map_min_x) * X_MKM_KOEF
            y = self.y_count * self.delta * (y_pos - self.map_min_y) / (self.map_max_y - self.map_min_y) * Y_MKM_KOEF
            width = self.x_scale * X_MKM_KOEF / 80
            height = self.y_count * self.delta * Y_MKM_KOEF / 80

            cross = dpg.draw_quad((x - width, y - height), (x - width, y + height),
                                       (x + width, y + height), (x + width, y - height),
                                       thickness=0.05, color=(100, 100, 100))
            dpg.pop_container_stack()  # pop chart context

        return cross

    def process_horiz_aiming(self, cross, num): # обработка выбора точек для выравнивания
        if self.is_prepared: # карта уже была создана
            x, y = dpg.get_plot_mouse_pos()
            # к шагам
            x_stp = x / X_MKM_KOEF
            y_stp = y / Y_MKM_KOEF
            if dpg.does_item_exist(cross):
                dpg.delete_item(cross)

            if num == 1:
                dpg.push_container_stack(context.meas_powermap.meas_chart)
                self.horiz1_y = y
            else:
                dpg.push_container_stack(context.meas_powermap.meas_chart2)
                self.horiz2_y = y

            width  = self.x_scale * X_MKM_KOEF / 80
            height = self.y_count * self.delta * Y_MKM_KOEF / 80

            cross  = dpg.draw_quad((x - width, y - height), (x - width, y + height),
                                       (x + width, y + height), (x + width, y - height),
                                       thickness=0.05, color=(100, 100, 100))
            dpg.pop_container_stack()  # pop chart context
            if (self.horiz1_y > 0) and (self.horiz2_y > 0): # выбрали обе точки
                self.horizont_platform_correction()
                self.is_prepared = False
                self.horiz1_y = -1
                self.horiz2_y = -1
            return cross

    def correct_horizont(self): # выровнять платформу по отношению к кристаллу
        x_speed = 0
        x_acc = 0
        x_dec = 0
        self.horiz1_y = -1
        self.horiz2_y = -1

        self.map_side = self.platform
        context.is_meas_in_process = True
        try:
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            context.current_proc = 3
            context.break_proc = False
            self.ser_data  = np.zeros(shape=[self.x_scale + 1, self.y_count])
            self.ser_data2 = np.zeros(shape=[self.x_scale + 1, self.y_count])

            # сохранили изходные позиции
            self.zero_pos_x = context.zplatform.get_pos(self.x_axis)
            self.zero_pos_y = context.zplatform.get_pos(self.y_axis)

            # устанавливаем скорость для сканирования
            res, x_acc = context.zplatform.get_accel(self.x_axis)
            res, x_dec = context.zplatform.get_decel(self.x_axis)
            res, x_speed = context.zplatform.get_speed(self.x_axis)
            spd = 2000
            context.zplatform.set_speed(self.x_axis, spd)
            acc = spd * 10
            context.zplatform.set_accel(self.x_axis, acc)
            dec = spd * 10
            context.zplatform.set_decel(self.x_axis, dec)

            t_spd = 1000000 * self.x_scale / spd  # расчет времени перемещени
            dt_spd = t_spd / self.x_scale - 5  # время между точками синхронизации
            t_acc = spd / acc  # расчет времени ускорения/замедления
            s_acc = t_acc * spd / 2  # путь ускорения/замедления
            s_accdec = s_acc * 2  # путь ускорения + замедления

            # Откатились в угол сканируемой области
            # X - Width/2
            context.zplatform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
            # Y - Width/2
            context.zplatform.move(self.x_axis, (-1 * (self.x_scale / 2 + s_acc)))

            while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:  # прерывание по кнопке
                return

            self.map_min_x = context.zplatform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.zplatform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count * self.delta
            # сохранили начальные позиции для сканирования
            self.init_pos_x = context.zplatform.get_pos(self.x_axis)

            # Start scan
            start = time.time()
            x_sign = 1

            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)

            x_sign = 1
            self.pm_dev.set_work_mode(4, False)
            for i in range(30):
                res = self.pm_dev.get_err()

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()
                x_pos = 0
                # идем в край -->
                self.pm_dev.startConst2(1535, 0.02, self.x_scale)  # запустили измерение
                context.zplatform.move(self.x_axis, x_sign * (self.x_scale + s_accdec))
                time.sleep(0.1)

                context.device_worker.syncroniser_ctrl.make_sync(int(self.x_scale),
                                                                 int(dt_spd));  # запускаем синхронизацию

                time.sleep(self.x_scale*(dt_spd+5)/1000000)


                y_pos = y  # int(context.zplatform.get_pos(self.y_axis) - init_pos_y)

                while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                    pass

                mead_done = '0'
                try:
                    for i in range(10):
                        mead_done, res2 = self.pm_dev.get_meas_state()
                        if mead_done == '1':
                            pm_values1 = self.pm_dev.get_meas_data(self.pm_module, self.pm_chan + 1)
                            pm_values2 = self.pm_dev.get_meas_data(self.pm_module2, self.pm_chan2 + 1)
                            break
                        time.sleep(0.001)
                except Exception as e:
                    context.logger.log_warning(f"Измерение прервано, ошибка: "+e)
                    context.break_proc = True
                    return

                if mead_done!='1':
                    context.logger.log_warning(f"Измерение прервано, нет готовности измерителя")
                    context.break_proc = True
                    return

                for i in range(self.x_scale):
                    if pm_values1[i] < -75: pm_values1[i] = -110
                    if pm_values2[i] < -75: pm_values2[i] = -110

                    if x_sign > 0:
                        self.ser_data[i][y_pos] = float(pm_values1[i])
                        self.ser_data2[i][y_pos] = float(pm_values2[i])
                    else:
                        self.ser_data[self.x_scale - i - 1][y_pos] = float(pm_values1[i])
                        self.ser_data2[self.x_scale - i - 1][y_pos] = float(pm_values2[i])

                x_sign *= -1
                # шаг вниз
                context.zplatform.move(self.y_axis, self.delta)
                while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                    pass

            end = time.time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:  # было прерывание по кнопке
                return

            res = self.prepArray(self.ser_data) and self.prepArray(self.ser_data2)

            # left chart
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")#, no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")
            maxLoc = self.draw_map(context.pmap_procedures.ser_data, 1, True, False)
#            self.draw_scale()
            dpg.pop_container_stack()  # pop chart context

            # right chart
            dpg.delete_item(context.meas_powermap.meas_chart2, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart2)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis2")
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis2")
            maxLoc = self.draw_map(context.pmap_procedures.ser_data2, 2, True, False)
#            self.draw_scale()
            dpg.pop_container_stack()  # pop chart context

        finally:
            self.pm_dev.stop_meas()
            self.pm_dev.set_work_mode(pm2100.PM_MODE_FREERUN, False)

            context.zplatform.set_speed(self.x_axis, x_speed)
            context.zplatform.set_accel(self.x_axis, x_acc)
            context.zplatform.set_decel(self.x_axis, x_dec)

            if self.after_measure == GO_TO_ZERO:  # Переход обратно в центр
                context.zplatform.move_to(self.x_axis, self.zero_pos_x)
                context.zplatform.move_to(self.y_axis, self.zero_pos_y)

            while context.zcontrollers.is_platforms_axis_busy() and (
            not context.break_proc):  # ждем установки позиции
                pass

            self.is_prepared = True

            if context.break_proc:  # прерывание по кнопке
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            context.gui_hlp.popup_close()

    # стыковка(измерение) из диалога с графиком и в синхронном режиме
    def scan_manual_sync(self):
        x_speed = 0
        x_acc = 0
        x_dec = 0
        self.map_side = self.platform
        context.is_meas_in_process = True
        try:
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.zeros(shape=[self.x_scale+1, self.y_count])

    # сохранили изходные позиции
            self.zero_pos_x = context.zplatform.get_pos(self.x_axis)
            self.zero_pos_y = context.zplatform.get_pos(self.y_axis)

    # устанавливаем скорость для сканирования
            res, x_acc = context.zplatform.get_accel(self.x_axis)
            res, x_dec = context.zplatform.get_decel(self.x_axis)
            res, x_speed = context.zplatform.get_speed(self.x_axis)
            spd = 1500
            context.zplatform.set_speed(self.x_axis, spd)
            acc = spd * 10
            context.zplatform.set_accel(self.x_axis, acc)
            dec = spd * 10
            context.zplatform.set_decel(self.x_axis, dec)
            t_spd = 1000000 * self.x_scale / spd  # расчет времени перемещени
            dt_spd = t_spd / self.x_scale - 5  # время между точками синхронизации
            t_acc = spd / acc  # расчет времени ускорения/замедления
            s_acc = t_acc * spd / 2  # путь ускорения/замедления
            s_accdec = s_acc*2  # путь ускорения + замедления

            # Откатились в угол сканируемой области
    # X - Width/2
            context.zplatform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
    # Y - Width/2
            context.zplatform.move(self.x_axis, (-1 * (self.x_scale / 2 + s_acc)))

            while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc: # прерывание по кнопке
                return

            self.map_min_x = context.zplatform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.zplatform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count*self.delta
    # сохранили начальные позиции для сканирования
            self.init_pos_x = context.zplatform.get_pos(self.x_axis)

    # Start scan
            start = time.time()
            x_sign = 1

            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)


            x_sign = 1
            self.pm_dev.set_work_mode(4, False)
            for i in range(30):
                res = self.pm_dev.get_err()

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()
                x_pos = 0
    # идем в край -->
                self.pm_dev.startConst2(1535, 0.02, self.x_scale) # запустили измерение
                context.zplatform.move(self.x_axis, x_sign * (self.x_scale + s_accdec))
                time.sleep(0.1)
                start = time.perf_counter()

                context.device_worker.syncroniser_ctrl.make_sync(int(self.x_scale), int(dt_spd)); # запускаем синхронизацию

                finish = time.perf_counter()
#                print('Wrk time: ' + str(finish - start))

                y_pos = y #int(context.zplatform.get_pos(self.y_axis) - init_pos_y)

                while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                    pass

                try:
                    res1, res2 = self.pm_dev.get_meas_state()
                    if res1 == '1':
                        pm_values = self.pm_dev.get_meas_data(self.pm_module, self.pm_chan+1)
                    else:
                        context.break_proc = True
                        return
                except Exception as e:
                    context.logger.log_warning(f"Измерение прервано, ошибка: "+e)
                    context.break_proc = True
                    return

                for i in range(self.x_scale):
                    if pm_values[i] < -75:
                        pm_values[i] = -110
                    if x_sign>0:
                        self.ser_data[i][y_pos] = float(pm_values[i])
                    else:
                        self.ser_data[self.x_scale-i-1][y_pos] = float(pm_values[i])

                x_sign *= -1
    # шаг вниз
                context.zplatform.move(self.y_axis, self.delta)
                while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                    pass

            end = time.time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:  # было прерывание по кнопке
                return

            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")#, no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")#, no_tick_labels=True, no_tick_marks=True)

            res = self.prepArray(self.ser_data)
#            if res:
            maxLoc = self.draw_map(self.ser_data, 1, True, True)
            self.draw_scale()

            dpg.pop_container_stack()  # pop chart context

        finally:
            self.pm_dev.stop_meas()
            self.pm_dev.set_work_mode(pm2100.PM_MODE_FREERUN, False)

            context.zplatform.set_speed(self.x_axis, x_speed)
            context.zplatform.set_accel(self.x_axis, x_acc)
            context.zplatform.set_decel(self.x_axis, x_dec)

            if self.after_measure == GO_TO_ZERO: # Переход обратно в центр
                context.zplatform.move_to(self.x_axis, self.zero_pos_x)
                context.zplatform.move_to(self.y_axis, self.zero_pos_y)

            while context.zcontrollers.is_platforms_axis_busy() and (not context.break_proc):  # ждем установки позиции
                pass

            if context.break_proc: # прерывание по кнопке
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            context.gui_hlp.popup_close()

    def horizont_platform_correction(self): # расчет угла и доворорот платформы
        hypo = (self.chan_dist+1) * context.chip_chans_dy # гипотенуза - расстояние между измеряемыми каналами, мкм
        cath = self.horiz1_y - self.horiz2_y # катет - разница по Z между каналами
        angle = -math.asin(cath/hypo)*180/math.pi # угол между платформой и кристаллом, градусы
        context.zplatform.move(self.horiz_axis, int(angle*STEP_PER_GRAD_X))
        context.logger.log_com(f"Поворот вокруг оси X на {angle} градусов")


context.pmap_procedures = PMapMeasureProcedures()
