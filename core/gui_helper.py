import time
import dearpygui.dearpygui as dpg
from core.context import Context
from core.consts import *
from core.utils import *
import core.texts as txt
import cv2

context = Context()

DLG_CT_BREAK_PROC = 0
DLG_CT_CLOSE = 1
DLG_CT_CONFIRM = 2
DLG_CT_NO_CLOSE = 3

class GUI_Helper:
    MSG_WIDTH = 240
    MSG_HEIGHT = 115

    """build cmd and convert to bytes with control sum"""
    def __init__(self):
        self.res = False
        self.prog_bar = None
        #self._cmd_int = 0

    def prepare_msg_window(self):
        with dpg.window(tag="popup_msg", no_resize=True, modal=True, show=False, no_close=True,
                        pos=(context.main_width/2-self.MSG_WIDTH/2, context.main_height/2-self.MSG_HEIGHT/2),
                        width=self.MSG_WIDTH, height=self.MSG_HEIGHT):
            dpg.add_text(default_value="msg", tag="popup_text", wrap=self.MSG_WIDTH-25)
            dpg.add_button(tag="popup_btn", pos = (self.MSG_WIDTH//2 - 50, self.MSG_HEIGHT - 30), callback=self.popup_close_callback, width=100)
            dpg.add_button(tag="popup_cancel_btn", pos = (self.MSG_WIDTH//2 + 150, self.MSG_HEIGHT - 30), callback=self.popup_cancel_callback, width=100, show=False)
            dpg.add_spacer(height=10)
            dpg.add_progress_bar(label="", tag="popup_pb", default_value=0, show=False, width=self.MSG_WIDTH-20, height=10)

    def init_progress_bar(self,steps):
        self.pb_step_d = 1 / steps
        self.pb_step = 0
        dpg.set_value("popup_pb", self.pb_step)

    def progress_bar_step(self,steps=1):
        self.pb_step += self.pb_step_d
        dpg.set_value("popup_pb", self.pb_step)

    def set_conn_states(self, state_label, button, state):
        if state == 1: # Connected
            dpg.configure_item(state_label, texture_tag="texture_dev_conn")
            #dpg.set_value(state_label, STATE_CONNECTED)
            #dpg.configure_item(state_label, color=CONNECTED_COLOR)
            dpg.configure_item(button, label=txt.BTN_DISCONNECT)
            self.setBtnEnabled(button, True)
        elif state == 2: # Connecting
            dpg.configure_item(state_label, texture_tag="texture_dev_conng")
            #dpg.set_value(state_label, STATE_CONNECTING)
            #dpg.configure_item(state_label, color=CONNECTING_COLOR)
            dpg.configure_item(button, label=txt.BTN_CONNECT)
            self.setBtnEnabled(button, False)
        else: # Disconnected
            dpg.configure_item(state_label, texture_tag="texture_dev_disc")
            #dpg.set_value(state_label, STATE_DISCONNECTED)
            #dpg.configure_item(state_label, color=DISCONNECTED_COLOR)
            dpg.configure_item(button, label=txt.BTN_CONNECT)
            self.setBtnEnabled(button, True)
        dpg.configure_item(button, user_data=state)

    def showMessage(self, msg, btn, close_type, prog_bar = False):
        dpg.push_container_stack("main_window")
        dpg.set_value("popup_text", msg)
        dpg.configure_item("popup_btn", label=btn)
        dpg.configure_item("popup_msg", show=True)
        if close_type != DLG_CT_NO_CLOSE:
            dpg.configure_item("popup_btn", show=True)
            dpg.configure_item("popup_btn", user_data=close_type)
        else:
            dpg.configure_item("popup_btn", show=False)

        width = dpg.get_item_width("popup_msg")
        height = dpg.get_item_height("popup_msg")

        if prog_bar:
            dpg.configure_item("popup_msg", height=self.MSG_HEIGHT + 15)
            dpg.configure_item("popup_pb", show=True)
            dpg.set_item_pos("popup_pb", [10, self.MSG_HEIGHT-5])
        else:
            dpg.configure_item("popup_pb", show=False)

        viewport_width = dpg.get_viewport_client_width()
        viewport_height = dpg.get_viewport_client_height()

        dpg.set_item_pos("popup_msg", [viewport_width / 2 - width / 2, viewport_height / 2 - height / 2])

        dpg.pop_container_stack()

    def popup_close(self):
        dpg.configure_item("popup_msg", show=False)

    def popup_close_callback(self, sender, app_data, user_data):
        if user_data == DLG_CT_CONFIRM:
            self.res = True
            self.popup_close()
        if user_data == DLG_CT_CLOSE:
            self.popup_close()
        elif user_data == DLG_CT_BREAK_PROC:
            context.break_proc = True

    def popup_cancel_callback(self, sender, app_data, user_data):
        self.res = False
        self.popup_close()

    def init_platforms_complete(self, performed):
#        if performed:
#            self.setBtnEnabled("btn_set_as_zero",True)
#            self.setBtnEnabled("btn_goto_zero",True)
#        else:
#            self.setBtnEnabled("btn_set_as_zero",False)
#            self.setBtnEnabled("btn_goto_zero",False)
        context.platforms_initialized = performed

    def setBtnEnabled(self, tag, en):
        if en:
            dpg.bind_item_theme(tag, context.enabled_btn_theme)
        else:
            dpg.bind_item_theme(tag, context.disabled_btn_theme)

    def initThemes(self):
        # активные кнопки
         with dpg.theme() as context.enabled_btn_theme:
             with dpg.theme_component(dpg.mvAll):
                 dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 50, 50), category=dpg.mvThemeCat_Core)
                 dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 30, 80), category=dpg.mvThemeCat_Core)
                 dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [29, 151, 236, 25], category=dpg.mvThemeCat_Core)
                 #dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 9, category=dpg.mvThemeCat_Core)
                 #dpg.add_theme_color(dpg.mvColorButton, (255, 255, 0, 255))

         # неактивные кнопки
         with dpg.theme() as context.disabled_btn_theme:
             with dpg.theme_component(dpg.mvAll):
                 dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 30, 30), category=dpg.mvThemeCat_Core)
                 dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 30, 30), category=dpg.mvThemeCat_Core)
                 dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (30, 30, 30), category=dpg.mvThemeCat_Core)
                 #dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                 #dpg.add_theme_color(dpg.mvColorButton, (255, 0, 0, 255))

    def apply_preset_name(self, sender, app_data, user_data):
        new_name = dpg.get_value('preset_name')
        if len(new_name)==0:
            context.logger.log('Название пресета не может быть пустым')
            return
        if user_data & 0x10:# left platform
            context.preset_left[user_data & 0xF]['name'] = new_name
            dpg.configure_item("preset_left_"+str(user_data & 0xF), default_value=f"{new_name : >15}")
        elif user_data & 0x20:# table platform
            context.preset_table[user_data & 0xF]['name'] = new_name
            dpg.configure_item("preset_table_"+str(user_data & 0xF), default_value=f"{new_name : >15}")
        elif user_data & 0x40:# right platform
            context.preset_right[user_data & 0xF]['name'] = new_name
            dpg.configure_item("preset_right_"+str(user_data & 0xF), default_value=f"{new_name : >15}")
        elif user_data & 0x80:# all platform
            context.preset_all[user_data & 0xF]['name'] = new_name
            dpg.configure_item("preset_all_"+str(user_data & 0xF), default_value=f"{new_name : >15}")

        dpg.configure_item("popup_name_dlg", show=False)
        save_presets()

    def cancel_preset_name(self, sender, app_data, user_data):
        dpg.configure_item("popup_name_dlg", show=False)

    def input_callback(self, sender, app_data, user_data):
        if len(app_data)>15:
            app_data = app_data[:15]
            dpg.set_value(sender,app_data)

    def prepare_input_window(self):
        with dpg.window(tag="popup_name_dlg", no_resize=True, modal=True, show=False, no_close=True,
                        #pos=(context.main_width/2-self.MSG_WIDTH/2, context.main_height/2-self.MSG_HEIGHT/2),
                        width=400, height=80):
            dpg.add_text(default_value="Введите имя предустановки")
            with dpg.group(horizontal=True):
                context.editor_list.append("preset_name")
                dpg.add_input_text(tag="preset_name", default_value=" ", width=160, height=16, callback=self.input_callback)
                dpg.add_button(tag="btn_save_preset_name", label="Сохранить", callback=self.apply_preset_name, width=100)
                dpg.add_button(tag="btn_cancel_preset_name", label="Отменить", callback=self.cancel_preset_name, width=100)

    def show_preset_dlg(self, presetId, presetName):
        dpg.configure_item("preset_name", default_value=presetName)
        dpg.configure_item("btn_save_preset_name", user_data=presetId)
        dpg.configure_item("popup_name_dlg", show=True)

