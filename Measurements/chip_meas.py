import threading

from core.gui_helper import *
from core.texts import *

context = Context()

MAX_AREA_SIZE = 1000
MIN_AREA_SIZE = 20


class ChipMeasureControl:
    CHIP_TABLE_WDTH = 500

    def __init__(self):
        self.max_val = 0
        self.pm_dev = None
        self.pm_module = -1
        self.meas_chan = -1
        self.pm_chan = -1

    def init_chip_meas_page(self):
        dpg.push_container_stack(context.texture_reg)
        self.width_area, self.height_area, channels_area, self.data_area = dpg.load_image("Pics/scan_area.png")
        dpg.add_static_texture(width=self.width_area, height=self.height_area,
                               default_value=self.data_area, tag="texture_area")
        dpg.pop_container_stack()

        with dpg.theme() as self.text_state_aimed:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 255, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (37, 37, 38, 255))
        with dpg.theme() as self.text_state_unaimed:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (37, 37, 38, 255))
        with dpg.theme() as self.meas_img_btns_theme:
            with dpg.theme_component(0):
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0)
        with dpg.theme() as self.meas_btns_active_theme:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 150, 50))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 30, 80))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [29, 151, 236, 25])
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0, 0)
        with dpg.theme() as self.meas_btns_passive_theme:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (37, 37, 38, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 30, 80))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [29, 151, 236, 25])
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0, 0)

        with dpg.group(horizontal=True):
            dpg.add_group(tag='meas_table')
            self.prepare_table()
            dpg.add_spacer(width=5)
            with dpg.group():
                dpg.add_button(label="Стыковка слева", width=200, height=30,
                               callback=self.aiming_callback, user_data=(LEFT_CHAN,))

                dpg.add_button(label="Стыковка справа", width=200, height=30,
                               callback=self.aiming_callback, user_data=(RIGHT_CHAN,))

                # Выбор измерителя для автоматизированной стыковки
                dpg.add_text(default_value="Выбор измерителя")
                dpg.add_combo(tag="chip_device", items=[DEV_NOT_FOUND], default_value=DEV_NOT_FOUND, width=200,
                              callback=self.select_pm)
                dpg.add_text(default_value="Канал измерителя")
                with dpg.group(horizontal=True):
                    dpg.add_combo(tag="chip_meas_chanel", items=["Нет"], default_value='Нет', width=100,
                                  callback=self.select_pm_chan)
                    dpg.add_spacer(width=10)
                    dpg.add_text(tag="chip_meas_power", default_value="")

                # Параметры области автоматизированной стыковки
                dpg.add_text(default_value="Параметры области стыковки")
                with dpg.group(horizontal=True):
                    context.editor_list.append("aim_area_width_step")
                    with dpg.group():
                        dpg.add_input_text(tag="aim_area_width_step", default_value="500", width=60, height=16,
                                           callback=self.input_area_width_step_callback)
                        dpg.add_text(default_value=" шаги ")
                    context.editor_list.append("aim_area_width_um")
                    with dpg.group():
                        dpg.add_input_text(tag="aim_area_width_um", default_value="500", width=60, height=16,
                                           callback=self.input_area_width_um_callback)
                        dpg.add_text(default_value=" мкм ")

                with dpg.group(horizontal=True):
                    dpg.add_image('texture_area', tag='area_pic')  # , pos=(400 + left_margin, 223 + top_margin))
                    dpg.add_tooltip('area_pic', tag="aiming_tooltip")
                    dpg.add_stage(label="qwe")
                    with dpg.group():
                        dpg.add_spacer(height=50)
                        with dpg.group(horizontal=True):
                            context.editor_list.append("aim_area_height_step")
                            with dpg.group():
                                dpg.add_input_text(tag="aim_area_height_step", default_value="500", width=60, height=16,
                                                   callback=self.input_area_height_step_callback)
                                dpg.add_text(default_value=" шаги ")
                            context.editor_list.append("aim_area_height_um")
                            with dpg.group():
                                dpg.add_input_text(tag="aim_area_height_um", default_value="500", width=60, height=16,
                                                   callback=self.input_area_height_um_callback)
                                dpg.add_text(default_value=" мкм ")

                self.input_area_width_step_callback("aim_area_width_step", 0, 0)
                self.input_area_height_step_callback("aim_area_height_step", 0, 0)

            #                with dpg.group():
            #                    dpg.add_spacer(height=10)
            #                    dpg.add_button(label="Измерить все каналы", width=200, height=30)
            #                    dpg.add_spacer(height=10)
            #                    dpg.add_text(default_value=" Файл отчета ")
            #                    context.editor_list.append("wl_report_file_auto")
            #                    dpg.add_input_text(label="", tag="wl_report_file_auto", width=250, default_value="report_ic.csv")

            dpg.add_spacer(width=10)
            with dpg.group():
                dpg.add_text(default_value="Тип кристалла")
                dpg.add_combo(tag="chip_select", width=125, items=context.chip_list, default_value=context.chip_list[0],
                              callback=self.chip_select_callback)
                dpg.add_spacer(height=10)
                dpg.add_text(default_value=f"{context.chip_chans_left} входов", tag='chip_chans_left')
                dpg.add_spacer(height=10)
                dpg.add_text(default_value=f"{context.chip_chans_right} выходов", tag='chip_chans_right')
                dpg.add_spacer(height=10)
                dpg.add_text(default_value=f"Расстояние между каналами: {context.chip_chans_dy} мкм",
                             tag='chip_chans_dy')
                dpg.add_spacer(height=10)
                dpg.add_text(default_value=f"Расстояние между чипами: {context.chip_chans_dy} мкм", tag='chips_dy')
                dpg.add_spacer(height=200)
                dpg.add_image_button(context.axis[1]['txt_p'], pos=(1350, 100), tag="strip_move_up",
                                     callback=self.strip_move_updown, user_data=1)
                dpg.add_image_button(context.axis[1]['txt_m'], pos=(1350, 220), tag="strip_move_down",
                                     callback=self.strip_move_updown, user_data=2)
            self.chip_select_callback(0, 0, 0)

    def strip_move_updown(self, sender, app_data, user_data):
        context.gui_hlp.showMessage("Переход к следующему чипу...", txt.BREAK, DLG_CT_BREAK_PROC)
        if user_data == 1:  # перемещение вверх
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_table_to_chip,
                                                args=[context.chips_dy], daemon=True)
        else:  # перемещение вниз
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_table_to_chip,
                                                args=[-context.chips_dy], daemon=True)
        self.thread_proc.start()

    def select_pm(self, sender, app_data, user_data):
        device = dpg.get_value('chip_device')
        chan_list = []
        if device == POWER_METER_1:
            self.pm_dev = context.device_worker.pm2100_1_ctrl
            for i in range(0, 20):
                if context.act_chans[i]:
                    chan_list.append(str(i))
        elif device == POWER_METER_2:
            self.pm_dev = context.device_worker.pm2100_2_ctrl
            for i in range(20, 40):
                if context.act_chans[i]:
                    chan_list.append(str(i - 20))
        elif device == POWER_METER_3:
            self.pm_dev = context.device_worker.pm2100_3_ctrl
            for i in range(40, 60):
                if context.act_chans[i]:
                    chan_list.append(str(i - 40))
        if len(chan_list) == 0:
            self.pm_dev = None
            chan_list = ['Нет']
        dpg.configure_item('chip_meas_chanel', items=chan_list)
        dpg.set_value('chip_meas_chanel', chan_list[0])

    def select_pm_chan(self, sender, app_data, user_data):
        chan = dpg.get_value('chip_meas_chanel')
        if not chan.isdigit():
            self.meas_chan = -1
            dpg.set_value("chip_meas_power", "***")
        else:
            self.meas_chan = int(chan)
            if self.pm_dev == context.device_worker.pm2100_2_ctrl:
                self.meas_chan += 20
            elif self.pm_dev == context.device_worker.pm2100_3_ctrl:
                self.meas_chan += 40

    def display_aiming_details(self, width, height):
        dpg.delete_item("aiming_tooltip", children_only=True)
        calc_aiming_window(width, height)
        dpg.push_container_stack("aiming_tooltip")
        dpg.add_text(f'Шагов стыковки:{context.aim_steps}')
        for i in range(context.aim_steps):
            dpg.add_text(f'Шаг {i + 1}й:')
            dpg.add_text(
                f'{context.aim_y_width[i]}x{context.aim_z_step[i] * context.aim_z_count[i]} ({context.aim_y_width[i] * NM_PER_STEP_Y / 1000}x'
                f'{context.aim_z_step[i] * context.aim_z_count[i] * NM_PER_STEP_Z / 1000} мкм)')
            dpg.add_text(f'  По Z - {context.aim_z_count[i]} шагов по {context.aim_z_step[i]}')
        dpg.pop_container_stack()

    def input_area_width_step_callback(self, sender, app_data, user_data):
        val = context.gui_hlp.check_edit_data(sender, int, MAX_AREA_SIZE, MIN_AREA_SIZE)
        val_um = val * NM_PER_STEP_Y / 1000
        dpg.set_value("aim_area_width_um", str(val_um))
        self.display_aiming_details(val, int(dpg.get_value('aim_area_height_step')))

    def input_area_width_um_callback(self, sender, app_data, user_data):
        val = context.gui_hlp.check_edit_data(sender, float, MAX_AREA_SIZE * NM_PER_STEP_Y / 1000,
                                              MIN_AREA_SIZE * NM_PER_STEP_Y / 1000)
        dpg.set_value("aim_area_width_um", str(val))
        val_steps = int(val * 1000 // NM_PER_STEP_Y)
        dpg.set_value("aim_area_width_step", val_steps)
        self.display_aiming_details(val_steps, int(dpg.get_value('aim_area_height_step')))

    def input_area_height_step_callback(self, sender, app_data, user_data):
        val = context.gui_hlp.check_edit_data(sender, int, MAX_AREA_SIZE, MIN_AREA_SIZE)
        val_um = val * NM_PER_STEP_Z / 1000
        dpg.set_value("aim_area_height_um", str(val_um))
        self.display_aiming_details(int(dpg.get_value('aim_area_width_step')), val)

    def input_area_height_um_callback(self, sender, app_data, user_data):
        val = context.gui_hlp.check_edit_data(sender, float, MAX_AREA_SIZE * NM_PER_STEP_Z / 1000,
                                              MIN_AREA_SIZE * NM_PER_STEP_Z / 1000)
        dpg.set_value("aim_area_height_um", str(val))
        val_steps = int(val * 1000 // NM_PER_STEP_Z)
        dpg.set_value("aim_area_height_step", val_steps)
        self.display_aiming_details(int(dpg.get_value('aim_area_width_step')), val_steps)

    def chip_select_callback(self, sender, app_data, user_data):
        chip_type = dpg.get_value('chip_select')
        load_chip_params(chip_type)
        dpg.set_value('chip_chans_left', f"{context.chip_chans_left} входов")
        dpg.set_value('chip_chans_right', f"{context.chip_chans_right} выходов")
        dpg.set_value('chip_chans_dy', f"Расстояние между каналами: {context.chip_chans_dy} мкм")
        dpg.set_value('chips_dy', f"Расстояние между чипами: {context.chips_dy} мкм")
        if context.chip_ctrl.active_chan_left >= context.chip_chans_left:
            context.chip_ctrl.active_chan_left = 0
        if context.chip_ctrl.active_chan_right >= context.chip_chans_right:
            context.chip_ctrl.active_chan_right = 0
        self.prepare_table()

    def prepare_table(self):
        dpg.delete_item("meas_table", children_only=True)

        dpg.push_container_stack('meas_table')
        # dpg.add_child_window(autosize_x=True, autosize_y=True)
        with dpg.child_window(height=500, width=700, tag="tg"):
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_image('chan_pos_left', show=True, tag='pos_chan_left', pos=(5, 29))
                with dpg.table(header_row=True, resizable=False, policy=dpg.mvTable_SizingStretchProp,
                               width=self.CHIP_TABLE_WDTH,
                               borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True):
                    max_chan = max(context.chip_chans_left, context.chip_chans_right)
                    dpg.add_table_column(label="  ")
                    dpg.add_table_column(label="    ")
                    dpg.add_table_column(label="")
                    dpg.add_table_column(label="                 ")
                    dpg.add_table_column(label="")
                    dpg.add_table_column(label="    ")
                    dpg.add_table_column(label="  ")
                    for i in range(max_chan):
                        if i < context.chip_chans_left:
                            context.chip_ctrl.add_channel(i, LEFT_CHAN)
                        if i < context.chip_chans_right:
                            context.chip_ctrl.add_channel(i, RIGHT_CHAN)

                        with dpg.table_row(height=1):
                            with dpg.table_cell():
                                if i < context.chip_chans_left:
                                    dpg.add_button(label=str(i + 1), width=50, callback=self.set_act_chan_callback,
                                                   user_data=(i | LEFT_CHAN,), tag="ch_num_l_" + str(i))
                                    dpg.bind_item_theme("ch_num_l_" + str(i), self.meas_btns_passive_theme)

                            with dpg.table_cell():
                                if i < context.chip_chans_left:
                                    with dpg.group(horizontal=True):
                                        dpg.add_image_button('left_arrow', show=True, user_data=i | LEFT_CHAN,
                                                             callback=self.goto_chan, tag='pos_chan_left' + str(i))
                                        dpg.bind_item_theme('pos_chan_left' + str(i), self.meas_img_btns_theme)

                                        dpg.add_image_button('aiming', show=True, user_data=i | LEFT_CHAN,
                                                             callback=self.show_aiming_res,
                                                             tag='charts_chan_left' + str(i))
                                        dpg.bind_item_theme('charts_chan_left' + str(i), self.meas_img_btns_theme)

                                        dpg.add_text(default_value='-', tag="state_chan_left" + str(i))
                                        dpg.bind_item_theme("state_chan_left" + str(i), self.text_state_unaimed)

                            with dpg.table_cell():
                                pass
                            #                                if i < context.chip_chans_left:
                            #                                    dpg.add_checkbox(default_value=context.chip_ctrl.get_chan_measure(i, LEFT_CHAN),
                            #                                                     tag="ch_test_l" + str(i),
                            #                                                     callback=self.test_turn, user_data=i | LEFT_CHAN)

                            with dpg.table_cell():
                                dpg.add_text(default_value=" ")

                            with dpg.table_cell():
                                pass
                            #                                if i < context.chip_chans_right:
                            #                                    dpg.add_checkbox(default_value=context.chip_ctrl.get_chan_measure(i, RIGHT_CHAN),
                            #                                                     tag="ch_test_r" + str(i),
                            #                                                     callback=self.test_turn, user_data=i | RIGHT_CHAN)
                            with dpg.table_cell():
                                if i < context.chip_chans_right:
                                    with dpg.group(horizontal=True):
                                        dpg.add_text(default_value='-', tag="state_chan_right" + str(i))
                                        dpg.bind_item_theme("state_chan_right" + str(i), self.text_state_unaimed)

                                        dpg.add_image_button("aiming", show=True, user_data=i | RIGHT_CHAN,
                                                             callback=self.show_aiming_res,
                                                             tag="charts_chan_right" + str(i))
                                        dpg.bind_item_theme("charts_chan_right" + str(i), self.meas_img_btns_theme)

                                        dpg.add_image_button("right_arrow", show=True, user_data=i | RIGHT_CHAN,
                                                             callback=self.goto_chan, tag="pos_chan_right" + str(i))
                                        dpg.bind_item_theme("pos_chan_right" + str(i), self.meas_img_btns_theme)
                            with dpg.table_cell():
                                if i < context.chip_chans_right:
                                    dpg.add_button(label=str(i + 1), width=50, callback=self.set_act_chan_callback,
                                                   user_data=(i | RIGHT_CHAN,), tag="ch_num_r_" + str(i))
                                    dpg.bind_item_theme("ch_num_r_" + str(i), self.meas_btns_passive_theme)

                with dpg.group():
                    dpg.add_image('chan_pos_right', show=True, tag='pos_chan_right',
                                  pos=(self.CHIP_TABLE_WDTH + 70, 30))
        self.set_act_chan_dlg(0 | LEFT_CHAN)
        self.set_act_chan_dlg(0 | RIGHT_CHAN)
        dpg.pop_container_stack()

    def set_act_chan_callback(self, sender, app_data, user_data):
        context.gui_hlp.confirm_msg(message='Установить позицию напортив канала как текущую? ',
                                    function=self.set_act_chan_dlg, args=user_data)

    def set_act_chan_dlg(self, *args):
        num = args[0] & 0xFF
        chan = args[0] & 0xF00
        if chan & LEFT_CHAN:  # left channel
            context.chip_ctrl.stateL = (context.chip_ctrl.stateL & 0xFF00) or num
        else:  # right channel
            context.chip_ctrl.stateR = (context.chip_ctrl.stateR & 0xFF00) or num

    def set_act_chan(self, *args):
        num = args[0] & 0xFF
        chan = args[0] & 0xF00
        if chan & LEFT_CHAN:  # left channel
            if context.chip_ctrl.active_chan_left != -1:
                dpg.bind_item_theme("ch_num_l_" + str(context.chip_ctrl.active_chan_left), self.meas_btns_passive_theme)

            context.chip_ctrl.set_active_chan(num, LEFT_CHAN)
            dpg.bind_item_theme("ch_num_l_" + str(num), self.meas_btns_active_theme)
            dpg.configure_item('pos_chan_left', pos=(0, 29 + 24 * num))
        else:  # right channel
            if context.chip_ctrl.active_chan_right != -1:
                dpg.bind_item_theme("ch_num_r_" + str(context.chip_ctrl.active_chan_right),
                                    self.meas_btns_passive_theme)

            context.chip_ctrl.set_active_chan(num, RIGHT_CHAN)
            dpg.bind_item_theme("ch_num_r_" + str(num), self.meas_btns_active_theme)
            dpg.configure_item('pos_chan_right', pos=(self.CHIP_TABLE_WDTH + 70, 29 + 24 * num))

    def show_aiming_res(self, sender, app_data, user_data):
        if user_data & LEFT_CHAN:
            context.gui_hlp.show_chan_chart_hint(user_data & 0xFF, LEFT_CHAN)
        else:
            context.gui_hlp.show_chan_chart_hint(user_data & 0xFF, RIGHT_CHAN)

    def goto_chan(self, sender, app_data, user_data):
        context.gui_hlp.showMessage(txt.PLATFORM_POSITIONING_MSG, txt.BREAK, DLG_CT_BREAK_PROC)
        if user_data & LEFT_CHAN:
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_platform_to_chan,
                                                args=[LEFT_CHAN, user_data & 0XFF, context.chip_chans_dy], daemon=True)
        else:
            self.thread_proc = threading.Thread(target=context.zcontrollers.move_platform_to_chan,
                                                args=[RIGHT_CHAN, user_data & 0XFF, context.chip_chans_dy], daemon=True)
        self.thread_proc.start()

    def aiming_callback(self, sender, app_data, user_data):
        context.gui_hlp.confirm_msg(message=f'Провести стыковку канала? ', function=self.aiming, args=user_data)

    def aiming(self, *args):
        side = args[0]
        if side & LEFT_CHAN:
            num = context.chip_ctrl.active_chan_left
        else:
            num = context.chip_ctrl.active_chan_right

        if ((not context.device_worker.is_pm2100_1_connected) and
                (not context.device_worker.is_pm2100_2_connected) and
                (not context.device_worker.is_pm2100_3_connected)):
            context.logger.log_warning(txt.PM_NOT_CONNECTED)
            context.gui_hlp.popup_close()
            return
        if not context.zplatform.is_connected:
            context.logger.log_warning(txt.PLATFORMS_NOT_CONNECTED)
            context.gui_hlp.popup_close()
            return

        pm_channel = int(dpg.get_value("chip_meas_chanel"))
        module = pm_channel // 4  # вычисляем модуль
        meas_chan = pm_channel % 4  # вычисляем канал

        context.gui_hlp.showMessage(txt.PLATFORM_AIMING_MSG, txt.BREAK, DLG_CT_BREAK_PROC, prog_bar=True)

        self.thread_proc = threading.Thread(target=context.pmap_procedures.aiming,
                                            args=[side, num, context.aim_steps, context.aim_y_width,
                                                  context.aim_z_count,
                                                  context.aim_z_step, self.pm_dev, module, meas_chan,
                                                  context.aim_x_speed], daemon=True)
        #        self.thread_proc = threading.Thread(target=self.exec_measure, args=[], daemon=True)
        self.thread_proc.start()

    def slide_chip(self, *args):
        pass

    def test_turn(self, sender, app_data, user_data):
        if user_data & LEFT_CHAN:
            context.chip_ctrl.set_chan_measure(user_data & 0xFF,
                                               bool(dpg.get_value("ch_test_l" + str(user_data & 0xFF))), LEFT_CHAN)
        else:
            context.chip_ctrl.set_chan_measure(user_data & 0xFF,
                                               bool(dpg.get_value("ch_test_r" + str(user_data & 0xFF))), RIGHT_CHAN)

    def chip_loop(self):
        def process_chanels(idx_, chan_, side):
            state = chan_.state
            if state & CHAN_IS_CHANGED:
                if state & CHAN_IS_AIMED:
                    dpg.set_value(f"state_chan_{side}{idx_}", 'А')
                    dpg.bind_item_theme(f"state_chan_{side}{idx_}", self.text_state_aimed)
                else:
                    dpg.set_value(f"state_chan_{side}{idx_}", '-')
                    dpg.bind_item_theme(f"state_chan_{side}{idx_}", self.text_state_unaimed)
                chan_.state &= ~CHAN_IS_CHANGED

        for idx, chan in enumerate(context.chip_ctrl.left_channels):
            process_chanels(idx, chan, "left")
        for idx, chan in enumerate(context.chip_ctrl.right_channels):
            process_chanels(idx, chan, "right")

        if context.chip_ctrl.active_chan_left != (context.chip_ctrl.stateL & 0xFF):
            self.set_act_chan((context.chip_ctrl.stateL & 0xFF) | LEFT_CHAN)
            context.chip_ctrl.stateL = (context.chip_ctrl.stateL & 0xFF00) or context.chip_ctrl.active_chan_left

        if context.chip_ctrl.active_chan_right != (context.chip_ctrl.stateR & 0xFF):
            self.set_act_chan((context.chip_ctrl.stateR & 0xFF) | RIGHT_CHAN)
            context.chip_ctrl.stateR = (context.chip_ctrl.stateR & 0xFF00) or context.chip_ctrl.active_chan_right


context.chip_meas_ctrl = ChipMeasureControl()
