import os
import threading
from time import sleep
import pandas as pd
from Measurements.meas_spectrum_zero import MeasureSpectrumZero, show_spectrum_zero_page
from core.gui_helper import *

context = Context()


def find_zero_arr_idx(wl):
    wave_len = wl
    return int((wave_len - 1525) * 100)


def pm1(pm_, logn, lev):
    pm_.send("STOP\r\n")
    err = pm_.get_err()
    # print(err)
    pm_.send("TRIG 1\r\n")
    pm_.send("AVG 0.2\r\n")
    pm_.send(f"LOGN {int(logn)}\r\n")
    pm_.send(f"LEV {lev}\r\n")
    pm_.send("WMOD CONST1\r\n")
    pm_.send("MEAS\r\n")
    err = pm_.get_err()
    # print(err)


def set_report_file(sender, app_data, user_data):
    dpg.delete_item("file_dialog_id")
    with dpg.file_dialog(directory_selector=False, show=True, callback=rep_browse_callback,
                         tag="file_dialog_id",
                         default_path="Reports//", width=800, height=500):
        dpg.add_file_extension(".csv")


class MeasureSpectrum:

    def __init__(self):
        self.thread_proc = None
        self.wave_len = 0
        self.can_run = 0
        self.wave_len_start = 1525
        self.wave_len_stop = 1565
        self.wave_len_step = 0.01
        self.ser_data_x = np.round(np.arange(self.wave_len_start, self.wave_len_stop, self.wave_len_step), 2)
        self.steps = len(self.ser_data_x)
        self.ser_data_y = []

    def init_spectrum_page(self):
        context.spectrum_zero_gui.prepare_spectrum_zero_page()
        with dpg.group(horizontal=True):
            dpg.add_group(tag="spectrum_legend")
            context.meas_chart = dpg.add_plot(label="Оптический спектр", height=480, width=850, crosshairs=True)

            with dpg.group():
                dpg.add_spacer(height=10)
                dpg.add_text(default_value="Параметры измерения:")
                with dpg.group():
                    dpg.add_text(default_value="Уровень мощности лазера, dBm:")
                    context.editor_list.append("wave_length_pow")
                    dpg.add_input_text(tag="wave_length_pow", default_value=context.spectrum_laser_power, width=100,
                                       height=16,
                                       callback=check_bounds, user_data=[float, 10, 1])
                with dpg.group():
                    dpg.add_text(default_value=" Уровень отсечки, dBm ")
                    context.editor_list.append("cutoff_level")
                    dpg.add_input_text(tag="cutoff_level", default_value='-70', width=100, height=16,
                                       callback=check_bounds, user_data=[float, 10, -100])

                dpg.add_text(default_value="  Источник:")
                dpg.add_radio_button(label="", tag="laser_type", items=["Golight OS-TL"],
                                     default_value="Golight OS-TL")
                dpg.add_text(default_value=" Файл отчета ")
                with dpg.group(horizontal=True):
                    dpg.add_input_text(label="", tag="wl_report_file", width=250,
                                       default_value=context.spectrum_report_path, callback=set_report_path)
                    dpg.add_button(label=' Обзор ', callback=set_report_file)
                dpg.add_spacer(height=10)
                dpg.add_button(label="Сохранить в файл", callback=self.save_report_file,
                               user_data=True, width=230, height=30)

                dpg.add_button(label="Открыть файл", callback=self.open_report_file, user_data=True, width=230,
                               height=30)

                dpg.add_spacer(height=10)
                dpg.add_button(label="Работа с опорными уровнями", callback=measure_zero_spectrum_callback,
                               user_data=True, width=230, height=30)
                dpg.add_spacer(height=10)
                dpg.add_button(label="Провести измерение", callback=self.measure_spectrum_callback,
                               user_data=False, width=230, height=30)

        dpg.push_container_stack(context.meas_chart)

        dpg.add_plot_axis(dpg.mvXAxis, label="Длина волны", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Мощность, dBm", tag="y_axis")
        for i in range(60):
            pm_num = i // 20 + 1
            ch_num = i % 20
            chan_name = f"PM{pm_num}CH{ch_num}"
            dpg.add_line_series([], [], label=chan_name, parent="y_axis",
                                tag=f"series_tag{i}")
        dpg.pop_container_stack()

    def measure_spectrum_callback(self, sender, app_data, user_data):
        context.spectrum_laser_power = float(dpg.get_value("wave_length_pow"))
        power = context.spectrum_laser_power
        if not context.device_worker.is_pm2100_1_connected and not context.device_worker.is_pm2100_2_connected and \
                not context.device_worker.is_pm2100_3_connected:
            context.logger.log_warning(txt.PM_NOT_CONNECTED)
            return
        if not context.device_worker.is_laser_golight_connected:
            context.logger.log_warning('Не подключен лазер Golight OS-TL')
            return
        context.gui_hlp.showMessage(txt.PLATFORM_MEASURING_MSG, txt.BREAK, DLG_CT_BREAK_PROC, prog_bar=True)
        self.thread_proc = threading.Thread(target=self.exec_measure_sync, args=[float(power)],
                                            daemon=True)
        self.thread_proc.start()

    def exec_measure_sync(self, power):
        logn = self.steps
        self.ser_data_y = np.zeros((60, logn))
        context.is_meas_in_process = True
        context.device_worker.laser_golight_ctrl.get_beam_state()
        context.device_worker.laser_golight_ctrl.store_state()
        context.device_worker.laser_golight_ctrl.turn_beam(1)
        context.device_worker.laser_golight_ctrl.set_power_dbm(power)
        sleep(1)
        context.break_proc = False
        if context.device_worker.is_pm2100_1_connected:
            context.device_worker.pm2100_1_ctrl.startConst1(1545, 0.23, logn)
        if context.device_worker.is_pm2100_2_connected:
            context.device_worker.pm2100_2_ctrl.startConst1(1545, 0.23, logn)
        if context.device_worker.is_pm2100_3_connected:
            context.device_worker.pm2100_3_ctrl.startConst1(1545, 0.23, logn)

        context.device_worker.laser_golight_ctrl.start_scan(int(self.wave_len_start * 1e3), int(self.wave_len_stop * 1e3),
                                                            int(self.wave_len_step * 1e2))
        context.gui_hlp.init_progress_bar(logn)
        ret1, ret2 = context.device_worker.pm2100_2_ctrl.get_meas_state()
        while ret1 != "1":
            ret1, ret2 = context.device_worker.pm2100_2_ctrl.get_meas_state()
            dpg.set_value("popup_pb", int(ret2) / logn)
            if context.break_proc:
                context.is_meas_in_process = False
                context.device_worker.pm2100_2_ctrl.stop_meas()
                popup_close()
                return
            sleep(0.1)
        if context.device_worker.is_pm2100_1_connected:
            for i in range(20):
                self.ser_data_y[i] = context.device_worker.pm2100_1_ctrl.get_meas_data(i // 4, i % 4 + 1)
                dpg.set_value("popup_pb", int(i) / 20)
        if context.device_worker.is_pm2100_2_connected:
            for i in range(20):
                self.ser_data_y[i + 20] = context.device_worker.pm2100_2_ctrl.get_meas_data(i // 4, i % 4 + 1)
                dpg.set_value("popup_pb", int(i) / 20)
        if context.device_worker.is_pm2100_3_connected:
            for i in range(20):
                self.ser_data_y[i + 40] = context.device_worker.pm2100_3_ctrl.get_meas_data(i // 4, i % 4 + 1)
                dpg.set_value("popup_pb", int(i) / 20)
        for power_idx in range(logn):
            wv = self.ser_data_x[power_idx]
            wv_index = find_zero_arr_idx(wv)
            self.ser_data_y[:, power_idx] -= context.spectrum_zero[wv_index]['pow']

        for i in range(60):
            if context.act_chans[i]:
                dpg.set_value(f"series_tag{i}", [self.ser_data_x, self.ser_data_y[i]])
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")

        # finally:
        context.is_meas_in_process = False
        context.device_worker.laser_golight_ctrl.restore_state()
        popup_close()

    def open_report_file(self):
        filename = dpg.get_value('wl_report_file')
        with open(filename) as txt_file:

            data = txt_file.readline().split(';')

            count = sum(1 for _ in txt_file)

            data_len = min(60, len(data) - 1)

            self.ser_data_y = np.zeros((data_len, count))
            self.ser_data_x = np.zeros(count)
            idx_x = 0

            txt_file.seek(0)
            txt_file.readline()
            for line in txt_file:
                data = line.split(';')
                t_wl = data[0].replace(',', '.')
                self.ser_data_x[idx_x] = float(t_wl)
                for idx_y in range(data_len):
                    val = data[idx_y + 1].replace(',', '.')
                    try:
                        self.ser_data_y[idx_y][idx_x] = float(val)
                    except Exception as e:
                        print(e)
                        self.ser_data_y[idx_y][idx_x] = -100
                idx_x += 1

            for i in range(data_len):
                dpg.delete_item(f"series_tag{i}")
                pm_num = i // 20 + 1
                ch_num = i % 20
                chan_name = f"PM{pm_num}CH{ch_num}"
                visible = dpg.get_value(f'spectrum_legend_{i}')
                dpg.add_line_series(list(self.ser_data_x), list(self.ser_data_y[i]), label=chan_name, parent="y_axis",
                                    tag=f"series_tag{i}", show=visible)

            dpg.fit_axis_data("x_axis")
            dpg.fit_axis_data("y_axis")

    def save_report_file(self):
        if len(self.ser_data_x) < 2:
            context.logger.log_warning('Не провели измерение, нечего сохранять')
            return
        filename = dpg.get_value('wl_report_file')
        df = pd.DataFrame(np.array(self.ser_data_y).T, index=self.ser_data_x, columns=[f"CH{i}" for i in range(1, 61)])

        df.to_csv(filename, sep=";")

        '''try:
            self.open_report_file()
            ds = DataSheet()
            ds.make_data_sheet(self.ser_data_x, self.ser_data_y, filename)
            context.logger.log_warning('Сформирован Datasheet')
        except Exception as e:
            context.logger.log_warning('Не удалось создать Datasheet')'''


def measure_zero_spectrum_callback(sender, app_data, user_data):
    MeasureSpectrumZero()
    show_spectrum_zero_page()


def rep_browse_callback(sender, app_data, user_data):
    dpg.set_value("wl_report_file", os.path.relpath(user_data["file_path_name"]))
    set_report_path(0, 0, 0)


def set_report_path(sender, app_data, user_data):
    #        dpg.get_value("wl_report_file")
    context.spectrum_report_path = dpg.get_value("wl_report_file")
    save_parameters()


context.spectrum_gui = MeasureSpectrum()
