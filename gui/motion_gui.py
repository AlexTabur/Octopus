import threading
from threading import Timer
from time import sleep

from pynput import keyboard
from win32gui import GetWindowText, GetForegroundWindow

import axis_ctrl
from camera.CameraParams_header import *
from camera.MvCameraControl_class import *
from camera.MvErrorDefine_const import *
from camera.scratch import get_y, Mono_numpy, display_img, isHorizontal
from core.gui_helper import *
from core.utils import *

context = Context()


def init_setting_page():
    with dpg.group(horizontal=True):
        with dpg.group():
            dpg.add_text(default_value=txt.LEFT_PLATFORM)
            dpg.add_text(default_value="               Acc     Dec")
            for i in range(0, 6, 1):
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value=context.axis[i]['label'])
                    context.editor_list.append(context.axis[i]['name'] + "Acc")
                    dpg.add_input_text(label="", tag=context.axis[i]['name'] + "Acc", decimal=True,
                                       default_value="0", width=50)
                    context.editor_list.append(context.axis[i]['name'] + "Dec")
                    dpg.add_input_text(label="", tag=context.axis[i]['name'] + "Dec", decimal=True,
                                       default_value="0", width=50)
                    dpg.add_button(label=txt.SET_BTN, height=22, width=100)
            dpg.add_spacer(height=5)
        dpg.add_spacer(width=20)
        with dpg.group():
            dpg.add_text(default_value=txt.RIGHT_PLATFORM)
            dpg.add_text(default_value="               Acc     Dec")
            for i in range(6, 12, 1):
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value=context.axis[i]['label'])
                    context.editor_list.append(context.axis[i]['name'] + "Acc")
                    dpg.add_input_text(label="", tag=context.axis[i]['name'] + "Acc", decimal=True,
                                       default_value="0", width=50)
                    context.editor_list.append(context.axis[i]['name'] + "Dec")
                    dpg.add_input_text(label="", tag=context.axis[i]['name'] + "Dec", decimal=True,
                                       default_value="0", width=50)
                    dpg.add_button(label=txt.SET_BTN, height=22, width=100)
            dpg.add_spacer(height=5)
        with dpg.group():
            dpg.add_text(default_value=txt.TABLE)
            dpg.add_text(default_value="      Acc     Dec")
            with dpg.group(horizontal=True):
                dpg.add_text(default_value=context.axis[12]['label'])
                context.editor_list.append(context.axis[12]['name'] + "Acc")
                dpg.add_input_text(label="", tag=context.axis[12]['name'] + "Acc", decimal=True, default_value="0",
                                   width=50)
                context.editor_list.append(context.axis[12]['name'] + "Dec")
                dpg.add_input_text(label="", tag=context.axis[12]['name'] + "Dec", decimal=True, default_value="0",
                                   width=50)
                dpg.add_button(label=txt.SET_BTN, height=22, width=100)
            dpg.add_spacer(height=5)


def set_step_value(steps_um: float):
    steps = int(steps_um / X_MKM_KOEF)
    steps_um = steps * X_MKM_KOEF
    dpg.set_value("SliderStep", steps_um)
    dpg.set_value("EditStep", steps_um)  # steps_um = steps * X_MKM_KOEF
    dpg.set_value("StepValue", str(steps) + ' шагов')
    context.step_value_platform = int(steps)  # установка скорости на все оси платформы
    steps = int(steps_um / TABLE_MKM_KOEF)
    context.step_value_table = int(steps)  # ?????????????????
    save_prameters()


def set_speed_value(speed: int):
    dpg.set_value("SliderSpeed", speed)
    dpg.set_value("EditSpeed", speed)
    dpg.set_value("SpeedValue", "X,Y,Z лин = " + str(speed * NM_PER_STEP_X / 1000) + ' ' + txt.SET_LIN_SPEED_DIM)
    context.speed_value_platform = speed
    context.zcontrollers.set_platforms_speed(speed)  # установка скорости на все оси платформы
    context.zcontrollers.set_table_speed(speed)  # установка скорости на все оси платформы
    save_prameters()


