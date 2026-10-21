from threading import Timer

from pynput import keyboard
from win32gui import GetWindowText, GetForegroundWindow

import axis_ctrl
from Measurements.meas_powermap import *
from Motion.position import add_pos_window
from axis_ctrl import *
from move_from_camera import *

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


def script_code_click_callback(sender, app_data, user_data):
    m_ = dpg.get_mouse_pos()
    p_ = dpg.get_item_pos("script_code")
    # TODO SMALL WINDOW SCROLL WRONG LINE
    context.line_n = int((m_[1] - p_[1] + 6) // 20 + 1 + 0.5)
    set_line()


def set_step_value(steps_um: float):
    steps = int(steps_um / X_MKM_KOEF)
    steps_um = steps * X_MKM_KOEF
    dpg.set_value("SliderStep", steps_um)
    dpg.set_value("EditStep", steps_um)
    dpg.set_value("StepValue", str(steps) + ' шагов')
    context.step_value_platform = int(steps)
    steps = int(steps_um / TABLE_MKM_KOEF)
    context.step_value_table = int(steps)
    save_parameters()


def set_speed_value(speed_: int):
    dpg.set_value("SliderSpeed", speed_)
    dpg.set_value("EditSpeed", speed_)
    dpg.set_value("SpeedValue", "X,Y,Z лин = " + str(speed_ * NM_PER_STEP_X / 1000) + ' ' + txt.SET_LIN_SPEED_DIM)
    context.speed_value_platform = speed_
    axis_ctrl.set_platforms_speed(speed_)
    axis_ctrl.set_table_speed(speed_)
    save_parameters()


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
                axis_ctrl.move_axis(int(context.axis[context.y1_ang_i]['dir_bw']),
                                    context.axis[context.y1_ang_i]['idx'])
            else:  # X Left
                move_axis(int(context.axis[context.x1_line_i]['dir_bw']),
                          context.axis[context.x1_line_i]['idx'])
        elif key_vk == 68:  # D
            if ctrl:  # Y Rotate
                move_axis(int(context.axis[context.y1_ang_i]['dir_fw']),
                          context.axis[context.y1_ang_i]['idx'])
            else:  # X Right
                move_axis(int(context.axis[context.x1_line_i]['dir_fw']),
                          context.axis[context.x1_line_i]['idx'])

        elif key_vk == 87:  # W
            if ctrl:  # X Rotate
                move_axis(int(context.axis[context.x1_ang_i]['dir_fw']),
                          context.axis[context.x1_ang_i]['idx'])
            else:  # Y Up
                move_axis(int(context.axis[context.y1_line_i]['dir_fw']),
                          context.axis[context.y1_line_i]['idx'])
        elif key_vk == 83:  # S
            if ctrl:  # X Rotate
                move_axis(int(context.axis[context.x1_ang_i]['dir_bw']),
                          context.axis[context.x1_ang_i]['idx'])
            else:  # Y Down
                move_axis(int(context.axis[context.y1_line_i]['dir_bw']),
                          context.axis[context.y1_line_i]['idx'])
        elif key_vk == 81:  # Q -  Z Up
            if ctrl:  # Z Rotate
                move_axis(int(context.axis[context.z1_ang_i]['dir_fw']),
                          context.axis[context.z1_ang_i]['idx'])
            else:
                move_axis(int(context.axis[context.z1_line_i]['dir_fw']),
                          context.axis[context.z1_line_i]['idx'])
        elif key_vk == 90:  # Z -  Z Down
            if not ctrl:
                move_axis(int(context.axis[context.z1_line_i]['dir_bw']),
                          context.axis[context.z1_line_i]['idx'])

        elif ctrl and key_vk == 69:  # 'c' # Z CCW
            move_axis(int(context.axis[context.z1_ang_i]['dir_bw']),
                      context.axis[context.z1_ang_i]['idx'])
    # Right platform
    if not context.lock_right_side:
        if key == keyboard.Key.left:
            if ctrl:  # Y Rotate
                move_axis(int(context.axis[context.y2_ang_i]['dir_bw']),
                          context.axis[context.y2_ang_i]['idx'])
            else:  # X Left
                move_axis(int(context.axis[context.x2_line_i]['dir_bw']),
                          context.axis[context.x2_line_i]['idx'])
        elif key == keyboard.Key.right:
            if ctrl:  # Y Rotate
                move_axis(int(context.axis[context.y2_ang_i]['dir_fw']),
                          context.axis[context.y2_ang_i]['idx'])
            else:  # X Right
                move_axis(int(context.axis[context.x2_line_i]['dir_fw']),
                          context.axis[context.x2_line_i]['idx'])
        elif key == keyboard.Key.up:
            if ctrl:  # X Rotate
                move_axis(int(context.axis[context.x2_ang_i]['dir_fw']),
                          context.axis[context.x2_ang_i]['idx'])
            else:  # Y Up
                move_axis(int(context.axis[context.y2_line_i]['dir_fw']),
                          context.axis[context.y2_line_i]['idx'])
        elif key == keyboard.Key.down:  # Y Down
            if ctrl:  # X Rotate
                move_axis(int(context.axis[context.x2_ang_i]['dir_bw']),
                          context.axis[context.x2_ang_i]['idx'])
            else:  # Y Down
                move_axis(int(context.axis[context.y2_line_i]['dir_bw']),
                          context.axis[context.y2_line_i]['idx'])
        elif key == keyboard.Key.home:  # Z Up
            if ctrl:
                move_axis(int(context.axis[context.z2_ang_i]['dir_fw']),
                          context.axis[context.z2_ang_i]['idx'])
            else:
                move_axis(int(context.axis[context.z2_line_i]['dir_fw']),
                          context.axis[context.z2_line_i]['idx'])
        elif key == keyboard.Key.end:  # Z Down
            if not ctrl:
                move_axis(int(context.axis[context.z2_line_i]['dir_bw']),
                          context.axis[context.z2_line_i]['idx'])
        elif ctrl and key == keyboard.Key.page_up:  # NUM 9 # Z CCW
            move_axis(int(context.axis[context.z2_ang_i]['dir_bw']),
                      context.axis[context.z2_ang_i]['idx'])
    # Table platform
    if key_vk == 74:  # 'J'
        if not ctrl:
            move_table(int(context.axis[context.y_table_i]['dir_fw']))
    elif key_vk == 85:  # ('U')
        if not ctrl:
            move_table(int(context.axis[context.y_table_i]['dir_bw']))


def get_axis_params():
    get_axis_move_params(AXIS_L_X)
    for i in range(0, 13, 1):
        dpg.set_value(context.axis[i]['name'] + "Acc", context.axis[i]['acc'])
        dpg.set_value(context.axis[i]['name'] + "Dec", context.axis[i]['dec'])


def move_table_(d):
    context.z_table.move(AXIS_TABLE, d / UM_PER_STEP_TABLE)


def set_line():
    a_str = "\n" * context.line_n + ">"
    dpg.set_value("script_pointer", a_str)


# 16 left 1
# 17 left 2
#
# 64 right1
# 65 right2
# 32 table1

def get_line():
    all_lines = dpg.get_value("script_code")
    if context.line_n < context.line_count:
        ret = all_lines.split("\n")[context.line_n]
    else:
        ret = ""
    # print("To return", ret, type(ret))
    a = ret.split("#")
    if len(a) < 2:
        a.append("Действие")
    command, msg = a[0], a[1]
    return ret, msg


def btn_run_cont_callback(sender, app_data, user_data):
    def func2():
        while True:
            a, msg = get_line()
            # text = "действие"
            # context.gui_hlp.showMessage(text, txt.BREAK, DLG_CT_BREAK_PROC)
            confirm_msg_ = a.find("confirm") > -1
            if confirm_msg_:
                exec(a)
                while context.confirm_state == 0:
                    pass
                print(context.confirm_state)
                if context.confirm_state == 2:
                    break
            else:
                context.gui_hlp.showMessage(msg, txt.BREAK, DLG_CT_BREAK_PROC)
                exec(a)
                popup_close()

            if context.line_count > context.line_n + 1:
                context.line_n += 1
            set_line()

    thread_proc = threading.Thread(target=func2, args=[], daemon=False)
    thread_proc.start()
    # thread_proc.join()


def btn_run_callback(sender, app_data, user_data):
    a, msg = get_line()
    # text = "действие"
    # context.gui_hlp.showMessage(text, txt.BREAK, DLG_CT_BREAK_PROC)
    context.gui_hlp.showMessage(msg, txt.BREAK, DLG_CT_BREAK_PROC)

    def func():
        exec(a)
        popup_close()

    thread_proc = threading.Thread(target=func, args=[], daemon=True)
    thread_proc.start()
    if context.line_count > context.line_n + 1:
        context.line_n += 1
    set_line()


def loop_motion_gui():
    get_angles()
    if context.moving_right:
        context.moving_right_shared.value = 1
    else:
        context.moving_right_shared.value = 0

    if context.z_platform.state_changed & 1:
        context.z_platform.state_changed &= 0xFE
        if context.z_platform.is_connected:
            set_conn_states("platform_ctrl_state", "platform_conn_btn", 1)
            set_platforms_speed(
                context.speed_value_platform)
            context.logger.log_com("Контроллер платформ подключен")
        #                self.get_axis_params()
        else:
            set_conn_states("platform_ctrl_state", "platform_conn_btn", 0)
            context.logger.log_com("Контроллер платформ отключен")

    if context.z_table.state_changed & 1:
        context.z_table.state_changed &= 0xFE
        if context.z_table.is_connected:
            set_conn_states("table_ctrl_state", "table_conn_btn", 1)
            set_table_speed(
                context.speed_value_platform)
            context.logger.log_com("Контроллер стола подключен")
        #                self.get_axis_params()
        else:
            set_conn_states("table_ctrl_state", "table_conn_btn", 0)
            context.logger.log_com("Контроллер стола отключен")


class MotionGUI:

    def __init__(self):
        self.alt_pressed = False
        self.ctrl_pressed = False
        self.platform_list = [txt.LEFT, txt.RIGHT]
        self.move_mode_list = [txt.CONTINUES_MODE, txt.STEP_MODE]
        self.step_slider_id = 1
        self.speed_slider_id = 2
        context.z_controllers = axis_ctrl.PlatformController()
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

    def btn_init_platform_click(self, sender, app_data, user_data):
        context.gui_hlp.showMessage(txt.PLATFORM_INIT_MSG, txt.BREAK, DLG_CT_BREAK_PROC)
        self.thread_proc = threading.Thread(target=platforms_homing2, args=[], daemon=True)
        self.thread_proc.start()

    def btn_move_to_preset_click(self, sender, app_data, user_data):
        print(user_data)
        context.gui_hlp.showMessage(txt.PLATFORM_POSITIONING_MSG, txt.BREAK, DLG_CT_BREAK_PROC)
        if user_data & 0x10:  # left platform
            self.thread_proc = threading.Thread(target=move_platform_to_preset, args=[user_data],
                                                daemon=True)
        elif user_data & 0x20:  # table platform
            self.thread_proc = threading.Thread(target=move_table_to_preset, args=[user_data],
                                                daemon=True)
        elif user_data & 0x40:  # right platform
            self.thread_proc = threading.Thread(target=move_platform_to_preset, args=[user_data],
                                                daemon=True)
        elif user_data & 0x80:  # all platform
            self.thread_proc = threading.Thread(target=move_all_to_preset, args=[user_data],
                                                daemon=True)
        self.thread_proc.start()

    def rb_move_mode_click(self, sender, app_data, user_data):
        if dpg.get_value("rb_move_mode_sel") == self.move_mode_list[CTRL_MODE_CONT]:
            context.ctrl_mode = CTRL_MODE_CONT
        else:
            context.ctrl_mode = CTRL_MODE_STEP

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
                stop_cur_axis()
            context.current_axis = -1

    def item_down_callback(self, sender, app_data, user_data):
        if context.current_axis != -1:
            return
        context.current_axis = -1
        for ax in context.axis:
            if (not context.lock_left_side or ax['side'] != 0) and (not context.lock_right_side or ax['side'] != 1):
                if dpg.is_item_hovered(ax['name'] + 'bnt_p'):
                    if ax['controller'] == 1:
                        move_axis(int(ax['dir_fw']), ax['idx'])
                    elif ax['controller'] == 2:
                        move_table(-1)
                    return

                if dpg.is_item_hovered(ax['name'] + 'bnt_m'):
                    if ax['controller'] == 1:
                        move_axis(int(ax['dir_bw']), ax['idx'])
                    elif ax['controller'] == 2:
                        move_table(1)
                    return
        if dpg.is_item_hovered("SliderStep"):
            context.clicked_on = self.step_slider_id
        elif dpg.is_item_hovered("SliderSpeed"):
            context.clicked_on = self.speed_slider_id
        elif dpg.is_item_hovered("sync_com"):
            context.comports = get_comports_list()
            dpg.configure_item("sync_com", items=context.comports)
        else:
            for idx, pres in enumerate(context.preset_left):
                if dpg.is_item_hovered("preset_left_" + str(idx)):
                    show_preset_dlg(idx | 0x10, pres['name'])
                    return
            for idx, pres in enumerate(context.preset_table):
                if dpg.is_item_hovered("preset_table_" + str(idx)):
                    show_preset_dlg(idx | 0x20, pres['name'])
                    return
            for idx, pres in enumerate(context.preset_right):
                if dpg.is_item_hovered("preset_right_" + str(idx)):
                    show_preset_dlg(idx | 0x40, pres['name'])
                    return
            for idx, pres in enumerate(context.preset_all):
                if dpg.is_item_hovered("preset_all_" + str(idx)):
                    show_preset_dlg(idx | 0x80, pres['name'])
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
                stop_cur_axis()
            context.current_axis = -1
            return

    def timer_read_axis(self):
        if context.current_proc == 0:
            axis_ctrl.get_all_axis_pos()
            get_all_axis_state()
            # f context.z_platform.is_connected:
            for i in range(0, 13, 1):
                dpg.set_value(context.axis[i]['name'], context.axis[i]['pos'])
                self.process_state(i)

        context.t = Timer(1, self.timer_read_axis)
        context.t.start()

    def init_manual_page(self):
        add_pos_window()
        w = int(40 * 0.5)
        h = int(40 * 0.5)
        _y = 140
        __y = 550
        _x = 200
        __x = 0
        scale = 500 / 973 * 0.4
        context.line_n = 0
        with dpg.group(pos=(_x + 500 + 60, _y), horizontal=False):
            dpg.add_button(tag="run_line", label="ВЫПОЛНИТЬ СТРОКУ", callback=btn_run_callback)
            dpg.add_spacer(height=30)
            with dpg.group(horizontal=True):
                height = 600
                dpg.add_input_text(multiline=True, width=20, height=height, tag="script_pointer")
                dpg.add_input_text(multiline=True, width=1000, height=height, tag="script_code")
                with open('script.txt', encoding="utf-8") as file:
                    lines_list = file.readlines()
                    context.line_count = len(lines_list)
                    dpg.set_value("script_code", "".join(lines_list))
                    dpg.set_value("script_pointer", ">")
                # with dpg.group(horizontal=False):

                #     # dpg.add_button(tag="run_cont_line", label="Непрерывное выполнение", callback=btn_run_cont_callback)
                #     # dpg.add_button(tag="prev_line", label="назад", callback=btn_prev_line_callback, user_data=15)
                #     # dpg.add_button(tag="next_line", label="вперёд", callback=btn_next_line_callback, user_data=15)
        dpg.add_image('texture_xyz', pos=(int(_x + w / 2), int(__y + h / 2)), height=int(973 * scale),
                      width=int(973 * scale))

        with dpg.theme() as i_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 200, 100, 0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0, category=dpg.mvThemeCat_Core)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 970 * scale), int(__y + 635 * scale)), tag=context.axis[0]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 185 * scale), int(__y + 635 * scale)), tag=context.axis[0]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 420 * scale), int(__y + 553 * scale)), tag=context.axis[1]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 100 * scale), int(__y + 875 * scale)), tag=context.axis[1]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 343 * scale), int(__y + 0 * scale)), tag=context.axis[2]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 343 * scale), int(__y + 785 * scale)), tag=context.axis[2]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 857 * scale), int(__y + 760 * scale)), tag=context.axis[3]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 905 * scale), int(__y + 566 * scale)), tag=context.axis[3]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 239 * scale), int(__y + 897 * scale)), tag=context.axis[4]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 83 * scale), int(__y + 971 * scale)), tag=context.axis[4]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 267 * scale), int(__y + 65 * scale)), tag=context.axis[5]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(_x + 467 * scale), int(__y + 112 * scale)), tag=context.axis[5]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)
        with dpg.group(pos=(_x + 195, _y + 250), horizontal=False):
            dpg.add_image_button(context.axis[12]['txt_p'],
                                 tag=context.axis[12]['name'] + 'bnt_p')
            dpg.add_image_button(context.axis[12]['txt_m'],
                                 tag=context.axis[12]['name'] + 'bnt_m')
        with dpg.group(pos=(_x + 60, _y), horizontal=True):
            # with dpg.group(horizontal=False):
            #     dpg.add_button(label="Z", callback=move_z)
            #     dpg.add_button(label="X", callback=move_x)
            #     dpg.add_button(label="Рыскание", callback=rotate_z)
            #     dpg.add_button(label="Тангаж", callback=rotate_y)
            #     dpg.add_button(label="Y", callback=move_y)

            with dpg.group(horizontal=False):
                # dpg.add_slider_int(label="Высота чипа", default_value=5700, max_value=10000, min_value=1, tag="th1",
                #                    width=250)
                # dpg.add_slider_int(label="длина чипа", default_value=int(255 * 0.5), max_value=255, min_value=1,
                #                    tag="th2",
                #                    width=250)
                # dpg.add_button(label="Предыдущий чип", callback=lambda: move_chip(False))
                # dpg.add_button(label="Следующий чип", callback=lambda: move_chip(True))

                dpg.add_text(tag="SpeedValue")
                dpg.add_text(txt.SET_SPEED_BTN)
                with dpg.group(horizontal=True):
                    dpg.add_slider_int(label="", default_value=1000, max_value=15000, min_value=10, tag="SliderSpeed",
                                       width=250)
                    context.editor_list.append("EditSpeed")
                    dpg.add_input_text(label="", tag="EditSpeed", decimal=True, default_value="0", width=50,
                                       callback=speed_edit_callback)
                dpg.add_text(txt.SET_STEP_BTN)
                dpg.add_text(tag="StepValue")
                with dpg.group(horizontal=True):
                    dpg.add_slider_float(label="", default_value=100, max_value=10000, min_value=0.2, tag="SliderStep",
                                         width=250)
                    context.editor_list.append("EditStep")
                    dpg.add_input_text(label="", tag="EditStep", decimal=True, default_value="0", width=80,
                                       callback=step_edit_callback)

                set_step_value(context.step_value_platform * X_MKM_KOEF)
                set_speed_value(context.speed_value_platform)

        # RIGHT PLATFORM BUTTONS
        _x = 450
        dpg.add_image('texture_xyzr', pos=(_x + int(w / 2), __y + int(h / 2)), height=int(973 * scale),
                      width=int(973 * scale))

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(792 * scale + _x), int(637 * scale + __y)), tag=context.axis[6]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(0 * scale + _x), int(637 * scale + __y)), tag=context.axis[6]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(555 * scale + _x), int(555 * scale + __y)), tag=context.axis[7]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(875 * scale + _x), int(875 * scale + __y)), tag=context.axis[7]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(630 * scale + _x), int(0 * scale + __y)), tag=context.axis[8]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(630 * scale + _x), int(784 * scale + __y)), tag=context.axis[8]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(70 * scale + _x), int(563 * scale + __y)), tag=context.axis[9]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(111 * scale + _x), int(763 * scale + __y)), tag=context.axis[9]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(880 * scale + _x), int(972 * scale + __y)), tag=context.axis[10]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(735 * scale + _x), int(900 * scale + __y)), tag=context.axis[10]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        dpg.bind_item_theme(
            dpg.add_button(pos=(int(505 * scale + _x), int(115 * scale + __y)), tag=context.axis[11]['name'] + 'bnt_p',
                           width=w,
                           height=h), i_theme)
        dpg.bind_item_theme(
            dpg.add_button(pos=(int(705 * scale + _x), int(70 * scale + __y)), tag=context.axis[11]['name'] + 'bnt_m',
                           width=w,
                           height=h), i_theme)

        with dpg.group(pos=(50, 800)):
            dpg.add_spacer(height=5)
            dpg.add_text(default_value=txt.SELECT_MOVE_MODE)
            dpg.add_radio_button(tag="rb_move_mode_sel", items=self.move_mode_list, horizontal=True,
                                 default_value=self.move_mode_list[context.ctrl_mode],
                                 callback=self.rb_move_mode_click)

        # with dpg.group(pos=(300, 800)):
        #     with dpg.group(horizontal=True):
        #         dpg.add_button(label=txt.INIT_PLATFORM_BTN, height=40, width=200,
        #                        callback=self.btn_init_platform_click, tag="btn_init_platform")
        #         setBtnEnabled("btn_init_platform", True)
        #     init_platforms_complete(False)
        context.t = Timer(1, self.timer_read_axis)
        context.t.start()
        with dpg.item_handler_registry(tag="script_code_handler"):
            dpg.add_item_clicked_handler(button=0, callback=script_code_click_callback)
        dpg.bind_item_handler_registry("script_code", "script_code_handler")
        with dpg.handler_registry():
            dpg.add_mouse_release_handler(callback=self.item_release_callback)
            dpg.add_mouse_down_handler(callback=self.item_down_callback)

    def add_preset_table(self, title, preset_arr, comm_name, pres_code):
        with dpg.group(horizontal=False):
            dpg.add_text(default_value=title)
            for i in range(0, 10):
                with dpg.group(horizontal=True):
                    dpg.add_text(tag=comm_name + str(i),
                                 default_value=f"{preset_arr[i]['name']}")

                    dpg.add_button(label=txt.SET_PRESET_BTN, height=20, width=100,
                                   callback=btn_store_as_preset,
                                   user_data=i + pres_code)  # tag="btn_save_preset_left_" + str(i)

                    dpg.add_button(label=txt.MOVE_TO_PRESET_BTN, height=20, width=100,
                                   callback=self.btn_move_to_preset_click,
                                   user_data=i + pres_code)  # tag="btn_goto_preset_" + str(i))

    def init_preset_page(self):
        with dpg.group(horizontal=True):
            self.add_preset_table("left", context.preset_left, "preset_left_", 0x10)

            self.add_preset_table("table", context.preset_table, "preset_table_", 0x20)

            self.add_preset_table("right", context.preset_right, "preset_right_", 0x40)

            self.add_preset_table("all", context.preset_all, "preset_all_", 0x80)

    def add_textures(self):

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
        dpg.pop_container_stack()


