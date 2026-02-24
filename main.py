from logger import Logger

from core.gui_helper import GUI_Helper
import gui.config_gui
import gui.motion_gui
import Chip.chip_control
import Measurements.meas_powermap
import Measurements.meas_spectrum
import Measurements.PMapping.measuring
from logger import Logger
import Measurements.chip_meas
import Motion.position

from core.utils import *
from core.context import Context
from core.consts import *
import core.texts as txt

context = Context()

load_prameters()  # Загрузка параметров

# arr = np.array([('Preset', np.zeros(13))], context.preset_dt)
# for i in range(0, 10):
#     context.preset_left  = np.append(context.preset_left,  arr)
#     context.preset_right = np.append(context.preset_right, arr)
#     context.preset_table = np.append(context.preset_table, arr)
#     context.preset_all   = np.append(context.preset_all, arr)
# save_presets()
load_presets()
# context.preset_left[7]['name'] = 'Пресет для бубубу'
# print(context.preset_left)
# print(context.preset_right)
# print(context.preset_table)
# print(context.preset_all)

dpg.create_context()
dpg.configure_app(manual_callback_management=True)

big_let_start = 0x00C0  # Capital "A" in cyrillic alphabet
big_let_end = 0x00DF  # Capital "Я" in cyrillic alphabet
small_let_end = 0x00FF  # small "я" in cyrillic alphabet
remap_big_let = 0x0410  # Starting number for remapped cyrillic alphabet
alph_len = big_let_end - big_let_start + 1  # adds the shift from big letters to small
alph_shift = remap_big_let - big_let_start  # adds the shift from remapped to non-remapped

with dpg.font_registry():
    with dpg.font(r"C:\Windows\Fonts\consola.ttf", 14, id="Default font") as default_font:
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
        biglet = remap_big_let  # Starting number for remapped cyrillic alphabet
        for i1 in range(big_let_start, big_let_end + 1):  # Cycle through big letters in cyrillic alphabet
            dpg.add_char_remap(i1, biglet)  # Remap the big cyrillic letter
            dpg.add_char_remap(i1 + alph_len, biglet + alph_len)  # Remap the small cyrillic letter
            biglet += 1  # choose next letter
    dpg.bind_font("Default font")

context.gui_hlp.initThemes()

# for i in chunked_list:
#     barr = bytes(reversed(i))
#     lennn = len(barr)
#     if lennn==4:
#         ff = struct.unpack('!f', barr)
#         print(ff[0])
# ##return bytes.decode(ans, "utf-8")


