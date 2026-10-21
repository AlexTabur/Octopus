import json

import cv2
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore

import zmotion
from camera import Camera
from scratch import isHorizontal
from core.consts import UM_PER_STEP_TABLE, PIX_PER_UM
from core.context_ import Context
from find_template import find_template2
from graph import Graph
from move_from_camera import points_to_k_b

table_angle = 89.4712502
context = Context()


def k_b_to_points(k, b):
    x1 = 20
    x2 = 5120 - 20
    y1 = k * x1 + b
    y2 = k * x2 + b
    return [y1, x1], [y2, x2]


# Начальные позиции точек (6 точек: 0-1 левая пара, 2-3 правая пара, 4-5 авто-углы)
pos = np.array([(100, 100), (100, 500), (400, 100), (400, 500), (0, 0), (0, 0)], dtype=np.float32)


def fill(im_th, right):
    im_floodfill = np.array(im_th.copy())
    h, w = im_th.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    if right:
        cv2.floodFill(im_floodfill, mask, [w - 2, 0], [255])
    else:
        cv2.floodFill(im_floodfill, mask, [0, 0], [255])
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
    return im_th | im_floodfill_inv


pos_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def worker_f(camera_points, cam_num, name, pos_, focus_side_view_l, focus_side_view_r, moving_right):
    saved_data = {'p1': None, 'p2': None, 'stage1': 0.0, 'stage2': 0.0}
    global pos_array
    pos_array = pos_
    cam = Camera(cam_num)
    shape1 = (5120, 5120)
    pg.mkQApp(name + "_")
    win = pg.GraphicsLayoutWidget(show=True, title=name)
    view_box = win.addViewBox()
    img_item = pg.ImageItem()
    view_box.addItem(img_item)
    histogram1 = pg.HistogramLUTItem()
    histogram2 = pg.HistogramLUTItem()
    histogram3 = pg.HistogramLUTItem()
    histogram4 = pg.HistogramLUTItem()
    histogram1.setToolTip("left")
    histogram1.setToolTip("left wg")
    histogram1.setToolTip("right")
    histogram1.setToolTip("right wg")
    win.addItem(histogram1)
    win.addItem(histogram2)
    win.addItem(histogram3)
    win.addItem(histogram4)
    histogram1.disableAutoHistogramRange()
    histogram2.disableAutoHistogramRange()
    histogram3.disableAutoHistogramRange()
    histogram4.disableAutoHistogramRange()
    histogram1.setHistogramRange(0, 255)
    histogram2.setHistogramRange(0, 255)
    histogram3.setHistogramRange(0, 255)
    histogram4.setHistogramRange(0, 255)
    view_box.invertY(True)
    view_box.setLimits(xMin=0, xMax=shape1[0], yMin=0, yMax=shape1[0])

    g = Graph()
    view_box.addItem(g)
    brushes = [pg.mkBrush('r'), pg.mkBrush('r'),  # 0, 1 - красные
               pg.mkBrush(150, 150, 150), pg.mkBrush(150, 150, 150),  # 2, 3 - зеленые
               pg.mkBrush(150, 150, 150), pg.mkBrush(150, 150, 150)]
    g.setData(pos=pos, size=12, pxMode=True, symbolBrush=brushes)

    text_1 = pg.TextItem("Left: ", color='r')
    text_2 = pg.TextItem("Right: ", anchor=(0, -0.5), color='r')
    text_3 = pg.TextItem("Difference: ", anchor=(0, -1), color='r')
    view_box.addItem(g)

    view_box.addItem(text_1)
    view_box.addItem(text_2)
    view_box.addItem(text_3)

    worker_1 = Image_Worker("left", g, name, histogram1, histogram2, focus_side_view_l, moving_right)
    worker_2 = Image_Worker("right", g, name, histogram3, histogram4, focus_side_view_r, moving_right)
    view_box.addItem(worker_1.roi)
    view_box.addItem(worker_2.roi)

    def update_image():

        cam.grab()
        img = np.frombuffer(cam.buf_grab_image, count=int(5120 * 5120), dtype=np.uint8).reshape(shape1)
        if cam_num == 1:
            img = cv2.flip(img, 1)
        worker_1.average_image(img)
        worker_2.average_image(img)
        for i in range(len(g.data['pos'])):
            camera_points[i * 2], camera_points[i * 2 + 1] = g.data['pos'][i]

        img_item.setImage(img.T, autoLevels=False, autoRange=False)

        k, b, angle1 = points_to_k_b(g.data['pos'][0], g.data['pos'][1])
        k, b, angle2 = points_to_k_b(g.data['pos'][2], g.data['pos'][3])
        diff_l = g.data['pos'][1] - g.data['pos'][0]
        diff_r = g.data['pos'][1] - g.data['pos'][0]
        dx_um_l = diff_l[0] / PIX_PER_UM
        dx_um_r = diff_r[0] / PIX_PER_UM
        dy_um_l = diff_l[1] / PIX_PER_UM
        dy_um_r = diff_r[1] / PIX_PER_UM
        text_1.setText(
            f"left angle {angle1:.3f}, right angle {angle2:.3f} dx left {dx_um_l:.3f} dy left {dy_um_l:.3f} dx right {dx_um_r:.3f} dy right {dy_um_r:.3f}")

        if saved_data['stage1'] is not None and saved_data['stage2'] is not None:
            s1 = saved_data['stage1'] if saved_data['stage1'] is not None else 0.0
            s2 = saved_data['stage2'] if saved_data['stage2'] is not None else 0.0

            stage_dy = s2 - s1
            val = stage_dy * UM_PER_STEP_TABLE
            stage_dy_um = val * np.sin(np.pi - angle2 * np.pi / 180)
            stage_dx_um = val * np.cos(np.pi - angle2 * np.pi / 180)
            total_dy_um = stage_dy_um - dy_um_l
            total_dx_um = dx_um_l - stage_dx_um
            total_um_dist = np.sqrt(total_dy_um ** 2 + total_dx_um ** 2)
            total_mm_dist = total_um_dist / 1000

            text_3.setHtml(
                f'<b style="color:red; font-size:18pt;">Measured: {total_mm_dist:.3f} mm</b>')

    timer = QtCore.QTimer()
    timer.timeout.connect(update_image)
    timer.start(150)
    pg.exec()


