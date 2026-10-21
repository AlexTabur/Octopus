import cv2
import numpy as np
import dearpygui.dearpygui as dpg


def isHorizontal(line):
    x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
    return abs(x2 - x1) > abs(y2 - y1)


def get_k(line):
    x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
    if x2 - x1 == 0:
        return 1000
    return (y2 - y1) / (x2 - x1)


def get_b(line):
    x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
    return y1 - get_k(line) * x1


def get_y(x, k, b):
    return k * x + b


def length(line):
    dx = line[0] - line[2]
    dy = line[1] - line[3]
    return (dx ** 2 + dy ** 2) ** 0.5


def angle(line):
    dx = line[2] - line[0]
    dy = line[3] - line[1]
    a = np.angle(dx + 1j * dy)
    if a < 0:
        a += np.pi
    a *= 180 / np.pi

    return -a


def resize_image(img, scale_percent: int):
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    return cv2.resize(img, dim, interpolation=cv2.INTER_AREA)


def display_img(label, img):
    data = np.astype(img, np.float32)
    data = np.true_divide(data, 255.0)
    dpg.set_value(label, data)


def Mono_numpy(data, nWidth, nHeight) -> np.ndarray:
    bytes_as_np_array = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8).reshape((nWidth, nHeight))

    return bytes_as_np_array
