import os
import threading
from time import sleep

from Measurements.meas_datasheet import DataSheet
from Measurements.meas_spectrum_zero import MeasureSpectrumZero
from core.gui_helper import *

context = Context()


def pm1(pm_, logn, lev):
    pm_.send("STOP\r\n")
    print(pm_.get_err())
    pm_.send("TRIG 1\r\n")
    pm_.send("AVG 0.2\r\n")
    pm_.send(f"LOGN {int(logn)}\r\n")
    pm_.send(f"LEV {lev}\r\n")
    pm_.send("WMOD CONST1\r\n")
    pm_.send("MEAS\r\n")
    print(pm_.get_err())


class MeasureSpectrum:

    def __init__(self):
        self.wave_len = 0
        self.can_run = 0
        self.ser_data_x = []
        self.ser_data_y = []

    def init_spectrum_page(self):
        context.spectrum_zero_gui.prepare_spectrum_zero_page()
        with dpg.group(horizontal=True):
            dpg.add_group(tag="spectrum_legend")
            context.meas_chart = dpg.add_plot(label="Оптический спектр", height=480, width=850, crosshairs=True)

            with dpg.group():
                dpg.add_spacer(height=10)
                dpg.add_text(default_value="Параметры измерения:")
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text(default_value="  от, нм  ")
                        context.editor_list.append("wave_length_start")
                        dpg.add_input_text(tag="wave_length_start", default_value="1525", width=100, height=16,
                                           callback=context.gui_hlp.check_bounds, user_data=[float, 1565, 1525])
                    with dpg.group():
                        dpg.add_text(default_value="  до, нм  ")
                        context.editor_list.append("wave_length_stop")
                        dpg.add_input_text(tag="wave_length_stop", default_value="1565", width=100, height=16,
                                           callback=context.gui_hlp.check_bounds, user_data=[float, 1565, 1525])
                    #                                      min_value=context.device_worker.laser_ctrl.wave_len_min, max_value=context.device_worker.laser_ctrl.wave_len_max, min_clamped=True, max_clamped=True)
                    with dpg.group():
                        dpg.add_text(default_value=" шаг, нм ")
                        context.editor_list.append("wave_length_step")
                        dpg.add_input_text(tag="wave_length_step", default_value='0.5', width=100, height=16,
                                           callback=context.gui_hlp.check_bounds, user_data=[float, 1, 0.01])

                with dpg.group():
                    dpg.add_text(default_value="Уровень мощности лазера, dBm:")
                    context.editor_list.append("wave_length_pow")
                    dpg.add_input_text(tag="wave_length_pow", default_value=context.spectrum_laser_power, width=100,
                                       height=16,
                                       callback=context.gui_hlp.check_bounds, user_data=[float, 10, 1])
                with dpg.group():
                    dpg.add_text(default_value=" Уровень отсечки, dBm ")
                    context.editor_list.append("cutoff_level")
                    dpg.add_input_text(tag="cutoff_level", default_value='-70', width=100, height=16,
                                       callback=context.gui_hlp.check_bounds, user_data=[float, 10, -100])

                dpg.add_text(default_value="  Источник:")
                dpg.add_radio_button(label="", tag="laser_type", items=["Golight OS-TL"],
                                     horizontal=False, default_value="Golight OS-TL")
                dpg.add_text(default_value=" Файл отчета ")
                with dpg.group(horizontal=True):
                    dpg.add_input_text(label="", tag="wl_report_file", width=250,
                                       default_value=context.spectrum_report_path, callback=self.set_report_path)
                    dpg.add_button(label=' Обзор ', callback=self.set_report_file)
                dpg.add_spacer(height=10)
                dpg.add_button(label="Сохранить в файл", callback=self.save_report_file,
                               user_data=True, width=230, height=30)

                dpg.add_button(label="Открыть файл", callback=self.open_report_file, user_data=True, width=230,
                               height=30)

                dpg.add_spacer(height=10)
                dpg.add_button(label="Работа с опорными уровнями", callback=self.measure_zero_spectrum_callback,
                               user_data=True, width=230, height=30)
                dpg.add_spacer(height=10)
                dpg.add_button(label="Провести измерение", callback=self.measure_spectrum_callback,
                               user_data=False, width=230, height=30)

        dpg.push_container_stack(context.meas_chart)

        # create legend
        # dpg.add_plot_legend(location=dpg.mvPlot_Location_West,outside=True)

        # create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, label="Длина волны", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Мощность, dBm", tag="y_axis")

        # series belong to a y axis
        #        dpg.add_line_series(self.ser_data_x, self.ser_data_y, label="", parent="y_axis", tag="series_tag")
        context.gui_hlp.show_channels_legend(legend_grp="spectrum_legend", prefix="spectrum_legend",
                                             callback=self.legend_callback)
        dpg.pop_container_stack()  # pop chart context

    def set_report_path(self, sender, app_data, user_data):
        #        dpg.get_value("wl_report_file")
        context.spectrum_report_path = dpg.get_value("wl_report_file")
        save_prameters()

    def set_report_file(self, sender, app_data, user_data):
        dpg.delete_item("file_dialog_id")
        with dpg.file_dialog(directory_selector=False, show=True, callback=self.rep_browse_callback,
                             tag="file_dialog_id",
                             default_path="Reports//", width=800, height=500):
            dpg.add_file_extension(".csv")

    def rep_browse_callback(self, sender, app_data, user_data):
        dpg.set_value("wl_report_file", os.path.relpath(user_data["file_path_name"]))
        context.spectrum_gui.set_report_path(0, 0, 0)

    def legend_callback(self, sender, app_data, user_data):
        val = dpg.get_value(sender)
        item = f"series_tag{user_data}"
        if dpg.does_item_exist(item):
            dpg.configure_item(item, show=val)

    def measure_zero_spectrum_callback(self, sender, app_data, user_data):
        zero_meas_wnd = MeasureSpectrumZero()
        zero_meas_wnd.show_spectrum_zero_page()

    def measure_spectrum_callback(self, sender, app_data, user_data):
        start_len = dpg.get_value("wave_length_start")
        stop_len = dpg.get_value("wave_length_stop")
        step = float(dpg.get_value("wave_length_step"))
        cutoff = float(dpg.get_value("cutoff_level"))
        context.spectrum_laser_power = float(dpg.get_value("wave_length_pow"))
        power = context.spectrum_laser_power

        laser_type = dpg.get_value("laser_type")
        #        chan       = int(dpg.get_value("meas_chanel"))

        if not context.device_worker.is_pm2100_1_connected and not context.device_worker.is_pm2100_2_connected and \
                not context.device_worker.is_pm2100_3_connected:
            context.logger.log_warning(txt.PM_NOT_CONNECTED)
            return
        if not context.device_worker.is_laser_golight_connected:
            context.logger.log_warning('Не подключен лазер Golight OS-TL')
            return
        if start_len > stop_len:
            context.logger.log_warning('Стартовая длина волны должна быть меньше конечной')
            return

        context.gui_hlp.showMessage(txt.PLATFORM_MEASURING_MSG, txt.BREAK, DLG_CT_BREAK_PROC, prog_bar=True)
        self.thread_proc = threading.Thread(target=self.exec_measure_sync, args=[float(start_len), float(stop_len),
                                                                                 float(power), float(step), cutoff],
                                            daemon=True)
        self.thread_proc.start()

    def exec_measure(self, wave_len_start, wave_len_stop, power, wave_len_step, cut_off_lvl):
        def find_zero_arr_idx(wl):
            # 1 округляем длину волны то требуемой точности
            #            round_to = 0.01
            #            wave_len = int(wl / round_to + 0.5) * round_to
            wave_len = wl
            # 2 ищем индекс значений для ближайшей к заданной длины волны
            for idx, zero in enumerate(context.spectrum_zero):
                if abs(zero["wl"] - wave_len) < 0.004:
                    return idx
            return -1

        def copy_to_chart(wl, arr_idx):
            z_idx = find_zero_arr_idx(wl)
            for i in range(60):
                val = float(context.pm_values[i])
                if z_idx == -1:
                    zero_lvl = 0
                else:
                    zero_lvl = context.spectrum_zero[z_idx]['pow'][i]
                value = val - zero_lvl
                if cut_off_lvl > value:
                    value = cut_off_lvl
                self.ser_data_y[i][arr_idx] = float(value)

        try:
            self.wave_len = wave_len_start

            data_len = int((-wave_len_start + wave_len_stop) / wave_len_step) + 1

            self.ser_data_y = np.zeros((60, data_len))
            self.ser_data_x = []  # np.round(np.arange(wave_len_start, wave_len_stop, wave_len_step), 2)

            context.is_meas_in_process = True

            laser_state = context.device_worker.laser_golight_ctrl.get_beam_state()
            context.device_worker.laser_golight_ctrl.store_state()
            context.device_worker.laser_golight_ctrl.turn_beam(1)
            context.device_worker.laser_golight_ctrl.set_power_dbm(power)
            context.device_worker.laser_golight_ctrl.set_wave_len(wave_len_start)
            if not laser_state:
                time.sleep(1)

            context.break_proc = False

            steps = (wave_len_stop - wave_len_start) / wave_len_step
            context.gui_hlp.init_progress_bar(steps)
            power_idx = 0
            while not context.break_proc and self.wave_len <= wave_len_stop:
                context.gui_hlp.progress_bar_step()
                if context.device_worker.is_pm2100_1_connected:
                    context.device_worker.pm2100_1_ctrl.set_wave_len(self.wave_len, False)
                if context.device_worker.is_pm2100_2_connected:
                    context.device_worker.pm2100_2_ctrl.set_wave_len(self.wave_len, False)
                if context.device_worker.is_pm2100_3_connected:
                    context.device_worker.pm2100_3_ctrl.set_wave_len(self.wave_len, False)
                context.device_worker.laser_golight_ctrl.set_wave_len(self.wave_len)
                self.ser_data_x.append(float(self.wave_len))
                if context.device_worker.is_pm2100_1_connected:
                    for i, module in enumerate(context.pm_modules1):
                        if module:
                            power_arr = context.device_worker.pm2100_1_ctrl.get_power(i)
                            for j in range(4):
                                context.pm_values[0 + i * 4 + j] = power_arr[j]
                if context.device_worker.is_pm2100_2_connected:
                    for i, module in enumerate(context.pm_modules2):
                        if module:
                            power_arr = context.device_worker.pm2100_2_ctrl.get_power(i)
                            for j in range(4):
                                context.pm_values[20 + i * 4 + j] = power_arr[j]
                if context.device_worker.is_pm2100_3_connected:
                    for i, module in enumerate(context.pm_modules3):
                        if module:
                            power_arr = context.device_worker.pm2100_3_ctrl.get_power(i)
                            for j in range(4):
                                context.pm_values[40 + i * 4 + j] = power_arr[j]
                copy_to_chart(self.wave_len, power_idx)
                power_idx += 1
                self.wave_len += wave_len_step
                time.sleep(0.1)
            # for i in range(60):
            #     pm_num = i // 20 + 1
            #     self.ser_data_y[i] = context.device_worker.pm2100_1_ctrl.get_meas_data()
            for i in range(60):
                dpg.delete_item(f"series_tag{i}")
                if context.act_chans[i]:
                    pm_num = i // 20 + 1
                    ch_num = i % 20
                    chan_name = f"PM{pm_num}CH{ch_num}"
                    visible = dpg.get_value(f'spectrum_legend_{i}')
                    dpg.add_line_series(self.ser_data_x, self.ser_data_y[i], label=chan_name, parent="y_axis",
                                        tag=f"series_tag{i}", show=visible)

            dpg.fit_axis_data("x_axis")
            dpg.fit_axis_data("y_axis")

        finally:
            context.device_worker.laser_golight_ctrl.restore_state()

            context.is_meas_in_process = False
            context.gui_hlp.popup_close()

    def exec_measure_sync(self, wave_len_start, wave_len_stop, power, wave_len_step, cut_off_lvl):
        def find_zero_arr_idx(wl):
            wave_len = wl
            for idx, zero in enumerate(context.spectrum_zero):
                if abs(zero["wl"] - wave_len) < 0.004:
                    return idx
            return -1

        def copy_to_chart(wl, arr_idx):
            z_idx = find_zero_arr_idx(wl)
            for i in range(60):
                val = float(context.pm_values[i])
                if z_idx == -1:
                    zero_lvl = 0
                else:
                    zero_lvl = context.spectrum_zero[z_idx]['pow'][i]
                value = val - zero_lvl
                if cut_off_lvl > value:
                    value = cut_off_lvl
                self.ser_data_y[i][arr_idx] = float(value)

        logn = int((wave_len_stop - wave_len_start) / wave_len_step)+1
        self.ser_data_y = np.zeros((60, logn))
        self.ser_data_x = np.round(np.arange(wave_len_start, wave_len_stop+wave_len_step, wave_len_step), 2)
        context.is_meas_in_process = True
        conn_state = context.device_worker.laser_golight_ctrl.get_beam_state()
        context.device_worker.laser_golight_ctrl.turn_beam(1)
        context.device_worker.laser_golight_ctrl.set_power_dbm(power)

        time.sleep(1)
        context.break_proc = False
        if context.device_worker.is_pm2100_1_connected:
            context.device_worker.pm2100_1_ctrl.startConst1(1545, 0.23, logn)
        if context.device_worker.is_pm2100_2_connected:
            context.device_worker.pm2100_2_ctrl.startConst1(1545, 0.23, logn)
        if context.device_worker.is_pm2100_3_connected:
            context.device_worker.pm2100_3_ctrl.startConst1(1545, 0.23, logn)

        context.device_worker.laser_golight_ctrl.start_scan(int(wave_len_start * 1e3), int(wave_len_stop * 1e3), int(wave_len_step*1e2))
        context.gui_hlp.init_progress_bar(logn)
        ret1, ret2 = context.device_worker.pm2100_1_ctrl.get_meas_state()
        while ret1 != "1":
            ret1, ret2 = context.device_worker.pm2100_1_ctrl.get_meas_state()
            dpg.set_value("popup_pb", int(ret2) / logn)
            sleep(0.1)
        if context.device_worker.is_pm2100_1_connected:
            for i in range(20):
                self.ser_data_y[i] = context.device_worker.pm2100_1_ctrl.get_meas_data(i // 4, i % 4 + 1)
        if context.device_worker.is_pm2100_2_connected:
            for i in range(20):
                self.ser_data_y[i + 20] = context.device_worker.pm2100_2_ctrl.get_meas_data(i // 4, i % 4 + 1)
        if context.device_worker.is_pm2100_3_connected:
            for i in range(20):
                self.ser_data_y[i + 40] = context.device_worker.pm2100_3_ctrl.get_meas_data(i // 4, i % 4 + 1)
        for power_idx in range(logn):
            wv = self.ser_data_x[power_idx]
            wv_indx = find_zero_arr_idx(wv)
            self.ser_data_y[:, power_idx] -= context.spectrum_zero[wv_indx]['pow']
        for i in range(60):
            dpg.delete_item(f"series_tag{i}")
            if context.act_chans[i]:
                pm_num = i // 20 + 1
                ch_num = i % 20
                chan_name = f"PM{pm_num}CH{ch_num}"
                visible = dpg.get_value(f'spectrum_legend_{i}')
                dpg.add_line_series(self.ser_data_x, self.ser_data_y[i], label=chan_name, parent="y_axis",
                                    tag=f"series_tag{i}", show=visible)
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")

        # finally:
        context.is_meas_in_process = False
        context.gui_hlp.popup_close()

    def open_report_file(self):
        filename = dpg.get_value('wl_report_file')
        with open(filename, "r") as txt_file:

            data = txt_file.readline().split(';')

            count = sum(1 for line in txt_file)

            datalen = min(60, len(data) - 1)

            self.ser_data_y = np.zeros((datalen, count))
            self.ser_data_x = np.zeros(count)
            idx_x = 0

            txt_file.seek(0)
            txt_file.readline()
            for line in txt_file:
                data = line.split(';')
                t_wl = data[0].replace(',', '.')
                self.ser_data_x[idx_x] = float(t_wl)
                for idx_y in range(datalen):
                    val = data[idx_y + 1].replace(',', '.')
                    try:
                        self.ser_data_y[idx_y][idx_x] = float(val)
                    except Exception as e:
                        self.ser_data_y[idx_y][idx_x] = -100
                idx_x += 1

            for i in range(datalen):
                dpg.delete_item(f"series_tag{i}")
                pm_num = i // 20 + 1
                ch_num = i % 20
                chan_name = f"PM{pm_num}CH{ch_num}"
                visible = dpg.get_value(f'spectrum_legend_{i}')
                dpg.add_line_series(self.ser_data_x, self.ser_data_y[i], label=chan_name, parent="y_axis",
                                    tag=f"series_tag{i}", show=visible)

            dpg.fit_axis_data("x_axis")
            dpg.fit_axis_data("y_axis")

    def save_report_file(self):
        filename = dpg.get_value('wl_report_file')
        with open(filename, "w") as txt_file:
            line = "Wavelen;"
            for idx_y in range(60):
                #                if context.act_chans[idx_y]:
                #                item = f"series_tag{idx_y}"
                #                if dpg.does_item_exist(item) and dpg.get_item_configuration(item)['show']:
                pm_num = idx_y // 20 + 1
                ch_num = idx_y % 20
                line += f"PM{pm_num}CH{ch_num};"
            txt_file.write(f"{line};\n")
            for idx_x in range(len(self.ser_data_x)):
                xval = str(self.ser_data_x[idx_x])
                xval = xval.replace('.', ',')
                line = f"{xval};"
                for idx_y in range(60):
                    #                    if context.act_chans[idx_y]:
                    #                    item = f"series_tag{idx_y}"
                    #                    if dpg.does_item_exist(item) and dpg.get_item_configuration(item)['show']:
                    yval = str(self.ser_data_y[idx_y][idx_x])
                    yval = yval.replace('.', ',')
                    line += f"{yval};"

                txt_file.write(f"{line};\n")
        # сохранить рядом в файл daatasheet

        try:
            self.open_report_file()
            ds = DataSheet()
            ds.make_data_sheet(self.ser_data_x, self.ser_data_y, filename)
            context.logger.log_warning('Сформирован Datasheet')
        except Exception as e:
            context.logger.log_warning('Не удалось создать Datasheet')


context.spectrum_gui = MeasureSpectrum()
