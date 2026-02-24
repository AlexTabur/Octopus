import time
from threading import Thread
from core.utils import *

context = Context()

LEFT_CHAN = 0x800
RIGHT_CHAN = 0x000


class PlatformController:
    # инициализация параметров
    def __init__(self):
        pass

    def set_platforms_speed(self, speed):
        if context.zplatform.is_connected:
            for i in range(0, 12, 1):
                context.zplatform.set_speed(i, speed)

    def get_all_axis_state(self):
        if context.zplatform.is_connected:
            for i in range(0, 13, 1):
                context.axis[i]['state'] = context.zplatform.get_state(context.axis[i]['idx'])
        if context.ztable.is_connected:
            context.axis[context.y_table_i]['state'] = context.ztable.get_state(context.axis[context.y_table_i]['idx'])

    def set_table_speed(self, speed):
        if context.ztable.is_connected:
            context.ztable.set_speed(context.axis[12]['idx'], speed)

    def store_preset_pos(self, platforms):
        if context.zplatform.is_connected and context.ztable.is_connected and context.platforms_initialized:
            match platforms & 0xf0:
                case 0x10:  # left platform
                    for i in range(0, 6):
                        context.preset_left[platforms & 0xf]['pos'][i] = context.zplatform.get_pos(
                            context.axis[i]['idx'])
                case 0x20:  # table
                    context.preset_table[platforms & 0xf]['pos'][context.y_table_i] = context.ztable.get_pos(
                        context.axis[context.y_table_i]['idx'])
                case 0x40:  # right platform
                    for i in range(6, 12):
                        context.preset_right[platforms & 0xf]['pos'][i] = context.zplatform.get_pos(
                            context.axis[i]['idx'])
                case 0x80:  # all platforms
                    for i in range(0, 12):
                        context.preset_all[platforms & 0xf]['pos'][i] = context.zplatform.get_pos(
                            context.axis[i]['idx'])
                    context.preset_all[platforms & 0xf]['pos'][context.y_table_i] = context.ztable.get_pos(
                        context.axis[context.y_table_i]['idx'])
        save_presets()

    def is_platforms_axis_busy(self):  # хот¤ бы одна из 6 осей платформы в движении
        axis_in_move = 0
        for i in range(0, 12, 1):
            is_stopped = context.zplatform.is_in_motion(context.axis[i]['idx'])
            if is_stopped == 0:
                axis_in_move += 1
        return bool(axis_in_move > 0)

    def is_table_axis_busy(self):  # стол в движении
        is_stopped = context.ztable.is_in_motion(context.axis[12]['idx'])
        return is_stopped == 0

    def platforms_homing(self):
        if context.zplatform.is_connected and context.ztable.is_connected:
            # Шаг 1. —тавим скорость побольше.
            for i in range(0, 12, 1):
                context.zplatform.set_speed(context.axis[i]['idx'], 12000)
            context.ztable.set_speed(context.axis[context.y_table_i]['idx'], 12000)

            # Шаг 2. отодвигаем платформы в стороны по X
            context.zplatform.vmove(context.axis[context.x1_line_i]['idx'], -1)
            context.zplatform.vmove(context.axis[context.x2_line_i]['idx'], -1)
            time.sleep(2)
            # Шаг 3. уходим в "0" по остальным ос¤м
            for i in range(0, 12, 1):
                if i != context.x1_line_i and i != context.x2_line_i:
                    context.zplatform.vmove(context.axis[i]['idx'], 1)
            context.ztable.vmove(context.axis[context.y_table_i]['idx'], 1)

            # Шаг 4. ждем останова по всем ос¤м
            context.break_proc = False
            while (self.is_platforms_axis_busy() or self.is_table_axis_busy()) and (not context.break_proc):
                pass

            # Шаг 5. запустили homing на средней скорости
            for i in range(0, 12, 1):
                context.zplatform.set_speed(context.axis[i]['idx'], 4000)
                if i == context.x1_line_i or i == context.x2_line_i:
                    context.zplatform.platform_to_home(context.axis[i]['idx'], 3)
                else:
                    context.zplatform.platform_to_home(context.axis[i]['idx'], 4)
            context.ztable.platform_to_home(context.axis[context.y_table_i]['idx'], 4)

            while (self.is_platforms_axis_busy() or self.is_table_axis_busy()) and (not context.break_proc):
                pass

            for i in range(0, 12, 1):
                context.zplatform.stop(context.axis[i]['idx'], 3)
                context.zplatform.set_speed(context.axis[i]['idx'], context.speed_value_platform)

            context.ztable.stop(context.axis[context.y_table_i]['idx'], 3)
            context.ztable.set_speed(context.axis[context.y_table_i]['idx'], context.speed_value_platform)

            for i in range(0, 12, 1):
                context.zplatform.set_pos(context.axis[i]['idx'], 0)
            context.ztable.set_pos(context.axis[context.y_table_i]['idx'], 0)

        context.gui_hlp.init_platforms_complete(context.break_proc is False)
        context.gui_hlp.popup_close()

    def platforms_homing2(self):
        if (not context.zplatform.is_connected) or (not context.ztable.is_connected):
            context.logger.log_warning('Не подключен контроллер платформ и/или стола')
            context.gui_hlp.popup_close()
            return

        datumIn = [0] * 13
        bgIn = [0] * 13
        endIn = [0] * 13
        try:
            # Шаг 1. Cтавим скорость побольше.
            for i in range(0, 12):
                context.zplatform.set_speed(context.axis[i]['idx'], 5000)  # 6000)
            context.ztable.set_speed(context.axis[context.y_table_i]['idx'], 5000)

            # Шаг 2. запоминаем и переназначаем значения концевиков
            for i in range(0, 12):
                axis = context.axis[i]['idx']
                datumIn[i] = context.zplatform.get_DatumIn(axis)
                bgIn[i] = context.zplatform.get_BckIn(axis)
                endIn[i] = context.zplatform.get_FwdIn(axis)

                if i == context.x1_line_i or i == context.x2_line_i:
                    context.zplatform.set_DatumIn(axis, bgIn[i])
                else:
                    context.zplatform.set_DatumIn(axis, endIn[i])

            axis = context.axis[context.y_table_i]['idx']
            datumIn[12] = context.ztable.get_DatumIn(axis)
            #            bgIn[i] = context.zplatform.get_BckIn(axis)
            endIn[12] = context.ztable.get_FwdIn(axis)
            context.ztable.set_DatumIn(axis, endIn[12])

            # Шаг 3. Запустили homing стола и платформ вверх
            context.ztable.platform_to_home(context.axis[context.y_table_i]['idx'], 4)
            context.zplatform.platform_to_home(context.axis[context.z1_line_i]['idx'], 3)
            context.zplatform.platform_to_home(context.axis[context.z2_line_i]['idx'], 3)
            time.sleep(2)

            # Шаг 4. Запустили homing остальных осей
            for i in range(0, 12, 1):
                if i == context.x1_line_i or i == context.x2_line_i:
                    context.zplatform.platform_to_home(context.axis[i]['idx'], 4)
                else:
                    context.zplatform.platform_to_home(context.axis[i]['idx'], 3)

            while (self.is_platforms_axis_busy() or self.is_table_axis_busy()) and (not context.break_proc):
                pass
        finally:
            # Восстанавливаем значения концевиков
            for i in range(0, 12):
                axis = context.axis[i]['idx']
                context.zplatform.set_DatumIn(axis, datumIn[i])

            axis = context.axis[context.y_table_i]['idx']
            context.ztable.set_DatumIn(axis, datumIn[12])

            # Восстанавливаем скорости перемещения
            for i in range(0, 12):
                context.zplatform.stop(context.axis[i]['idx'], 3)
                context.zplatform.set_pos(context.axis[i]['idx'], 0)
            context.ztable.stop(context.axis[context.y_table_i]['idx'], 3)
            context.ztable.set_pos(context.axis[context.y_table_i]['idx'], 0)

            self.set_platforms_speed(context.speed_value_platform)
            self.set_table_speed(context.speed_value_platform)

            context.gui_hlp.init_platforms_complete(context.break_proc is False)
            context.gui_hlp.popup_close()

            if context.platforms_initialized:
                context.zplatform.move_to(context.axis[context.y1_line_i]['idx'], -125000)
                context.zplatform.move_to(context.axis[context.y2_line_i]['idx'], -125000)
                context.zplatform.move_to(context.axis[context.x1_ang_i]['idx'], -20000)
                context.zplatform.move_to(context.axis[context.y1_ang_i]['idx'], -20000)
                context.zplatform.move_to(context.axis[context.z1_ang_i]['idx'], -20000)
                context.zplatform.move_to(context.axis[context.x2_ang_i]['idx'], -20000)
                context.zplatform.move_to(context.axis[context.y2_ang_i]['idx'], -20000)
                context.zplatform.move_to(context.axis[context.z2_ang_i]['idx'], -20000)

    def move_platform_to_preset(self, preset):
        if context.zplatform.is_connected and context.platforms_initialized:
            if preset & 0x10:
                pl_range = range(0, 6)
            else:
                pl_range = range(6, 12)

            for i in pl_range:
                context.zplatform.set_speed(context.axis[i]['idx'], 5000)
                if preset & 0x10:
                    context.zplatform.move_to(context.axis[i]['idx'], context.preset_left[preset & 0xF]['pos'][i])
                else:
                    context.zplatform.move_to(context.axis[i]['idx'], context.preset_right[preset & 0xF]['pos'][i])

            # context.ztable.set_speed(context.axis[context.y_table_i]['idx'], 5000)
            # context.ztable.move_to(context.axis[context.y_table_i]['idx'], context.zero_pos[context.y_table_i])

            # context.zplatform.platform_to_home(i, 4)
            # ждем останова по всем ос¤м
            context.break_proc = False
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass
            for i in pl_range:
                context.zplatform.stop(context.axis[i]['idx'], 3)
                context.zplatform.set_speed(context.axis[i]['idx'], context.speed_value_platform)

        context.gui_hlp.popup_close()

    def move_platform_to_chan(self, platform, chan, chan_dy):
        if not context.zplatform.is_connected:  # context.platforms_initialized:
            context.logger.log_warning('Не подключен контроллер платформ и/или стола')
            context.gui_hlp.popup_close()
            return False

        x_axis = 0
        x_speed = 0
        y_axis = 0
        y_speed = 0
        try:
            if platform & LEFT_CHAN:
                y_idx = context.y1_line_i
                x_idx = context.x1_line_i
                x_dir = int(context.axis[x_idx]['dir_bw'])  # Left X to left dir
                y_dir = int(context.axis[y_idx]['dir_bw'])  # Left Y down dir
                channel = context.chip_ctrl.left_channels[chan]
                active_chan = context.chip_ctrl.active_chan_left
            else:
                y_idx = context.y2_line_i
                x_idx = context.x2_line_i
                x_dir = int(context.axis[x_idx]['dir_fw'])  # Right X to right dir
                y_dir = int(context.axis[y_idx]['dir_bw'])  # Right Y down dir
                channel = context.chip_ctrl.right_channels[chan]
                active_chan = context.chip_ctrl.active_chan_right

            dy = int(1000 * chan_dy / NM_PER_STEP_Y) * (chan - active_chan)
            y_axis = int(context.axis[y_idx]['idx'])
            x_axis = int(context.axis[x_idx]['idx'])

            res, x_speed = context.zplatform.get_speed(x_axis)
            context.zplatform.set_speed(x_axis, 6000)
            res, y_speed = context.zplatform.get_speed(y_axis)
            context.zplatform.set_speed(y_axis, 6000)

            context.zplatform.move(x_axis, x_dir * 2000)  # отоддвинуть волокно от чипа
            context.break_proc = False
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass

            #            if channel.state & CHAN_IS_AIMED:
            #                context.zplatform.move_to(x_axis, channel.position[0])
            #                context.zplatform.move_to(y_axis, channel.position[1])
            #            else:
            context.zplatform.move(y_axis, y_dir * dy)
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass
            context.zplatform.move(x_axis, -x_dir * 2000)  # вернуть волокно к чипу
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass

            # context.ztable.set_speed(context.axis[context.y_table_i]['idx'], 5000)

            # ждем останова по всем осям
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass
        finally:
            context.zplatform.set_speed(x_axis, x_speed)
            context.zplatform.set_speed(y_axis, y_speed)

            context.gui_hlp.popup_close()
            if context.break_proc is False:
                if platform & LEFT_CHAN:
                    context.chip_ctrl.stateL = chan
                else:
                    context.chip_ctrl.stateR = chan

            return context.break_proc is False

    def move_table_to_chip(self, travel_path_um):
        if (not context.zplatform.is_connected) or (not context.ztable.is_connected):  # context.platforms_initialized:
            context.logger.log_warning('Не подключен контроллер платформ и/или стола')
            context.gui_hlp.popup_close()
            return False

        x_axis1 = 0
        x_axis2 = 0
        x_speed = 0
        table_speed = 0
        try:
            x_idx1 = context.x1_line_i
            x_dir1 = int(context.axis[x_idx1]['dir_bw'])  # Left X to left dir

            x_idx2 = context.x2_line_i
            x_dir2 = int(context.axis[x_idx2]['dir_fw'])  # Right X to right dir

            dy = int(travel_path_um / TABLE_MKM_KOEF)
            x_axis1 = int(context.axis[x_idx1]['idx'])
            x_axis2 = int(context.axis[x_idx2]['idx'])
            table_axis = int(context.axis[context.y_table_i]['idx'])

            res, x_speed = context.zplatform.get_speed(x_axis1)
            context.zplatform.set_speed(x_axis1, 6000)
            res, table_speed = context.ztable.get_speed(table_axis)
            context.ztable.set_speed(table_axis, 6000)

            # отоддвинуть волокно от чипа
            context.zplatform.move(x_axis1, x_dir1 * 2000)
            context.zplatform.move(x_axis2, x_dir2 * 2000)
            context.break_proc = False
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass

            context.ztable.move(table_axis, dy)
            while self.is_table_axis_busy() and (not context.break_proc):
                pass

            # вернуть волокно к чипу
            context.zplatform.move(x_axis1, -x_dir1 * 2000)
            context.zplatform.move(x_axis2, -x_dir2 * 2000)
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass

        finally:
            context.zplatform.set_speed(x_axis1, x_speed)
            context.zplatform.set_speed(x_axis2, x_speed)
            context.ztable.set_speed(table_axis, table_speed)

            context.gui_hlp.popup_close()

            return context.break_proc is False

    def move_table_to_preset(self, preset):
        if context.ztable.is_connected and context.platforms_initialized:
            context.ztable.set_speed(context.axis[context.y_table_i]['idx'], 5000)
            context.ztable.move_to(context.axis[context.y_table_i]['idx'],
                                   context.preset_table[preset & 0xf]['pos'][context.y_table_i])

            # ждем останова по всем ос¤м
            context.break_proc = False
            while self.is_table_axis_busy() and (not context.break_proc):
                pass

            context.ztable.stop(context.axis[context.y_table_i]['idx'], 3)
            context.ztable.set_speed(context.axis[context.y_table_i]['idx'], context.speed_value_platform)

        context.gui_hlp.popup_close()

    def move_all_to_preset(self, preset):
        if context.zplatform.is_connected and context.ztable.is_connected and context.platforms_initialized:

            context.ztable.set_speed(context.axis[context.y_table_i]['idx'], 20000)
            context.ztable.move_to(context.axis[context.y_table_i]['idx'],
                                   context.preset_all[preset & 0xf]['pos'][context.y_table_i])

            context.break_proc = False
            while self.is_table_axis_busy() and (not context.break_proc):
                pass

            for i in range(0, 12):
                context.zplatform.set_speed(context.axis[i]['idx'], 10000)
                context.zplatform.move_to(context.axis[i]['idx'], context.preset_all[preset & 0xF]['pos'][i])

            # ждем останова по всем ос¤м
            while self.is_platforms_axis_busy() and (not context.break_proc):
                pass

            for i in range(0, 12):
                context.zplatform.stop(context.axis[i]['idx'], 3)
                context.zplatform.set_speed(context.axis[i]['idx'], context.speed_value_platform)

            context.ztable.stop(context.axis[context.y_table_i]['idx'], 3)
            context.ztable.set_speed(context.axis[context.y_table_i]['idx'], context.speed_value_platform)

        context.gui_hlp.popup_close()

    def get_all_axis_pos(self):
        if context.zplatform.is_connected:
            for i in range(0, 13, 1):
                pos = context.zplatform.get_pos(context.axis[i]['idx'])
                if pos == 100000000:  # disconnected
                    context.zplatform.state_changed |= 1
                    context.zplatform.is_connected = False
                    pos = 99999999  # '***'
                context.axis[i]['pos'] = pos

        if context.ztable.is_connected:
            pos = context.ztable.get_pos(context.axis[context.y_table_i]['idx'])
            if pos == 100000000:  # disconnected
                context.ztable.state_changed |= 1
                context.ztable.is_connected = False
                pos = 99999999  # '***'

            context.axis[context.y_table_i]['pos'] = pos

    def get_axis_move_params(self, axis):
        if context.zplatform.is_connected:
            acc = context.zplatform.get_accel(axis)
            dec = context.zplatform.get_decel(axis)
        else:
            acc = -1
            dec = -1
        return acc, dec

    def stop_cur_axis(self):
        if context.zplatform.is_connected and context.current_axis != -1:
            if context.current_axis < 12:
                context.zplatform.stop(context.current_axis, 3)
            else:
                context.ztable.stop(AXIS_TABLE, 3)
        context.current_axis = -1

    def move_table(self, dir_):
        context.current_axis = AXIS_TABLE + 14
        if context.ztable.is_connected:
            if context.ctrl_mode == CTRL_MODE_CONT:
                print('ztable.vmove axis ', AXIS_TABLE)
                context.ztable.vmove(AXIS_TABLE, dir_)
            else:
                context.ztable.move(AXIS_TABLE, dir_ * context.step_value_table)
        else:
            context.logger.log_warning("Контроллер стола не подключен")

    def readAccValues(self, platform):
        if context.zplatform.is_connected:
            for i in range(0, 13, 1):
                context.axis[i]['acc'] = context.zplatform.get_accel(context.axis[i]['idx'])

    def readDecValues(self, platform):
        if context.zplatform.is_connected:
            for i in range(0, 13, 1):
                context.axis[i]['dec'] = context.zplatform.get_decel(context.axis[i]['idx'])

    def move_axis(self, dir_, axis):
        # context.logger.log_warning(str(axis) + " " + str(dir))
        # return
        if axis != -1:
            context.current_axis = axis
            if context.zplatform.is_connected:
                # print("moving on axis = ", abs(context.current_axis))
                if context.ctrl_mode == CTRL_MODE_CONT:
                    context.zplatform.vmove(axis, dir_)
                else:
                    context.zplatform.move(axis, dir_ * context.step_value_platform)
            else:
                context.logger.log_warning("Контроллер платформ не подключен")

    def disconnect_platform(self):
        if context.zplatform.is_connected:
            context.zplatform.disconnect()
            context.gui_hlp.init_platforms_complete(False)

    def disconnect_table(self):
        if context.ztable.is_connected:
            context.ztable.disconnect()

    def connect_table(self):
        if (not context.table_connect_thread.is_alive()) and (not context.ztable.is_connected):
            context.table_connect_thread = Thread(target=context.ztable.connect, args=[context.table_controller_ip, ],
                                                  daemon=True)
            context.table_connect_thread.start()
            return True
        return False

    def connect_platform(self):
        if not context.platform_connect_thread.is_alive():
            context.platform_connect_thread = Thread(target=context.zplatform.connect,
                                                     args=[context.plarforms_controller_ip, ], daemon=True)
            context.platform_connect_thread.start()
            return True
        return False
        # str_iplist, num = context.zplatform.search()
        # print('num=',num)
        # print('str_iplist=', str_iplist)
        # if context.zplatform.search(context.plarforms_controller_ip):
        # context.zplatform.search(context.plarforms_controller_ip)
        # if context.zplatform.search(context.table_controller_ip):
        # context.zplatform.search(context.table_controller_ip)
        # context.zplatform.search("192.168.0.13")

    #        if context.zplatform.is_connected:
    #            context.platforms_initialized = False
    #            self.set_platforms_speed(context.speed_value_platform)

    #        if context.ztable.is_connected:
    #            context.ztable.set_speed(AXIS_TABLE,50000)
    #            context.ztable.set_accel(AXIS_TABLE,20000)