#    def processDeviceStates(self):
#        if context.zplatform.is_connected:
#            dpg.set_value(state_label, STATE_CONNECTED)
#            dpg.configure_item(state_label, color=CONNECTED_COLOR)
#            dpg.configure_item(button, label=BTN_DISCONNECT)
#            self.setBtnEnabled(button, True)

    def prepare_chart_hint(self):
        with dpg.window(tag="aiming_chart_hint", no_resize=True, modal=False, show=False, no_close=False, autosize=True,
                        pos=(context.main_width/2-self.MSG_WIDTH/2, context.main_height/2-self.MSG_HEIGHT/2)):
            with dpg.group(horizontal=True):
                with dpg.plot(label="", height=150, width=150, no_menus=True, no_title=True) as self.chart1:
                    dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_axis1", no_tick_labels=True, no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis1", no_tick_labels=True, no_tick_marks=True)
                with dpg.plot(label="", height=150, width=150, no_menus=True, no_title=True) as self.chart2:
                    dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_axis2", no_tick_labels=True, no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis2", no_tick_labels=True, no_tick_marks=True)
                with dpg.plot(label="", height=150, width=150, no_menus=True, no_title=True) as self.chart3:
                    dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_axis3", no_tick_labels=True, no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis3", no_tick_labels=True, no_tick_marks=True)
                with dpg.plot(label="", height=150, width=150, no_menus=True, no_title=True) as self.chart4:
                    dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_axis4", no_tick_labels=True, no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis4", no_tick_labels=True, no_tick_marks=True)
                with dpg.plot(label="", height=150, width=150, no_menus=True, no_title=True) as self.chart5:
                    dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_axis5", no_tick_labels=True, no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis5", no_tick_labels=True, no_tick_marks=True)

    def prepare_horiz_chart(self):
        with dpg.window(tag="horiz_chart_hint", no_resize=True, modal=False, show=False, no_close=False, autosize=True,
                        pos=(context.main_width/2-self.MSG_WIDTH/2, context.main_height/2-self.MSG_HEIGHT/2)):
            with dpg.group(horizontal=True):
                with dpg.plot(label="", height=300, width=300, no_menus=True, no_title=True) as self.horiz_chart1:
                    dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_h_axis1", no_tick_labels=True, no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_h_axis1", no_tick_labels=True, no_tick_marks=True)
                with dpg.plot(label="", height=300, width=300, no_menus=True, no_title=True) as self.horiz_chart2:
                    dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_h_axis2", no_tick_labels=True, no_tick_marks=True)
                    dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_h_axis2", no_tick_labels=True, no_tick_marks=True)

