import math
import numpy as np
import pandas as pd

from core.context_ import Context

context = Context()


class DataSheet:

    def __init__(self):
        self.pow_list_sorted = None
        self.wl_list = None

        self.dt = [('ChanNum', int), ('wl', float), ('min_loss', float), ('max_loss', float), ('ITU', float),
                   ('ITU_delt', int),
                   ('ITU_num', int), ('PB_20', float), ('PB_3', float), ('PB_1', float), ('PB_5', float),
                   ('XT', float), ('TXT', float), ('NXT', float)]

        # ('name', 'U10'), ('idx', int), ('acc', 'f4'),
        self.fin_arr = np.array([], self.dt)

    def find_wl(self, data_pow):
        min_loss = np.max(data_pow)
        max_loss = np.min(data_pow)
        ch_loss = data_pow[data_pow >= min_loss - 3]
        lambda1_idx = np.where(data_pow == ch_loss[0])[0][0]
        lambda2_idx = np.where(data_pow == ch_loss[len(ch_loss) - 1])[0][0]

        pb3db = self.wl_list[lambda2_idx] - self.wl_list[lambda1_idx]
        wl = pb3db / 2 + self.wl_list[lambda1_idx]
        # if len(data_pow) - (lambda2_idx - lambda1_idx) < len(data_pow)/4:
        if min_loss < -40:
            wl = 9999
        return wl, min_loss, max_loss

    def prepare_line_chan(self, data_pow, chan_num):
        chan_wl, min_loss, max_loss = self.find_wl(data_pow)
        chan_row = np.array([(chan_num, chan_wl, min_loss, max_loss, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)], self.dt)
        self.fin_arr = np.append(self.fin_arr, chan_row)

    def make_data_sheet(self, wl, pow_list, report_filename):
        self.wl_list = wl

        for idx_y in range(len(pow_list)):
            self.prepare_line_chan(pow_list[idx_y], idx_y)

        self.fin_arr = np.sort(self.fin_arr, order='wl')
        self.pow_list_sorted = np.copy(pow_list)
        for idx, d in enumerate(self.fin_arr):
            self.pow_list_sorted[idx] = np.copy(pow_list[d['ChanNum']])
        itu = np.zeros(72)
        for i in range(72):
            itu[i] = 299792458 / (190100 + 100 * i)

        for p in range(len(self.fin_arr)):
            for i in range(72):
                if abs(self.fin_arr[p]['wl'] - itu[i]) < 0.41:
                    self.fin_arr[p]['ITU'] = itu[i]
                    self.fin_arr[p]['ITU_num'] = i + 1
                    self.fin_arr[p]['ITU_delt'] = np.round((self.fin_arr[p]['wl'] - itu[i]) * 1000)

        NXT = np.zeros(len(pow_list)) - 100
        for idx, chan in enumerate(self.pow_list_sorted):
            #            if idx == 59:
            #                print(idx)
            fin_arr_idx = idx  # np.where(self.fin_arr['ChanNum'] == idx)[0][0]
            if self.fin_arr[fin_arr_idx]['wl'] == 9999:
                continue
            min_loss = self.fin_arr[fin_arr_idx]['min_loss']
            cur_wl = self.fin_arr[fin_arr_idx]['wl']
            for PB in (-20, -3, -1, -0.5):
                chanel_slice = chan[chan >= (PB + min_loss)]
                if len(chanel_slice) < 2:
                    continue
                idx0 = np.where(chan == chanel_slice[0])[0][0]
                idx1 = np.where(chan == chanel_slice[len(chanel_slice) - 1])[0][0]

                if abs(chanel_slice[0] - (PB + min_loss)) < abs(chan[idx0 - 1] - (PB + min_loss)):
                    chanel_slice = chan[idx0 - 1:idx1]
                elif abs(chanel_slice[0] - (PB + min_loss)) < abs(chan[idx0 + 1] - (PB + min_loss)):
                    chanel_slice = chan[idx0:idx1 + 1]

                if len(chanel_slice) < 2:
                    continue

                idx0 = np.where(chan == chanel_slice[0])[0][0]
                idx1 = np.where(chan == chanel_slice[len(chanel_slice) - 1])[0][0]

                pb_slice = self.wl_list[idx1] - self.wl_list[idx0]
                if PB == -20:
                    self.fin_arr[fin_arr_idx]['PB_20'] = pb_slice
                elif PB == -3:
                    self.fin_arr[fin_arr_idx]['PB_3'] = pb_slice
                elif PB == -1:
                    self.fin_arr[fin_arr_idx]['PB_1'] = pb_slice
                else:
                    self.fin_arr[fin_arr_idx]['PB_5'] = pb_slice

            #            wv = self.wl_list[(self.wl_list <= (cur_wl + 0.0998)) & (self.wl_list >= (cur_wl - 0.0998))]
            #            wl_idx0 = np.where(self.wl_list == np.min(wv))[0][0]
            #            wl_idx1 = np.where(self.wl_list == np.max(wv))[0][0]
            wv = self.wl_list[(self.wl_list <= (cur_wl + 0.0998)) & (self.wl_list >= (cur_wl - 0.0998))]
            if len(wv) == 0:
                continue
            wl_idx0 = np.where(self.wl_list == wv[0])[0][0]
            wl_idx1 = np.where(self.wl_list == wv[len(wv) - 1])[0][0]
            XT_other_chan = np.zeros(len(pow_list))
            XT_other_chan_mvt = np.zeros(len(pow_list))

            for chan_XT_idx, chan_XT in enumerate(self.pow_list_sorted):
                if self.fin_arr[chan_XT_idx]['wl'] == 9999:
                    continue
                chanel_XT = chan_XT[wl_idx0:wl_idx1]
                if chan_XT_idx != idx:
                    XT_other_chan[chan_XT_idx] = np.max(chanel_XT) - min_loss  # ????
                    XT_other_chan_mvt[chan_XT_idx] = 10 ** (XT_other_chan[chan_XT_idx] / 10)
                    if chan_XT_idx <= idx - 2 or chan_XT_idx >= idx + 2:
                        if NXT[idx] <= XT_other_chan[chan_XT_idx]:
                            NXT[idx] = XT_other_chan[chan_XT_idx]

            self.fin_arr[fin_arr_idx]['TXT'] = -10 * math.log10(XT_other_chan_mvt.sum())
            if idx == 0:
                self.fin_arr[fin_arr_idx]['XT'] = XT_other_chan[idx + 1]
            elif idx == len(pow_list) - 1:
                self.fin_arr[fin_arr_idx]['XT'] = XT_other_chan[idx - 1]
            else:
                self.fin_arr[fin_arr_idx]['XT'] = max(XT_other_chan[idx + 1], XT_other_chan[idx - 1])

            self.fin_arr[fin_arr_idx]['NXT'] = NXT[idx]

        filename = report_filename[:-4] + '_datasheet.csv'
        df = pd.DataFrame(self.fin_arr)
        df.to_excel(filename, index=False)