def get_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denominator == 0:
        return np.nan, np.nan
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator
    return px, py


def erosion(src, size=5, shape=0):
    element = cv2.getStructuringElement(shape, (2 * size + 1, 2 * size + 1),
                                        (size, size))
    return cv2.erode(src, element)


def dilatation(src, size=5, shape=0):
    element = cv2.getStructuringElement(shape, (2 * size + 1, 2 * size + 1),
                                        (size, size))
    return cv2.dilate(src, element)


def detect(l_th, canny_th1, canny_th2, aperture, out_, x1, y1):
    detector = cv2.ximgproc.createFastLineDetector(length_threshold=l_th, canny_th1=canny_th1, canny_th2=canny_th2,
                                                   canny_aperture_size=aperture)
    lines_ = detector.detect(out_)
    hx, hy, vx, vy = [], [], [], []
    if lines_ is not None:
        for line in lines_:
            line_ = line[0]
            if isHorizontal(line_):
                hx.extend([line_[0], line_[2]])
                hy.extend([line_[1], line_[3]])
            else:
                vx.extend([line_[0], line_[2]])
                vy.extend([line_[1], line_[3]])
    for i in range(len(hx)):
        hx[i] += x1
    for i in range(len(hy)):
        hy[i] += y1
    for i in range(len(vx)):
        vx[i] += x1
    for i in range(len(vy)):
        vy[i] += y1
    return vx, vy, hx, hy


