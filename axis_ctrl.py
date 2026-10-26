from threading import Thread

from core.gui_helper import init_platforms_complete, popup_close
from core.utils import *
from core.consts import *
from time import sleep

context = Context()

LEFT_CHAN = 0x800
RIGHT_CHAN = 0x000
speed = 6000


def platforms_homing2():
    if (not context.z_platform.is_connected) or (not context.z_table.is_connected):
        context.logger.log_warning('Не подключен контроллер платформ и/или стола')
        popup_close()
        return

    datumIn = [0] * 13
    bgIn = [0] * 13
    endIn = [0] * 13
    try:

        for i in range(0, 12):
            context.z_platform.set_speed(context.axis[i]['idx'], speed)  # 6000)
        context.z_table.set_speed(context.axis[context.y_table_i]['idx'], speed)

        for i in range(0, 12):
            axis = context.axis[i]['idx']
            datumIn[i] = context.z_platform.get_DatumIn(axis)
            bgIn[i] = context.z_platform.get_BckIn(axis)
            endIn[i] = context.z_platform.get_FwdIn(axis)

            if i == context.x1_line_i or i == context.x2_line_i:
                context.z_platform.set_DatumIn(axis, bgIn[i])
            else:
                context.z_platform.set_DatumIn(axis, endIn[i])

        axis = context.axis[context.y_table_i]['idx']
        datumIn[12] = context.z_table.get_DatumIn(axis)
        #            bgIn[i] = context.z_platform.get_BckIn(axis)
        endIn[12] = context.z_table.get_FwdIn(axis)
        context.z_table.set_DatumIn(axis, endIn[12])

        for i in (context.x1_line_i, context.x2_line_i):
            context.z_platform.platform_to_home(context.axis[i]['idx'], 4)

        for _ in range(50):
            if context.break_proc:
                return
            sleep(0.1)

        context.z_table.platform_to_home(context.axis[context.y_table_i]['idx'], 3)
        # context.z_platform.platform_to_home(context.axis[context.z1_line_i]['idx'], 3)
        # context.z_platform.platform_to_home(context.axis[context.z2_line_i]['idx'], 3)
        # sleep(2)

        for i in range(0, 12):
            if i != context.x1_line_i and i != context.x2_line_i:
                context.z_platform.platform_to_home(context.axis[i]['idx'], 3)

        while (is_platforms_axis_busy() or is_table_axis_busy()) and (not context.break_proc):
            pass
    except Exception as e:
        print(e)
    finally:

        for i in range(0, 12):
            axis = context.axis[i]['idx']
            context.z_platform.set_DatumIn(axis, datumIn[i])

        axis = context.axis[context.y_table_i]['idx']
        context.z_table.set_DatumIn(axis, datumIn[12])

        for i in range(0, 12):
            context.z_platform.stop(context.axis[i]['idx'], 3)
            context.z_platform.set_pos(context.axis[i]['idx'], 0)
        context.z_table.stop(context.axis[context.y_table_i]['idx'], 3)
        context.z_table.set_pos(context.axis[context.y_table_i]['idx'], 0)

        set_platforms_speed(context.speed_value_platform)
        set_table_speed(context.speed_value_platform)
        context.z_table.stop(12, 3)
        context.z_table.set_creep(12, 0)
        context.z_table.set_decel(12, 0)
        init_platforms_complete(context.break_proc is False)
        popup_close()

        if context.platforms_initialized:
            # context.z_platform.move_to(context.axis[context.y1_line_i]['idx'], -125000)
            # context.z_platform.move_to(context.axis[context.y2_line_i]['idx'], -125000)
            # context.z_platform.move_to(context.axis[context.x1_ang_i]['idx'], -20000)
            # context.z_platform.move_to(context.axis[context.y1_ang_i]['idx'], -20000)
            # context.z_platform.move_to(context.axis[context.z1_ang_i]['idx'], -20000)
            # context.z_platform.move_to(context.axis[context.x2_ang_i]['idx'], -20000)
            # context.z_platform.move_to(context.axis[context.y2_ang_i]['idx'], -20000)
            # context.z_platform.move_to(context.axis[context.z2_ang_i]['idx'], -20000)
            move_all_to_preset(128)
        context.break_proc = False


