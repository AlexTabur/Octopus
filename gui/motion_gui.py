import threading
from threading import Timer

import cv2
from pynput import keyboard
from win32gui import GetWindowText, GetForegroundWindow

import axis_ctrl
from camera.CameraParams_header import *
from camera.MvCameraControl_class import *
from camera.MvErrorDefine_const import *
from camera.scratch import get_k, get_y, resize_image, Mono_numpy, display_img, rotate_z, move_x
from core.gui_helper import *
from core.utils import *

context = Context()


def append_to_lines(line_, lines_2_x, lines_2_y, lines_3_x, lines_3_y):
    if line_[1] < 1000 and line_[3] < 1000:
        lines_2_x.append(line_[0])
        lines_2_y.append(line_[1])
        lines_2_x.append(line_[2])
        lines_2_y.append(line_[3])
    else:
        lines_3_x.append(line_[0])
        lines_3_y.append(line_[1])
        lines_3_x.append(line_[2])
        lines_3_y.append(line_[3])


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


class MotionGUI:

    def __init__(self):
        self.b1 = None
        self.b2 = None
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

        self.width_btn = 0
        self.height_btn = 0
        self.thread_proc = 0
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.buf_save_image = None
        self.angle1 = 0
        self.angle2 = 0

        # self.width_xyz, self.height_xyz, self.channels_xyz, self.data_xyz   = dpg.load_image("Pics//xyz.png")
        # dpg.add_dynamic_texture(width=self.width_btn, height=self.height_btn, default_value=self.data_x_p, tag="texture_btn_"+context.axis[0]['name']+"P")
        # "texture_btn_" + context.axis[0]['name'] + "P"
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
        self.val = 30
        self.val2 = 10 * 2 + 1
        self.threshold1 = 100
        self.threshold2 = 150
        self.rho = 1  # ui.rho.value()
        self.theta = np.pi / 180 / 10  # ui.theta.value()
        self.threshold = 300
        self.n_w, self.n_h = 5120, 5120
        self.minLineLength = 5 / 100 * self.n_w * self.val / 100
        self.maxLineGap = 3 / 100 * self.n_w * self.val / 100
        self.c_x, self.c_y = 2600, 2600
        self.last_photo_taken = time.time()
        if self.buf_grab_image_size < self.NeedBufSize:
            self.buf_grab_image = (self.NeedBufSize * ctypes.c_ubyte)()
            self.buf_grab_image_size = self.NeedBufSize
        thread = threading.Thread(target=self.run_task, args=(), daemon=True)
        thread.start()
        # self.mask = np.zeros((int(self.n_w * self.val / 100), int(self.n_w * self.val / 100)), dtype="uint8")
        # cv2.circle(self.mask, (int(self.c_x * self.val / 100), int(self.c_y * self.val / 100)),
        #            int(self.c_y * self.val / 100),
        #            255, -1)
        # self.obj_cam.MV_CC_GetOneFrameTimeout(self.buf_grab_image, self.buf_grab_image_size, self.stFrameInfo)

    def run_task(self):
        while True:
            # Camera
            if time.time() - self.last_photo_taken > 0.5:
                self.obj_cam.MV_CC_GetOneFrameTimeout(self.buf_grab_image, self.buf_grab_image_size, self.stFrameInfo)
                self.last_photo_taken = time.time()

            resized = resize_image(Mono_numpy(self.buf_grab_image, self.n_w, self.n_h), self.val)
            resized = cv2.transpose(cv2.flip(resized, flipCode=1))
            # cv2.medianBlur(resized, 3, 3, dst=resized)
            edges = cv2.Canny(resized, self.threshold1, self.threshold2)
            # edges &= self.mask

            final = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
            if not self.fixed:
                self.lines_ = cv2.HoughLinesP(edges, self.rho, self.theta, self.threshold,
                                              minLineLength=self.minLineLength,
                                              maxLineGap=self.maxLineGap)
            lines_2_x = []
            lines_2_y = []
            lines_3_x = []
            lines_3_y = []
            if self.lines_ is not None:
                if len(self.lines_) > 1:
                    for line in self.lines_:
                        k = get_k(line[0])
                        if abs(k) < 1:
                            append_to_lines(line[0], lines_2_x, lines_2_y, lines_3_x, lines_3_y)

            if len(lines_2_x) > 0:
                m, b = np.polyfit(lines_2_x, lines_2_y, 1)
                self.angle1 = np.atan(m) * 180 / np.pi
                cv2.line(final, (0, int(get_y(0, m, b))),
                         (int(self.n_w * self.val), int(get_y(int(self.n_w * self.val), m, b))),
                         (0, 255, 0),
                         int(0.1 * self.val))
                self.b1 = b
            if len(lines_3_x) > 0:
                m, b = np.polyfit(lines_3_x, lines_3_y, 1)
                self.angle2 = np.atan(m) * 180 / np.pi
                cv2.line(final, (0, int(get_y(0, m, b))),
                         (int(self.n_w * self.val), int(get_y(int(self.n_w * self.val), m, b))),
                         (0, 255, 0),
                         int(0.1 * self.val))
                self.b2 = b

            # display_img("camera_1", cv2.resize(cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB), (400, 400)))
            display_img("camera_1", cv2.resize(final, (400, 400)))

    def loop(self):
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
            self.set_step_value(float(steps))
        else:
            steps = dpg.get_value('SliderStep')
            self.set_step_value(float(steps))

    def speed_edit_callback(self, sender, app_data, user_data):
        speed = dpg.get_value("EditSpeed")
        speed = re.sub(r'\D', '', speed)
        if speed.isdigit():
            self.set_speed_value(int(speed))
        else:
            speed = dpg.get_value('SliderSpeed')
            self.set_speed_value(int(speed))

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

    def get_axis_params(self):
        context.zcontrollers.get_axis_move_params(AXIS_L_X)
        for i in range(0, 13, 1):
            dpg.set_value(context.axis[i]['name'] + "Acc", context.axis[i]['acc'])
            dpg.set_value(context.axis[i]['name'] + "Dec", context.axis[i]['dec'])

    def movement_by_keys(self, key_vk, key, ctrl, alt):
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
                if ctrl:  # # X Rotate
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
            elif key == keyboard.Key.home:  # # Z Up
                if ctrl:
                    context.zcontrollers.move_axis(int(context.axis[context.z2_ang_i]['dir_fw']),
                                                   context.axis[context.z2_ang_i]['idx'])
                else:
                    context.zcontrollers.move_axis(int(context.axis[context.z2_line_i]['dir_fw']),
                                                   context.axis[context.z2_line_i]['idx'])
            elif key == keyboard.Key.end:  # # Z Down
                if not ctrl:
                    context.zcontrollers.move_axis(int(context.axis[context.z2_line_i]['dir_bw']),
                                                   context.axis[context.z2_line_i]['idx'])
            elif ctrl and key == keyboard.Key.page_up:  # NUM 9 # Z CCW
                context.zcontrollers.move_axis(int(context.axis[context.z2_ang_i]['dir_bw']),
                                               context.axis[context.z2_ang_i]['idx'])
        # # Table platform
        if key_vk == 74:  # 'J'
            if not ctrl:
                context.zcontrollers.move_table(int(context.axis[context.y_table_i]['dir_fw']))
        elif key_vk == 85:  # ('U')
            if not ctrl:
                context.zcontrollers.move_table(int(context.axis[context.y_table_i]['dir_bw']))

    def on_key_down_callback(self, key):
        if context.current_axis != -1:
            return
        if GetWindowText(GetForegroundWindow()) != txt.MAIN_TITLE:  # or dpg.get_value(context.tabBar)!=TAB_MANUAL_ID:
            return

        #        context.logger.log('alphanumeric key {0} pressed'.format(key.vk))
        if key == keyboard.Key.ctrl_r or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl:
            self.ctrl_pressed = True

        # # Show hotkeys
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt or key == keyboard.Key.alt_gr:
            self.alt_pressed = True
            for i in range(0, 26):
                dpg.show_item(str(i) + '_hint')
        elif context.ctrl_by_keyboard:
            if type(key) is keyboard.KeyCode:
                key_vk = key.vk
            else:
                key_vk = 0
            self.movement_by_keys(key_vk, key, self.ctrl_pressed, self.alt_pressed)

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
            self.set_step_value(dpg.get_value("SliderStep"))
            context.clicked_on = 0
            return
        if context.clicked_on == self.speed_slider_id:
            self.set_speed_value(dpg.get_value("SliderSpeed"))
            context.clicked_on = 0
            return
        if context.current_axis != -1:
            if context.ctrl_mode == CTRL_MODE_CONT:
                context.zcontrollers.stop_cur_axis()
            context.current_axis = -1
            return

    #        dpg.delete_item("msg_window", slot=1)

    def set_speed_value(self, speed: int):
        dpg.set_value("SliderSpeed", speed)
        dpg.set_value("EditSpeed", speed)
        dpg.set_value("SpeedValue", "X,Y,Z лин = " + str(speed * NM_PER_STEP_X / 1000) + ' ' + txt.SET_LIN_SPEED_DIM)
        context.speed_value_platform = speed
        context.zcontrollers.set_platforms_speed(speed)  # установка скорости на все оси платформы
        context.zcontrollers.set_table_speed(speed)  # установка скорости на все оси платформы
        save_prameters()

    def set_step_value(self, steps_um: float):
        steps = int(steps_um / X_MKM_KOEF)
        steps_um = steps * X_MKM_KOEF
        dpg.set_value("SliderStep", steps_um)
        dpg.set_value("EditStep", steps_um)  # steps_um = steps * X_MKM_KOEF
        dpg.set_value("StepValue", str(steps) + ' шагов')
        context.step_value_platform = int(steps)  # установка скорости на все оси платформы
        steps = int(steps_um / TABLE_MKM_KOEF)
        context.step_value_table = int(steps)  # ?????????????????
        save_prameters()

    def init_manual_page(self):
        # )
        context.positions.add_pos_window()

        # dpg.add_input_text(label="", tag="EditAccX", decimal=True, default_value="0", width=50)
        # dpg.add_input_text(label="", tag="EditDecX", decimal=True, default_value="0", width=50)
        top_margin = 70
        left_margin = 100
        dpg.add_image('texture_xy', pos=(400 + left_margin, 223 + top_margin))
        dpg.add_image('texture_z', pos=(89 + left_margin, 223 + top_margin))

        dpg.add_image('camera_1', pos=(left_margin, top_margin + 500))
        dpg.add_button(label="rotate", pos=(left_margin + 400, top_margin + 500),
                       callback=lambda: rotate_z(context, self.angle1 - self.angle2, False))
        dpg.add_button(label="rotate", pos=(left_margin + 500, top_margin + 500),
                       callback=lambda: rotate_z(context, self.angle2 - self.angle1, True))
        dpg.add_button(label="move", pos=(left_margin + 400, top_margin + 550),
                       callback=lambda: move_x(context, self.b1 - self.b2, False))
        dpg.add_button(label="move", pos=(left_margin + 500, top_margin + 550),
                       callback=lambda: move_x(context, self.b2 - self.b1, True))
        #dpg.add_image('camera_2', pos=(x_, 223 + top_margin))
        # dpg.add_button(label="Начать", pos=(x_, -23 + top_margin+201), callback=lambda sender, app_data: camera_connect(sender, app_data, 0))
        # stOutFrame = MV_FRAME_OUT()
        stFrameInfo = MV_FRAME_OUT_INFO_EX()
        img_buff = None
        numArray = None

        stPayloadSize = MVCC_INTVALUE_EX()
        ret_temp = self.obj_cam.MV_CC_GetIntValueEx("PayloadSize", stPayloadSize)
        if ret_temp != MV_OK:
            return
        NeedBufSize = int(stPayloadSize.nCurValue)
        # dpg.add_button(label="Подключить", pos=(x_, 223 + top_margin+201), callback=lambda sender, app_data: camera_connect(sender, app_data, 0))
        # LEFT PLATFORM BUTTONS
        dpg.add_image_button(context.axis[0]['txt_p'], pos=(494 + left_margin, 223 + top_margin),
                             tag=context.axis[0]['name'] + 'bnt_p')  # X линейное +
        dpg.add_image_button(context.axis[0]['txt_m'], pos=(314 + left_margin, 223 + top_margin),
                             tag=context.axis[0]['name'] + 'bnt_m')  # X линейное -
        dpg.add_button(show=False, label="D", pos=(494 + left_margin, 223 + top_margin), tag='0_hint', width=72,
                       height=72, )  # X линейное +
        dpg.add_button(show=False, label="A", pos=(314 + left_margin, 223 + top_margin), tag='1_hint', width=72,
                       height=72)  # X линейное -

        dpg.add_image_button(context.axis[1]['txt_p'], pos=(404 + left_margin, 134 + top_margin),
                             tag=context.axis[1]['name'] + 'bnt_p')  # Y линейное
        dpg.add_image_button(context.axis[1]['txt_m'], pos=(404 + left_margin, 313 + top_margin),
                             tag=context.axis[1]['name'] + 'bnt_m')  # Y линейное
        dpg.add_button(show=False, label="W", pos=(404 + left_margin, 134 + top_margin), tag='2_hint', width=72,
                       height=72)  # Y линейное
        dpg.add_button(show=False, label="S", pos=(404 + left_margin, 313 + top_margin), tag='3_hint', width=72,
                       height=72)  # Y линейное

        dpg.add_image_button(context.axis[2]['txt_p'], pos=(89 + left_margin, 134 + top_margin),
                             tag=context.axis[2]['name'] + 'bnt_p')  # Z линейное
        dpg.add_image_button(context.axis[2]['txt_m'], pos=(89 + left_margin, 313 + top_margin),
                             tag=context.axis[2]['name'] + 'bnt_m')  # Z линейное
        dpg.add_button(show=False, label="Q", pos=(89 + left_margin, 134 + top_margin), tag='4_hint', width=72,
                       height=72)  # Z линейное
        dpg.add_button(show=False, label="Z", pos=(89 + left_margin, 313 + top_margin), tag='5_hint', width=72,
                       height=72)  # Z линейное

        dpg.add_image_button(context.axis[3]['txt_p'], pos=(224 + left_margin, 179 + top_margin),
                             tag=context.axis[3]['name'] + 'bnt_p')  # X вращение
        dpg.add_image_button(context.axis[3]['txt_m'], pos=(224 + left_margin, 268 + top_margin),
                             tag=context.axis[3]['name'] + 'bnt_m')  # X вращение
        dpg.add_button(show=False, label="CTRL\n  +\n  W", pos=(224 + left_margin, 179 + top_margin), tag='6_hint',
                       width=72, height=72)  # X вращение
        dpg.add_button(show=False, label="CTRL\n  +\n  S", pos=(224 + left_margin, 268 + top_margin), tag='7_hint',
                       width=72, height=72)  # X вращение

        dpg.add_image_button(context.axis[4]['txt_p'], pos=(360 + left_margin, 45 + top_margin),
                             tag=context.axis[4]['name'] + 'bnt_p')  # Y вращение
        dpg.add_image_button(context.axis[4]['txt_m'], pos=(450 + left_margin, 45 + top_margin),
                             tag=context.axis[4]['name'] + 'bnt_m')  # Y вращение
        dpg.add_button(show=False, label="CTRL\n  +\n  A", pos=(360 + left_margin, 45 + top_margin), tag='8_hint',
                       width=72, height=72)  # Y вращение
        dpg.add_button(show=False, label="CTRL\n  +\n  D", pos=(450 + left_margin, 45 + top_margin), tag='9_hint',
                       width=72, height=72)  # Y вращение

        dpg.add_image_button(context.axis[5]['txt_p'], pos=(45 + left_margin, 45 + top_margin),
                             tag=context.axis[5]['name'] + 'bnt_p')  # Z вращение
        dpg.add_image_button(context.axis[5]['txt_m'], pos=(135 + left_margin, 45 + top_margin),
                             tag=context.axis[5]['name'] + 'bnt_m')  # Z вращение
        dpg.add_button(show=False, label="CTRL\n  +\n  Q", pos=(45 + left_margin, 45 + top_margin), tag='10_hint',
                       width=72, height=72)  # Z вращение
        dpg.add_button(show=False, label="CTRL\n  +\n  E", pos=(135 + left_margin, 45 + top_margin), tag='11_hint',
                       width=72, height=72)  # Z вращение
        # TABLE BUTTONS
        dpg.add_image_button(context.axis[12]['txt_p'], pos=(584 + left_margin, 45 + top_margin),
                             tag=context.axis[12]['name'] + 'bnt_p')  # Y СТОЛ
        dpg.add_image_button(context.axis[12]['txt_m'], pos=(584 + left_margin, 313 + top_margin),
                             tag=context.axis[12]['name'] + 'bnt_m')  # Y СТОЛ
        dpg.add_button(show=False, label="U", pos=(584 + left_margin, 45 + top_margin), tag='12_hint', width=72,
                       height=72)  # Y СТОЛ
        dpg.add_button(show=False, label="J", pos=(584 + left_margin, 313 + top_margin), tag='13_hint', width=72,
                       height=72)  # Y СТОЛ

        # RIGHT PLATFORM BUTTONS
        dpg.add_image('texture_table', pos=(590 + left_margin, 150 + top_margin))
        right_manipulator = left_margin + 360
        dpg.add_image('texture_xy', pos=(404 + right_manipulator, 223 + top_margin))
        dpg.add_image('texture_z', pos=(720 + right_manipulator, 223 + top_margin))
        dpg.add_image_button(context.axis[6]['txt_p'], pos=(494 + right_manipulator, 223 + top_margin),
                             tag=context.axis[6]['name'] + 'bnt_p')  # X линейное
        dpg.add_image_button(context.axis[6]['txt_m'], pos=(314 + right_manipulator, 223 + top_margin),
                             tag=context.axis[6]['name'] + 'bnt_m')  # X линейное
        dpg.add_button(show=False, label="NUM 6", pos=(494 + right_manipulator, 223 + top_margin), tag='14_hint',
                       width=72, height=72)  # X линейное
        dpg.add_button(show=False, label="NUM 4", pos=(314 + right_manipulator, 223 + top_margin), tag='15_hint',
                       width=72, height=72)  # X линейное

        dpg.add_image_button(context.axis[7]['txt_p'], pos=(404 + right_manipulator, 134 + top_margin),
                             tag=context.axis[7]['name'] + 'bnt_p')  # Y линейное
        dpg.add_image_button(context.axis[7]['txt_m'], pos=(404 + right_manipulator, 313 + top_margin),
                             tag=context.axis[7]['name'] + 'bnt_m')  # Y линейное
        dpg.add_button(show=False, label="NUM 8", pos=(404 + right_manipulator, 134 + top_margin), tag='16_hint',
                       width=72, height=72)  # Y линейное
        dpg.add_button(show=False, label="NUM 2", pos=(404 + right_manipulator, 313 + top_margin), tag='17_hint',
                       width=72, height=72)  # Y линейное

        dpg.add_image_button(context.axis[8]['txt_p'], pos=(720 + right_manipulator, 134 + top_margin),
                             tag=context.axis[8]['name'] + 'bnt_p')  # Z линейное
        dpg.add_image_button(context.axis[8]['txt_m'], pos=(720 + right_manipulator, 313 + top_margin),
                             tag=context.axis[8]['name'] + 'bnt_m')  # Z линейное
        dpg.add_button(show=False, label="NUM 7", pos=(720 + right_manipulator, 134 + top_margin), tag='18_hint',
                       width=72, height=72)  # Z линейное
        dpg.add_button(show=False, label="NUM 1", pos=(720 + right_manipulator, 313 + top_margin), tag='19_hint',
                       width=72, height=72)  # Z линейное

        dpg.add_image_button(context.axis[9]['txt_p'], pos=(585 + right_manipulator, 179 + top_margin),
                             tag=context.axis[9]['name'] + 'bnt_p')  # X вращение
        dpg.add_image_button(context.axis[9]['txt_m'], pos=(585 + right_manipulator, 268 + top_margin),
                             tag=context.axis[9]['name'] + 'bnt_m')  # X вращение
        dpg.add_button(show=False, label="CTRL\n  +\nNUM 8", pos=(585 + right_manipulator, 179 + top_margin),
                       tag='20_hint', width=72, height=72)  # X вращение
        dpg.add_button(show=False, label="CTRL\n  +\nNUM 2", pos=(585 + right_manipulator, 268 + top_margin),
                       tag='21_hint', width=72, height=72)  # X вращение

        dpg.add_image_button(context.axis[10]['txt_p'], pos=(360 + right_manipulator, 45 + top_margin),
                             tag=context.axis[10]['name'] + 'bnt_p')  # Y вращение
        dpg.add_image_button(context.axis[10]['txt_m'], pos=(450 + right_manipulator, 45 + top_margin),
                             tag=context.axis[10]['name'] + 'bnt_m')  # Y вращение
        dpg.add_button(show=False, label="CTRL\n  +\nNUM 4", pos=(360 + right_manipulator, 45 + top_margin),
                       tag='22_hint', width=72, height=72)  # Y вращение
        dpg.add_button(show=False, label="CTRL\n  +\nNUM 6", pos=(450 + right_manipulator, 45 + top_margin),
                       tag='23_hint', width=72, height=72)  # Y вращение

        dpg.add_image_button(context.axis[11]['txt_p'], pos=(675 + right_manipulator, 45 + top_margin),
                             tag=context.axis[11]['name'] + 'bnt_p')  # Z вращение
        dpg.add_image_button(context.axis[11]['txt_m'], pos=(765 + right_manipulator, 45 + top_margin),
                             tag=context.axis[11]['name'] + 'bnt_m')  # Z вращение
        dpg.add_button(show=False, label="CTRL\n  +\nNUM 7", pos=(675 + right_manipulator, 45 + top_margin),
                       tag='24_hint', width=72, height=72)  # Z вращение
        dpg.add_button(show=False, label="CTRL\n  +\nNUM 9", pos=(765 + right_manipulator, 45 + top_margin),
                       tag='25_hint', width=72, height=72)  # Z вращение

        with dpg.group(pos=(50, 470)):
            dpg.add_spacer(height=5)
            dpg.add_text(default_value=txt.SELECT_MOVE_MODE)
            dpg.add_radio_button(tag="rb_move_mode_sel", items=self.move_mode_list, horizontal=True,
                                 default_value=self.move_mode_list[context.ctrl_mode],
                                 callback=self.rb_move_mode_click)

        # Кнопки позиционирования
        with dpg.group(pos=(300, 480)):
            with dpg.group(horizontal=True):
                dpg.add_button(label=txt.INIT_PLATFORM_BTN, height=40, width=200,
                               callback=self.btn_init_plaform_click, tag="btn_init_platform")
                context.gui_hlp.setBtnEnabled("btn_init_platform", True)
            #                dpg.add_spacer(width=10)
            #                dpg.add_button(label=txt.SET_PRESET_BTN, height=40, width=200,
            #                               callback=self.btn_set_zero_click, tag="btn_set_as_zero")
            #                dpg.add_spacer(width=10)
            #                dpg.add_button(label=txt.MOVE_TO_PRESET_BTN, height=40, width=200,
            #                               callback=self.btn_move_to_zero_click, tag="btn_goto_zero")
            context.gui_hlp.init_platforms_complete(False)
            # Управления скоростью и шагом
        with dpg.group(pos=(600, 480)):
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

            self.set_step_value(context.step_value_platform * X_MKM_KOEF)
            self.set_speed_value(context.speed_value_platform)

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
                                         default_value=f"{preset_arr[i]['name'] : >15}")
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

        self.width_xyz, self.height_xyz, channels_btn, self.data_xy = dpg.load_image("Pics/xy.png")
        dpg.add_static_texture(width=self.width_xyz, height=self.height_xyz,
                               default_value=self.data_xy, tag="texture_xy")

        self.width_xyz, self.height_xyz, channels_btn, self.data_z = dpg.load_image("Pics/z.png")
        dpg.add_static_texture(width=self.width_xyz, height=self.height_xyz,
                               default_value=self.data_z, tag="texture_z")

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

        dpg.add_raw_texture(width=400, height=400, default_value=np.zeros((400, 400, 3), dtype=np.float32),
                            tag="camera_1", format=dpg.mvFormat_Float_rgb)

        # dpg.add_raw_texture(width=400, height=400, default_value=np.zeros((400,400,3), dtype=np.float32), tag="camera_2", format=dpg.mvFormat_Float_rgb)
        dpg.pop_container_stack()


context.motionGUI = MotionGUI()
