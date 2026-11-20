import threading
from time import sleep

from axis_ctrl import is_platforms_axis_busy
from core.gui_helper import *
from core.texts import *
from core.utils import *
from core.consts import *

context = Context()

GO_TO_ZERO = 1
GO_TO_MAX = 2


def set_platform_pos(x_axis, y_axis, x, y):
    #        context.logger.log_com("shift x -> " + str(x) + ", y -> " + str(y))
    x = context.pmap_procedures.map_min_x + x
    y = context.pmap_procedures.map_min_y + y
    context.z_platform.move_to(y_axis, y)
    context.z_platform.move_to(x_axis, x)
    while is_platforms_axis_busy():
        pass


def recalc_um():
    delta = int(dpg.get_value("pmap_delta") / Y_MKM_KOEF)
    x_scale = int(dpg.get_value("pmap_y_width") / Y_MKM_KOEF)
    dpg.set_value("pmap_delta", delta * Y_MKM_KOEF)
    dpg.set_value("delta_steps", f"{delta} шагов")
    dpg.set_value("xscale_steps", f"{x_scale} шагов")


def set_scan_size(x_scale, y_scale, delta):
    context.pmap_procedures.x_count = int(x_scale / delta)
    context.pmap_procedures.y_count = int(y_scale / delta)
    context.pmap_procedures.x_scale = int(x_scale * 8)
    context.pmap_procedures.y_scale = int(y_scale * 8)
    context.pmap_procedures.delta = int(delta * 8)


def set_powermap_measure_params(pm_channel, pm_channel2, x_scale, y_scale, delta, chan_dist, after_measure):
    # print(pm_channel, pm_channel2, y_count, x_scale, delta, chan_dist, after_measure)
    set_scan_size(x_scale, y_scale, delta)
    context.pmap_procedures.chan_dist = chan_dist
    context.pmap_procedures.after_measure = after_measure

    context.pmap_procedures.pm_module = pm_channel // 4
    context.pmap_procedures.pm_chan = pm_channel % 4

    context.pmap_procedures.pm_module2 = pm_channel2 // 4
    context.pmap_procedures.pm_chan2 = pm_channel2 % 4

    if ((not context.device_worker.is_pm2100_1_connected) and
            (not context.device_worker.is_pm2100_2_connected) and
            (not context.device_worker.is_pm2100_3_connected)):
        context.logger.log_warning(txt.PM_NOT_CONNECTED)
        return
        # if not context.device_worker.is_pm2100_2_connected:
        #     context.device_worker.connectPM2100(2)
        #     sleep(5)
    if not context.z_platform.is_connected:
        context.logger.log_warning(txt.PLATFORMS_NOT_CONNECTED)
        return

    if context.pmap_procedures.sync_mode and not context.device_worker.is_sync_connected:
        context.logger.log_warning(txt.sync_NOT_CONNECTED)
        return

    context.gui_hlp.showMessage(txt.PLATFORM_AIMING_MSG, txt.BREAK, DLG_CT_BREAK_PROC, prog_bar=True)