'''def platforms_homing2():
    if (not context.z_platform.is_connected) or (not context.z_table.is_connected):
        context.logger.log_warning('Не подключен контроллер платформ и/или стола')
        popup_close()
        return

    datumIn = [0] * 13
    bgIn = [0] * 13
    endIn = [0] * 13
    try:

        for i in range(0, 12):
            context.z_platform.set_speed(context.axis[i]['idx'], speed)  # 6000)
        context.z_table.set_speed(context.axis[context.y_table_i]['idx'], speed)

        for i in range(0, 12):
            axis = context.axis[i]['idx']
            datumIn[i] = context.z_platform.get_DatumIn(axis)
            bgIn[i] = context.z_platform.get_BckIn(axis)
            endIn[i] = context.z_platform.get_FwdIn(axis)

            if i == context.x1_line_i or i == context.x2_line_i:
                context.z_platform.set_DatumIn(axis, bgIn[i])
            else:
                context.z_platform.set_DatumIn(axis, endIn[i])

        axis = context.axis[context.y_table_i]['idx']
        datumIn[12] = context.z_table.get_DatumIn(axis)
        #            bgIn[i] = context.z_platform.get_BckIn(axis)
        endIn[12] = context.z_table.get_FwdIn(axis)
        context.z_table.set_DatumIn(axis, endIn[12])

        context.z_table.platform_to_home(context.axis[context.y_table_i]['idx'], 3)
        context.z_platform.platform_to_home(context.axis[context.z1_line_i]['idx'], 3)
        context.z_platform.platform_to_home(context.axis[context.z2_line_i]['idx'], 3)
        sleep(2)

        for i in range(0, 12, 1):
            if i == context.x1_line_i or i == context.x2_line_i:
                context.z_platform.platform_to_home(context.axis[i]['idx'], 4)
            else:
                context.z_platform.platform_to_home(context.axis[i]['idx'], 3)

        while (is_platforms_axis_busy() or is_table_axis_busy()) and (not context.break_proc):
            pass
    except Exception as e:
        print(e)
    finally:

        for i in range(0, 12):
            axis = context.axis[i]['idx']
            context.z_platform.set_DatumIn(axis, datumIn[i])

        axis = context.axis[context.y_table_i]['idx']
        context.z_table.set_DatumIn(axis, datumIn[12])

        for i in range(0, 12):
            context.z_platform.stop(context.axis[i]['idx'], 3)
            context.z_platform.set_pos(context.axis[i]['idx'], 0)
        context.z_table.stop(context.axis[context.y_table_i]['idx'], 3)
        context.z_table.set_pos(context.axis[context.y_table_i]['idx'], 0)

        set_platforms_speed(context.speed_value_platform)
        set_table_speed(context.speed_value_platform)
        context.z_table.stop(12, 3)
        context.z_table.set_creep(12, 0)
        context.z_table.set_decel(12, 0)
        init_platforms_complete(context.break_proc is False)
        popup_close()

        if context.platforms_initialized:
            context.z_platform.move_to(context.axis[context.y1_line_i]['idx'], -125000)
            context.z_platform.move_to(context.axis[context.y2_line_i]['idx'], -125000)
            context.z_platform.move_to(context.axis[context.x1_ang_i]['idx'], -20000)
            context.z_platform.move_to(context.axis[context.y1_ang_i]['idx'], -20000)
            context.z_platform.move_to(context.axis[context.z1_ang_i]['idx'], -20000)
            context.z_platform.move_to(context.axis[context.x2_ang_i]['idx'], -20000)
            context.z_platform.move_to(context.axis[context.y2_ang_i]['idx'], -20000)
            context.z_platform.move_to(context.axis[context.z2_ang_i]['idx'], -20000)
        move_all_to_preset(128)
'''


def move_platform_to_preset(preset):
    if context.z_platform.is_connected:  # and context.platforms_initialized:
        if preset & 0x10:
            pl_range = range(0, 6)
        else:
            pl_range = range(6, 12)

        for i in pl_range:
            context.z_platform.set_speed(context.axis[i]['idx'], speed)
            if preset & 0x10:
                context.z_platform.move_to(context.axis[i]['idx'], context.preset_left[preset & 0xF]['pos'][i])
            else:
                context.z_platform.move_to(context.axis[i]['idx'], context.preset_right[preset & 0xF]['pos'][i])

        # context.z_table.set_speed(context.axis[context.y_table_i]['idx'], 5000)
        # context.z_table.move_to(context.axis[context.y_table_i]['idx'], context.zero_pos[context.y_table_i])

        # context.z_platform.platform_to_home(i, 4)

        context.break_proc = False
        while is_platforms_axis_busy() and (not context.break_proc):
            pass
        for i in pl_range:
            context.z_platform.stop(context.axis[i]['idx'], 3)
            context.z_platform.set_speed(context.axis[i]['idx'], context.speed_value_platform)

    popup_close()