def btn_connect_table_callback(sender, app_data, user_data):
    if user_data == 1:
        disconnect_table()
    elif user_data == 0:
        if connect_table():
            set_conn_states("table_ctrl_state", "table_conn_btn", 2)


def btn_connect_platform_callback(sender, app_data, user_data):
    if user_data == 1:
        disconnect_platform()
    elif user_data == 0:
        if connect_platform():
            set_conn_states("platform_ctrl_state", "platform_conn_btn", 2)


def btn_store_as_preset(sender, app_data, user_data):
    store_preset_pos(user_data)
    save_presets()


def speed_edit_callback(app_data, user_data):
    speed_ = dpg.get_value("EditSpeed")
    speed_ = re.sub(r'\D', '', speed_)
    if speed_.isdigit():
        # print("speed is digit")
        set_speed_value(int(speed_))
    else:
        # print("speed is not digit")
        speed_ = dpg.get_value('SliderSpeed')
        set_speed_value(int(speed_))


def step_edit_callback(sender, app_data, user_data):
    steps = dpg.get_value("EditStep")
    if steps.replace('.', '', 1).isdigit():
        set_step_value(float(steps))
    else:
        steps = dpg.get_value('SliderStep')
        set_step_value(float(steps))


context.motionGUI = MotionGUI()
context.moving_right = False