class MeasurePowerMap:

    def __init__(self):
        self.meas_chart2 = None
        self.cross = 999999
        self.cross2 = 999999

        self.pm_mode = 0
        self.meas_chan = -1
        self.meas_chan2 = -1

        self.meas_chart = None
        self.thread_proc = None

    def mode_sel_callback(self, sender, app_data, user_data):
        context.pmap_procedures.is_prepared = False

        if dpg.get_value("pmap_mode") == PM_MODE_CHAN:
            self.pm_mode = 0
        elif dpg.get_value("pmap_mode") == PM_MODE_ROLL:
            self.pm_mode = 1
            dpg.show_item("pm_pm2")
            dpg.show_item("pm_chan_dist")
            dpg.show_item(self.meas_chart2)
        else:
            self.pm_mode = 2

    def plot_callback(self, sender, app_data, user_data):
        if self.pm_mode == 0:
            if context.z_platform.is_connected:
                x, y = dpg.get_plot_mouse_pos()
                print(
                    f"Перемещение Y -> {x} мкм ({int(x / Y_MKM_KOEF)} шагов) , y -> {y} мкм({int(y / Z_MKM_KOEF)}шагов)")
                context.gui_hlp.showMessage(txt.PLATFORM_AIMING_MSG, txt.BREAK, DLG_CT_NO_CLOSE)
                set_platform_pos(context.pmap_procedures.x_axis, context.pmap_procedures.y_axis,
                                 int(x / Y_MKM_KOEF), int(y / Z_MKM_KOEF))
                popup_close()
        elif self.pm_mode == 1:
            self.cross = context.pmap_procedures.process_horiz_aiming(self.cross, 1)
        else:
            if context.z_platform.is_connected:
                x, y = dpg.get_plot_mouse_pos()
                print(
                    f"Перемещение Y -> {x} мкм ({int(x / STEP_PER_GRAD_Y)} шагов) , y -> {y} мкм({int(y / Z_MKM_KOEF)}шагов)")
                context.gui_hlp.showMessage(txt.PLATFORM_AIMING_MSG, txt.BREAK, DLG_CT_NO_CLOSE)
                set_platform_pos(context.pmap_procedures.pitch_axis, context.pmap_procedures.y_axis,
                                 int(x / STEP_PER_GRAD_Y), int(y / Z_MKM_KOEF))
                popup_close()

    def plot_callback2(self, sender, app_data, user_data):
        #        if context.z_platform.is_connected:
        # x, y = dpg.get_plot_mouse_pos()
        if self.pm_mode == 1:
            self.cross2 = context.pmap_procedures.process_horiz_aiming(self.cross2, 2)

    # Эта функция должна бы переключать какал измерений, правый или левый
    def measure_powermap_callback(self, sender, app_data, user_data):
        pm_channel = int(dpg.get_value("pmap_meas_chanel"))  # Вот тут как раз
        pm_channel2 = int(dpg.get_value("pmap_meas_chanel2"))
        y_count = int(dpg.get_value("pmap_z_count"))
        x_scale = float(dpg.get_value("pmap_y_width") / Y_MKM_KOEF)
        delta = float(dpg.get_value("pmap_delta") / Y_MKM_KOEF)
        chan_dist = float(dpg.get_value("pmap_chans_dist"))
        after_measure = GO_TO_ZERO
        set_powermap_measure_params(pm_channel, pm_channel2, y_count, x_scale, delta, chan_dist, after_measure)
        if self.pm_mode == 0:
            if context.pmap_procedures.sync_mode:
                self.thread_proc = threading.Thread(target=context.pmap_procedures.scan_manual_sync, args=[],
                                                    daemon=True)
            else:
                self.thread_proc = threading.Thread(target=context.pmap_procedures.scan_manual, args=[], daemon=True)
        elif self.pm_mode == 1:
            # if context.pmap_procedures.sync_mode:
            self.thread_proc = threading.Thread(target=context.pmap_procedures.correct_horizont_sync, args=[],
                                                daemon=True)

            #     # self.thread_proc = threading.Thread(target=self.exec_measure, args=[], daemon=True)
            # else:
            #     self.thread_proc = threading.Thread(target=context.pmap_procedures.correct_pitch, args=[],
            #                                         daemon=True)
        self.thread_proc.start()

    def prepare(self):
        context.pmap_procedures.is_prepared = True
        context.pmap_procedures.ser_data = np.ones(
            shape=[context.pmap_procedures.y_count, context.pmap_procedures.x_count]) * (-110)
        with dpg.group(horizontal=True):
            with dpg.group(horizontal=True):
                with dpg.plot(label="Левая платформа", height=500, width=600, no_menus=True, no_title=True,
                              crosshairs=True) as plot_id:
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="X, мкм", tag="my_x_axis1")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Y, мкм", tag="my_y_axis1")
                    dpg.add_heat_series(
                        x=[.1, .1, .1, .1],
                        rows=4,
                        cols=4,
                        format="",
                        tag="heatmap1",
                        parent="my_y_axis1"
                    )
                scale_id = dpg.add_colormap_scale(
                    tag="intensity1",
                    height=400,
                    width=80
                )
            style_ = dpg.mvPlotColormap_Hot
            dpg.bind_colormap(plot_id, style_)
            dpg.bind_colormap(scale_id, style_)
            with dpg.group(horizontal=True):
                with dpg.plot(label="Левая платформа", height=500, width=600, no_menus=True, no_title=True,
                              crosshairs=True) as plot_id:
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="X, мкм", tag="my_x_axis2")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Y, мкм", tag="my_y_axis2")
                    dpg.add_heat_series(
                        x=[.1, .1, .1, .1],
                        rows=4,
                        cols=4,
                        format="",
                        tag="heatmap2",
                        parent="my_y_axis2"
                    )
                scale_id = dpg.add_colormap_scale(
                    tag="intensity2",
                    height=400,
                    width=80
                )
            style_ = dpg.mvPlotColormap_Hot
            dpg.bind_colormap(plot_id, style_)
            dpg.bind_colormap(scale_id, style_)

        with dpg.group():
            with dpg.group(horizontal=False):
                dpg.add_text(tag="pmap_meas_power_diff")
                dpg.add_text(tag="pmap_meas_power_avg")
                dpg.add_combo(tag="pmap_device", items=[DEV_NOT_FOUND], default_value=DEV_NOT_FOUND,
                              width=200, callback=select_pm)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        # dpg.add_text(default_value="Канал измерителя")
                        dpg.add_text(tag="pmap_meas_power")
                        dpg.add_combo(tag="pmap_meas_chanel", items=["Нет"], default_value='Нет', width=100,
                                      callback=self.select_pm_chan)
                    with dpg.group(tag="pm_pm2", show=False):
                        # dpg.add_text(default_value="Канал измерителя 2")
                        dpg.add_text(tag="pmap_meas_power2")
                        dpg.add_combo(tag="pmap_meas_chanel2", items=["Нет"], default_value='Нет', width=100,
                                      callback=self.select_pm_chan2)
        context.pmap_procedures.draw_map(context.pmap_procedures.ser_data, 1)
        context.pmap_procedures.draw_map(context.pmap_procedures.ser_data, 2)

    def select_pm_chan(self, sender, app_data, user_data):
        chan = dpg.get_value('pmap_meas_chanel')
        if not chan.isdigit():
            dpg.set_value("pmap_meas_power", "***")
        else:
            self.meas_chan = int(chan)
            if context.pmap_procedures.pm_dev == context.device_worker.pm2100_2_ctrl:
                self.meas_chan += 20
            elif context.pmap_procedures.pm_dev == context.device_worker.pm2100_3_ctrl:
                self.meas_chan += 40

    def select_pm_chan2(self, sender, app_data, user_data):
        chan = dpg.get_value('pmap_meas_chanel2')
        if chan.isdigit():
            self.meas_chan2 = int(chan)
            if context.pmap_procedures.pm_dev == context.device_worker.pm2100_2_ctrl:
                self.meas_chan2 += 20
            elif context.pmap_procedures.pm_dev == context.device_worker.pm2100_3_ctrl:
                self.meas_chan2 += 40

    def powermap_loop(self):
        # context.current_proc
        if dpg.get_value(context.tabBar) != TAB_POWERMAP_ID:
            return
        if self.pm_mode == 0:
            pass
            # self.cross = context.pmap_procedures.process_crosshair(self.cross)