def move_platform_to_chan(platform, chan, chan_dy):
    if not context.z_platform.is_connected:  # context.platforms_initialized:
        context.logger.log_warning('Не подключен контроллер платформ и/или стола')
        popup_close()
        return False

    x_axis = 0
    x_speed = 0
    y_axis = 0
    y_speed = 0
    try:
        if platform & LEFT_CHAN:
            y_idx = context.y1_line_i
            x_idx = context.x1_line_i
            x_dir = int(context.axis[x_idx]['dir_bw'])  # Left X to left dir_
            y_dir = int(context.axis[y_idx]['dir_bw'])  # Left Y down dir_
            # channel = context.chip_ctrl.left_channels[chan]
            active_chan = context.chip_ctrl.active_chan_left
        else:
            y_idx = context.y2_line_i
            x_idx = context.x2_line_i
            x_dir = int(context.axis[x_idx]['dir_fw'])  # Right X to right dir_
            y_dir = int(context.axis[y_idx]['dir_bw'])  # Right Y down dir_
            # channel = context.chip_ctrl.right_channels[chan]
            active_chan = context.chip_ctrl.active_chan_right

        dy = int(1000 * chan_dy / NM_PER_STEP_Y) * (chan - active_chan)
        y_axis = int(context.axis[y_idx]['idx'])
        x_axis = int(context.axis[x_idx]['idx'])

        res, x_speed = context.z_platform.get_speed(x_axis)
        context.z_platform.set_speed(x_axis, speed)
        res, y_speed = context.z_platform.get_speed(y_axis)
        context.z_platform.set_speed(y_axis, speed)

        context.z_platform.move(x_axis, x_dir * 2000)
        context.break_proc = False
        while is_platforms_axis_busy() and (not context.break_proc):
            pass

        #            if channel.state & CHAN_IS_AIMED:
        #                context.z_platform.move_to(x_axis, channel.position[0])
        #                context.z_platform.move_to(y_axis, channel.position[1])
        #            else:
        context.z_platform.move(y_axis, y_dir * dy)
        while is_platforms_axis_busy() and (not context.break_proc):
            pass
        context.z_platform.move(x_axis, -x_dir * 2000)
        while is_platforms_axis_busy() and (not context.break_proc):
            pass

        # context.z_table.set_speed(context.axis[context.y_table_i]['idx'], 5000)

        while is_platforms_axis_busy() and (not context.break_proc):
            pass
    except Exception as e:
        print(e)
    finally:
        context.z_platform.set_speed(x_axis, x_speed)
        context.z_platform.set_speed(y_axis, y_speed)

        popup_close()
        if context.break_proc is False:
            if platform & LEFT_CHAN:
                context.chip_ctrl.stateL = chan
            else:
                context.chip_ctrl.stateR = chan

        return context.break_proc is False


def move_table_to_chip(travel_path_um):
    if (not context.z_platform.is_connected) or (
            not context.z_table.is_connected):  # context.platforms_initialized:
        context.logger.log_warning('Не подключен контроллер платформ и/или стола')
        popup_close()
        return False

    x_speed = 0
    table_speed = 0
    x_idx1 = context.x1_line_i
    x_dir1 = int(context.axis[x_idx1]['dir_bw'])  # Left X to left dir_

    x_idx2 = context.x2_line_i
    x_dir2 = int(context.axis[x_idx2]['dir_fw'])  # Right X to right dir_

    dy = int(travel_path_um / TABLE_MKM_KOEF)
    x_axis1 = int(context.axis[x_idx1]['idx'])
    x_axis2 = int(context.axis[x_idx2]['idx'])
    table_axis = int(context.axis[context.y_table_i]['idx'])
    try:
        res, x_speed = context.z_platform.get_speed(x_axis1)
        context.z_platform.set_speed(x_axis1, speed)
        res, table_speed = context.z_table.get_speed(table_axis)
        context.z_table.set_speed(table_axis, speed)

        context.z_platform.move(x_axis1, x_dir1 * 2000)
        context.z_platform.move(x_axis2, x_dir2 * 2000)
        context.break_proc = False
        while is_platforms_axis_busy() and (not context.break_proc):
            pass

        context.z_table.move(table_axis, dy)
        while is_table_axis_busy() and (not context.break_proc):
            pass

        context.z_platform.move(x_axis1, -x_dir1 * 2000)
        context.z_platform.move(x_axis2, -x_dir2 * 2000)
        while is_platforms_axis_busy() and (not context.break_proc):
            pass
    except Exception as e:
        print(e)
    finally:
        context.z_platform.set_speed(x_axis1, x_speed)
        context.z_platform.set_speed(x_axis2, x_speed)
        context.z_table.set_speed(table_axis, table_speed)

        popup_close()

        return context.break_proc is False