with dpg.window(tag="main_window", no_resize=True):
    with dpg.texture_registry(show=False) as context.texture_reg:
        width_dev, height_dev, channels_dev, data_dev = dpg.load_image("Pics/dev_conn.png")
        dpg.add_static_texture(width=width_dev, height=height_dev,
                               default_value=data_dev, tag="texture_dev_conn")
        width_dev, height_dev, channels_dev1, data_dev = dpg.load_image("Pics/dev_disc.png")
        dpg.add_static_texture(width=width_dev, height=height_dev,
                               default_value=data_dev, tag="texture_dev_disc")
        width_dev, height_dev, channels_dev2, data_dev = dpg.load_image("Pics/dev_conng.png")
        dpg.add_static_texture(width=width_dev, height=height_dev,
                               default_value=data_dev, tag="texture_dev_conng")
        width_dev, height_dev, channels_dev3, data_dev = dpg.load_image("Pics/locking.png")
        dpg.add_static_texture(width=width_dev, height=height_dev,
                               default_value=data_dev, tag="texture_locking")

    context.gui_hlp.prepare_msg_window()
    context.gui_hlp.prepare_input_window()
    context.gui_hlp.prepare_chart_hint()
    context.gui_hlp.prepare_horiz_chart()

    with dpg.item_handler_registry(tag="horiz_widget_handler1"):
        dpg.add_item_clicked_handler(button=0, callback=context.gui_hlp.plot_h_callback1)
    #    with dpg.item_handler_registry(tag="horiz_widget_handler2"):
    #        dpg.add_item_clicked_handler(button=0, callback=context.gui_hlp.plot_h_callback2)
    dpg.bind_item_handler_registry(context.gui_hlp.horiz_chart1, "horiz_widget_handler1")
    #    dpg.bind_item_handler_registry(context.gui_hlp.horiz_chart2, "horiz_widget_handler2")

    with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingFixedFit):  # , freeze_columns=9):
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        with dpg.table_row():
            with dpg.table_cell():
                dpg.add_spacer(width=10)
                dpg.add_text(default_value=txt.PLATFORM_CTRL_TITLE)
            with dpg.table_cell():
                #                dpg.add_text(tag="platform_ctrl_state", default_value=txt.STATE_DISCONNECTED, color=[255, 0, 0])
                dpg.add_image("texture_dev_disc", tag="platform_ctrl_state")
            with dpg.table_cell():
                dpg.add_button(label=txt.BTN_CONNECT, tag="platform_conn_btn", user_data=0,
                               callback=context.motionGUI.btn_connect_platform_callback, height=25, width=100)
            with dpg.table_cell():
                dpg.add_spacer(width=10)
                dpg.add_text(default_value=txt.METER_TITLE + '1')
            with dpg.table_cell():
                #                dpg.add_text(tag="pm2100_ctrl_state", default_value=txt.STATE_DISCONNECTED, color=[255, 0, 0])
                dpg.add_image("texture_dev_disc", tag="pm2100_ctrl_state1")
            with dpg.table_cell():
                dpg.add_button(label=txt.BTN_CONNECT, tag="pm2100_conn_btn1", user_data=0,
                               callback=context.config_ctrl.connect_pm2100_device1, height=25, width=100)
            with dpg.table_cell():
                dpg.add_spacer(width=10)
                dpg.add_text(default_value=txt.METER_TITLE + '2')
            with dpg.table_cell():
                #                dpg.add_text(tag="pm2100_ctrl_state", default_value=txt.STATE_DISCONNECTED, color=[255, 0, 0])
                dpg.add_image("texture_dev_disc", tag="pm2100_ctrl_state2")
            with dpg.table_cell():
                dpg.add_button(label=txt.BTN_CONNECT, tag="pm2100_conn_btn2", user_data=0,
                               callback=context.config_ctrl.connect_pm2100_device2, height=25, width=100)
            with dpg.table_cell():
                dpg.add_spacer(width=10)
                dpg.add_text(default_value=txt.METER_TITLE + '3')
            with dpg.table_cell():
                #                dpg.add_text(tag="pm2100_ctrl_state", default_value=txt.STATE_DISCONNECTED, color=[255, 0, 0])
                dpg.add_image("texture_dev_disc", tag="pm2100_ctrl_state3")
            with dpg.table_cell():
                dpg.add_button(label=txt.BTN_CONNECT, tag="pm2100_conn_btn3", user_data=0,
                               callback=context.config_ctrl.connect_pm2100_device3, height=25, width=100)
            with dpg.table_cell():
                pass
        with dpg.table_row():
            # УПРАВЛЕНИЕ СТОЛОМ
            with dpg.table_cell():
                dpg.add_text(default_value=txt.TABLE_CTRL_TITLE)
            with dpg.table_cell():
                #                dpg.add_text(tag="table_ctrl_state", default_value=txt.STATE_DISCONNECTED, color=[255, 0, 0])
                dpg.add_image("texture_dev_disc", tag="table_ctrl_state")
            with dpg.table_cell():
                dpg.add_button(label=txt.BTN_CONNECT, tag="table_conn_btn", user_data=0,
                               callback=context.motionGUI.btn_connect_table_callback, height=25, width=100)

            # УПРАВЛЕНИЕ ЛАЗЕРОМ GoLight
            with dpg.table_cell():
                dpg.add_text(default_value=txt.LASER_GOLIGHT_TITLE)
            with dpg.table_cell():
                dpg.add_image("texture_dev_disc", tag="laser_golight_ctrl_state")
            with dpg.table_cell():
                dpg.add_button(label=txt.BTN_CONNECT, tag="laser_golight_conn_btn", user_data=0,
                               callback=context.config_ctrl.connect_laser_golight_device, height=25, width=100)
            # УПРАВЛЕНИЕ СИНХРОНИЗАТОРОМ
            with dpg.table_cell():
                dpg.add_text(default_value=txt.SYNCRONIZER_TITLE)
            with dpg.table_cell():
                dpg.add_image("texture_dev_disc", tag="syncronizer_ctrl_state")
            with dpg.table_cell():
                dpg.add_button(label=txt.BTN_CONNECT, tag="syncronizer_conn_btn", user_data=0,
                               callback=context.config_ctrl.connect_syncronizer_device, height=25, width=100)

            # пустая ячейка
            with dpg.table_cell():
                dpg.add_text(default_value="  ")
            with dpg.table_cell():
                dpg.add_text(default_value="  ")
            with dpg.table_cell():
                dpg.add_text(default_value=" ")

    context.motionGUI.add_textures()

    with dpg.tab_bar(label="tabBar", show=True) as context.tabBar:
        with dpg.tab(label=txt.TS_MANUAL_TITLE, id=TAB_MANUAL_ID):
            context.motionGUI.init_manual_page()

        #        with dpg.tab(label=txt.TS2_TITLE):
        #            motionGUI.init_setting_page()

        with dpg.tab(label=txt.TS_PRESETS_TITLE, id=TAB_PRESETS_ID):
            context.motionGUI.init_preset_page()

        with dpg.tab(label=txt.TS_MEAS_TITLE, id=TAB_MEAS_ID):
            context.spectrum_gui.init_spectrum_page()

        with dpg.tab(label=txt.TS_POWERMAP_TITLE, id=TAB_POWERMAP_ID):
            context.meas_powermap.prepare()

        with dpg.tab(label=txt.TS_MEAS_CTRL_TITLE, id=TAB_MEAS_CTRL_ID):
            context.chip_meas_ctrl.init_chip_meas_page()

        with dpg.tab(label=txt.TS_CONFIGURATONS, id=TAB_CONFIG_ID):
            context.config_ctrl.init_config_page()

    log_window = dpg.add_child_window(autosize_x=True, autosize_y=True)
    context.logger = Logger(
        parent=log_window)  # , w_width=context.main_width-15, w_heigth=100, w_x=0, w_y=context.main_height-140)

# dpg.show_style_editor()

dpg.create_viewport(title=txt.MAIN_TITLE, width=context.main_width, height=context.main_height)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("main_window", True)

# dpg.start_dearpygui()
while dpg.is_dearpygui_running():
    context.motionGUI.loop()
    context.config_ctrl.loop()
    context.chip_meas_ctrl.chip_loop()
    context.meas_powermap.powermap_loop()
    if context.call_count != -1:
        context.call_count -= 1
        if context.call_count == 0:
            context.call_count = -1
            context.call_function(*context.function_params)

    jobs = dpg.get_callback_queue()  # retrieves and clears queue
    dpg.run_callbacks(jobs)
    dpg.render_dearpygui_frame()

context.t.cancel()
dpg.destroy_context()