def movement_by_keys(key_vk, key, ctrl, alt):
    if not ctrl and not alt:
        return
    #        for editor in context.editor_list:
    #            if dpg.is_item_focused(editor):
    #                return
    # Left platform
    if not context.lock_left_side:
        if key_vk == 65:  # A
            if ctrl:  # Y Rotate
                context.zcontrollers.move_axis(int(context.axis[context.y1_ang_i]['dir_bw']),
                                               context.axis[context.y1_ang_i]['idx'])
            else:  # X Left
                context.zcontrollers.move_axis(int(context.axis[context.x1_line_i]['dir_bw']),
                                               context.axis[context.x1_line_i]['idx'])
        elif key_vk == 68:  # D
            if ctrl:  # Y Rotate
                context.zcontrollers.move_axis(int(context.axis[context.y1_ang_i]['dir_fw']),
                                               context.axis[context.y1_ang_i]['idx'])
            else:  # X Right
                context.zcontrollers.move_axis(int(context.axis[context.x1_line_i]['dir_fw']),
                                               context.axis[context.x1_line_i]['idx'])

        elif key_vk == 87:  # W
            if ctrl:  # X Rotate
                context.zcontrollers.move_axis(int(context.axis[context.x1_ang_i]['dir_fw']),
                                               context.axis[context.x1_ang_i]['idx'])
            else:  # Y Up
                context.zcontrollers.move_axis(int(context.axis[context.y1_line_i]['dir_fw']),
                                               context.axis[context.y1_line_i]['idx'])
        elif key_vk == 83:  # S
            if ctrl:  # X Rotate
                context.zcontrollers.move_axis(int(context.axis[context.x1_ang_i]['dir_bw']),
                                               context.axis[context.x1_ang_i]['idx'])
            else:  # Y Down
                context.zcontrollers.move_axis(int(context.axis[context.y1_line_i]['dir_bw']),
                                               context.axis[context.y1_line_i]['idx'])
        elif key_vk == 81:  # Q -  Z Up
            if ctrl:  # Z Rotate
                context.zcontrollers.move_axis(int(context.axis[context.z1_ang_i]['dir_fw']),
                                               context.axis[context.z1_ang_i]['idx'])
            else:
                context.zcontrollers.move_axis(int(context.axis[context.z1_line_i]['dir_fw']),
                                               context.axis[context.z1_line_i]['idx'])
        elif key_vk == 90:  # Z -  Z Down
            if not ctrl:
                context.zcontrollers.move_axis(int(context.axis[context.z1_line_i]['dir_bw']),
                                               context.axis[context.z1_line_i]['idx'])

        elif ctrl and key_vk == 69:  # 'c' # Z CCW
            context.zcontrollers.move_axis(int(context.axis[context.z1_ang_i]['dir_bw']),
                                           context.axis[context.z1_ang_i]['idx'])
    # Right platform
    if not context.lock_right_side:
        if key == keyboard.Key.left:
            if ctrl:  # Y Rotate
                context.zcontrollers.move_axis(int(context.axis[context.y2_ang_i]['dir_bw']),
                                               context.axis[context.y2_ang_i]['idx'])
            else:  # X Left
                context.zcontrollers.move_axis(int(context.axis[context.x2_line_i]['dir_bw']),
                                               context.axis[context.x2_line_i]['idx'])
        elif key == keyboard.Key.right:
            if ctrl:  # Y Rotate
                context.zcontrollers.move_axis(int(context.axis[context.y2_ang_i]['dir_fw']),
                                               context.axis[context.y2_ang_i]['idx'])
            else:  # X Right
                context.zcontrollers.move_axis(int(context.axis[context.x2_line_i]['dir_fw']),
                                               context.axis[context.x2_line_i]['idx'])
        elif key == keyboard.Key.up:
            if ctrl:  # X Rotate
                context.zcontrollers.move_axis(int(context.axis[context.x2_ang_i]['dir_fw']),
                                               context.axis[context.x2_ang_i]['idx'])
            else:  # Y Up
                context.zcontrollers.move_axis(int(context.axis[context.y2_line_i]['dir_fw']),
                                               context.axis[context.y2_line_i]['idx'])
        elif key == keyboard.Key.down:  # Y Down
            if ctrl:  # X Rotate
                context.zcontrollers.move_axis(int(context.axis[context.x2_ang_i]['dir_bw']),
                                               context.axis[context.x2_ang_i]['idx'])
            else:  # Y Down
                context.zcontrollers.move_axis(int(context.axis[context.y2_line_i]['dir_bw']),
                                               context.axis[context.y2_line_i]['idx'])
        elif key == keyboard.Key.home:  # Z Up
            if ctrl:
                context.zcontrollers.move_axis(int(context.axis[context.z2_ang_i]['dir_fw']),
                                               context.axis[context.z2_ang_i]['idx'])
            else:
                context.zcontrollers.move_axis(int(context.axis[context.z2_line_i]['dir_fw']),
                                               context.axis[context.z2_line_i]['idx'])
        elif key == keyboard.Key.end:  # Z Down
            if not ctrl:
                context.zcontrollers.move_axis(int(context.axis[context.z2_line_i]['dir_bw']),
                                               context.axis[context.z2_line_i]['idx'])
        elif ctrl and key == keyboard.Key.page_up:  # NUM 9 # Z CCW
            context.zcontrollers.move_axis(int(context.axis[context.z2_ang_i]['dir_bw']),
                                           context.axis[context.z2_ang_i]['idx'])
    # Table platform
    if key_vk == 74:  # 'J'
        if not ctrl:
            context.zcontrollers.move_table(int(context.axis[context.y_table_i]['dir_fw']))
    elif key_vk == 85:  # ('U')
        if not ctrl:
            context.zcontrollers.move_table(int(context.axis[context.y_table_i]['dir_bw']))


def get_axis_params():
    context.zcontrollers.get_axis_move_params(AXIS_L_X)
    for i in range(0, 13, 1):
        dpg.set_value(context.axis[i]['name'] + "Acc", context.axis[i]['acc'])
        dpg.set_value(context.axis[i]['name'] + "Dec", context.axis[i]['dec'])