class Image_Worker:
    def __init__(self, side, g, name, histogram, histogram_wg, focus_side_view, moving_right):
        self.moving_right_ = False
        self.prev_moving_right = False
        self.focus = focus_side_view
        self.max_n = 3
        self.changing = False
        self.y1 = None
        self.x1 = None
        self.i_n = 0
        self.img_array = None
        self.side = side
        self.histogram = histogram
        self.histogram_wg = histogram_wg
        self.moving_right = moving_right
        self.ready = False
        self.ready2 = False
        self.g = g
        self.name = name
        self.num = 0 if side == "left" else 1
        self.name_ = f"{name} {side}"
        self.histogram_name = f"{self.name_} hist"
        self.histogram_wg_name = f"{self.name_} hist wg"
        roi_pen = pg.mkPen({'color': "#500", 'width': 2})
        _pos = [2100, 2300]
        size = [300, 800]
        self.roi = pg.ROI(pos=_pos, size=size, pen=roi_pen)
        self.roi.addScaleHandle(pos=(1, 1), center=(0, 0))
        self.roi.sigRegionChangeFinished.connect(self.on_roi_size_change_end)
        self.load_hist_state()
        self.params_name = f'parameters {self.name_} roi'

        # _pos[0], _pos[1], size[0], size[1] = np.load(f"{self.name_} roi.npy")

        self._initialize_array()
        cv2.namedWindow(self.params_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.params_name, 400, 600)
        self.histogram.sigLevelChangeFinished.connect(self.save_hist_state)
        self.histogram_wg.sigLevelChangeFinished.connect(self.save_hist_state)
        a = np.array([36, 175, 212, 0, 175, 212])
        try:
            a = list(np.load(f"Config/{self.params_name}.npy").astype(int))
        except Exception as e:
            print(e)
        cv2.createTrackbar('length_threshold', self.params_name, a[0], 100, self.save_parameters)
        cv2.createTrackbar('th1', self.params_name, a[1], 512, self.save_parameters)
        cv2.createTrackbar('th2', self.params_name, a[2], 512, self.save_parameters)
        cv2.createTrackbar('canny_aperture_size', self.params_name, a[3], 2, self.save_parameters)
        cv2.createTrackbar('canny_th1', self.params_name, a[4], 512, self.save_parameters)
        cv2.createTrackbar('canny_th2', self.params_name, a[5], 512, self.save_parameters)
        self.ready = True
        self.ready2 = True
        self.focus_side_view = focus_side_view
        self.focus_array = []
        self.focus_array_x = []
        self.table = zmotion.ZMCWrapper()

    def save_hist_state(self):
        try:
            if self.ready:
                with open(f"Config/{self.name_} {self.moving_right_} roi.json", "w") as f:
                    a = self.roi.saveState()
                    json.dump(a, f)
        except Exception as e:
            print("save_hist_state 1", e)
        try:
            if self.ready:
                with open(f"Config/{self.histogram_name} {self.moving_right_}.json", "w") as f:
                    json.dump(self.histogram.saveState(), f)
                with open(f"Config/{self.histogram_wg_name} {self.moving_right_}.json", "w") as g:
                    json.dump(self.histogram_wg.saveState(), g)
        except Exception as e:
            print("save_hist_state 2", e)

    def load_hist_state(self):
        try:
            self.ready = False
            with open(f"Config/{self.name_} {self.moving_right_} roi.json") as f:
                self.roi.setState(json.load(f))
            self.ready = True
        except Exception as e:
            print("load_hist_state 1", e)
        try:
            self.ready = False
            with open(f"Config/{self.histogram_name} {self.moving_right_}.json") as f:
                self.histogram.restoreState(json.load(f))
            with open(f"Config/{self.histogram_wg_name} {self.moving_right_}.json") as g:
                self.histogram_wg.restoreState(json.load(g))
            self.ready = True
        except Exception as e:
            print("load_hist_state 2", e)

    def _initialize_array(self):
        size = self.roi.size()
        _pos = self.roi.pos()
        np.save(f"Config/{self.name_} roi", np.array([_pos.x(), _pos.y(), size[0], size[1]]))
        if size[0] > 0 and size[1] > 0:
            width, height = int(size[0]), int(size[1])
            self.img_array = np.zeros((self.max_n, height, width), dtype=np.uint8)
            self.i_n = 0

    def on_roi_size_change_start(self):
        self.changing = True

    def on_roi_size_change_end(self):
        self._initialize_array()
        self.changing = False

    def average_image(self, img):
        if self.changing:
            return
        pos_, size = self.roi.pos(), self.roi.size()
        width, height = int(size[0]), int(size[1])
        if self.img_array is None or self.img_array.shape[1] != height or self.img_array.shape[2] != width:
            self._initialize_array()
            return
        x1, y1 = int(pos_.x()), int(pos_.y())
        self.x1, self.y1 = x1, y1

        roi_img = img[max(0, y1):y1 + height, max(0, x1):x1 + width]
        if roi_img.shape[0] == height and roi_img.shape[1] == width:
            self.img_array[self.i_n] = roi_img
            self.i_n = (self.i_n + 1) % self.max_n
            chip_img = np.mean(self.img_array, axis=0).astype(np.uint8)

            if self.prev_moving_right != bool(self.moving_right.value):
                self.save_hist_state()
                self.moving_right_ = bool(self.moving_right.value)
                self.prev_moving_right = self.moving_right_
                self.load_hist_state()
            self.computer_vision(chip_img)

    def save_parameters(self, val):
        a = np.array([36, 175, 212, 0, 175, 212])
        if self.ready2:
            a[0] = cv2.getTrackbarPos('length_threshold', self.params_name)
            a[1] = cv2.getTrackbarPos('th1', self.params_name)
            a[2] = cv2.getTrackbarPos('th2', self.params_name)
            a[3] = cv2.getTrackbarPos('canny_aperture_size', self.params_name)
            a[4] = cv2.getTrackbarPos('th1', self.params_name)
            a[5] = cv2.getTrackbarPos('th2', self.params_name)
            np.save(f"Config/{self.params_name}", a)
        return

    def computer_vision(self, chip_img):
        canny_th1 = cv2.getTrackbarPos('canny_th1', self.params_name)
        canny_th2 = cv2.getTrackbarPos('canny_th2', self.params_name)

        aperture = (cv2.getTrackbarPos('canny_aperture_size', self.params_name) + 1) * 2 + 1
        l_th = cv2.getTrackbarPos('length_threshold', self.params_name) + 1

        def out(hist):
            lut = hist.getLookupTable(chip_img, n=256)
            lut = lut[:, 0]
            scale = 255
            levels = hist.getLevels()
            croi_ = pg.functions.makeARGB(chip_img, lut, levels, scale)
            return croi_[0][:, :, 0].astype(np.uint8)

        out_wg = out(self.histogram_wg)
        out_ = out(self.histogram)

        # if self.name_ == "topdown right" and self.moving_right_:
        #     ret, out_ = cv2.threshold(out_, 127, 255, cv2.THRESH_BINARY)
        # else:
        #     out_ = fill(~out_, self.moving_right_)
        out_ = fill(~out_, self.moving_right_)
        self.get_waveguide_img(out_, out_wg, chip_img)
        contours, _ = cv2.findContours(out_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 4. Loop through contours and apply cv2.boundingRect
        width = None
        height = 0
        for cnt in contours:
            x0, y0, width, height = cv2.boundingRect(cnt)

        def get_points(mask):
            mask = cv2.Canny(mask, canny_th1, canny_th2, apertureSize=aperture)
            # 1. Получаем координаты ненулевых пикселей
            pts = cv2.findNonZero(mask)

            # 2. Проверяем, что пиксели найдены (массив не None и содержит достаточно точек)
            if pts is not None and len(pts) >= 2:

                pts = pts.astype(np.float32)

                # 4. Линейная аппроксимация
                [vx_, vy_, _x, _y] = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01)

                # Извлекаем скалярные значения из массивов NumPy
                vx_, vy_, _x, _y = float(vx_[0]), float(vy_[0]), float(_x[0]), float(_y[0])

                # Вычисление граничных точек для отрисовки
                _m = 1000
                line_point1 = _x - _m * vx_, _y - _m * vy_
                line_point2 = _x + _m * vx_, _y + _m * vy_

                return line_point1, line_point2
            else:
                return (0, 0), (1, 1)

        img = out_

        def func(_a, _b, _c, _d):
            border = 100
            _a += x0
            _b += x0 + border
            _c += y0
            _d += y0 + border
            cropped = img[_c:_d, _a:_b]
            p1, p2 = (0, 0), (0, 0)
            try:
                p1, p2 = get_points(cropped)
            except Exception as e:
                # print("can't find points,", e)
                pass
            cv2.rectangle(croi, (_a, _c), (_b, _d), (0, 255, 0))
            p1 = p1[0] + _a, p1[1] + _c
            p2 = p2[0] + _a, p2[1] + _c
            cv2.line(croi, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 0, 255), 1)
            return p1, p2

        croi = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        if width is not None:
            if self.name_.find("right") > -1:
                a1, a2 = func(int(width * 0.3), int(width * 0.6 - 1), 0, int(height * 0.2))
                a3, a4 = func(int(width * 0.3), int(width * 0.6), int(height * 0.8), int(height - 1))
                a5, a6 = func(0, int(width * 0.2), int(height * 0.15), int(height * 0.6))
                a1 = self.x1 + a1[0], self.y1 + a1[1]
                a2 = self.x1 + a2[0], self.y1 + a2[1]
                a3 = self.x1 + a3[0], self.y1 + a3[1]
                a4 = self.x1 + a4[0], self.y1 + a4[1]
                a5 = self.x1 + a5[0], self.y1 + a5[1]
                a6 = self.x1 + a6[0], self.y1 + a6[1]
            else:
                a1, a2 = func(0, int(width * 0.3), -20, int(height * 0.2))
                a3, a4 = func(0, int(width * 0.3), int(height * 0.8)+20, int(height - 1))
                a5, a6 = func(int(width * 0.8), int(width - 1), int(height * 0.15), int(height * 0.6))
                a1 = self.x1 + a1[0], self.y1 + a1[1]
                a2 = self.x1 + a2[0], self.y1 + a2[1]
                a3 = self.x1 + a3[0], self.y1 + a3[1]
                a4 = self.x1 + a4[0], self.y1 + a4[1]
                a5 = self.x1 + a5[0], self.y1 + a5[1]
                a6 = self.x1 + a6[0], self.y1 + a6[1]
            x1, y1 = get_intersect(a1[0], a1[1], a2[0], a2[1], a5[0], a5[1], a6[0], a6[1])
            if not np.isnan(x1):
                cv2.circle(croi, (int(x1), int(y1)), 6, (0, 255, 0), 2)
            x2, y2 = get_intersect(a3[0], a3[1], a4[0], a4[1], a5[0], a5[1], a6[0], a6[1])
            if not np.isnan(x2):
                cv2.circle(croi, (int(x2), int(y2)), 6, (0, 255, 0), 2)
            if not np.isnan(x1) and not np.isnan(x2):
                m, b = np.polyfit((a5[1], a6[1]), (a5[0], a6[0]), 1)
                self.g.data['pos'][0 + self.num * 2], self.g.data['pos'][1 + self.num * 2] = k_b_to_points(m, b)
                self.g.updateGraph()
            if self.name_ == "side view right" or self.name_ == "side view left":
                self.g.data['pos'][self.num + 4] = [x1, y1]
            if (self.name_ == "topdown left" and not self.moving_right_) or (
                    self.name_ == "topdown right" and self.moving_right_):
                if not np.isnan(x1) and not np.isnan(x2):
                    if self.name_ == "topdown right" and self.moving_right_:  # Правый фав
                        k, b, angle2 = points_to_k_b(self.g.data['pos'][2], self.g.data['pos'][3])
                        x = (x1 + x2) / 2
                        y = (y1 + y2) / 2
                        chan_num = 8
                        chan_offset = (24 - chan_num)
                        x += -(np.sin(np.deg2rad(angle2 + 90)) * 127 * chan_offset) * PIX_PER_UM
                        y += (np.cos(np.deg2rad(angle2 + 90)) * 127 * chan_offset + 30 - 180) * PIX_PER_UM  # 100 на себя 30 вверх
                        # 20 вниз 30 вверх
                    if self.name_ == "topdown left" and not self.moving_right_:  # Левый фав
                        k, b, angle2 = points_to_k_b(self.g.data['pos'][0], self.g.data['pos'][1])
                        x = (x1 + x2) / 2
                        y = (y1 + y2) / 2
                        chan_num = 23
                        chan_offset = (24 - chan_num)
                        x += -(np.sin(np.deg2rad(angle2 + 90)) * 127 * chan_offset) * PIX_PER_UM
                        y += (np.cos(np.deg2rad(angle2 + 90)) * 127 * chan_offset + 20 + 90) * PIX_PER_UM    # 90 от себя
                    cv2.circle(croi, (int(x - self.x1), int(y - self.y1)), 6, (0, 255, 0), 2)
                    self.g.data['pos'][self.num + 4] = [x, y]
        if (self.name_ == "topdown right" and not self.moving_right_) or (
                self.name_ == "topdown left" and self.moving_right_):
            detector = cv2.ximgproc.createFastLineDetector(length_threshold=l_th, canny_th1=canny_th1,
                                                           canny_th2=canny_th2,
                                                           canny_aperture_size=aperture)

            lines_ = detector.detect(~out_)

            def check_type(var):
                # Check for list (or other list-like sequences like tuples)
                if isinstance(var, (list, tuple)):
                    return "list-like"

                # Alternatively, check if it's an instance of a specific scalar type
                # (int, float, str, bool)
                return "scalar"

            hx, hy, vx, vy = [], [], [], []
            try:
                if lines_ is not None:

                    for line in lines_:
                        if check_type(line[0]) == 'scalar':
                            if isHorizontal(line):
                                hx.extend([line[0], line[2]])
                                hy.extend([line[1], line[3]])
                            else:
                                vx.extend([line[0], line[2]])
                                vy.extend([line[1], line[3]])
                        else:
                            line_ = line[0]
                            # print(line)
                            if isHorizontal(line_):
                                hx.extend([line_[0], line_[2]])
                                hy.extend([line_[1], line_[3]])
                            else:
                                vx.extend([line_[0], line_[2]])
                                vy.extend([line_[1], line_[3]])
                for i in range(len(hx)):
                    hx[i] += self.x1
                for i in range(len(hy)):
                    hy[i] += self.y1
                for i in range(len(vx)):
                    vx[i] += self.x1
                for i in range(len(vy)):
                    vy[i] += self.y1
                if len(vx) > 0:
                    m, b = np.polyfit(vy, vx, 1)
                    self.g.data['pos'][0 + self.num * 2], self.g.data['pos'][1 + self.num * 2] = k_b_to_points(m, b)
                    self.g.updateGraph()
            except Exception as e:
                print(e)
        cri = croi  # (~down) & up
        cv2.imshow(self.params_name, cri)
        self.g.updateGraph()

    def get_waveguide_img(self, img, img_wg, chip_img):
        if self.name_ == "topdown left" and not self.moving_right_:  # Левый фав
            ret, img = cv2.threshold(img, 255 / 2, 255, cv2.THRESH_BINARY)
            img = dilatation(img, 20)
            img = fill(img, self.moving_right_)
            img = ~erosion(img, 10)
            ret, img_wg = cv2.threshold(img_wg, 255 / 2, 255, cv2.THRESH_BINARY)
            img_wg = cv2.bitwise_and(~img_wg, img)
        if self.name_ == "topdown right" and self.moving_right_:  # Правый фав
            ret, img = cv2.threshold(img, 255 / 2, 255, cv2.THRESH_BINARY)
            img = dilatation(img, 20)
            img = fill(img, self.moving_right_)
            img = ~erosion(img, 10)
            ret, img_wg = cv2.threshold(img_wg, 255 / 2, 255, cv2.THRESH_BINARY)
            img_wg = cv2.bitwise_and(~img_wg, img)

        if self.name_ == "topdown right" and not self.moving_right_:  # левый стрип
            k, b, angle2 = points_to_k_b(self.g.data['pos'][2], self.g.data['pos'][3])
            img_wg, res2 = find_template2(chip_img, -(90 - angle2), self.moving_right_)
            chan_num = 7
            self.g.data['pos'][self.num + 4] = self.x1 + res2[chan_num][0], res2[chan_num][1] + self.y1

        if self.name_ == "topdown left" and self.moving_right_:  # правый стрип
            chan_num = 7
            k, b, angle2 = points_to_k_b(self.g.data['pos'][2], self.g.data['pos'][3])
            img_wg, res2 = find_template2(chip_img, -(90 - angle2), self.moving_right_)
            self.g.data['pos'][self.num + 4] = self.x1 + res2[chan_num][0], res2[chan_num][1] + self.y1

        if self.name_ == "side view right" and (not self.moving_right_):  # левый стрип
            self.focus.value = np.sum(img)
        if self.name_ == "side view left" and self.moving_right_:  # правый стрип
            self.focus.value = np.sum(img)

        return img_wg
