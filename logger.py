import dearpygui.dearpygui as dpg

filt_items = ["COMMON", "COMMUNICATION", "WARNING", "ERROR", "CRITICAL"]


class Logger:

    def __init__(self, parent=None, w_width=1, w_heigth=1, w_x=0, w_y=1):
        self.log_level = 0
        self.filter = 0xf
        self._auto_scroll = True
        self.filter_id = None
        # if parent:
        #     self.window_id = parent
        # else:
        self.window_id = dpg.add_window(label="Log", pos=(w_x, w_y), width=w_width, height=w_heigth,
                                            no_close=True, no_collapse=True, autosize=True)
        self.count = 0
        self.flush_count = 1000

        with dpg.group(horizontal=True, parent=self.window_id):
            with dpg.group():
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="Auto-scroll", default_value=True,
                                     callback=lambda sender: self.auto_scroll(dpg.get_value(sender)))
                dpg.add_spacer(height=5)
                with dpg.group():
                    dpg.add_checkbox(label=filt_items[0], callback=self.set_filter_callback, user_data=0x01,
                                     default_value=True)
                    dpg.add_checkbox(label=filt_items[1], callback=self.set_filter_callback, user_data=0x02,
                                     default_value=True)
                    dpg.add_checkbox(label=filt_items[2], callback=self.set_filter_callback, user_data=0x04,
                                     default_value=True)
                    dpg.add_checkbox(label=filt_items[3], callback=self.set_filter_callback, user_data=0x08,
                                     default_value=True)
                    dpg.add_checkbox(label=filt_items[4], callback=self.set_filter_callback, user_data=0x10,
                                     default_value=True)
                dpg.add_spacer(height=5)
                dpg.add_button(label="Clear", width=200, height=30,
                               callback=lambda: dpg.delete_item(self.filter_id, children_only=True))

            self.child_id = dpg.add_child_window(autosize_x=True, autosize_y=True)
            self.filter_id = dpg.add_filter_set(parent=self.child_id, )
            flt = "[TRACE]"
            for f in filt_items:
                flt += ',[' + f + ']'
            dpg.set_value(self.filter_id, flt)

            with dpg.theme() as self.trace_theme:
                with dpg.theme_component(0):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 255, 0, 255))

            with dpg.theme() as self.debug_theme:
                with dpg.theme_component(0):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (64, 128, 255, 255))

            with dpg.theme() as self.info_theme:
                with dpg.theme_component(0):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

            with dpg.theme() as self.warning_theme:
                with dpg.theme_component(0):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 0, 255))

            with dpg.theme() as self.error_theme:
                with dpg.theme_component(0):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 0, 0, 255))

            with dpg.theme() as self.critical_theme:
                with dpg.theme_component(0):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 0, 0, 255))

    def auto_scroll(self, value):
        self._auto_scroll = value

    def _log(self, message, level):

        if level & self.log_level:
            return

        self.count += 1

        if self.count > self.flush_count:
            self.clear_log()

        theme = self.info_theme

        if level == 0:
            message = "[TRACE]\t\t" + message  # COMMON
            theme = self.trace_theme
        elif level == 0x01:
            message = f"[{filt_items[0]}]\t\t" + message  # COMMON
            theme = self.warning_theme
        elif level == 0x02:
            message = f"[{filt_items[1]}]\t\t" + message  # WARNING
            theme = self.warning_theme
        elif level == 0x04:
            message = f"[{filt_items[2]}]\t\t" + message  # WARNING
            theme = self.warning_theme
        elif level == 0x08:
            message = f"[{filt_items[3]}]\t\t" + message  # ERROR
            theme = self.error_theme
        elif level == 0x10:
            message = f"[{filt_items[4]}]\t\t" + message  # CRITICAL
            theme = self.critical_theme

        new_log = dpg.add_text(message, parent=self.filter_id, filter_key=message)
        dpg.bind_item_theme(new_log, theme)
        if self._auto_scroll:
            scroll_max = dpg.get_y_scroll_max(self.child_id)
            dpg.set_y_scroll(self.child_id, -1.0)

    def log(self, message):
        self._log(message, 0x00)

    def log_com(self, message):
        self._log(message, 0x01)

    def log_comunication(self, message):
        self._log(message, 0x02)

    def log_warning(self, message):
        self._log(message, 0x04)

    def log_error(self, message):
        self._log(message, 0x08)

    def log_critical(self, message):
        self._log(message, 0x10)

    def clear_log(self):
        dpg.delete_item(self.filter_id, children_only=True)
        self.count = 0

    def set_filter_callback(self, sender, app_data, user_data):
        if dpg.get_value(sender):
            self.filter |= user_data
        else:
            self.filter &= ~user_data
        flt = "[TRACE]"
        for idx, fstr in enumerate(filt_items):
            if self.filter & (1 << idx):
                flt += ",[" + fstr + "]"
        dpg.set_value(self.filter_id, flt)
        # self.log_level