class MotionGUI:

    def __init__(self):

        self.lines_2 = None
        self.moving_y = False
        self.y1 = 0
        self.y2 = 0
        self.max_y = 0
        self.min_y = 5000
        self.center_y = 0
        self.pos_1 = None
        self.pos_2 = None
        self.pos_3 = None
        self.pos_4 = None
        self.prev_len = 0
        self.moving_z2 = False
        self.pix_per_step = 500
        self.get_pix_per_step = False
        self.prev_x = None
        self.moving_right = False
        self.moving_z1 = False
        self.h1k = None
        self.h2k = None
        self.v1k = None
        self.v2k = None
        self.h1b = None
        self.h2b = None
        self.v1b = None
        self.v2b = None
        self.fixed = False
        self.lines_ = []
        self.buf_grab_image = None
        self.platform_list = [txt.LEFT, txt.RIGHT]
        self.move_mode_list = [txt.CONTINUES_MODE, txt.STEP_MODE]
        self.step_slider_id = 1
        self.speed_slider_id = 2
        context.zcontrollers = axis_ctrl.PlatformController()
        self.width_end = 0
        self.height_end = 0
        self.data_end = 0
        self.width_xyz = 0
        self.height_xyz = 0
        self.data_xy = 0
        self.data_z = 0
        self.width_table = 0
        self.height_table = 0
        self.data_table = 0
        self.magnification = 5
        self.width_btn = 0

        self.height_btn = 0
        self.thread_proc = 0
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.buf_save_image = None
        self.angle1 = 0
        self.angle2 = 0
        self.angle3 = 0
        self.angle4 = 0
        self.buf_grab_image_size = 0
        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()
        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, self.deviceList)
        stDeviceList = cast(self.deviceList.pDeviceInfo[int(0)],
                            POINTER(MV_CC_DEVICE_INFO)).contents
        self.obj_cam = MvCamera()
        self.obj_cam.MV_CC_CreateHandle(stDeviceList)
        self.obj_cam.MV_CC_OpenDevice()
        self.obj_cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        self.obj_cam.MV_CC_SetImageNodeNum(2)
        self.obj_cam.MV_CC_StartGrabbing()
        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()
        self.img_buff = None
        self.numArray = None
        stPayloadSize = MVCC_INTVALUE_EX()
        ret_temp = self.obj_cam.MV_CC_GetIntValueEx("PayloadSize", stPayloadSize)
        if ret_temp != MV_OK:
            return
        self.NeedBufSize = int(stPayloadSize.nCurValue)
        self.val = 100
        self.val2 = 3
        self.rho = 200
        self.theta = np.pi / 180
        self.n_w, self.n_h = 5120, 5120
        self.width = int(self.n_w * self.val / 100)
        self.minLineLength = 10 / 1000 * self.width
        self.maxLineGap = 0.5 / 100 * self.width
        self.c_x, self.c_y = int(self.width / 2), int(self.width / 2)
        self.mask = cv2.circle(np.zeros((int(5120 * self.val / 100), int(5120 * self.val / 100)), dtype="uint8"),
                               (self.c_x, self.c_y), self.c_x - 300, 255, -1)
        self.last_photo_taken = time.time()
        if self.buf_grab_image_size < self.NeedBufSize:
            self.buf_grab_image = (self.NeedBufSize * ctypes.c_ubyte)()
            self.buf_grab_image_size = self.NeedBufSize
        thread = threading.Thread(target=self.run_task, args=(), daemon=True)
        thread.start()

    def move_(self, axis, d):
        if self.moving_right:
            axis = context.axis[axis - 1 + 6]['idx']
        else:
            axis = context.axis[axis - 1]['idx']
        if axis != -1:
            context.current_axis = axis
            if context.zplatform.is_connected:
                # print("moving on axis = ", abs(context.current_axis))
                context.zplatform.move(axis, d * 8)
            else:
                print("not connected")

    def rotate_z(self, right):
        if right:
            axis = context.axis[context.z2_ang_i]['idx']
        else:
            axis = context.axis[context.z1_ang_i]['idx']
        angle1 = self.angle2 - self.angle1
        # context.logger.log_warning(str(axis) + " " + str(dir))
        # return

        if axis != -1:
            context.current_axis = axis
            if context.zplatform.is_connected:
                print(angle1)
                context.zplatform.move(axis, STEP_PER_GRAD_Z * angle1)
            else:
                print("not connected")

    def move_z1(self, right):
        self.moving_z1 = True
        self.moving_right = right

    def move_z2(self, right):
        self.moving_z2 = True
        self.moving_right = right

    def move_y(self, right):
        self.moving_y = True
        self.moving_right = right

    def move_x(self, right):
        self.moving_right = right
        offset = 100
        if right:
            self.move_(1, (self.v2b - self.v1b) / np.sqrt(self.v1k ** 2 + 1) - offset)
        else:
            self.move_(1, (self.v2b - self.v1b) / np.sqrt(self.v2k ** 2 + 1) - offset)

    def set_pix_per_step(self, sender, app_data, user_data):
        prev_x = (self.v2b - self.v1b) / np.sqrt(self.v1k ** 2 + 1)
        print("prev: ", prev_x)
        if user_data:
            axis = context.axis[context.x2_line_i]['idx']
        else:
            axis = context.axis[context.x1_line_i]['idx']
        if axis != -1:
            context.current_axis = axis
            if context.zplatform.is_connected:
                # print("moving on axis = ", abs(context.current_axis))
                context.zplatform.move(axis, -200 * 8)

            else:
                print("not connected")

        sleep(3)
        x = (self.v2b - self.v1b) / np.sqrt(self.v1k ** 2 + 1)
        self.pix_per_step = np.abs(x - prev_x) / (8 * 200)
        print("pix per step", self.pix_per_step)


    def click_callback(self):
        a = np.array(dpg.get_mouse_pos(local=False))
        b = np.array(dpg.get_item_pos("group_123"))
        if self.pos_1 is None:
            self.pos_1 = a - b

        elif self.pos_2 is None:
            self.pos_2 = a - b

        elif self.pos_3 is None:
            self.pos_3 = a - b

        elif self.pos_4 is None:
            self.pos_4 = a - b

        else:
            self.pos_1 = None
            self.pos_2 = None
            self.pos_3 = None
            self.pos_4 = None

    def run_task(self):
        while True:
            self.obj_cam.MV_CC_GetOneFrameTimeout(self.buf_grab_image, self.buf_grab_image_size, self.stFrameInfo)

            resized = Mono_numpy(self.buf_grab_image, self.n_w, self.n_h)[:1000, :1000]
            normalized_image = resized.copy()

            final = cv2.cvtColor(normalized_image, cv2.COLOR_GRAY2RGB)
            if self.pos_1 is not None and self.pos_2 is not None and self.pos_3 is not None and self.pos_4 is not None:
                a = (self.pos_1 / 400 * 1000).astype(int)
                b = (self.pos_2 / 400 * 1000).astype(int)
                c = (self.pos_3 / 400 * 1000).astype(int)
                d = (self.pos_4 / 400 * 1000).astype(int)
                x1, y1 = a
                x2, y2 = b
                x3, y3 = c
                x4, y4 = d
                th1 = 3.8 * 255  # dpg.get_value("th1")
                th2 = 3.9 * 255  # dpg.get_value("th2")
                # print(x1, y1, x2, y2, x3, y3, x4, y4)
                chip_img = resized[y3:y4, x3:x4].copy()
                resized = resized[y1:y2, x1:x2]
                cv2.normalize(chip_img, chip_img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
                cv2.normalize(resized, resized, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
                detector = cv2.ximgproc.createFastLineDetector(length_threshold=int(self.minLineLength),
                                                               distance_threshold=int(self.maxLineGap),
                                                               canny_th1=th1,
                                                               canny_th2=th2,
                                                               canny_aperture_size=5, do_merge=True)
                self.lines_ = detector.detect(resized)
                self.lines_2 = detector.detect(chip_img)
                resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
                chip_img = cv2.cvtColor(chip_img, cv2.COLOR_GRAY2RGB)
                vertical_1_x = []
                vertical_1_y = []
                vertical_2_x = []
                vertical_2_y = []
                horizontal_1_x = []
                horizontal_1_y = []
                horizontal_2_x = []
                horizontal_2_y = []

                if self.lines_ is not None:
                    if len(self.lines_) > 1:
                        for line in self.lines_:
                            line_ = line[0]
                            if isHorizontal(line_):
                                if line_[0] < line_[2]:
                                    horizontal_1_x.append(line_[0])
                                    horizontal_1_y.append(line_[1])
                                    horizontal_1_x.append(line_[2])
                                    horizontal_1_y.append(line_[3])
                                else:
                                    horizontal_1_x.append(line_[2])
                                    horizontal_1_y.append(line_[3])
                                    horizontal_1_x.append(line_[0])
                                    horizontal_1_y.append(line_[1])
                            else:
                                vertical_1_x.append(line_[0])
                                vertical_1_y.append(line_[1])
                                vertical_1_x.append(line_[2])
                                vertical_1_y.append(line_[3])

                if self.lines_2 is not None:
                    if len(self.lines_2) > 1:
                        for line in self.lines_2:
                            line__ = line[0]
                            if isHorizontal(line__):
                                if line__[0] < line__[2]:
                                    horizontal_2_x.append(line__[0])
                                    horizontal_2_y.append(line__[1])
                                    horizontal_2_x.append(line__[2])
                                    horizontal_2_y.append(line__[3])
                                else:
                                    horizontal_2_x.append(line__[2])
                                    horizontal_2_y.append(line__[3])
                                    horizontal_2_x.append(line__[0])
                                    horizontal_2_y.append(line__[1])
                            else:
                                vertical_2_x.append(line__[0])
                                vertical_2_y.append(line__[1])
                                vertical_2_x.append(line__[2])
                                vertical_2_y.append(line__[3])

                for i in range(len(vertical_1_x)):
                    vertical_1_x[i] += x1
                for i in range(len(vertical_1_y)):
                    vertical_1_y[i] += y1
                for i in range(len(horizontal_1_x)):
                    horizontal_1_x[i] += x1
                for i in range(len(horizontal_1_y)):
                    horizontal_1_y[i] += y1
                for i in range(len(vertical_2_x)):
                    vertical_2_x[i] += x3
                for i in range(len(vertical_2_y)):
                    vertical_2_y[i] += y3
                for i in range(len(horizontal_2_x)):
                    horizontal_2_x[i] += x3
                for i in range(len(horizontal_2_y)):
                    horizontal_2_y[i] += y3
                if len(vertical_1_x) > 0:
                    m, b = np.polyfit(vertical_1_y, vertical_1_x, 1)
                    self.angle1 = np.atan(m) * 180 / np.pi
                    cv2.line(final, (int(get_y(0, m, b)), 0),
                             (int(get_y(int(self.width), m, b)), int(self.width)),
                             (0, 255, 0),
                             int(1))  # 0.1 * self.val
                    self.v1b = b
                    self.v1k = m
                if len(vertical_2_x) > 0:
                    m, b = np.polyfit(vertical_2_y, vertical_2_x, 1)
                    self.angle2 = np.atan(m) * 180 / np.pi
                    cv2.line(final, (int(get_y(0, m, b)), 0),
                             (int(get_y(int(self.width), m, b)), int(self.width)),
                             (0, 255, 0),
                             int(1))  # 0.1 * self.val
                    self.v2b = b
                    self.v2k = m
                for i in range(0, len(horizontal_1_x), 2):
                    cv2.line(final, (int(horizontal_1_x[i]), int(horizontal_1_y[i])),
                             (int(horizontal_1_x[i + 1]), int(horizontal_1_y[i + 1])),
                             (255, 0, 0), int(1))  # 0.1 * self.val
                for i in range(0, len(horizontal_2_x), 2):
                    cv2.line(final, (int(horizontal_2_x[i]), int(horizontal_2_y[i])),
                             (int(horizontal_2_x[i + 1]), int(horizontal_2_y[i + 1])),
                             (255, 0, 0), int(1))  # 0.05 * self.val

                if self.moving_z1:
                    if self.moving_right:
                        if len(vertical_2_x) < 1:
                            self.move_(3, 3)

                        else:
                            self.moving_z1 = False
                            self.move_(3, 20)
                    else:
                        if len(vertical_1_x) < 1:
                            self.move_(3, 1)
                        else:
                            if len(horizontal_1_y) > 0:
                                min_y = np.min(horizontal_1_y)
                                max_y = np.max(horizontal_1_y)
                                self.min_y = min(min_y, self.min_y)
                                self.max_y = max(max_y, self.max_y)
                                self.center_y = (self.max_y + self.min_y) / 2
                                self.y1 = self.center_y
                            self.moving_z1 = False
                            self.move_(3, 20)

                if self.moving_z2:
                    self.move_(3, 700)
                    self.moving_z2 = False

                if self.moving_y:
                    min_dy = 1000
                    if self.moving_right:
                        if len(horizontal_2_y) > 1:
                            for i in range(0, len(horizontal_1_y), 2):
                                cv2.line(chip_img, (int(horizontal_1_x[i]), int(horizontal_1_y[i])),
                                         (int(horizontal_1_x[i + 1]), int(horizontal_1_y[i + 1])),
                                         (255, 255, 0), int(1))  # 0.2 * self.val
                                j = (len(horizontal_2_y) - 1) // 4 * 2
                                dy = horizontal_2_y[j] - horizontal_1_y[i]
                                if abs(dy) < abs(min_dy):
                                    min_dy = dy
                    else:
                        if len(horizontal_1_y) > 1:
                            for i in range(0, len(horizontal_2_y), 2):
                                cv2.line(resized, (int(horizontal_2_x[i]), int(horizontal_2_y[i])),
                                         (int(horizontal_2_x[i + 1]), int(horizontal_2_y[i + 1])),
                                         (255, 255, 0), int(1))  # 0.2 * self.val
                                j = (len(horizontal_1_y) - 1) // 4 * 2
                                dy = horizontal_2_y[i] - horizontal_1_y[j]
                                if abs(dy) < abs(min_dy):
                                    min_dy = dy
                    print(min_dy)
                    if 1000 > abs(min_dy):
                        self.move_(2, (min_dy) / self.pix_per_step - 127/2)
                        self.moving_y = False
                        self.move_(3, 400 - 200 + 34)

                cv2.line(resized, (int(0), int(self.y1)),
                         (int(self.c_x), int(self.y1)),
                         (255, 255, 0), int(1))
                cv2.line(resized, (int(0), int(self.y2)),
                         (int(self.c_x), int(self.y2)),
                         (255, 255, 0), int(1))  # 0.05 * self.val

                # final[y1:y2, x1:x2] = resized
                # final[y3:y4, x3:x4] = chip_img
                # cv2.rectangle(final, a, b, (0, 255, 255), int(0.05 * self.val))
            # z right -8002.0 -2402.0 -802.0 bruh 135.0
            display_img("camera_1", cv2.resize(final, (400, 400), interpolation=cv2.INTER_AREA))

    @staticmethod
    def loop():
        if context.zplatform.state_changed & 1:
            context.zplatform.state_changed &= 0xFE
            if context.zplatform.is_connected:
                context.gui_hlp.set_conn_states("platform_ctrl_state", "platform_conn_btn", 1)
                context.zcontrollers.set_platforms_speed(
                    context.speed_value_platform)  # установка скорости на все оси платформы
                context.logger.log_com("Контроллер платформ подключен")
            #                self.get_axis_params()
            else:
                context.gui_hlp.set_conn_states("platform_ctrl_state", "platform_conn_btn", 0)
                context.logger.log_com("Контроллер платформ отключен")

        if context.ztable.state_changed & 1:
            context.ztable.state_changed &= 0xFE
            if context.ztable.is_connected:
                context.gui_hlp.set_conn_states("table_ctrl_state", "table_conn_btn", 1)
                context.zcontrollers.set_table_speed(
                    context.speed_value_platform)  # установка скорости на все оси платформы
                context.logger.log_com("Контроллер стола подключен")
            #                self.get_axis_params()
            else:
                context.gui_hlp.set_conn_states("table_ctrl_state", "table_conn_btn", 0)
                context.logger.log_com("Контроллер стола отключен")

    # display_img("camera_1", cv2.resize(cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB), (400, 400)))

    def btn_init_plaform_click(self, sender, app_data, user_data):
        context.gui_hlp.showMessage(txt.PLATFORM_INIT_MSG, txt.BREAK, DLG_CT_BREAK_PROC)
        self.thread_proc = threading.Thread(target=context.zcontrollers.platforms_homing2, args=[], daemon=True)
        self.thread_proc.start()

    def btn_move_to_preset_click(self, sender, app_data, user_data):
        context.gui_hlp.showMessage(txt.PLATFORM_POSITIONING_MSG, txt.BREAK, DLG_CT_BREAK_PROC)
        if user_data & 0x10:  # left platform
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_platform_to_preset, args=[user_data],
                                                daemon=True)
        elif user_data & 0x20:  # table platform
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_table_to_preset, args=[user_data],
                                                daemon=True)
        elif user_data & 0x40:  # right platform
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_platform_to_preset, args=[user_data],
                                                daemon=True)
        elif user_data & 0x80:  # all platform
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_all_to_preset, args=[user_data],
                                                daemon=True)
        self.thread_proc.start()

    def step_edit_callback(self, sender, app_data, user_data):
        steps = dpg.get_value("EditStep")
        if steps.replace('.', '', 1).isdigit():
            set_step_value(float(steps))
        else:
            steps = dpg.get_value('SliderStep')
            set_step_value(float(steps))

    def speed_edit_callback(self, sender, app_data, user_data):
        speed = dpg.get_value("EditSpeed")
        speed = re.sub(r'\D', '', speed)
        if speed.isdigit():
            set_speed_value(int(speed))
        else:
            speed = dpg.get_value('SliderSpeed')
            set_speed_value(int(speed))

    def btn_store_as_preset(self, sender, app_data, user_data):
        context.zcontrollers.store_preset_pos(user_data)
        save_presets()

    def rb_move_mode_click(self, sender, app_data, user_data):
        if dpg.get_value("rb_move_mode_sel") == self.move_mode_list[CTRL_MODE_CONT]:
            context.ctrl_mode = CTRL_MODE_CONT  # выбрали непрерывный режим перемещения
        else:
            context.ctrl_mode = CTRL_MODE_STEP  # выбрали пошаговый режим перемещения

    def timer_read_axis(self):
        if context.current_proc == 0:
            context.zcontrollers.get_all_axis_pos()
            context.zcontrollers.get_all_axis_state()
            # f context.zplatform.is_connected:
            for i in range(0, 13, 1):
                dpg.set_value(context.axis[i]['name'], context.axis[i]['pos'])
                self.process_state(i)

        context.t = Timer(1, self.timer_read_axis)
        context.t.start()

    def process_state(self, axis_i):
        state = int(context.axis[axis_i]['state'])
        dir_ = context.axis[axis_i]['dir_fw']
        if dir_ > 0 and axis_i != context.y_table_i:
            pos_v = "txt_p"
            neg_v = "txt_m"
            _pv = "img_d_p"
            _nv = "img_d_m"
        else:
            pos_v = "txt_m"
            neg_v = "txt_p"
            _pv = "img_d_m"
            _nv = "img_d_p"
        if state & 0x10:  # Positive limit
            dpg.set_value(context.axis[axis_i][pos_v], self.data_end)
        else:
            dpg.set_value(context.axis[axis_i][pos_v], context.axis[axis_i][_pv])

        if state & 0x20:  # Negative limit
            # f context.axis[axis_i]["txt_m"]:
            dpg.set_value(context.axis[axis_i][neg_v], self.data_end)
        else:
            dpg.set_value(context.axis[axis_i][neg_v], context.axis[axis_i][_nv])

    def btn_connect_platform_callback(self, sender, app_data, user_data):
        if user_data == 1:
            context.zcontrollers.disconnect_platform()
        elif user_data == 0:
            if context.zcontrollers.connect_platform():
                context.gui_hlp.set_conn_states("platform_ctrl_state", "platform_conn_btn", 2)

    def btn_connect_table_callback(self, sender, app_data, user_data):
        if user_data == 1:
            context.zcontrollers.disconnect_table()
        elif user_data == 0:
            if context.zcontrollers.connect_table():
                context.gui_hlp.set_conn_states("table_ctrl_state", "table_conn_btn", 2)

    def on_key_down_callback(self, key):
        if context.current_axis != -1:
            return
        if GetWindowText(GetForegroundWindow()) != txt.MAIN_TITLE:  # or dpg.get_value(context.tabBar)!=TAB_MANUAL_ID:
            return

        #        context.logger.log('alphanumeric key {0} pressed'.format(key.vk))
        if key == keyboard.Key.ctrl_r or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl:
            self.ctrl_pressed = True

        # Show hotkeys
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt or key == keyboard.Key.alt_gr:
            self.alt_pressed = True
            for i in range(0, 26):
                dpg.show_item(str(i) + '_hint')
        elif context.ctrl_by_keyboard:
            if type(key) is keyboard.KeyCode:
                key_vk = key.vk
            else:
                key_vk = 0
            movement_by_keys(key_vk, key, self.ctrl_pressed, self.alt_pressed)

    def on_key_release_callback(self, key):
        #        context.logger.log('Released')
        if key == keyboard.Key.ctrl_r or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl:
            self.ctrl_pressed = False
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt or key == keyboard.Key.alt_gr:
            self.alt_pressed = False
            for i in range(0, 26):
                dpg.hide_item(str(i) + '_hint')
        elif context.current_axis != -1:
            if context.ctrl_mode == CTRL_MODE_CONT:
                context.zcontrollers.stop_cur_axis()
            context.current_axis = -1

    def item_down_callback(self, sender, app_data, user_data):
        if context.current_axis != -1:
            return
        context.current_axis = -1
        # - УПРАВЛЕНИЕ ПЛАТФОРМАМИ ------------------------------------------
        for ax in context.axis:
            if (not context.lock_left_side or ax['side'] != 0) and (not context.lock_right_side or ax['side'] != 1):
                if dpg.is_item_hovered(ax['name'] + 'bnt_p'):
                    if ax['controler'] == 1:
                        context.zcontrollers.move_axis(int(ax['dir_fw']), ax['idx'])
                    elif ax['controler'] == 2:
                        context.zcontrollers.move_table(-1)
                    return

                if dpg.is_item_hovered(ax['name'] + 'bnt_m'):
                    if ax['controler'] == 1:
                        context.zcontrollers.move_axis(int(ax['dir_bw']), ax['idx'])
                    elif ax['controler'] == 2:
                        context.zcontrollers.move_table(1)
                    return
        if dpg.is_item_hovered("SliderStep"):
            context.clicked_on = self.step_slider_id
        elif dpg.is_item_hovered("SliderSpeed"):
            context.clicked_on = self.speed_slider_id
        elif dpg.is_item_hovered("syncronizer_com"):
            context.comports = get_comports_list()
            dpg.configure_item("syncronizer_com", items=context.comports)
        else:
            for idx, pres in enumerate(context.preset_left):
                if dpg.is_item_hovered("preset_left_" + str(idx)):
                    context.gui_hlp.show_preset_dlg(idx | 0x10, pres['name'])
                    return
            for idx, pres in enumerate(context.preset_table):
                if dpg.is_item_hovered("preset_table_" + str(idx)):
                    context.gui_hlp.show_preset_dlg(idx | 0x20, pres['name'])
                    return
            for idx, pres in enumerate(context.preset_right):
                if dpg.is_item_hovered("preset_right_" + str(idx)):
                    context.gui_hlp.show_preset_dlg(idx | 0x40, pres['name'])
                    return
            for idx, pres in enumerate(context.preset_all):
                if dpg.is_item_hovered("preset_all_" + str(idx)):
                    context.gui_hlp.show_preset_dlg(idx | 0x80, pres['name'])
                    return

    def item_release_callback(self, sender, app_data, user_data):
        if context.clicked_on == self.step_slider_id:
            set_step_value(dpg.get_value("SliderStep"))
            context.clicked_on = 0
            return
        if context.clicked_on == self.speed_slider_id:
            set_speed_value(dpg.get_value("SliderSpeed"))
            context.clicked_on = 0
            return
        if context.current_axis != -1:
            if context.ctrl_mode == CTRL_MODE_CONT:
                context.zcontrollers.stop_cur_axis()
            context.current_axis = -1
            return

    def init_manual_page(self):
        context.positions.add_pos_window()
        w = 40
        h = 40
        _y = 140
        __y = 140
        _x = 70
        __x = 70
        scale = 500/973

        dpg.add_image('texture_xyz', pos=(_x+w/2, _y+h/2), height=973 * scale, width=973 * scale)

        stPayloadSize = MVCC_INTVALUE_EX()
        ret_temp = self.obj_cam.MV_CC_GetIntValueEx("PayloadSize", stPayloadSize)
        if ret_temp != MV_OK:
            return
        with dpg.theme() as itheme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 200, 100, 0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0, category=dpg.mvThemeCat_Core)
        # X линейное
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 970 * scale, _y + 635 * scale), tag=context.axis[0]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 185 * scale, _y + 635 * scale), tag=context.axis[0]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Y линейное
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 420 * scale, _y + 553 * scale), tag=context.axis[1]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 100 * scale, _y + 875 * scale), tag=context.axis[1]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Z линейное
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 343 * scale, _y + 0 * scale), tag=context.axis[2]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 343 * scale, _y + 785 * scale), tag=context.axis[2]['name'] + 'bnt_m', width=w, height=h), itheme)
        # X вращение
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 857 * scale, _y + 760 * scale), tag=context.axis[3]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 905 * scale, _y + 566 * scale), tag=context.axis[3]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Y вращение
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 239 * scale, _y + 897 * scale), tag=context.axis[4]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 83 * scale, _y + 971 * scale), tag=context.axis[4]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Z вращение
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 267 * scale, _y + 65 * scale), tag=context.axis[5]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(_x + 467 * scale, _y + 112 * scale), tag=context.axis[5]['name'] + 'bnt_m', width=w, height=h), itheme)

        # CAMERA
        with dpg.group(pos=(500 + _x, 50 + _y), horizontal=True):
            with dpg.group(horizontal=False):
                dpg.add_button(label="Z1", callback=lambda: self.move_z1(False))
                dpg.add_button(label="Рыскание", callback=lambda: self.rotate_z(False))
                dpg.add_button(label="Увеличение", callback=self.set_pix_per_step, user_data=False)

                dpg.add_button(label="Z2", callback=lambda: self.move_z2(False))
                dpg.add_button(label="Y", callback=lambda: self.move_y(False))
                dpg.add_button(label="X", callback=lambda: self.move_x(False))
            with dpg.group(horizontal=False):
                # dpg.add_slider_int(label="", default_value=int(255 * 3.7), max_value=255 * 4, min_value=10, tag="th1",
                #                    width=250)
                # dpg.add_slider_int(label="", default_value=int(255 * 3.7), max_value=255 * 4, min_value=10, tag="th2",
                #                    width=250)
                dpg.add_image('camera_1', tag="group_123")
                with dpg.item_handler_registry(tag="widget_handler"):
                    dpg.add_item_clicked_handler(callback=self.click_callback)
                dpg.bind_item_handler_registry('group_123', "widget_handler")

            with dpg.group(horizontal=False):
                dpg.add_button(label="Z1", callback=lambda: self.move_z1(True))
                dpg.add_button(label="Рыскание", callback=lambda: self.rotate_z(True))
                dpg.add_button(label="Увеличение", callback=self.set_pix_per_step, user_data=True)

                dpg.add_button(label="Z2", callback=lambda: self.move_z2(True))
                dpg.add_button(label="Y", callback=lambda: self.move_y(True))
                dpg.add_button(label="X", callback=lambda: self.move_x(True))

        # TABLE BUTTONS
        dpg.add_image_button(context.axis[12]['txt_p'], pos=(750 + __x, -45 + __y), tag=context.axis[12]['name'] + 'bnt_p')
        dpg.add_image_button(context.axis[12]['txt_m'], pos=(750 + __x, 460 + __y), tag=context.axis[12]['name'] + 'bnt_m')

        # RIGHT PLATFORM BUTTONS
        __y = 140
        _x = 1150
        dpg.add_image('texture_xyzr', pos=(_x+w/2, _y+h/2), height=973 * scale, width=973 * scale)
        # X линейное
        dpg.bind_item_theme(dpg.add_button(pos=(792*scale + _x, 637*scale + _y), tag=context.axis[6]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(0 * scale + _x, 637*scale + _y), tag=context.axis[6]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Y линейное
        dpg.bind_item_theme(dpg.add_button(pos=(555*scale + _x, 555*scale + _y), tag=context.axis[7]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(875*scale + _x, 875*scale + _y), tag=context.axis[7]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Z линейное
        dpg.bind_item_theme(dpg.add_button(pos=(630*scale + _x, 0 * scale + _y), tag=context.axis[8]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(630*scale + _x, 784*scale + _y), tag=context.axis[8]['name'] + 'bnt_m', width=w, height=h), itheme)
        # X вращение
        dpg.bind_item_theme(dpg.add_button(pos=(70*scale + _x, 563*scale + _y), tag=context.axis[9]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(111*scale + _x, 763*scale + _y), tag=context.axis[9]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Y вращение
        dpg.bind_item_theme(dpg.add_button(pos=(880*scale + _x, 972*scale + _y), tag=context.axis[10]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(735*scale + _x, 900*scale + _y), tag=context.axis[10]['name'] + 'bnt_m', width=w, height=h), itheme)
        # Z вращение
        dpg.bind_item_theme(dpg.add_button(pos=(505*scale + _x, 115*scale + _y), tag=context.axis[11]['name'] + 'bnt_p', width=w, height=h), itheme)
        dpg.bind_item_theme(dpg.add_button(pos=(705*scale + _x, 70*scale + _y), tag=context.axis[11]['name'] + 'bnt_m', width=w, height=h), itheme)

        with dpg.group(pos=(50, 800)):
            dpg.add_spacer(height=5)
            dpg.add_text(default_value=txt.SELECT_MOVE_MODE)
            dpg.add_radio_button(tag="rb_move_mode_sel", items=self.move_mode_list, horizontal=True,
                                 default_value=self.move_mode_list[context.ctrl_mode],
                                 callback=self.rb_move_mode_click)

        # Кнопки позиционирования
        with dpg.group(pos=(300, 800)):
            with dpg.group(horizontal=True):
                dpg.add_button(label=txt.INIT_PLATFORM_BTN, height=40, width=200,
                               callback=self.btn_init_plaform_click, tag="btn_init_platform")
                context.gui_hlp.setBtnEnabled("btn_init_platform", True)
            context.gui_hlp.init_platforms_complete(False)
            # Управления скоростью и шагом
        with dpg.group(pos=(600, 800)):
            with dpg.group(horizontal=True):
                dpg.add_text(txt.SET_SPEED_BTN)
                dpg.add_slider_int(label="", default_value=1000, max_value=15000, min_value=10, tag="SliderSpeed",
                                   width=250)
                context.editor_list.append("EditSpeed")
                dpg.add_input_text(label="", tag="EditSpeed", decimal=True, default_value="0", width=50,
                                   callback=self.speed_edit_callback)
                dpg.add_text(tag="SpeedValue")
            with dpg.group(horizontal=True):
                dpg.add_text(txt.SET_STEP_BTN)
                dpg.add_slider_float(label="", default_value=100, max_value=10000, min_value=0.2, tag="SliderStep",
                                     width=250)
                context.editor_list.append("EditStep")
                dpg.add_input_text(label="", tag="EditStep", decimal=True, default_value="0", width=80,
                                   callback=self.step_edit_callback)
                dpg.add_text(tag="StepValue")

            set_step_value(context.step_value_platform * X_MKM_KOEF)
            set_speed_value(context.speed_value_platform)

        context.t = Timer(1, self.timer_read_axis)
        context.t.start()
        with dpg.handler_registry():
            dpg.add_mouse_release_handler(callback=self.item_release_callback)
            dpg.add_mouse_down_handler(callback=self.item_down_callback)

        listener = keyboard.Listener(on_press=self.on_key_down_callback, on_release=self.on_key_release_callback)
        try:
            listener.start()
        except Exception as e:
            print('{0} was pressed'.format(e.args[0]))

    def add_preset_table(self, title, preset_arr, comm_name, pres_code):
        with dpg.group():
            dpg.add_text(default_value=title)
            with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingFixedFit):
                dpg.add_table_column()
                dpg.add_table_column()
                dpg.add_table_column()
                for i in range(0, 10):
                    with dpg.table_row(height=40):
                        with dpg.table_cell():
                            dpg.add_text(tag=comm_name + str(i),
                                         default_value=f"{preset_arr[i]['name']} : > 15")
                        with dpg.table_cell():
                            dpg.add_button(label=txt.SET_PRESET_BTN, height=20, width=100,
                                           callback=self.btn_store_as_preset,
                                           user_data=i + pres_code)  # tag="btn_save_preset_left_" + str(i)
                        with dpg.table_cell():
                            dpg.add_button(label=txt.MOVE_TO_PRESET_BTN, height=20, width=100,
                                           callback=self.btn_move_to_preset_click,
                                           user_data=i + pres_code)  # tag="btn_goto_preset_" + str(i))

    def init_preset_page(self):
        with dpg.group(horizontal=True):
            self.add_preset_table("           Левая платформа", context.preset_left, "preset_left_", 0x10)
            dpg.add_spacer(width=10)
            self.add_preset_table("           Стол", context.preset_table, "preset_table_", 0x20)
            dpg.add_spacer(width=10)
            self.add_preset_table("           Правая платформа", context.preset_right, "preset_right_", 0x40)
            dpg.add_spacer(width=10)
            self.add_preset_table("           Все оси ", context.preset_all, "preset_all_", 0x80)
            dpg.add_spacer(width=10)

    def add_textures(self):
        # добавляем картинки
        dpg.push_container_stack(context.texture_reg)
        for ax in context.axis:
            self.width_btn, self.height_btn, channels_btn, data_p = dpg.load_image("Pics//" + ax['img_p'])
            self.width_btn, self.height_btn, channels_btn, data_m = dpg.load_image("Pics//" + ax['img_m'])
            ax['img_d_p'] = data_p
            ax['img_d_m'] = data_m
            dpg.add_dynamic_texture(width=self.width_btn, height=self.height_btn, default_value=data_p,
                                    tag=ax['txt_p'])
            dpg.add_dynamic_texture(width=self.width_btn, height=self.height_btn, default_value=data_m,
                                    tag=ax['txt_m'])

        self.width_xyz, self.height_xyz, channels_btn, self.data_xy = dpg.load_image("Pics/xyz.png")
        dpg.add_static_texture(width=self.width_xyz, height=self.height_xyz,
                               default_value=self.data_xy, tag="texture_xyz")

        self.width_xyz, self.height_xyz, channels_btn, self.data_z = dpg.load_image("Pics/xyzr.png")
        dpg.add_static_texture(width=self.width_xyz, height=self.height_xyz,
                               default_value=self.data_z, tag="texture_xyzr")

        self.width_end, self.height_end, channels_end, self.data_end = dpg.load_image("Pics/end.png")
        dpg.add_static_texture(width=self.width_end, height=self.height_end,
                               default_value=self.data_end, tag="texture_end")

        self.width_table, self.height_table, channels_table, self.data_table = dpg.load_image("Pics/table.png")
        dpg.add_static_texture(width=self.width_table, height=self.height_table,
                               default_value=self.data_table, tag="texture_table")

        pic_width, pic_height, pic_channels, pic_data = dpg.load_image("Pics//left_arrow.png")
        dpg.add_dynamic_texture(width=pic_width, height=pic_height, default_value=pic_data,
                                tag="left_arrow")
        pic_width, pic_height, pic_channels, pic_data = dpg.load_image("Pics//right_arrow.png")
        dpg.add_dynamic_texture(width=pic_width, height=pic_height, default_value=pic_data, tag="right_arrow")

        pic_width, pic_height, pic_channels, context.aimed_data = dpg.load_image("Pics//aimed.png")
        pic_width, pic_height, pic_channels, context.unaimed_data = dpg.load_image("Pics//unaimed.png")
        dpg.add_dynamic_texture(width=pic_width, height=pic_height, default_value=context.aimed_data, tag="aiming")

        pic_width, pic_height, pic_channels, pic_data = dpg.load_image("Pics//chan_pos_left.png")
        dpg.add_dynamic_texture(width=pic_width, height=pic_height, default_value=pic_data, tag="chan_pos_left")

        pic_width, pic_height, pic_channels, pic_data = dpg.load_image("Pics//chan_pos_right.png")
        dpg.add_dynamic_texture(width=pic_width, height=pic_height, default_value=pic_data, tag="chan_pos_right")

        dpg.add_raw_texture(width=400, height=400, default_value=[0.0] * 400 * 400 * 3,
                            tag="camera_1", format=dpg.mvFormat_Float_rgb)
        dpg.pop_container_stack()


context.motionGUI = MotionGUI()
