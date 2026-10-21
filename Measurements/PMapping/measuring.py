import traceback
from time import time, sleep, perf_counter

import threading
import Measurements.devices.pm2100 as pm2100
from axis_ctrl import is_platforms_axis_busy
from core.consts import *
from core.gui_helper import *
from core.utils import *
from move_from_camera import get_axis_platforms

context = Context()

GO_TO_ZERO = 1
GO_TO_MAX = 2


class PMapMeasureProcedures:

    def __init__(self):

        self.init_pos_y = None
        self.last_max_y_coord = None
        self.last_max_x_coord = None
        self.last_max_power = None
        self.x_idx = context.y2_line_i
        self.y_idx = context.z2_line_i
        self.y_axis = int(context.axis[self.y_idx]['idx'])
        self.x_axis = int(context.axis[self.x_idx]['idx'])
        self.init_pos_x = None
        self.accT = 0
        self.accS = 0
        self.moveT = 0
        self.moveS = 0
        self.decT = 0
        self.decS = 0

        self.sync_mode = False

        self.max_val = 0
        self.min_val = 0
        self.diap = 0

        self.pm_dev = None
        self.pm_module = -1
        self.pm_module2 = -1
        self.pm_chan = -1
        self.pm_chan2 = -1

        self.y_count = 20
        self.delta = 8 * 0.5
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
        # self.map_side  = 0

        self.map_side = LEFT_CHAN

        self.ser_data = np.zeros(shape=[self.x_scale, self.y_count])
        self.ser_data2 = np.zeros(shape=[self.x_scale, self.y_count])
        self.ser_data_res = [0, 0, 0, 0, 0]

        self.after_measure = GO_TO_ZERO
        self.set_platform(False)
        self.platform = LEFT_CHAN

        self.pitch_idx = context.y1_ang_i
        self.horiz_idx = context.x1_ang_i
        self.set_platform(False)
        self.pitch_axis = int(context.axis[self.pitch_idx]['idx'])
        self.horiz_axis = int(context.axis[self.horiz_idx]['idx'])

        self.horiz1_y = -1
        self.horiz2_y = -1
        self.chan_dist = 0

        self.x_speed = 0
        self.x_acc = 0
        self.x_dec = 0

    @staticmethod
    def save_anchor():

        context.logger.log("Сохранение эталонных координат (Якоря)...")

        idx_l_x = int(context.axis[context.x1_line_i]['idx'])
        idx_l_y = int(context.axis[context.y1_line_i]['idx'])
        idx_l_z = int(context.axis[context.z1_line_i]['idx'])

        idx_r_x = int(context.axis[context.x2_line_i]['idx'])
        idx_r_y = int(context.axis[context.y2_line_i]['idx'])
        idx_r_z = int(context.axis[context.z2_line_i]['idx'])

        context.anchor_l_x = context.z_platform.get_pos(idx_l_x)
        context.anchor_l_y = context.z_platform.get_pos(idx_l_y)
        context.anchor_l_z = context.z_platform.get_pos(idx_l_z)

        context.anchor_r_x = context.z_platform.get_pos(idx_r_x)
        context.anchor_r_y = context.z_platform.get_pos(idx_r_y)
        context.anchor_r_z = context.z_platform.get_pos(idx_r_z)

        context.logger.log("Якорь сохранен.")

    @staticmethod
    def blind_move_right_side():
        if context.anchor_l_x is None:
            context.logger.log("Нету якоря! Сначала Чип №1.")
            return False

        context.logger.log("Расчет подвода правой стороны")

        idx_l_x = int(context.axis[context.x1_line_i]['idx'])
        idx_l_y = int(context.axis[context.y1_line_i]['idx'])

        idx_r_x = int(context.axis[context.x2_line_i]['idx'])
        idx_r_y = int(context.axis[context.y2_line_i]['idx'])
        idx_r_z = int(context.axis[context.z2_line_i]['idx'])

        cur_l_x = context.z_platform.get_pos(idx_l_x)
        cur_l_y = context.z_platform.get_pos(idx_l_y)

        shift_x = cur_l_x - context.anchor_l_x
        shift_y = cur_l_y - context.anchor_l_y

        mirror_coef_x = -1
        mirror_coef_y = 1
        safe_gap = 20

        target_r_x = context.anchor_r_x + (shift_x * mirror_coef_x)

        target_r_x -= safe_gap

        target_r_y = context.anchor_r_y + (shift_y * mirror_coef_y)
        target_r_z = context.anchor_r_z

        context.logger.log(f"Сдвиг относительно Якоря -> X: {shift_x:.2f}, Y: {shift_y:.2f}")

        context.z_platform.move_to(idx_r_x, target_r_x)
        context.z_platform.move_to(idx_r_y, target_r_y)
        context.z_platform.move_to(idx_r_z, target_r_z)

        sleep(0.1)
        while context.z_platform.is_in_motion(idx_r_x) == 0 or \
                context.z_platform.is_in_motion(idx_r_y) == 0 or \
                context.z_platform.is_in_motion(idx_r_z) == 0:

            if context.break_proc:
                context.logger.log("Слепой подвод прерван.")
                return False

        context.logger.log("Подвод завершен.")
        return True

    def set_platform(self, right):
        if not right:
            self.x_idx = context.y1_line_i
            self.y_idx = context.z1_line_i
            self.x_axis = int(context.axis[self.x_idx]['idx'])
            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.pitch_idx = context.y1_ang_i
            self.horiz_idx = context.x1_ang_i
            self.pitch_axis = int(context.axis[self.pitch_idx]['idx'])
            self.horiz_axis = int(context.axis[self.horiz_idx]['idx'])
        else:
            self.x_idx = context.y2_line_i
            self.y_idx = context.z2_line_i
            self.x_axis = int(context.axis[self.x_idx]['idx'])
            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.pitch_idx = context.y2_ang_i
            self.horiz_idx = context.x2_ang_i
            self.pitch_axis = int(context.axis[self.pitch_idx]['idx'])
            self.horiz_axis = int(context.axis[self.horiz_idx]['idx'])

    def save(self, acc, dec, speed):
        res, self.x_acc = context.z_platform.get_accel(self.x_axis)
        res, self.x_dec = context.z_platform.get_decel(self.x_axis)
        res, self.x_speed = context.z_platform.get_speed(self.x_axis)
        context.z_platform.set_accel(self.x_axis, acc)
        context.z_platform.set_decel(self.x_axis, dec)
        context.z_platform.set_speed(self.x_axis, speed)

    def restore(self):
        context.z_platform.set_speed(self.x_axis, self.x_speed)
        context.z_platform.set_accel(self.x_axis, self.x_acc)
        context.z_platform.set_decel(self.x_axis, self.x_dec)

    def draw_scale(self):
        leg_count = 15
        sideX = 1
        sideY = self.delta * self.y_count / leg_count
        for y in range(0, leg_count):
            legend_width = self.x_scale / 4
            # red = (int(self.min_val+y*self.diap/self.z_count) >> 32) & 0xFF
            red = int(y / leg_count * 0xFF)
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
            value = "{:5.2f}".format(self.min_val + y * self.diap / leg_count)
            dpg.draw_text(pos=(x0, y1), text=value, color=(200, 200, 200), size=self.x_scale * X_MKM_KOEF / 20)

    def prepArray(self, arr):

        self.max_val = -100000
        self.min_val = 100000
        x_cnt = arr.shape[0]
        y_cnt = arr.shape[1]

        for x in range(0, x_cnt):
            for y in range(0, y_cnt):
                if arr[x][y] != 0:
                    if arr[x][y] < self.min_val:
                        self.min_val = arr[x][y]
                    if arr[x][y] > self.max_val:
                        self.max_val = arr[x][y]

        self.diap = self.max_val - self.min_val

        if self.diap == 0:
            context.logger.log("Не обнаружено различающихся значений")
            return False

        for x in range(0, self.x_scale):
            for y in range(0, self.y_count):
                if arr[x][y] == 0:
                    arr[x][y] = self.min_val
                color = int(0xFF * (arr[x][y] - self.min_val) / self.diap)
                arr[x][y] = color
        arr[:] = arr
        return True

    def draw_map(self, arr, num, draw, scale_place):
        sideX = 1
        sideY = self.delta
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

        if draw:
            dpg.draw_circle(center=(maxLoc[1] * X_MKM_KOEF, maxLoc[0] * sideY * Y_MKM_KOEF),
                            radius=self.x_scale * X_MKM_KOEF / 50, thickness=0.05, color=(255, 255, 255))
            dpg.set_axis_limits(f"pm_y_axis{num}", 0, self.y_count * self.delta * Y_MKM_KOEF)
            if scale_place:
                dpg.set_axis_limits(f"pm_x_axis{num}", 0, (self.x_scale + self.x_scale / 4) * X_MKM_KOEF)
            else:
                dpg.set_axis_limits(f"pm_x_axis{num}", 0, self.x_scale * X_MKM_KOEF)
        return maxLoc

    def scan_manual(self):
        self.map_side = self.platform
        context.is_meas_in_process = True
        res = False
        maxLoc = (0, 0)
        try:
            # dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            context.current_proc = 3
            context.break_proc = False
            # self.ser_data = np.zeros(shape=[self.x_scale + 1, self.y_count])
            self.ser_data = np.ones(shape=[self.x_scale + 1, self.y_count]) * (-75)
            self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)
            # self.save(25000, 25000, 100)
            self.save(25000, 25000, 100)
            # X - Width/2
            context.z_platform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
            # Y - Width/2
            context.z_platform.move(self.x_axis, (-1 * self.x_scale / 2) + 1)
            while is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:
                return
            self.map_min_x = context.z_platform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count * self.delta
            self.init_pos_x = context.z_platform.get_pos(self.x_axis)
            # Start scan
            start = time()
            x_sign = 1
            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)
            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()  # Шаг progress_bar
                context.z_platform.move(self.x_axis, x_sign * self.x_scale)
                y_pos = y  # int(context.z_platform.get_pos(self.y_axis) - init_pos_y)
                while True:
                    pm_values = self.pm_dev.get_power(self.pm_module)
                    x_pos = int(context.z_platform.get_pos(self.x_axis) - self.init_pos_x)
                    self.ser_data[x_pos][y_pos] = float(pm_values[self.pm_chan])
                    if (not is_platforms_axis_busy()) or context.break_proc:
                        x_sign *= -1
                        context.z_platform.move(self.y_axis, self.delta)
                        while is_platforms_axis_busy() and (
                                not context.break_proc):
                            pass
                        break
            end = time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")
            if context.break_proc:
                return
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")  # , no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")  # , no_tick_labels=True, no_tick_marks=True)
            res = self.prepArray(self.ser_data)
            if res:
                (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(self.ser_data)
                self.draw_map(self.ser_data, 1, True, True)
                self.draw_scale()

            dpg.pop_container_stack()  # pop chart context
        except Exception as e:
            print(e)
        finally:
            self.restore()  # Возвращаем начальные параметры приборов (скорости моторов)

            if res and self.after_measure == GO_TO_MAX:
                target_x = self.map_min_x + maxLoc[1]
                target_y = self.map_min_y + (maxLoc[0] * self.delta)

                context.z_platform.move_to(self.x_axis, int(target_x))
                context.z_platform.move_to(self.y_axis, int(target_y))
            else:
                context.z_platform.move_to(self.x_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            if context.break_proc:
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            popup_close()

    def scan_auto(self):
        self.after_measure = GO_TO_MAX
        device = self.pm_dev
        module = self.pm_module
        chan = self.pm_chan
        res = False
        try:
            self.ser_data = np.zeros(shape=[self.x_scale + 1, self.y_count])

            self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)
            self.save(20000, 20000, 1000)

            # X - Width/2
            context.z_platform.move(self.y_axis, -1 * self.delta * self.y_count / 2)
            # Y - Width/2
            context.z_platform.move(self.x_axis, -1 * self.x_scale / 2)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            self.map_min_x = context.z_platform.get_pos(self.x_axis)
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            context.z_platform.set_speed(self.x_axis, 1000)

            if context.break_proc:
                return

            self.init_pos_x = context.z_platform.get_pos(self.x_axis)

            # Start scan
            start = time()
            x_sign = 1

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()

                context.z_platform.move(self.x_axis, x_sign * self.x_scale)
                y_pos = y  # int(context.z_platform.get_pos(self.y_axis) - init_pos_y)

                while True:
                    pm_values = device.get_power(module)
                    x_pos = int(context.z_platform.get_pos(self.x_axis) - self.init_pos_x)
                    self.ser_data[x_pos][y_pos] = float(pm_values[chan])

                    if (not is_platforms_axis_busy()) or context.break_proc:
                        x_sign *= -1

                        context.z_platform.move(self.y_axis, self.delta)
                        while is_platforms_axis_busy() and \
                                (not context.break_proc):
                            pass
                        break

            end = time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:
                return

            res = self.prepArray(self.ser_data)
            maxLoc = self.draw_map(context.pmap_procedures.ser_data, 1, False, True)

            if res and self.after_measure == GO_TO_MAX:
                x = maxLoc[1]
                y = maxLoc[0] * self.delta
                context.z_platform.set_platform_pos(self.x_axis, self.y_axis, int(x), int(y))
            else:
                context.z_platform.move_to(self.x_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass
        except Exception as e:
            print("354")
            print(e)
        finally:
            self.restore()

            context.current_proc = 0
            return res

    def aiming(self, left, chan_num, aim_steps, aim_x_width, aim_y_count, aim_y_step, device, module, meas_chan,
               scan_x_speed):
        try:
            context.is_meas_in_process = True
            self.set_platform(not left)

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
                res = context.spectrum_gui.exec_measure(aim_y_count[i], aim_y_step[i], aim_x_width[i], device, module,
                                                        meas_chan, GO_TO_MAX, scan_x_speed[i])

                if context.break_proc:
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

                if left:
                    xl = context.z_platform.get_pos(context.x1_line_i)
                    yl = context.z_platform.get_pos(context.y1_line_i)
                    zl = context.z_platform.get_pos(context.z1_line_i)
                    xa = context.z_platform.get_pos(context.x1_ang_i)
                    ya = context.z_platform.get_pos(context.y1_ang_i)
                    za = context.z_platform.get_pos(context.z1_ang_i)
                    context.chip_ctrl.left_channels[chan_num].make_aimed(xl, yl, zl, xa, ya, za)
                    context.gui_hlp.show_chart_hint(context.chip_ctrl.left_channels[chan_num].aiming_data, aim_steps)
                else:  # RIGHT platform
                    xl = context.z_platform.get_pos(context.x2_line_i)
                    yl = context.z_platform.get_pos(context.y2_line_i)
                    zl = context.z_platform.get_pos(context.z2_line_i)
                    xa = context.z_platform.get_pos(context.x2_ang_i)
                    ya = context.z_platform.get_pos(context.y2_ang_i)
                    za = context.z_platform.get_pos(context.z2_ang_i)
                    context.chip_ctrl.right_channels[chan_num].make_aimed(xl, yl, zl, xa, ya, za)
                    context.gui_hlp.show_chart_hint(context.chip_ctrl.right_channels[chan_num].aiming_data, aim_steps)
        except Exception as e:
            print(e)
        finally:
            context.is_meas_in_process = False
            popup_close()

    def process_crosshair(self, cross):
        if not self.is_prepared:
            return 99999999
        if self.map_side == LEFT_CHAN:
            x_pos = context.axis[context.y1_line_i]['pos']
            y_pos = context.axis[context.z1_line_i]['pos']
        else:
            x_pos = context.axis[context.y2_line_i]['pos']
            y_pos = context.axis[context.z2_line_i]['pos']

        if self.map_min_x < x_pos < self.map_max_x and self.map_min_y < y_pos < self.map_max_y and \
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

    def process_horiz_aiming(self, cross, num):
        if self.is_prepared:
            x, y = dpg.get_plot_mouse_pos()

            if dpg.does_item_exist(cross):
                dpg.delete_item(cross)

            if num == 1:
                dpg.push_container_stack(context.meas_powermap.meas_chart)
                self.horiz1_y = y
            else:
                dpg.push_container_stack(context.meas_powermap.meas_chart2)
                self.horiz2_y = y

            width = self.x_scale * X_MKM_KOEF / 80
            height = self.y_count * self.delta * Y_MKM_KOEF / 80

            cross = dpg.draw_quad((x - width, y - height), (x - width, y + height),
                                  (x + width, y + height), (x + width, y - height),
                                  thickness=0.05, color=(100, 100, 100))
            dpg.pop_container_stack()  # pop chart context
            if (self.horiz1_y > 0) and (self.horiz2_y > 0):
                self.horizont_platform_correction()
                self.is_prepared = False
                self.horiz1_y = -1
                self.horiz2_y = -1
            return cross

    def correct_horizont_sync(self):
        self.horiz1_y = -1
        self.horiz2_y = -1

        self.map_side = self.platform
        context.is_meas_in_process = True
        try:
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.zeros(shape=[self.x_scale + 1, self.y_count])
            self.ser_data2 = np.zeros(shape=[self.x_scale + 1, self.y_count])

            # сохранили иcходные позиции
            self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)

            # устанавливаем скорость для сканирования

            spd = 2000
            acc = spd * 10
            dec = spd * 10
            self.save(acc, dec, spd)

            t_spd = 1000000 * self.x_scale / spd  # расчет времени перемещени
            dt_spd = t_spd / self.x_scale - 5  # время между точками синхронизации
            t_acc = spd / acc  # расчет времени ускорения/замедления
            s_acc = t_acc * spd / 2  # путь ускорения/замедления
            s_accdec = s_acc * 2  # путь ускорения + замедления

            # Откатились в угол сканируемой области
            # X - Width/2
            context.z_platform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
            # Y - Width/2
            context.z_platform.move(self.x_axis, (-1 * (self.x_scale / 2 + s_acc)))

            while is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:  # прерывание по кнопке
                return

            self.map_min_x = context.z_platform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count * self.delta
            # сохранили начальные позиции для сканирования
            self.init_pos_x = context.z_platform.get_pos(self.x_axis)

            # Start scan
            start = time()

            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)

            x_sign = 1
            self.pm_dev.set_work_mode(4, False)
            for i in range(30):
                err = self.pm_dev.get_err()
                # print(err)

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()
                # идем в край -->
                self.pm_dev.startConst2(1535, 0.02, self.x_scale)  # запустили измерение
                context.z_platform.move(self.x_axis, x_sign * (self.x_scale + s_accdec))
                sleep(0.1)

                context.device_worker.sync_ctrl.make_sync(int(self.x_scale),
                                                          int(dt_spd))  # запускаем синхронизацию

                sleep(self.x_scale * (dt_spd + 5) / 1000000)

                y_pos = y  # int(context.z_platform.get_pos(self.y_axis) - init_pos_y)

                while is_platforms_axis_busy() and (
                        not context.break_proc):  # ждем установки позиции
                    pass

                meas_done = '0'
                pm_values1 = []
                pm_values2 = []
                try:
                    for i in range(10):
                        meas_done, res2 = self.pm_dev.get_meas_state()
                        if meas_done == '1':
                            pm_values1 = self.pm_dev.get_meas_data(self.pm_module, self.pm_chan + 1)
                            pm_values2 = self.pm_dev.get_meas_data(self.pm_module2, self.pm_chan2 + 1)
                            break
                        sleep(0.001)
                except Exception as e:
                    context.logger.log_warning(f"Измерение прервано, ошибка: {e}")
                    context.break_proc = True
                    return

                if meas_done != '1':
                    context.logger.log_warning(f"Измерение прервано, нет готовности измерителя")
                    context.break_proc = True
                    return

                for i in range(self.x_scale):
                    # if pm_values1[i] < -75:
                    #     pm_values1[i] = -110
                    # if pm_values2[i] < -75:
                    #     pm_values2[i] = -110

                    if x_sign > 0:
                        self.ser_data[i][y_pos] = float(pm_values1[i])
                        self.ser_data2[i][y_pos] = float(pm_values2[i])
                    else:
                        self.ser_data[self.x_scale - i - 1][y_pos] = float(pm_values1[i])
                        self.ser_data2[self.x_scale - i - 1][y_pos] = float(pm_values2[i])

                x_sign *= -1
                # шаг вниз
                context.z_platform.move(self.y_axis, self.delta)
                while is_platforms_axis_busy() and (
                        not context.break_proc):  # ждем установки позиции
                    pass

            end = time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:  # было прерывание по кнопке
                return

            self.prepArray(self.ser_data) and self.prepArray(self.ser_data2)

            # left chart
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")  # , no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")
            self.draw_map(context.pmap_procedures.ser_data, 1, True, False)
            #            self.draw_scale()
            dpg.pop_container_stack()  # pop chart context

            # right chart
            dpg.delete_item(context.meas_powermap.meas_chart2, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart2)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis2")
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis2")
            self.draw_map(context.pmap_procedures.ser_data2, 2, True, False)
            #            self.draw_scale()
            dpg.pop_container_stack()  # pop chart context

        finally:
            self.pm_dev.stop_meas()
            self.pm_dev.set_work_mode(pm2100.PM_MODE_FREERUN, False)

            self.restore()

            if self.after_measure == GO_TO_ZERO:  # Переход обратно в центр
                context.z_platform.move_to(self.x_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (
                    not context.break_proc):  # ждем установки позиции
                pass

            self.is_prepared = True

            if context.break_proc:  # прерывание по кнопке
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            popup_close()

    # Эта функция корректирует крен без синхронизатора, ну, по крайней мере должна
    def correct_horizont_manual(self):
        self.horiz1_y = -1
        self.horiz2_y = -1
        self.map_side = self.platform
        context.is_meas_in_process = True
        try:
            # Очищаем оба графика
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            dpg.delete_item(context.meas_powermap.meas_chart2, children_only=True)

            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.zeros(shape=[self.x_scale + 1, self.y_count])
            self.ser_data2 = np.zeros(shape=[self.x_scale + 1, self.y_count])

            # Сохраняем исходные позиции
            self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)

            # Получаем текущие настройки и устанавливаем медленные для ручного опроса
            self.save(25000, 25000, 100)  # Медленная скорость для успевания опроса USB

            # Откатываемся в стартовый угол сканируемой области
            context.z_platform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
            context.z_platform.move(self.x_axis, (-1 * self.x_scale / 2) + 1)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:
                return

            self.map_min_x = context.z_platform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count * self.delta

            self.init_pos_x = context.z_platform.get_pos(self.x_axis)

            start = perf_counter()
            x_sign = 1

            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)

            # Основной цикл сканирования
            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()

                # Даем команду мотору ехать до конца строки
                context.z_platform.move(self.x_axis, x_sign * self.x_scale)
                y_pos = y

                # Цикл ручного (программного) опроса измерителя
                while True:
                    # Опрашиваем ОБА модуля (канала) измерителя
                    pm_values1 = self.pm_dev.get_power(self.pm_module)
                    pm_values2 = self.pm_dev.get_power(self.pm_module2)

                    # Читаем текущую координату и вычисляем индекс массива
                    x_pos = int(context.z_platform.get_pos(self.x_axis) - self.init_pos_x)

                    # Защита от выхода за границы массива при инерции мотора
                    if 0 <= x_pos <= self.x_scale:
                        self.ser_data[x_pos][y_pos] = float(pm_values1[self.pm_chan])
                        self.ser_data2[x_pos][y_pos] = float(pm_values2[self.pm_chan2])

                    # Если мотор доехал ИЛИ нажата кнопка стоп
                    if (not is_platforms_axis_busy()) or context.break_proc:
                        x_sign *= -1  # Меняем направление для следующей строки (змейка)
                        context.z_platform.move(self.y_axis, self.delta)  # Шаг по Y

                        while is_platforms_axis_busy() and (not context.break_proc):
                            pass
                        break

            end = perf_counter()
            context.logger.log(f"Время выравнивания крена: {round(end-start, 3)} с")

            if context.break_proc:
                return

            self.prepArray(self.ser_data) and self.prepArray(self.ser_data2)

            # Отрисовка левого графика
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")
            self.draw_map(self.ser_data, 1, True, False)
            dpg.pop_container_stack()

            # Отрисовка правого графика
            dpg.delete_item(context.meas_powermap.meas_chart2, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart2)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis2")
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis2")
            self.draw_map(self.ser_data2, 2, True, False)
            dpg.pop_container_stack()

            idx_max1 = np.unravel_index(np.argmax(self.ser_data), self.ser_data.shape)
            idx_max2 = np.unravel_index(np.argmax(self.ser_data2), self.ser_data2.shape)

            y_pixel_1 = idx_max1[1]
            y_pixel_2 = idx_max2[1]

            self.horiz1_y = self.map_min_y + (y_pixel_1 * self.delta)
            self.horiz2_y = self.map_min_y + (y_pixel_2 * self.delta)

            context.logger.log(
                f"Автовыравнивание: Пик 1 на высоте Z={self.horiz1_y}, Пик 2 на высоте Z={self.horiz2_y}")

            self.horizont_platform_correction()

        except Exception as e:
            print(f"Ошибка в correct_horizont_manual: {e}")
        finally:
            # Возвращаем исходные скорости
            self.restore()

            # Возвращаемся в ноль по завершению
            if self.after_measure == GO_TO_ZERO:
                context.z_platform.move_to(self.x_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            self.is_prepared = True

            if context.break_proc:
                context.logger.log(txt.PROCESS_IS_BRAKED)

            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            popup_close()

    def correct_horizont_linear(self):
        # Просто задаём параметры для действий
        context.pmap_procedures.set_platform(True)
        context.is_meas_in_process = True
        context.break_proc = False

        # Задаем параметры одномерного сканирования по вертикали, но всё это нужно правильно перевести в микроны
        scan_range = 100.0  # Общий ход в микронах (вверх-вниз)
        step_y = 0.5  # Шаг сканирования
        steps_count = int(scan_range / step_y)

        steps_real = STEP_PER[self.y_axis]
        # Списки для записи профиля интенсивности
        power_profile1 = []
        power_profile2 = []
        y_coords = []

        try:
            # 1. Запоминаем исходную точку (мы уже стоим в максимуме 1-го канала по X и Y)
            start_y = context.z_platform.get_pos(self.y_axis)

            # 2. Опускаемся на половину диапазона сканирования вниз, чтобы начать снизу вверх
            perevod_polovin = int((-scan_range / 2) * steps_real)
            context.z_platform.move(self.y_axis, perevod_polovin)
            while is_platforms_axis_busy(): pass

            # 3. Линейный подъем вверх с одновременным чтением двух каналов
            for _ in range(steps_count):
                if context.break_proc:
                    break

                perevod_po_y = int(step_y * steps_real)
                context.z_platform.move(self.y_axis, perevod_po_y)
                while is_platforms_axis_busy(): pass

                # Запоминаем текущую физическую высоту
                current_y = context.z_platform.get_pos(self.y_axis)
                current_y_real = current_y / steps_real
                y_coords.append(current_y_real)

                # Опрашиваем ОБА канала измерителя одновременно
                pm_values1 = self.pm_dev.get_power(self.pm_module)
                pm_values2 = self.pm_dev.get_power(self.pm_module2)

                power_profile1.append(float(pm_values1[self.pm_chan]))
                power_profile2.append(float(pm_values2[self.pm_chan2]))

            if context.break_proc:
                return

            # 4. Математический поиск максимумов в полученных профилях
            max_idx1 = np.argmax(power_profile1)
            max_idx2 = np.argmax(power_profile2)

            # Получаем точные координаты высоты (Z) для обоих максимумов
            self.horiz1_y = y_coords[max_idx1]
            self.horiz2_y = y_coords[max_idx2]

            context.logger.log(f"Линейный поиск завершен. Пик 1 на Y={self.horiz1_y}, Пик 2 на Y={self.horiz2_y}")

            # 5. Возвращаем платформу в исходную центральную точку по высоте
            context.z_platform.move_to(self.y_axis, start_y)
            while is_platforms_axis_busy(): pass

            # 6. Вызываем функцию поворота платформы
            self.horizont_platform_correction()

        except Exception as e:
            print(f"Ошибка в коде быстрого горизонта: {e}")
        finally:
            context.is_meas_in_process = False

    def correct_pitch(self):
        x_speed = 0
        x_acc = 0
        x_dec = 0
        self.map_side = self.platform
        context.is_meas_in_process = True
        try:
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.zeros(shape=[self.x_scale + 1, self.y_count])

            self.zero_pos_x = context.z_platform.get_pos(self.pitch_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)

            res, x_acc = context.z_platform.get_accel(self.pitch_axis)
            res, x_dec = context.z_platform.get_decel(self.pitch_axis)
            res, x_speed = context.z_platform.get_speed(self.pitch_axis)
            context.z_platform.set_accel(self.pitch_axis, 25000)
            context.z_platform.set_decel(self.pitch_axis, 25000)
            context.z_platform.set_speed(self.pitch_axis, 100)

            # X - Width/2
            context.z_platform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
            # Y - Width/2
            context.z_platform.move(self.pitch_axis, (-1 * self.x_scale / 2) + 1)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:
                return

            self.map_min_x = context.z_platform.get_pos(self.pitch_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count * self.delta

            self.init_pos_x = context.z_platform.get_pos(self.pitch_axis)

            # Start scan
            start = time()
            x_sign = 1

            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()

                context.z_platform.move(self.pitch_axis, x_sign * self.x_scale)
                y_pos = y  # int(context.z_platform.get_pos(self.y_axis) - init_pos_y)

                while True:
                    pm_values = self.pm_dev.get_power(self.pm_module)
                    x_pos = int(context.z_platform.get_pos(self.pitch_axis) - self.init_pos_x)
                    self.ser_data[x_pos][y_pos] = float(pm_values[self.pm_chan])

                    if (not is_platforms_axis_busy()) or context.break_proc:
                        x_sign *= -1

                        context.z_platform.move(self.y_axis, self.delta)
                        while is_platforms_axis_busy() and (
                                not context.break_proc):
                            pass
                        break

            end = time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:
                return

            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="градусы",
                              tag="pm_x_axis1")  # , no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")  # , no_tick_labels=True, no_tick_marks=True)

            res = self.prepArray(self.ser_data)
            if res:
                self.draw_map(self.ser_data, 1, True, True)
                self.draw_scale()

            dpg.pop_container_stack()  # pop chart context
        except Exception as e:
            print(e)
        finally:
            context.z_platform.set_speed(self.pitch_axis, x_speed)
            context.z_platform.set_accel(self.pitch_axis, x_acc)
            context.z_platform.set_decel(self.pitch_axis, x_dec)

            if self.after_measure == GO_TO_ZERO:
                context.z_platform.move_to(self.pitch_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            if context.break_proc:
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            popup_close()

    def scan_manual_sync(self):
        self.map_side = self.platform
        context.is_meas_in_process = True
        res = False
        maxLoc = (0, 0)
        try:
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.zeros(shape=[self.x_scale + 1, self.y_count])

            self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)

            spd = 1500
            acc = spd * 10
            dec = spd * 10
            self.save(acc, dec, spd)
            t_spd = 1000000 * self.x_scale / spd
            dt_spd = t_spd / self.x_scale - 5
            t_acc = spd / acc
            s_acc = t_acc * spd / 2
            s_acc_dec = s_acc * 2

            # X - Width/2
            context.z_platform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
            # Y - Width/2
            context.z_platform.move(self.x_axis, (-1 * (self.x_scale / 2 + s_acc)))

            while is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:
                return

            self.map_min_x = context.z_platform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count * self.delta

            self.init_pos_x = context.z_platform.get_pos(self.x_axis)

            start = time()

            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)

            x_sign = 1
            self.pm_dev.set_work_mode(4, False)
            for i in range(30):
                err = self.pm_dev.get_err()
                print(err)

            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()

                self.pm_dev.startConst2(1535, 0.02, self.x_scale)
                context.z_platform.move(self.x_axis, x_sign * (self.x_scale + s_acc_dec))
                sleep(0.1)
                start = perf_counter()

                context.device_worker.sync_ctrl.make_sync(int(self.x_scale),
                                                          int(dt_spd))

                # finish = perf_counter()
                #                print('Wrk time: ' + str(finish - start))
                y_pos = y
                while is_platforms_axis_busy() and not context.break_proc:
                    pass
                try:
                    res1, res2 = self.pm_dev.get_meas_state()
                    if res1 == '1':
                        pm_values = self.pm_dev.get_meas_data(self.pm_module, self.pm_chan + 1)
                    else:
                        context.break_proc = True
                        return
                except Exception as e:
                    context.logger.log_warning(f"Измерение прервано, ошибка: {e}")
                    context.break_proc = True
                    return

                for i in range(self.x_scale):
                    if pm_values[i] < -75:
                        pm_values[i] = -110
                    if x_sign > 0:
                        self.ser_data[i][y_pos] = float(pm_values[i])
                    else:
                        self.ser_data[self.x_scale - i - 1][y_pos] = float(pm_values[i])

                x_sign *= -1

                context.z_platform.move(self.y_axis, self.delta)
                while is_platforms_axis_busy() and (
                        not context.break_proc):
                    pass

            end = time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:
                return

            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)

            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")

            res = self.prepArray(self.ser_data)
            maxLoc = (0, 0)
            if res:
                maxLoc = self.draw_map(self.ser_data, 1, True, True)
                self.draw_scale()

            dpg.pop_container_stack()
        except Exception as e:
            print(e)
        finally:
            self.pm_dev.stop_meas()
            self.pm_dev.set_work_mode(pm2100.PM_MODE_FREERUN, False)

            self.restore()

            # Поменял условие, чтобы возвращалось в точку максимума
            if res and self.after_measure == GO_TO_MAX:
                target_x = self.map_min_x + maxLoc[1]
                target_y = self.map_min_y + (maxLoc[0] * self.delta)

                context.z_platform.move_to(self.x_axis, int(target_x))
                context.z_platform.move_to(self.y_axis, int(target_y))
            elif self.after_measure == GO_TO_ZERO:
                context.z_platform.move_to(self.x_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            if context.break_proc:
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            popup_close()

    def horizont_platform_correction(self):
        hypo = self.chan_dist * context.chip_chans_dy
        cath = self.horiz1_y - self.horiz2_y
        angle = -math.atan(cath / hypo) * 180 / math.pi  # Тут был минус !!!
        context.z_platform.move(self.horiz_axis, int(angle * STEP_PER_GRAD_X))
        context.logger.log_com(f"Поворот вокруг оси X на {angle} градусов")

    # Новая функция, она будет юстировать и вход и выход, пока не достигнет прописанного значения (по идее)

    def adjustment_l_and_r(self, target_power=-30.0, max_iterations=5, tolerance=0.01):
        confirm_msg("ВКЛЮЧИТЕ ШИРИК", self.start_adjustment_l_and_r_thread, [target_power, max_iterations, tolerance])

    def start_adjustment_l_and_r_thread(self, target_power, max_iterations, tolerance):
        threading.Thread(
            target=self.adjustment_l_and_r_logic,
            args=(target_power, max_iterations, tolerance),
            daemon=True).start()

    def adjustment_l_and_r_logic(self, target_power, max_iterations, tolerance):
        context.logger.log("--- Запуск автоматической юстировки (право - лево)---")

        self.after_measure = GO_TO_MAX
        last_power = -1000.0  # Стартовое значение для сравнения

        for i in range(max_iterations):
            context.logger.log(f"--- Итерация  {i + 1} из {max_iterations} ---")

            # левая сторона
            context.logger.log("Сканирование левого волокна...")
            self.platform = LEFT_CHAN
            self.y_idx = context.z1_line_i
            self.x_idx = context.y1_line_i
            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.x_axis = int(context.axis[self.x_idx]['idx'])

            self.scan_manual()
            if context.break_proc:  # "Отмена"
                return

            # правая сторона
            context.logger.log("Сканирование правого волокна...")
            self.platform = RIGHT_CHAN
            self.y_idx = context.z2_line_i
            self.x_idx = context.y2_line_i
            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.x_axis = int(context.axis[self.x_idx]['idx'])

            self.scan_manual()
            if context.break_proc:
                return

            # === ШАГ 3: ПРОВЕРКА УСЛОВИЙ ОСТАНОВКИ ===
            # Считываем текущую мощность напрямую с измерителя
            pm_values = self.pm_dev.get_power(self.pm_module)
            current_power = float(pm_values[self.pm_chan])

            context.logger.log(f"Текущая оптическая мощность: {current_power:.2f} дБм")

            # Условие 1: Всё супер, нашли максимум
            if current_power >= target_power:
                context.logger.log(f"Достигнуты нужные потери ({target_power} дБм)")
                break

            # Условие 2: Проверяем прирост
            if i > 0 and (current_power - last_power) <= tolerance:
                context.logger.log(f"Мощность больше не растет (прирост менее {tolerance} дБм). Предел достигнут.")
                break

            last_power = current_power

        context.logger.log("Автоматическая юстировка успешно завершена.")
        context.is_meas_in_process = False

        context.B_r = get_axis_platforms(True)
        context.B_l = get_axis_platforms(False)
        print(context.B_r)
        print(context.B_l)

        context.delta_y_r = context.B_r[1] - context.pos_Focus_r[1]
        context.delta_z_r = context.B_r[2] - context.pos_Focus_r[2]

        context.delta_y_l = context.B_l[1] - context.pos_Focus_l[1]
        context.delta_z_l = context.B_l[2] - context.pos_Focus_l[2]

    def scan_manual_2(self):
        self.map_side = self.platform
        context.is_meas_in_process = True
        res = False
        maxLoc = (0, 0)
        try:
            # dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.ones(shape=[self.x_scale + 1, self.y_count]) * (-70)
            self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)
            # self.save(25000, 25000, 100)
            # self.save(25000, 25000, 60)
            self.save(20000, 20000, 1000)
            # X - Width/2
            context.z_platform.move(self.y_axis, (-1 * self.delta * self.y_count / 2))
            # Y - Width/2
            context.z_platform.move(self.x_axis, (-1 * self.x_scale / 2) + 1)
            while is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:
                return
            self.map_min_x = context.z_platform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count * self.delta
            self.init_pos_x = context.z_platform.get_pos(self.x_axis)
            # Start scan
            start = time()
            x_sign = 1
            steps = self.y_count
            context.gui_hlp.init_progress_bar(steps)
            for y in range(0, self.y_count):
                context.gui_hlp.progress_bar_step()  # Шаг progress_bar
                context.z_platform.move(self.x_axis, x_sign * self.x_scale)
                y_pos = y  # int(context.z_platform.get_pos(self.y_axis) - init_pos_y)
                while True:
                    pm_values = self.pm_dev.get_power(self.pm_module)
                    x_pos = int(context.z_platform.get_pos(self.x_axis) - self.init_pos_x)
                    self.ser_data[x_pos][y_pos] = float(pm_values[self.pm_chan])
                    if (not is_platforms_axis_busy()) or context.break_proc:
                        x_sign *= -1
                        context.z_platform.move(self.y_axis, self.delta)
                        while is_platforms_axis_busy() and (
                                not context.break_proc):
                            pass
                        break
            end = time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")
            if context.break_proc:
                return
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")  # , no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")  # , no_tick_labels=True, no_tick_marks=True)
            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(self.ser_data)

            self.last_max_power = maxVal
            self.last_max_x_coord = self.map_min_x + maxLoc[1]
            self.last_max_y_coord = self.map_min_y + (maxLoc[0] * self.delta)
            res = self.prepArray(self.ser_data)
            if res:
                self.draw_map(self.ser_data, 1, True, True)
                self.draw_scale()
            dpg.pop_container_stack()  # pop chart context
        except Exception as e:
            print(e)
        finally:
            self.restore()  # Возвращаем начальные параметры приборов (скорости моторов)

            if res and self.after_measure == GO_TO_MAX:  # and max_power > -29
                target_x = self.map_min_x + maxLoc[1]
                target_y = self.map_min_y + (maxLoc[0] * self.delta)

                context.z_platform.move_to(self.x_axis, int(target_x))
                context.z_platform.move_to(self.y_axis, int(target_y))
            else:
                context.z_platform.move_to(self.x_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            if context.break_proc:
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            popup_close()

    def scan_manual_3(self):
        self.map_side = self.platform
        context.is_meas_in_process = True
        res = False
        maxLoc = (0, 0)
        # delta = 0.125 * self.delta
        try:
            context.current_proc = 3
            context.break_proc = False
            self.ser_data = np.ones(shape=[self.x_scale, self.y_count + 1]) * (-70)
            self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
            self.zero_pos_y = context.z_platform.get_pos(self.y_axis)

            self.save(20000, 20000, 1000)
            # X - Width/2
            context.z_platform.move(self.x_axis, (-1 * self.delta * self.x_scale / 2))
            # Y - Width/2
            context.z_platform.move(self.y_axis, (-1 * self.y_count / 2) + 1)
            while is_platforms_axis_busy() and (not context.break_proc):
                pass
            if context.break_proc:
                return
            self.map_min_x = context.z_platform.get_pos(self.x_axis)
            self.map_max_x = self.map_min_x + self.x_scale
            self.map_min_y = context.z_platform.get_pos(self.y_axis)
            self.map_max_y = self.map_min_y + self.y_count
            self.init_pos_y = context.z_platform.get_pos(self.y_axis)

            start = time()
            y_sign = 1
            steps = self.x_scale
            context.gui_hlp.init_progress_bar(steps)
            for x in range(0, self.x_scale):
                context.gui_hlp.progress_bar_step()
                context.z_platform.move(self.y_axis, y_sign * self.y_count)
                x_pos = x
                while True:
                    pm_values = self.pm_dev.get_power(self.pm_module)
                    y_pos = int(context.z_platform.get_pos(self.y_axis) - self.init_pos_y)
                    self.ser_data[x_pos][y_pos] = float(pm_values[self.pm_chan])
                    if (not is_platforms_axis_busy()) or context.break_proc:
                        y_sign *= -1
                        context.z_platform.move(self.x_axis, self.delta)
                        while is_platforms_axis_busy() and (not context.break_proc):
                            pass
                        break
            end = time()
            context.logger.log("Время сканирования :" + str((end - start) * 10 ** 3) + "ms")

            if context.break_proc:
                return
            dpg.delete_item(context.meas_powermap.meas_chart, children_only=True)
            dpg.push_container_stack(context.meas_powermap.meas_chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="мкм", tag="pm_x_axis1")
            dpg.add_plot_axis(dpg.mvYAxis, label="мкм", tag="pm_y_axis1")
            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(self.ser_data)

            self.last_max_power = maxVal
            self.last_max_x_coord = self.map_min_x + (maxLoc[1] * self.delta)
            self.last_max_y_coord = self.map_min_y + maxLoc[0]
            res = self.prepArray(self.ser_data)
            if res:
                self.draw_map(self.ser_data, 1, True, True)
                self.draw_scale()
            dpg.pop_container_stack()
        except Exception as e:
            print(e)
        finally:
            self.restore()

            if res and self.after_measure == GO_TO_MAX:
                target_y = self.map_min_y + maxLoc[1]
                target_x = self.map_min_x + (maxLoc[0] * self.delta)

                context.z_platform.move_to(self.x_axis, int(target_x))
                context.z_platform.move_to(self.y_axis, int(target_y))
            else:
                context.z_platform.move_to(self.x_axis, self.zero_pos_x)
                context.z_platform.move_to(self.y_axis, self.zero_pos_y)

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            if context.break_proc:
                context.logger.log(txt.PROCESS_IS_BRAKED)
            self.x_pos = -10000
            self.y_pos = -10000
            context.current_proc = 0
            context.is_meas_in_process = False
            popup_close()

    def adjustment_all(self):
        confirm_msg("ВКЛЮЧИТЕ ШИРИК", self.start_adjustment_all_thread, [])

    def start_adjustment_all_thread(self):
        threading.Thread(target=self.adjustment_all_logic, daemon=True).start()

    def adjustment_all_logic(self):

        context.logger.log("--- Запуск 4D-юстировки ---")
        context.is_meas_in_process = True

        x_steps = context.pmap_procedures.x_scale
        z_steps_count = context.pmap_procedures.y_count
        delta = context.pmap_procedures.delta

        y_steps_count_now_Z = 2 * round(z_steps_count / (2 * delta)) + 1

        if y_steps_count_now_Z < 1:
            y_steps_count_now_Z = 1

        global_max_power = -9999.0
        best_config = {}

        self.after_measure = GO_TO_ZERO

        try:
            self.platform = RIGHT_CHAN
            self.y_idx = context.z2_line_i
            self.x_idx = context.y2_line_i
            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.x_axis = int(context.axis[self.x_idx]['idx'])

            start_y = context.z_platform.get_pos(int(context.axis[context.y1_line_i]['idx']))
            start_z = context.z_platform.get_pos(int(context.axis[context.z1_line_i]['idx']))
            total_iter = y_steps_count_now_Z * x_steps
            for i_y in range(x_steps):
                for i_z in range(y_steps_count_now_Z):

                    target_y = start_y + (i_y - x_steps // 2) * delta
                    target_z = start_z + (i_z - y_steps_count_now_Z // 2) * delta

                    context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), target_y)
                    context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), target_z)

                    while is_platforms_axis_busy() and not context.break_proc:
                        pass
                    if context.break_proc:
                        return

                    self.scan_manual_3()
                    context.logger.log(f" итерация {i_y * y_steps_count_now_Z + (i_z + 1)} из {total_iter}")

                    current_power = self.last_max_power

                    if current_power > global_max_power:
                        global_max_power = current_power
                        best_config = {
                            'y1': target_y,
                            'z1': target_z,
                            'y2': self.last_max_x_coord,
                            'z2': self.last_max_y_coord
                        }

            if best_config:
                context.logger.log(f"Юстировка успешно завершена. Максимум мощности: {global_max_power:.4f}")
                context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), best_config['y1'])
                context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), best_config['z1'])
                context.z_platform.move_to(int(context.axis[context.y2_line_i]['idx']), best_config['y2'])
                context.z_platform.move_to(int(context.axis[context.z2_line_i]['idx']), best_config['z2'])

        finally:
            context.is_meas_in_process = False

    """def adjustment_all_logic(self):
        context.logger.log("--- Запуск 4D-юстировки ---")
        context.is_meas_in_process = True

        x_steps = context.pmap_procedures.x_scale
        z_steps_count = context.pmap_procedures.y_count
        delta = context.pmap_procedures.delta

        y_steps_count = 2 * round(x_steps / (2 * delta)) + 1

        if y_steps_count < 1:
            y_steps_count = 1

        global_max_power = -9999.0
        best_config = {}

        self.after_measure = GO_TO_ZERO

        try:
            self.platform = RIGHT_CHAN
            self.y_idx = context.z2_line_i
            self.x_idx = context.y2_line_i
            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.x_axis = int(context.axis[self.x_idx]['idx'])

            start_y = context.z_platform.get_pos(int(context.axis[context.y1_line_i]['idx']))
            start_z = context.z_platform.get_pos(int(context.axis[context.z1_line_i]['idx']))
            total_iter = y_steps_count * z_steps_count
            for i_y in range(y_steps_count):
                for i_z in range(z_steps_count):

                    target_y = start_y + (i_y - y_steps_count // 2) * delta
                    target_z = start_z + (i_z - z_steps_count // 2) * delta

                    context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), target_y)
                    context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), target_z)

                    while is_platforms_axis_busy() and not context.break_proc:
                        pass
                    if context.break_proc:
                        return

                    self.scan_manual_2()
                    context.logger.log(f"номер итерации из {total_iter} : {i_y * z_steps_count + i_z}")

                    current_power = self.last_max_power

                    if current_power > global_max_power:
                        global_max_power = current_power
                        best_config = {
                            'y1': target_y,
                            'z1': target_z,
                            'y2': self.last_max_x_coord,
                            'z2': self.last_max_y_coord
                        }

            if best_config:
                context.logger.log(f"Юстировка успешно завершена. Максимум мощности: {global_max_power:.4f}")
                context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), best_config['y1'])
                context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), best_config['z1'])
                context.z_platform.move_to(int(context.axis[context.y2_line_i]['idx']), best_config['y2'])
                context.z_platform.move_to(int(context.axis[context.z2_line_i]['idx']), best_config['z2'])

        finally:
            context.is_meas_in_process = False"""

    def adjustment_all_logic_2(self, min_power):
        context.logger.log("--- Запуск 4D-юстировки ---")
        context.is_meas_in_process = True

        x_steps = context.pmap_procedures.x_scale
        z_steps_count = context.pmap_procedures.y_count
        delta = context.pmap_procedures.delta

        y_steps_count_now_Z = 2 * round(z_steps_count / (2 * delta)) + 1

        if y_steps_count_now_Z < 1:
            y_steps_count_now_Z = 1

        global_max_power = -9999.0
        best_config = {}

        self.after_measure = GO_TO_ZERO

        try:
            self.platform = RIGHT_CHAN
            self.y_idx = context.z2_line_i
            self.x_idx = context.y2_line_i
            self.y_axis = int(context.axis[self.y_idx]['idx'])
            self.x_axis = int(context.axis[self.x_idx]['idx'])

            start_y1 = context.z_platform.get_pos(int(context.axis[context.y1_line_i]['idx']))
            start_z1 = context.z_platform.get_pos(int(context.axis[context.z1_line_i]['idx']))
            start_y2 = context.z_platform.get_pos(int(context.axis[context.y2_line_i]['idx']))
            start_z2 = context.z_platform.get_pos(int(context.axis[context.z2_line_i]['idx']))

            total_iter = y_steps_count_now_Z * x_steps
            for i_y in range(x_steps):
                for i_z in range(y_steps_count_now_Z):

                    target_y = start_y1 + (i_y - x_steps // 2) * delta
                    target_z = start_z1 + (i_z - y_steps_count_now_Z // 2) * delta

                    context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), target_y)
                    context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), target_z)

                    while is_platforms_axis_busy() and not context.break_proc:
                        pass
                    if context.break_proc:
                        return False
                    if (i_y + i_z) % 2 != 0:
                        continue

                    self.scan_manual_3()
                    context.logger.log(f" итерация {i_y * y_steps_count_now_Z + (i_z + 1)} из {total_iter}")

                    current_power = self.last_max_power

                    if current_power > global_max_power:
                        global_max_power = current_power
                        best_config = {
                            'y1': target_y,
                            'z1': target_z,
                            'y2': self.last_max_x_coord,
                            'z2': self.last_max_y_coord
                        }

            if best_config and global_max_power >= min_power:
                context.logger.log(f"Юстировка успешна. Сигнал: {global_max_power:.4f} dBm")
                context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), best_config['y1'])
                context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), best_config['z1'])
                context.z_platform.move_to(int(context.axis[context.y2_line_i]['idx']), best_config['y2'])
                context.z_platform.move_to(int(context.axis[context.z2_line_i]['idx']), best_config['z2'])
                return True
            else:
                context.logger.log(
                    f"Сигнал ниже порога ({global_max_power:.2f} < {min_power}). Возврат в исходные координаты.")
                context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), start_y1)
                context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), start_z1)
                context.z_platform.move_to(int(context.axis[context.y2_line_i]['idx']), start_y2)
                context.z_platform.move_to(int(context.axis[context.z2_line_i]['idx']), start_z2)
                return False

        finally:
            while is_platforms_axis_busy() and not context.break_proc: pass
            context.is_meas_in_process = False

    def yustirovka_all(self, min_power, target_power, max_iterations, tolerance):
        confirm_msg("ВКЛЮЧИТЕ ШИРИК", self.yustirovka_alll_thread, [min_power, target_power, max_iterations, tolerance])

    def yustirovka_alll_thread(self, min_power, target_power, max_iterations, tolerance):
        threading.Thread(target=self.yustirovka_all_logic, args=(min_power, target_power, max_iterations, tolerance),
                         daemon=True).start()

    def yustirovka_all_logic(self, min_power, target_power, max_iterations, tolerance):

        context.logger.log("Super Yustirovka")
        context.logger.log("Сканирование малой зоны")

        success = self.adjustment_all_logic_2(min_power)

        if context.break_proc: return

        if not success:
            context.logger.log("Сигнал не найден. Расширение зоны")
            self.y_count = 720
            self.x_scale = 6
            success = self.adjustment_all_logic_2(min_power)

        if context.break_proc: return

        if success:
            context.logger.log("Сигнал найден! Точная юстировка.")
            self.x_scale = 10
            self.y_count = 5
            self.delta = int(2 * 1000 / NM_PER_STEP_Z)
            self.adjustment_l_and_r_logic(target_power, max_iterations, tolerance)

            if context.break_proc: return

            context.logger.log("Юстировка крена.")
            self.correct_horizont_linear()

            if context.break_proc: return

            context.logger.log("Крен скорректирован. Финальная юстирока.")
            self.adjustment_l_and_r_logic(target_power, max_iterations, tolerance)

            context.logger.log("Цикл юстироки завершён")

        else:
            context.logger.log("Сигнал не найден даже в расширенной зоне")

    def run_full_4d_scan(self, axis_in_y, axis_in_z, axis_out_y, axis_out_z, steps_y, step_y_um, steps_z, step_z_um):

        context.current_proc = 3
        context.break_proc = False

        zero_in_y = context.z_platform.get_pos(axis_in_y)
        zero_in_z = context.z_platform.get_pos(axis_in_z)
        zero_out_y = context.z_platform.get_pos(axis_out_y)
        zero_out_z = context.z_platform.get_pos(axis_out_z)

        start_offset_y = - (steps_y - 1) * step_y_um / 2.0
        start_offset_z = - (steps_z - 1) * step_z_um / 2.0

        start_in_y = zero_in_y + start_offset_y
        start_in_z = zero_in_z + start_offset_z
        start_out_y = zero_out_y + start_offset_y
        start_out_z = zero_out_z + start_offset_z

        context.z_platform.move_to(axis_in_y, int(start_in_y))
        context.z_platform.move_to(axis_in_z, int(start_in_z))
        context.z_platform.move_to(axis_out_y, int(start_out_y))
        context.z_platform.move_to(axis_out_z, int(start_out_z))

        while is_platforms_axis_busy() and (not context.break_proc):
            pass
        if context.break_proc:
            return False

        best_signal = -1000.0
        best_coords = (zero_in_y, zero_in_z, zero_out_y, zero_out_z)

        curr_in_y = start_in_y
        curr_in_z = start_in_z

        dir_in_y = 1

        context.gui_hlp.init_progress_bar(steps_z)

        for i_z in range(steps_z):
            if context.break_proc: return False
            context.gui_hlp.progress_bar_step()

            if i_z > 0:
                context.z_platform.move(axis_in_z, step_z_um)
                curr_in_z += step_z_um
                while is_platforms_axis_busy() and (not context.break_proc): pass

            for i_y in range(steps_y):
                if context.break_proc: return False

                if i_y > 0:
                    context.z_platform.move(axis_in_y, step_y_um * dir_in_y)
                    curr_in_y += step_y_um * dir_in_y
                    while is_platforms_axis_busy() and (not context.break_proc): pass

                curr_out_y = start_out_y
                curr_out_z = start_out_z
                dir_out_y = 1

                for o_z in range(steps_z):
                    if context.break_proc: return False

                    if o_z > 0:
                        context.z_platform.move(axis_out_z, step_z_um)
                        curr_out_z += step_z_um
                        while is_platforms_axis_busy() and (not context.break_proc): pass

                    for o_y in range(steps_y):
                        if context.break_proc: return False

                        if o_y > 0:
                            context.z_platform.move(axis_out_y, step_y_um * dir_out_y)
                            curr_out_y += step_y_um * dir_out_y
                            while is_platforms_axis_busy() and (not context.break_proc): pass

                        pm_values = self.pm_dev.get_power(self.pm_module)
                        current_signal = float(pm_values[self.pm_chan])

                        if current_signal > best_signal:
                            best_signal = current_signal
                            best_coords = (curr_in_y, curr_in_z, curr_out_y, curr_out_z)

                    dir_out_y *= -1

                context.z_platform.move_to(axis_out_y, int(start_out_y))
                context.z_platform.move_to(axis_out_z, int(start_out_z))
                while is_platforms_axis_busy() and (not context.break_proc): pass

            dir_in_y *= -1

        if best_signal > -990.0:
            context.z_platform.move_to(axis_in_y, int(best_coords[0]))
            context.z_platform.move_to(axis_in_z, int(best_coords[1]))
            context.z_platform.move_to(axis_out_y, int(best_coords[2]))
            context.z_platform.move_to(axis_out_z, int(best_coords[3]))

            while is_platforms_axis_busy() and (not context.break_proc):
                pass

            context.logger.log(f"4D Юстировка завершена. Максимум: {best_signal:.2f} дБм.")
            return True
        else:
            context.z_platform.move_to(axis_in_y, zero_in_y)
            context.z_platform.move_to(axis_in_z, zero_in_z)
            context.z_platform.move_to(axis_out_y, zero_out_y)
            context.z_platform.move_to(axis_out_z, zero_out_z)
            while is_platforms_axis_busy() and (not context.break_proc): pass
            context.logger.log("Сигнал не обнаружен. Возврат в исходные позиции.")
            return False

    '''def go_strip(self, total_chips):

        context.logger.log(f"Запуск автоматического сканирования стрипа. Всего чипов: {total_chips}")

        axes_to_save = [
            self.y_axis,

        ]

        context.logger.log("Сохранение правильных координат Входа и Выхода...")

        array_b_in = {}
        array_b_out = {}
        for axis in axes_to_save:
            array_b_in[axis] = context.z_platform.get_pos(axis)

        x_retract_steps = 15000

        current_x_in = context.z_platform.get_pos(self.x_axis)
        array_a_in_x = current_x_in - x_retract_steps

        for chip_idx in range(total_chips):
            context.logger.log(f"=== ОБРАБОТКА ЧИПА {chip_idx + 1} из {total_chips} ===")

            if chip_idx > 0:

                context.logger.log("Безопасный отвод позиционеров по оси X...")
                context.z_platform.move_to(self.x_axis, int(array_a_in_x))
                self.wait_for_hardware()

                context.logger.log("Перемещение стола к следующему чипу...")
                self.next_chip()
                self.wait_for_hardware()

                context.logger.log("Поиск каналов через машинное зрение...")

                context.logger.log("Сближение с чипом по оси X...")
                context.z_platform.move_to(self.x_axis, int(current_x_in - 2000))
                self.wait_for_hardware()

                context.logger.log("Восстановление эталонных углов и высот (Массив B)...")
                for axis, saved_pos in array_b_in.items():
                    context.z_platform.move_to(axis, int(saved_pos))
                self.wait_for_hardware()

                context.logger.log("Запуск точного сканирования и поиска максимума...")
                res_adj = self.adjustment_l_and_r()

                if not res_adj:
                    context.logger.log("Предупреждение: Не удалось поймать оптимум на этом шаге!")
                    if context.break_proc:
                        return

            context.logger.log(f"Юстировка чипа {chip_idx + 1} завершена. Снятие показаний...")
            self.measure_chip_data()  # Твоя функция измерения

            if context.break_proc:
                context.logger.log("Процесс сканирования стрипа прерван пользователем.")
                return

        context.logger.log("Стрип успешно отсканирован! Все данные собраны.")'''

    @staticmethod
    def wait_for_hardware():
        while is_platforms_axis_busy() and (not context.break_proc):
            pass


context.pmap_procedures = PMapMeasureProcedures()