def sync_mode_callback(sender, app_data, user_data):
    if dpg.get_value(sender):
        context.pmap_procedures.sync_mode = True
    else:
        context.pmap_procedures.sync_mode = False


def select_pm(sender, app_data, user_data):
    device = dpg.get_value('pmap_device')
    chan_list = []
    if device == POWER_METER_1:
        context.pmap_procedures.pm_dev = context.device_worker.pm2100_1_ctrl
        for i in range(0, 20):
            if context.act_chans[i]:
                chan_list.append(str(i))
    elif device == POWER_METER_2:
        context.pmap_procedures.pm_dev = context.device_worker.pm2100_2_ctrl
        for i in range(20, 40):
            if context.act_chans[i]:
                chan_list.append(str(i - 20))
    elif device == POWER_METER_3:
        context.pmap_procedures.pm_dev = context.device_worker.pm2100_3_ctrl
        for i in range(40, 60):
            if context.act_chans[i]:
                chan_list.append(str(i - 40))
    if len(chan_list) == 0:
        context.pmap_procedures.pm_dev = None
        chan_list = ['Нет']
        dpg.configure_item('pmap_meas_chanel', items=chan_list)
        dpg.configure_item('pmap_meas_chanel2', items=chan_list)
        dpg.set_value('pmap_meas_chanel', chan_list[0])
        dpg.set_value('pmap_meas_chanel2', chan_list[0])
    else:
        dpg.configure_item('pmap_meas_chanel', items=chan_list)
        dpg.configure_item('pmap_meas_chanel2', items=chan_list)
        dpg.set_value('pmap_meas_chanel', chan_list[0])
        dpg.set_value('pmap_meas_chanel2', chan_list[1])


def make_sync_dbg_sync(sender, app_data, user_data):
    if context.device_worker.is_sync_connected:
        context.device_worker.sync_ctrl.make_sync(10000, 1000)


def make_sync_dbg_get_err(sender, app_data, user_data):
    if context.device_worker.is_pm2100_1_connected:
        res = context.device_worker.pm2100_1_ctrl.get_err()
        print("err=", res)


def make_sync_dbg_get_meas(sender, app_data, user_data):
    if context.device_worker.is_pm2100_1_connected:
        res = context.device_worker.pm2100_1_ctrl.get_meas_data(0, 1)
        print("meas=", res)


def make_sync_dbg_get_meas_state(sender, app_data, user_data):
    if context.device_worker.is_pm2100_1_connected:
        res1, res2, = context.device_worker.pm2100_1_ctrl.get_meas_state()
        print("res1=", res1)
        print("res2=", res2)


def make_sync_dbg_stop_meas(sender, app_data, user_data):
    if context.device_worker.is_pm2100_1_connected:
        context.device_worker.pm2100_1_ctrl.stop_meas()
        context.device_worker.pm2100_1_ctrl.set_work_mode(4, False)


def make_sync_dbg_start_meas(sender, app_data, user_data):
    if context.device_worker.is_pm2100_1_connected:
        context.device_worker.pm2100_1_ctrl.startConst2(1535, 0.01, 10000)


def platform_sel_callback(sender, app_data, user_data):
    if dpg.get_value("pmap_platform") == LEFT:
        context.pmap_procedures.set_platform(False)

    else:
        context.pmap_procedures.set_platform(True)


context.meas_powermap = MeasurePowerMap()
