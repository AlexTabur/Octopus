from core.gui_helper import GUI_Helper, initThemes, plot_h_callback1, prepare_input_window
import Measurements.meas_ctrl
import gui.config_gui
import gui.motion_gui
import Chip.chip_control
import Measurements.meas_powermap
import Measurements.meas_spectrum
import Measurements.PMapping.measuring
from logger import Logger
import Measurements.chip_meas
import Motion.position
import dearpygui.dearpygui as dpg
from core.utils import *
from core.context_ import Context
from core.consts import *
import core.texts as txt
from gui.motion_gui import btn_connect_platform_callback, connect_platform, btn_connect_table_callback, loop_motion_gui
from gui.config_gui import connect_pm2100_device2, connect_pm2100_device1, connect_pm2100_device3, \
    connect_sync_device, connect_laser_golight_device, init_config_page


def main_func(td, sv, pos_array, focus_side_view_r, focus_side_view_l, moving_right_shared):
    context.camera_points_td = td
    context.camera_points_sv = sv
    context.pos_array = pos_array
    context.focus_side_view_r = focus_side_view_r
    context.focus_side_view_l = focus_side_view_l
    context.moving_right_shared = moving_right_shared
    load_parameters()
    arr = np.array([('Preset', np.zeros(13))], context.preset_dt)
    # Этот цикл "бронирует" места для, допустим, координат стола.
    # Когда мы дальше получаем координаты позиционеров, у нас, благодаря этому циклу,
    # уже есть места, куда можно эти координаты записать
    for i in range(0, 10):
        context.preset_left = np.append(context.preset_left, arr)
        context.preset_right = np.append(context.preset_right, arr)
        context.preset_table = np.append(context.preset_table, arr)
        context.preset_all = np.append(context.preset_all, arr)
    load_presets()
    '''
    r before  -86403
    after -163270
    76867
    '''

    dpg.create_context()
    dpg.configure_app(manual_callback_management=True)  # Now, мы устанавливаем, что мы вручную будем обрабатывать нажатие кнопок,
    # то-есть делаем безопасную очередь выполняемых задач, чтобы ставить действие с кнопки в своеобразную очередь

    # Здесь мы можем узреть, фикс со старыми кодировками, как я понял.
    big_let_start = 0x00C0  # Capital "A" in cyrillic alphabet
    big_let_end = 0x00DF
    remap_big_let = 0x0410  # Это кодировка "A" в международном стандарте
    alph_len = big_let_end - big_let_start + 1

    with dpg.font_registry():
        with dpg.font(r"C:\Windows\Fonts\consola.ttf", 20, id="Default font"):
            big_letter = remap_big_let
            for i1 in range(big_let_start, big_let_end + 1):
                dpg.add_char_remap(i1, big_letter)
                dpg.add_char_remap(i1 + alph_len, big_letter + alph_len)
                big_letter += 1
        dpg.bind_font("Default font")

    initThemes()  # Задание тем. Размеры кнопок, цвет, фон, всё это можно сделать через эту функцию

    # Вот тут как раз и реализован with для удобного выполнения отдельных
    # элементов одного окна
    with dpg.window(tag="main_window", no_resize=True):
        # Здесь мы добавляем, или лучше сказать, привязываем данные с png файлов
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
        prepare_input_window()
        context.gui_hlp.prepare_chart_hint()
        context.gui_hlp.prepare_horiz_chart()
        # Этот "With" задаёт реагирование графика на мышку
        with dpg.item_handler_registry(tag="horiz_widget_handler1"):
            dpg.add_item_clicked_handler(button=0, callback=plot_h_callback1)  # При нажатии на ЛКМ
            # должно что-то случиться, судя по всему перемещение на поставленную точку
        dpg.bind_item_handler_registry(context.gui_hlp.horiz_chart1, "horiz_widget_handler1")
        with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingFixedFit):  # , freeze_columns=9):
            # Тут я заменил 16 строк add_table_column() на один цикл,
            # вроде это не должно сломать работу кода
            for _ in range(16):
                dpg.add_table_column()

            with dpg.table_row():  # А здесь, как видно из названия, создаётся строка внутри таблицы.
                # А дальше создаются ячейки для разных приборов
                with dpg.table_cell():
                    dpg.add_spacer(width=10)
                    dpg.add_text(default_value=txt.PLATFORM_CTRL_TITLE)
                with dpg.table_cell():
                    dpg.add_image("texture_dev_disc", tag="platform_ctrl_state")
                with dpg.table_cell():
                    dpg.add_button(label=txt.BTN_CONNECT, tag="platform_conn_btn", user_data=0,
                                   callback=btn_connect_platform_callback, height=25, width=100)
                with dpg.table_cell():
                    dpg.add_spacer(width=10)
                    dpg.add_text(default_value=txt.METER_TITLE + '1')
                with dpg.table_cell():
                    dpg.add_image("texture_dev_disc", tag="pm2100_ctrl_state1")
                with dpg.table_cell():
                    dpg.add_button(label=txt.BTN_CONNECT, tag="pm2100_conn_btn1", user_data=0,
                                   callback=connect_pm2100_device1, height=25, width=100)
                with dpg.table_cell():
                    dpg.add_spacer(width=10)
                    dpg.add_text(default_value=txt.METER_TITLE + '2')
                with dpg.table_cell():
                    dpg.add_image("texture_dev_disc", tag="pm2100_ctrl_state2")
                with dpg.table_cell():
                    dpg.add_button(label=txt.BTN_CONNECT, tag="pm2100_conn_btn2", user_data=0,
                                   callback=connect_pm2100_device2, height=25, width=100)
                with dpg.table_cell():
                    dpg.add_spacer(width=10)
                    dpg.add_text(default_value=txt.METER_TITLE + '3')
                with dpg.table_cell():
                    dpg.add_image("texture_dev_disc", tag="pm2100_ctrl_state3")
                with dpg.table_cell():
                    dpg.add_button(label=txt.BTN_CONNECT, tag="pm2100_conn_btn3", user_data=0,
                                   callback=connect_pm2100_device3, height=25, width=100)
                    # Это можно убрать
                with dpg.table_cell():
                    pass
            with dpg.table_row():
                with dpg.table_cell():
                    dpg.add_text(default_value=txt.TABLE_CTRL_TITLE)
                with dpg.table_cell():
                    #                dpg.add_text(tag="table_ctrl_state", default_value=txt.STATE_DISCONNECTED, color=[255, 0, 0])
                    dpg.add_image("texture_dev_disc", tag="table_ctrl_state")
                with dpg.table_cell():
                    dpg.add_button(label=txt.BTN_CONNECT, tag="table_conn_btn", user_data=0,
                                   callback=btn_connect_table_callback, height=25, width=100)

                with dpg.table_cell():
                    dpg.add_text(default_value=txt.LASER_GOLIGHT_TITLE)
                with dpg.table_cell():
                    dpg.add_image("texture_dev_disc", tag="laser_golight_ctrl_state")
                with dpg.table_cell():
                    dpg.add_button(label=txt.BTN_CONNECT, tag="laser_golight_conn_btn", user_data=0,
                                   callback=connect_laser_golight_device, height=25, width=100)

                with dpg.table_cell():
                    dpg.add_text(default_value=txt.sync_TITLE)
                with dpg.table_cell():
                    dpg.add_image("texture_dev_disc", tag="sync_ctrl_state")
                with dpg.table_cell():
                    dpg.add_button(label=txt.BTN_CONNECT, tag="sync_conn_btn", user_data=0,
                                   callback=connect_sync_device, height=25, width=100)

                with dpg.table_cell():
                    dpg.add_text(default_value="  ")
                with dpg.table_cell():
                    dpg.add_text(default_value="  ")
                with dpg.table_cell():
                    dpg.add_text(default_value=" ")
        context.cur_tab = TAB_MANUAL_ID
        context.motionGUI.add_textures()

        def tab_menu_callback(sender, app_data, user_data):
            context.cur_tab = app_data
            context.running_cameras = context.cur_tab == TAB_MANUAL_ID

        with dpg.tab_bar(label="tabBar", show=True, callback=tab_menu_callback) as context.tabBar:
            with dpg.tab(label=txt.TS_MANUAL_TITLE, id=TAB_MANUAL_ID):
                context.motionGUI.init_manual_page()

            with dpg.tab(label=txt.TS_PRESETS_TITLE, id=TAB_PRESETS_ID):
                context.motionGUI.init_preset_page()

            with dpg.tab(label=txt.TS_MEAS_TITLE, id=TAB_MEAS_ID):
                context.spectrum_gui.init_spectrum_page()

            with dpg.tab(label=txt.TS_POWERMAP_TITLE, id=TAB_POWERMAP_ID):
                context.meas_powermap.prepare()

            with dpg.tab(label=txt.TS_MEAS_CTRL_TITLE, id=TAB_MEAS_CTRL_ID):
                context.chip_meas_ctrl.init_chip_meas_page()

            with dpg.tab(label=txt.TS_CONFIGURATIONS, id=TAB_CONFIG_ID):
                init_config_page()
        log_window = dpg.add_child_window(autosize_y=True)
        context.logger = Logger(parent=log_window)
    dpg.create_viewport(title=txt.MAIN_TITLE, width=context.main_width, height=context.main_height)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.maximize_viewport()
    dpg.set_primary_window("main_window", True)

    # Этот цикл можно заменить на встроенную функцию библиотеки
    while dpg.is_dearpygui_running():
        loop_motion_gui()
        context.config_ctrl.loop()
        context.chip_meas_ctrl.chip_loop()
        context.meas_powermap.powermap_loop()
        # Есть вероятность, что из-за цикла будет зависать картинка
        if context.call_count != -1:
            context.call_count -= 1
            if context.call_count == 0:
                context.call_count = -1
                context.call_function(*context.function_params)

        jobs = dpg.get_callback_queue()
        dpg.run_callbacks(jobs)
        dpg.render_dearpygui_frame()

    context.t.cancel()
    dpg.destroy_context()