def move_table_to_preset(preset):
    if context.z_table.is_connected:  # and context.platforms_initialized:

        context.z_table.set_speed(context.axis[context.y_table_i]['idx'], speed)
        context.z_table.move_to(context.axis[context.y_table_i]['idx'],
                                context.preset_table[preset & 0xf]['pos'][context.y_table_i])

        context.break_proc = False
        while is_table_axis_busy() and (not context.break_proc):
            pass

        context.z_table.stop(context.axis[context.y_table_i]['idx'], 3)
        context.z_table.set_speed(context.axis[context.y_table_i]['idx'], context.speed_value_platform)
    context.z_table.stop(context.axis[context.y_table_i]['idx'], 3)
    popup_close()


def move_all_to_preset(preset):
    if context.z_platform.is_connected and context.z_table.is_connected:  # and context.platforms_initialized:

        context.z_table.set_speed(context.axis[context.y_table_i]['idx'], speed)
        context.z_table.move_to(context.axis[context.y_table_i]['idx'],
                                context.preset_all[preset & 0xf]['pos'][context.y_table_i])
        context.break_proc = False
        # while is_table_axis_busy() and (not context.break_proc):
        #     pass
        for i in range(0, 12):
            context.z_platform.set_speed(context.axis[i]['idx'], speed)
            context.z_platform.move_to(context.axis[i]['idx'], context.preset_all[preset & 0xF]['pos'][i])
        while (is_platforms_axis_busy() or is_table_axis_busy()) and (not context.break_proc):
            pass
        for i in range(0, 12):
            context.z_platform.stop(context.axis[i]['idx'], 3)
            context.z_platform.set_speed(context.axis[i]['idx'], context.speed_value_platform)
        context.z_table.stop(context.axis[context.y_table_i]['idx'], 3)
        context.z_table.set_speed(context.axis[context.y_table_i]['idx'], context.speed_value_platform)
    popup_close()


def connect_platform():
    if not context.platform_connect_thread.is_alive():
        context.platform_connect_thread = Thread(target=context.z_platform.connect,
                                                 args=[context.platforms_controller_ip, ], daemon=True)
        context.platform_connect_thread.start()
        return True
    return False
    # str_iplist, num = context.z_platform.search()
    # print('num=',num)
    # print('str_iplist=', str_iplist)
    # if context.z_platform.search(context.platforms_controller_ip):
    # context.z_platform.search(context.platforms_controller_ip)
    # if context.z_platform.search(context.table_controller_ip):
    # context.z_platform.search(context.table_controller_ip)
    # context.z_platform.search("192.168.0.13")


def connect_table():
    if (not context.table_connect_thread.is_alive()) and (not context.z_table.is_connected):
        context.table_connect_thread = Thread(target=context.z_table.connect, args=[context.table_controller_ip, ],
                                              daemon=True)
        context.table_connect_thread.start()
        return True
    return False


def disconnect_table():
    if context.z_table.is_connected:
        context.z_table.disconnect()


def disconnect_platform():
    if context.z_platform.is_connected:
        context.z_platform.disconnect()
        init_platforms_complete(False)


def move_axis(dir_, axis):
    # context.logger.log_warning(str(axis) + " " + str(dir_))
    # return
    if axis != -1:
        context.current_axis = axis
        if context.z_platform.is_connected:
            # print("moving on axis = ", abs(context.current_axis))
            if context.ctrl_mode == CTRL_MODE_CONT:
                context.z_platform.v_move(axis, dir_)
            else:
                context.z_platform.move(axis, dir_ * context.step_value_platform)
        else:
            context.logger.log_warning("Контроллер платформ не подключен")


