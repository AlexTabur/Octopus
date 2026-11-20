from time import time, sleep

from Measurements.meas_powermap import set_scan_size
from axis_ctrl import is_platforms_axis_busy
from core.consts import *
from core.gui_helper import *
from core.utils import *
from move_from_camera import get_axis_platforms, wait_for_hardware

context = Context()

GO_TO_ZERO = 1
GO_TO_MAX = 2


class PMapMeasureProcedures:

    def __init__(self):
        self.init_pos_x = None
        self.init_pos_y = None
        self.last_max_y_coord = None
        self.last_max_x_coord = None
        self.last_max_power = -9999.0
        self.broadband_active = False
        self.y_axis = int(context.axis[context.z2_line_i]['idx'])
        self.x_axis = int(context.axis[context.y2_line_i]['idx'])

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

        self.x_count = 25
        self.y_count = 25
        self.delta = int(4 * 8)
        self.x_scale = 100
        self.y_scale = 100

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

        self.ser_data = np.ones(shape=[self.y_scale, self.x_scale]) * 130
        self.ser_data2 = np.ones(shape=[self.y_scale, self.x_scale]) * 130
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
            self.pitch_idx = context.y1_ang_i
            self.horiz_idx = context.x1_ang_i
            self.pitch_axis = int(context.axis[self.pitch_idx]['idx'])
            self.horiz_axis = int(context.axis[self.horiz_idx]['idx'])
            self.platform = LEFT_CHAN
            self.x_axis = int(context.axis[context.y1_line_i]['idx'])
            self.y_axis = int(context.axis[context.z1_line_i]['idx'])
        else:
            self.pitch_idx = context.y2_ang_i
            self.horiz_idx = context.x2_ang_i
            self.pitch_axis = int(context.axis[self.pitch_idx]['idx'])
            self.horiz_axis = int(context.axis[self.horiz_idx]['idx'])
            self.platform = RIGHT_CHAN
            self.x_axis = int(context.axis[context.y2_line_i]['idx'])
            self.y_axis = int(context.axis[context.z2_line_i]['idx'])

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

    def draw_map(self, arr, num):
        min_, max_ = np.min(arr), np.max(arr)
        bounds_min = [0.0, 0.0]
        bounds_max = [self.x_scale // 8, self.y_scale // 8]
        # print(arr.shape, bounds_max)
        arr = arr[::-1, :]
        dpg.configure_item(f"heatmap{num}", rows=self.y_scale, cols=self.x_scale, scale_min=min_, scale_max=max_,
                           bounds_min=bounds_min, bounds_max=bounds_max)
        dpg.configure_item(f"intensity{num}", min_scale=min_, max_scale=max_)
        dpg.set_value(f"heatmap{num}", [arr.flatten().astype(float).tolist()])
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(arr)
        self.last_max_power = maxVal
        return maxLoc

    def scan_step_y(self):
        self.map_side = self.platform
        context.is_meas_in_process = True

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
            print(e)
        finally:
            self.restore()

            context.current_proc = 0
            return res

    def aiming(self, left, chan_num, aim_steps, aim_x_width, aim_y_count, aim_y_step, device, module, meas_chan,
               scan_x_speed):
        context.is_meas_in_process = True
        self.set_platform(not left)

        context.current_proc = 3
        context.break_proc = False

        steps = 0
        for i in range(aim_steps):
            steps += aim_y_count[i]
        context.gui_hlp.init_progress_bar(steps)

        res = True
        for i in range(aim_steps):
            res = False  # context.spectrum_gui.exec_measure(aim_y_count[i], aim_y_step[i], aim_x_width[i], device, module, meas_chan, GO_TO_MAX, scan_x_speed[i])

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
        context.is_meas_in_process = False
        popup_close()

    def process_crosshair(self, cross):
        if not self.is_prepared:
            return 99999999
        if self.map_side == LEFT_CHAN:
            x_pos = context.axis[context.y1_line_i]['pos']
            y_pos = context.axis[context.z1_line_i]['pos']
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
        wait_for_hardware()

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
        context.break_proc = False

        scan_range = 100.0  # Общий ход в микронах (вверх-вниз)
        step_y = 0.5  # Шаг сканирования
        steps_count = int(scan_range / step_y)

        steps_real = STEP_PER[self.y_axis]
        power_profile1 = []
        power_profile2 = []
        y_coords = []

        # 1. Запоминаем исходную точку (мы уже стоим в максимуме 1-го канала по X и Y)
        start_y = context.z_platform.get_pos(self.y_axis)

        perevod_polovin = int((-scan_range / 2) * steps_real)
        context.z_platform.move(self.y_axis, perevod_polovin)
        while is_platforms_axis_busy(): pass

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
        max_idx1 = np.argmax(power_profile1)
        max_idx2 = np.argmax(power_profile2)

        self.horiz1_y = y_coords[max_idx1]
        self.horiz2_y = y_coords[max_idx2]

        context.logger.log(f"Линейный поиск завершен. Пик 1 на Y={self.horiz1_y}, Пик 2 на Y={self.horiz2_y}")
        context.z_platform.move_to(self.y_axis, start_y)
        while is_platforms_axis_busy(): pass

        self.horizont_platform_correction()
        context.is_meas_in_process = False

    def horizont_platform_correction(self):
        hypo = self.chan_dist * context.chip_chans_dy
        cath = self.horiz1_y - self.horiz2_y
        angle = -math.atan(cath / hypo) * 180 / math.pi  # Тут был минус !!!
        context.z_platform.move(self.horiz_axis, int(angle * STEP_PER_GRAD_X))
        context.logger.log_com(f"Поворот вокруг оси X на {angle} градусов")

    def adjustment_l_and_r(self, target_power=-30.0, max_iterations=5, tolerance=0.01):
        self.turn_broadband_on()
        context.logger.log("--- Запуск автоматической юстировки (право - лево)---")

        self.after_measure = GO_TO_MAX
        last_power = -1000.0  # Стартовое значение для сравнения

        for i in range(max_iterations):
            context.logger.log(f"--- Итерация  {i + 1} из {max_iterations} ---")
            context.logger.log("Сканирование левого волокна...")
            self.set_platform(False)
            # self.scan_step_y()
            self.scan_step_x()
            if context.break_proc:
                return

            context.logger.log("Сканирование правого волокна...")
            self.set_platform(True)
            # self.scan_step_y()
            self.scan_step_x()
            if context.break_proc:
                return

            pm_values = self.pm_dev.get_power(self.pm_module)
            current_power = float(pm_values[self.pm_chan])

            context.logger.log(f"Текущая оптическая мощность: {current_power:.2f} дБм")

            if current_power >= target_power:
                context.logger.log(f"Достигнуты нужные потери ({target_power} дБм)")
                break

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

    def move_to_bottom_corner(self):
        # X - Width/2
        context.z_platform.move(self.x_axis, int(-1 * self.x_scale / 2))
        # Y - Width/2
        context.z_platform.move(self.y_axis, int(-1 * self.y_scale / 2))
        wait_for_hardware()
        self.map_min_x = context.z_platform.get_pos(self.x_axis)
        self.map_max_x = self.map_min_x + self.x_scale
        self.map_min_y = context.z_platform.get_pos(self.y_axis)
        self.map_max_y = self.map_min_y + self.y_scale

    def scan_step_x(self):
        self.turn_broadband_on()
        self.map_side = self.platform
        context.is_meas_in_process = True
        context.current_proc = 3
        context.break_proc = False
        self.ser_data = np.ones(shape=[self.y_scale, self.x_scale]) * 130
        self.zero_pos_x = context.z_platform.get_pos(self.x_axis)
        self.zero_pos_y = context.z_platform.get_pos(self.y_axis)

        self.save(20000, 20000, 1000)
        self.move_to_bottom_corner()
        wait_for_hardware()
        if context.break_proc:
            return
        self.init_pos_y = context.z_platform.get_pos(self.y_axis)
        start = time()
        y_sign = 1
        context.gui_hlp.init_progress_bar(self.x_count)
        prev_y_pos = 0
        for x in range(0, self.x_scale, self.delta):
            context.gui_hlp.progress_bar_step()
            context.z_platform.move(self.y_axis, y_sign * self.y_scale)
            while is_platforms_axis_busy() and not context.break_proc:
                pm_values = self.pm_dev.get_power(self.pm_module)
                y_pos = int(context.z_platform.get_pos(self.y_axis) - self.init_pos_y)
                if y_sign > 0:
                    self.ser_data[prev_y_pos:y_pos, x:x + self.delta] = float(pm_values[self.pm_chan])
                else:
                    self.ser_data[y_pos:prev_y_pos, x:x + self.delta] = float(pm_values[self.pm_chan])
                prev_y_pos = y_pos
            y_sign *= -1
            context.z_platform.move(self.x_axis, self.delta)
            wait_for_hardware()
        if context.break_proc:
            return
        self.ser_data[self.ser_data > 129] = np.min(self.ser_data)
        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(self.ser_data)
        self.last_max_power = maxVal
        self.last_max_x_coord = self.map_min_x + maxLoc[0]
        self.last_max_y_coord = self.map_min_y + maxLoc[1]
        end = time()
        context.logger.log(
            f"Время сканирования :{round((end - start) * 10 ** 3, 3)} ms, Максимальная интенсивность: {maxVal}")
        self.draw_map(self.ser_data, 1)
        self.restore()

        if self.after_measure == GO_TO_MAX:
            target_y = self.map_min_y + maxLoc[1]
            target_x = self.map_min_x + maxLoc[0]

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
        wait_for_hardware()
        popup_close()

    def adjustment_all_2(self, min_power):
        self.turn_broadband_on()
        context.logger.log("--- Запуск 4D-юстировки ---")
        context.is_meas_in_process = True
        self.ser_data2 = np.ones(shape=[self.y_scale, self.x_scale]) * 130
        global_max_power = -9999.0
        best_config = {}
        start_y1 = context.z_platform.get_pos(int(context.axis[context.y1_line_i]['idx']))
        start_z1 = context.z_platform.get_pos(int(context.axis[context.z1_line_i]['idx']))
        self.set_platform(False)
        self.move_to_bottom_corner()
        self.after_measure = GO_TO_ZERO
        self.set_platform(True)
        a = range(0, self.x_scale, self.delta)
        b = range(0, self.y_scale, self.delta)
        total_iter = len(a) * len(b)
        for i_z, z_ in enumerate(b):
            for i_y, y_ in enumerate(a):
                # if (i_y + i_z) % 2 != 0:
                #     continue
                target_y = start_y1 + y_
                target_z = start_z1 + z_
                context.z_platform.move_to(int(context.axis[context.y1_line_i]['idx']), target_y)
                context.z_platform.move_to(int(context.axis[context.z1_line_i]['idx']), target_z)
                wait_for_hardware()
                self.scan_step_x()
                context.logger.log(f" итерация {i_z * len(a) + i_y + 1} из {total_iter}")
                current_power = self.last_max_power
                self.ser_data2[z_:z_ + self.delta, y_:y_ + self.delta] = current_power
                data = self.ser_data2.copy()
                data[data > 129] = np.min(data)
                self.draw_map(data, 2)
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
            return False
        while is_platforms_axis_busy() and not context.break_proc: pass
        context.is_meas_in_process = False
        return False

    def yustirovka_all(self, min_power, target_power, max_iterations, tolerance):
        self.turn_broadband_on()
        context.logger.log("Сканирование малой зоны")
        success = self.adjustment_all_2(min_power)
        if context.break_proc: return
        if not success:
            context.logger.log("Сигнал не найден. Расширение зоны")
            set_scan_size(30, 90, 3)
            success = self.adjustment_all_2(min_power)
        if context.break_proc: return
        if success:
            context.logger.log("Сигнал найден! Точная юстировка.")
            set_scan_size(10, 10, 2)
            self.adjustment_l_and_r(target_power, max_iterations, tolerance)
            if context.break_proc: return
            self.correct_horizont_linear()
            if context.break_proc: return
            context.logger.log("Крен скорректирован. Финальная юстирока.")
            set_scan_size(40, 40, 4)
            self.adjustment_l_and_r(target_power, max_iterations, tolerance)
            context.logger.log("Цикл юстироки завершён")
            self.turn_broadband_off()

        else:
            context.logger.log("Сигнал не найден даже в расширенной зоне")

    def turn_broadband_on(self):
        if not self.broadband_active:
            state = context.device_worker.laser_broadband_ctrl.get_beam_state()
            if state == 0:
                context.device_worker.laser_broadband_ctrl.turn_beam(True)
                sleep(5)
            self.broadband_active = True
        if not context.device_worker.is_pm2100_2_connected:
            context.device_worker.connectPM2100(2)
            sleep(5)

    def turn_broadband_off(self):
        context.device_worker.laser_broadband_ctrl.turn_beam(False)
        self.broadband_active = False


context.pmap_procedures = PMapMeasureProcedures()
