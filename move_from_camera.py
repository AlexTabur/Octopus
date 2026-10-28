from axis_ctrl import is_platforms_axis_busy
from core.utils import *
from core.consts import *
import time
import statistics


def points_to_k_b(point0, point1):
    x_, y_ = point0
    x_2, y_2 = point1
    try:
        dx = x_2 - x_
        dy = y_2 - y_
        angle = np.arctan2(dy, dx) * 180 / np.pi
        return 0, 0, angle
    except Exception as e:
        print(e)
        return 0, 0, 0


def focus_side_view():
    focus_array_y = []
    focus_array_x = []
    context.z_table.move(AXIS_TABLE, 6000 / UM_PER_STEP_TABLE)
    if context.moving_right:
        focus = context.focus_side_view_r
    else:
        focus = context.focus_side_view_l
    while len(focus_array_y) < 150 and not context.break_proc:

        context.z_table.move(AXIS_TABLE, -200 / UM_PER_STEP_TABLE)
        while context.z_table.is_in_motion(AXIS_TABLE) == 0:
            pass
        a = context.z_table.get_pos(AXIS_TABLE)
        b = focus.value
        focus_array_x.append(a)
        focus_array_y.append(b)
    if not context.break_proc:
        index = np.argmax(focus_array_y)
        coord = focus_array_x[index]
        context.z_table.move_to(AXIS_TABLE, coord)
    context.break_proc = False


def get_angles():
    td = context.camera_points_td[:]
    sv = context.camera_points_sv[:]
    context.camera_angles_sv[0], context.camera_angles_sv[1] = get_angles2(sv)
    context.camera_angles_td[0], context.camera_angles_td[1] = get_angles2(td)


def get_angles2(pos):
    k, b, a0 = points_to_k_b((pos[0], pos[1]), (pos[2], pos[3]))
    k, b, a1 = points_to_k_b((pos[4], pos[5]), (pos[6], pos[7]))
    return a0, a1


def move_table_(d):
    context.z_table.move(AXIS_TABLE, d / UM_PER_STEP_TABLE)


def move_(axis, d):
    if context.moving_right:
        axis = context.axis[axis + 6]['idx']
    else:
        axis = context.axis[axis]['idx']
    if axis != -1:
        context.current_axis = axis
        if context.z_platform.is_connected:
            context.z_platform.move(axis, d * STEP_PER[axis])
    else:
        context.logger.log_warning(str(axis) + " " + str(dir))


def move_y():
    uchet = 20
    # 1) A = в move_y() запоминаем абсолютное положение фавов. Готово
    # 2) C = в move_y() запоминаем x, y стрипа 8 канал. Готово
    x1, y1 = context.camera_points_td[4 * 2], context.camera_points_td[4 * 2 + 1]
    x2, y2 = context.camera_points_td[5 * 2], context.camera_points_td[5 * 2 + 1]
    dx = x2 - x1
    dy = y2 - y1
    if context.moving_right:
        # for next_chip()  --START--
        context.C_r = [x1, y1, 0, 0, 0, 0]
        context.A_r = get_axis_platforms(True)
        print("A_r", context.A_r)
        # --END --
        move_(1, -dy / PIX_PER_UM)
        move_(0, dx / PIX_PER_UM - uchet)
        move_(1, -10)
        # move_(1, -100)  # Переезжаем на 40 мкм
    else:
        # for next_chip() --START--
        context.C_l = [x2, y2, 0, 0, 0, 0]
        context.A_l = get_axis_platforms(False)
        print("A_l", context.A_l)
        # --END--
        move_(1, dy / PIX_PER_UM)
        move_(0, dx / PIX_PER_UM - 0)  # uchet)
        move_(1, -40)
        # move_(1, 50)  # Переезжаем на 40 мкм
        if hasattr(context, "anchor_l_z"):
            context.z_platform.move_to(1, context.anchor_l_z)


def move_z():
    n = 4
    x1, y1 = context.camera_points_sv[n * 2], context.camera_points_sv[n * 2 + 1]
    n = 5
    x2, y2 = context.camera_points_sv[n * 2], context.camera_points_sv[n * 2 + 1]
    dz = y2 - y1
    if context.moving_right:
        move_(2, dz / PIX_PER_UM)
    else:
        move_(2, -dz / PIX_PER_UM)
    move_(1, -9608)


def rotate_y(poputka=3, num_samples=20, delay_between_samples=0.2):
    context.logger.log("тангаж")
    for i in range(poputka):
        dx_values = []
        for _ in range(num_samples):
            dx_raw = context.camera_angles_sv[1] - context.camera_angles_sv[0]
            dx_values.append(dx_raw)
            time.sleep(delay_between_samples)

        dx_stable = statistics.median(dx_values)
        context.logger.log(f"Угол для поворота: {dx_stable:.4f}")

        if context.moving_right:
            move_(4, dx_stable)
        else:
            move_(4, dx_stable)

        while is_platforms_axis_busy():
            time.sleep(0.05)

        time.sleep(1.2)


"""def rotate_y(poputka=8, pogreshnost=0.02):
    for i in range(poputka):

        dx = context.camera_angles_sv[1] - context.camera_angles_sv[0]
        if abs(dx) <= pogreshnost:
            break

        if context.moving_right:
            move_(4, dx)
        else:
            move_(4, dx)

        while is_platforms_axis_busy():
            time.sleep(0.05)

        time.sleep(1.2)

    else:
        print("Максимально одинаковый угол достигнут")"""


def rotate_z():
    angle1 = context.camera_angles_td[1] - context.camera_angles_td[0]
    if context.moving_right:
        move_(5, -angle1)
    else:
        move_(5, -angle1)


def get_axis_platforms(right):
    a = []
    offset = 0
    if right:
        offset = 6
    for i in range(6):
        a.append(context.z_platform.get_pos(i + offset))

    return a


def next_chip(up=True):
    chip_length = 15600
    table_angle = 89.4712502
    context.B_l = get_axis_platforms(False)
    context.B_r = get_axis_platforms(True)
    i = 2
    context.z_platform.move_to(i, context.A_r[i])
    context.z_platform.move_to(i + 6, context.A_l[i])
    i = 1
    context.z_platform.move_to(i, context.A_l[i])
    ugol = np.deg2rad(context.strip_angle - table_angle)
    dist_1 = chip_length * np.cos(ugol)
    if up:
        dist_1 *= -1
    dist = dist_1 / UM_PER_STEP_TABLE
    context.pmap_procedures.wait_for_hardware()
    context.z_table.move(1, dist)