def readDecValues():
    if context.z_platform.is_connected:
        for i in range(0, 13, 1):
            context.axis[i]['dec'] = context.z_platform.get_decel(context.axis[i]['idx'])


def readAccValues():
    if context.z_platform.is_connected:
        for i in range(0, 13, 1):
            context.axis[i]['acc'] = context.z_platform.get_accel(context.axis[i]['idx'])


def move_table(dir_):
    context.current_axis = AXIS_TABLE + 14
    if context.z_table.is_connected:
        if context.ctrl_mode == CTRL_MODE_CONT:
            context.z_table.v_move(AXIS_TABLE, dir_)
        else:
            context.z_table.move(AXIS_TABLE, dir_ * context.step_value_table)
    else:
        context.logger.log_warning("Контроллер стола не подключен")


def stop_cur_axis():
    if context.current_axis != -1:
        if context.current_axis < 12:
            if context.z_platform.is_connected:
                context.z_platform.stop(context.current_axis, 3)
        else:
            if context.z_table.is_connected:
                context.z_table.stop(AXIS_TABLE, 3)
    context.current_axis = -1


def get_axis_move_params(axis):
    if context.z_platform.is_connected:
        acc = context.z_platform.get_accel(axis)
        dec = context.z_platform.get_decel(axis)
    else:
        acc = -1
        dec = -1
    return acc, dec


def get_all_axis_pos():
    if context.z_platform.is_connected:
        for i in range(0, 13, 1):
            pos = context.z_platform.get_pos(context.axis[i]['idx'])
            if pos == 100000000:  # disconnected
                context.z_platform.state_changed |= 1
                context.z_platform.is_connected = False
                pos = 99999999  # '***'
            context.axis[i]['pos'] = pos

    if context.z_table.is_connected:
        pos = context.z_table.get_pos(context.axis[context.y_table_i]['idx'])
        if pos == 100000000:  # disconnected
            context.z_table.state_changed |= 1
            context.z_table.is_connected = False
            pos = 99999999  # '***'

        context.axis[context.y_table_i]['pos'] = pos
    for i in range(0, 13, 1):
        context.pos_array[i] = context.axis[i]['pos']


def is_table_axis_busy():
    is_stopped = context.z_table.is_in_motion(context.axis[12]['idx'])
    return is_stopped == 0


def is_platforms_axis_busy():
    axis_in_move = 0
    for i in range(0, 12, 1):
        is_stopped = context.z_platform.is_in_motion(context.axis[i]['idx'])
        if is_stopped == 0:
            axis_in_move += 1
    return bool(axis_in_move > 0)


def store_preset_pos(platforms):
    if context.z_platform.is_connected and context.z_table.is_connected:  # and context.platforms_initialized:
        match platforms & 0xf0:
            case 0x10:  # left platform
                for i in range(0, 6):
                    context.preset_left[platforms & 0xf]['pos'][i] = context.z_platform.get_pos(
                        context.axis[i]['idx'])
            case 0x20:  # table
                context.preset_table[platforms & 0xf]['pos'][context.y_table_i] = context.z_table.get_pos(
                    context.axis[context.y_table_i]['idx'])
            case 0x40:  # right platform
                for i in range(6, 12):
                    context.preset_right[platforms & 0xf]['pos'][i] = context.z_platform.get_pos(
                        context.axis[i]['idx'])
            case 0x80:  # all platforms
                for i in range(0, 12):
                    context.preset_all[platforms & 0xf]['pos'][i] = context.z_platform.get_pos(
                        context.axis[i]['idx'])
                context.preset_all[platforms & 0xf]['pos'][context.y_table_i] = context.z_table.get_pos(
                    context.axis[context.y_table_i]['idx'])
    save_presets()


def set_table_speed(speed_):
    if context.z_table.is_connected:
        context.z_table.set_speed(context.axis[12]['idx'], speed_)


def get_all_axis_state():
    if context.z_platform.is_connected:
        for i in range(0, 13, 1):
            context.axis[i]['state'] = context.z_platform.get_state(context.axis[i]['idx'])
    if context.z_table.is_connected:
        context.axis[context.y_table_i]['state'] = context.z_table.get_state(context.axis[context.y_table_i]['idx'])


def set_platforms_speed(speed_):
    if context.z_platform.is_connected:
        for i in range(0, 12, 1):
            context.z_platform.set_speed(i, speed_)
