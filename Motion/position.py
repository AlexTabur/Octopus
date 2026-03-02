import dearpygui.dearpygui as dpg

from core.consts import *
from core.context import Context

context = Context()


class Positions:
    MSG_WIDTH = 240
    MSG_HEIGHT = 100

    """build cmd and convert to bytes with control sum"""

    def __init__(self):
        pass

    def add_pos_window(self):
        with dpg.window(tag="pos_window", label="Позиционирование", no_close=True, no_resize=True, pos=(1400, 700)):
            #            with dpg.texture_registry(show=False):
            #                width, height, channels, data = dpg.load_image("Pics//positions.png")
            #                dpg.add_dynamic_texture(width=width, height=height, default_value=data, tag="texture_img")
            #            dpg.add_image("texture_img", pos=(5, 5))
            with dpg.group(horizontal=True):
                dpg.add_checkbox(label='Управление с клавиатуры', callback=self.set_key_ctrl_callback,
                                 default_value=False)
                dpg.add_spacer(width=20)
                dpg.add_checkbox(label='', callback=self.set_left_lock_callback, default_value=False)
                dpg.add_image("texture_locking")
                dpg.add_checkbox(label='', callback=self.set_right_lock_callback, default_value=False)
            dpg.add_spacer(height=5)
            with dpg.group(horizontal=True):
                with dpg.table(header_row=True, resizable=False, policy=dpg.mvTable_SizingStretchProp, width=400,
                               borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True):
                    # dpg.add_table_column(label=txt.AXIS, width=20)
                    # dpg.add_table_column(label=txt.POSITION)
                    dpg.add_table_column(label="")
                    dpg.add_table_column(label="  Левая   ", no_resize=True)
                    dpg.add_table_column(label="")
                    dpg.add_table_column(label="  Стол    ", no_resize=True)
                    dpg.add_table_column(label="")
                    dpg.add_table_column(label="  Правая  ", no_resize=True)
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(default_value="X  ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.x1_line_i]['name'])
                        with dpg.table_cell():
                            dpg.add_text(default_value="")
                        with dpg.table_cell():
                            dpg.add_text(default_value="         ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="X  ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.x2_line_i]['name'])
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(default_value="Y  ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.y1_line_i]['name'])
                        with dpg.table_cell():
                            dpg.add_text(default_value="Y  ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.y_table_i]['name'])
                        with dpg.table_cell():
                            dpg.add_text(default_value="Y  ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.y2_line_i]['name'])
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(default_value="Z  ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.z1_line_i]['name'])
                        with dpg.table_cell():
                            dpg.add_text(default_value="")
                        with dpg.table_cell():
                            dpg.add_text(default_value="         ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="Z  ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.z2_line_i]['name'])
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(default_value="X° ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.x1_ang_i]['name'])
                        with dpg.table_cell():
                            dpg.add_text(default_value="")
                        with dpg.table_cell():
                            dpg.add_text(default_value="         ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="X° ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.x2_ang_i]['name'])
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(default_value="Y° ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.y1_ang_i]['name'])
                        with dpg.table_cell():
                            dpg.add_text(default_value="")
                        with dpg.table_cell():
                            dpg.add_text(default_value="         ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="Y° ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.y2_ang_i]['name'])
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(default_value="Z° ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.z1_ang_i]['name'])
                        with dpg.table_cell():
                            dpg.add_text(default_value="")
                        with dpg.table_cell():
                            dpg.add_text(default_value="         ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="Z° ")
                        with dpg.table_cell():
                            dpg.add_text(default_value="***", tag=context.axis[context.z2_ang_i]['name'])

    def set_key_ctrl_callback(self, sender, app_data, user_data):
        if dpg.get_value(sender):
            context.ctrl_by_keyboard = True
        else:
            context.ctrl_by_keyboard = False

    def set_left_lock_callback(self, sender, app_data, user_data):
        if dpg.get_value(sender):
            context.lock_left_side = True
        else:
            context.lock_left_side = False

    def set_right_lock_callback(self, sender, app_data, user_data):
        if dpg.get_value(sender):
            context.lock_right_side = True
        else:
            context.lock_right_side = False

    def x_pos_to_um(self, pos):
        return pos * NM_PER_STEP_X / 1000

    def y_pos_to_um(self, pos):
        return pos * NM_PER_STEP_Y / 1000

    def z_pos_to_um(self, pos):
        return pos * NM_PER_STEP_Z / 1000


context.positions = Positions()