#                with dpg.item_handler_registry(tag="horiz_widget_handler1"):
#                    dpg.add_item_clicked_handler(button=0, callback=self.plot_h_callback1)
#                with dpg.item_handler_registry(tag="horiz_widget_handler2"):
#                    dpg.add_item_clicked_handler(button=0, callback=self.plot_h_callback2)
#                dpg.bind_item_handler_registry(self.horiz_chart1, "horiz_widget_handler1")
#                dpg.bind_item_handler_registry(self.horiz_chart2, "horiz_widget_handler2")

    def plot_h_callback1(self):
        x,y = dpg.get_plot_mouse_pos()
        context.logger.log_com(f"Перемещение Y -> {x} мкм, y -> {y}")
#            context.gui_hlp.showMessage(txt.PLATFORM_AIMING_MSG, txt.BREAK, DLG_CT_NO_CLOSE)
#            self.set_platform_pos(context.pmap_procedures.x_axis, context.pmap_procedures.y_axis, int(x/X_MKM_KOEF), int(y/Y_MKM_KOEF))
#            context.gui_hlp.popup_close()

    def plot_h_callback2(self):
        x,y = dpg.get_plot_mouse_pos()
        context.logger.log_com(f"Перемещениеw Y -> {x} мкм, y -> {y}")

    def draw_on_horiz_chart(self,data1,data2):
        def draw_on_chart(chart,data,chart_num):
            dpg.push_container_stack(chart)
            dpg.add_plot_axis(dpg.mvXAxis, label="", tag=f"x_h_axis{chart_num}", no_tick_labels=True, no_tick_marks=True)
            dpg.add_plot_axis(dpg.mvYAxis, label="", tag=f"y_h_axis{chart_num}", no_tick_labels=True, no_tick_marks=True)
            side = 1
            y_width = data.shape[1]
            x_width = data.shape[0]
            if y_width != 0 and x_width != 0:
                for y in range(0, y_width):
                    for x in range(0, x_width):
                        #                   self.ser_data[i][j] = 1 - ((i-25)*(j-25)/(25*25))
                        #                   dpg.draw_quad((-2, -2), (-2, 2), (2, 2), (2, -2), label="qwe", thickness=0.1)
                        red = int(data[x][y]) & 0xFF
                        color = (red, 0, 0)
                        x0 = x * side
                        x1 = x * side + side
                        y0 = y * side
                        y1 = y * side + side
                        dpg.draw_quad((x0, y0), (x0, y1), (x1, y1), (x1, y0), thickness=0.05, fill=color, color=color)

                (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(data)
                # круг на максимальном пикселе
                dpg.draw_circle(center=(maxLoc[1], maxLoc[0]), radius=2, thickness=0.05, color=(255, 255, 255))
                dpg.set_axis_limits(f"y_h_axis{chart_num}", 0, y_width)
                dpg.set_axis_limits(f"x_h_axis{chart_num}", 0, x_width)

            dpg.pop_container_stack()
#        dpg.show_item(chart)

        dpg.delete_item(self.horiz_chart1,children_only=True)
        dpg.delete_item(self.horiz_chart2,children_only=True)

        draw_on_chart(self.horiz_chart1,data1,1)
        draw_on_chart(self.horiz_chart2,data2,2)

        dpg.configure_item("horiz_chart_hint", show=True)

    def draw_on_chart(self,data,chart_num):
        chart = None
        if chart_num==0:
            chart=self.chart1
            dpg.hide_item(self.chart2)
            dpg.hide_item(self.chart3)
            dpg.hide_item(self.chart4)
            dpg.hide_item(self.chart5)
        elif chart_num==1:
            chart=self.chart2
        elif chart_num==2:
            chart=self.chart3
        elif chart_num==3:
            chart=self.chart4
        elif chart_num==4:
            chart=self.chart5
        dpg.show_item(chart)

        dpg.delete_item(chart,children_only=True)
        dpg.push_container_stack(chart)
        dpg.add_plot_axis(dpg.mvXAxis, label="", tag="x_axis"+str(chart_num), no_tick_labels=True, no_tick_marks=True)
        dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis"+str(chart_num), no_tick_labels=True, no_tick_marks=True)
        side = 1
        y_width = data.shape[1]
        x_width = data.shape[0]
        if y_width!=0 and x_width!=0:
            for y in range(0, y_width):
                for x in range(0, x_width):
                    #                   self.ser_data[i][j] = 1 - ((i-25)*(j-25)/(25*25))
                    #                   dpg.draw_quad((-2, -2), (-2, 2), (2, 2), (2, -2), label="qwe", thickness=0.1)
                    red = int(data[x][y]) & 0xFF
                    color = (red, 0, 0)
                    x0 = x * side
                    x1 = x * side + side
                    y0 = y * side
                    y1 = y * side + side
                    dpg.draw_quad((x0, y0), (x0, y1), (x1, y1), (x1, y0), thickness=0.05,
                                  fill=color, color=color)

            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(data)
        # круг на максимальном пикселе
            dpg.draw_circle(center=(maxLoc[1], maxLoc[0]), radius=2, thickness=0.05, color=(255, 255, 255))
            dpg.set_axis_limits("y_axis"+str(chart_num), 0, y_width)
            dpg.set_axis_limits("x_axis"+str(chart_num), 0, x_width)

        dpg.pop_container_stack()

    def show_chart_hint(self,data, count):
        for i in range(count):
            self.draw_on_chart(data[i],i)
        dpg.configure_item("aiming_chart_hint", show=True)

    def show_chan_chart_hint(self, num, left):
        for i in range(5):
            if left:
                self.draw_on_chart(context.chip_ctrl.left_channels[num].aiming_data[i], i)
            else:
                self.draw_on_chart(context.chip_ctrl.right_channels[num].aiming_data[i], i)
        dpg.configure_item("aiming_chart_hint", show=True)

    def selection_callback(self, sender, app_data, user_data):
        # delete window
        with dpg.mutex():
            dpg.configure_item(user_data[0],show = False)
            dpg.delete_item(user_data[0])
        if user_data[1]:
            context.call_count = 2
            context.call_function   = user_data[2]
            context.function_params = user_data[3]#(*user_data[3])

    def confirm_msg(self, message, function, args):

        dpg.push_container_stack("main_window")

        viewport_width = dpg.get_viewport_client_width()
        viewport_height = dpg.get_viewport_client_height()

        with dpg.window(label="", modal=True, no_close=True) as modal_id:
            dpg.add_spacer(height=10)
            dpg.add_text(message, wrap=250)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Ок", width=75, user_data=(modal_id, True, function, args), callback=self.selection_callback)
                dpg.add_button(label="Отмена", width=75, user_data=(modal_id, False), callback=self.selection_callback)

        dpg.pop_container_stack()

        # guarantee these commands happen in another frame
#        dpg.split_frame()
        width = dpg.get_item_width(modal_id)
        height = dpg.get_item_height(modal_id)
        #pos = (context.main_width / 2 - self.MSG_WIDTH / 2, context.main_height / 2 - self.MSG_HEIGHT / 2),
        dpg.set_item_pos(modal_id, [viewport_width / 2 - width / 2, viewport_height / 2 - height / 2])

    def check_edit_data(self, sender, type, upper_bound, lower_bound):
        val = dpg.get_value(sender)
        if type == int:
            val = text_to_int(val)
        elif type == float:
            val = text_to_float(val)

        if val>upper_bound:
            val = upper_bound
        elif val<lower_bound:
            val = lower_bound

        dpg.set_value(sender, val)
        return val

    def check_bounds(self, sender, app_data, user_data):
        self.check_edit_data(sender, user_data[0], user_data[1], user_data[2])

    def show_channels_legend(self, legend_grp, prefix, callback):
        dpg.delete_item(legend_grp,children_only=True)
        dpg.push_container_stack(legend_grp)
        with dpg.table(header_row=False, resizable=False, borders_innerV=True, borders_outerH=True, width=200):
            for i in range(3):
                dpg.add_table_column()
            for i in range(20):
                with dpg.table_row():
                    with dpg.table_cell():
                        dpg.add_checkbox(label=f'Ch{i}',
                                         default_value=True, user_data=i,
                                         tag=f"{prefix}_{i}",callback=callback)
                    with dpg.table_cell():
                        dpg.add_checkbox(label=f'Ch{i+20}',
                                         default_value=True, user_data=i+20,
                                         tag=f"{prefix}_{i+20}",callback=callback)
                    with dpg.table_cell():
                        dpg.add_checkbox(label=f'Ch{i+40}',
                                         default_value=True, user_data=i+40,
                                         tag=f"{prefix}_{i+40}",callback=callback)
        with dpg.group(horizontal=True):
            dpg.add_button(label=f'Показать все',
                           callback=self.show_all_callback, user_data=[1, prefix, callback])
            dpg.add_button(label=f'Скрыть все',
                           callback=self.show_all_callback, user_data=[0, prefix, callback])
        dpg.pop_container_stack()

    def show_all_callback(self, sender, app_data, user_data):
        for i in range(60):
            item = f"{user_data[1]}_{i}"
            if dpg.does_item_exist(item):
                if user_data[0]:
                    dpg.set_value(item, True)
                else:
                    dpg.set_value(item, False)
                user_data[2](item, 0, i)


context.gui_hlp = GUI_Helper()