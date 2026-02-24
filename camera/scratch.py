import cv2
import numpy as np
import dearpygui.dearpygui as dpg


def get_k(line):
    x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
    if x2-x1 == 0:
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


def resize_image(img, scale_percent):
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    return cv2.resize(img, dim, interpolation=cv2.INTER_AREA)


def display_img(label, img):
    data = np.astype(img, np.float32)
    data = np.true_divide(data, 255.0)
    dpg.set_value(label, data)


def Mono_numpy_old(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
    data_mono_arr = data_.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 1], "uint8")
    numArray[:, :, 0] = data_mono_arr
    return numArray


def Mono_numpy(data, nWidth, nHeight):
    bytes_as_np_array = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8).reshape((nWidth, nHeight))

    return bytes_as_np_array



    # context.zcontrollers.move_axis(int(context.axis[context.z2_line_i]['dir_fw']),
    #                                 context.axis[context.z2_line_i]['idx'])
# k, b = 2, 3
# line_a = [0.1, get_y(0.1, k, 3), 5, get_y(5, 2, 3)]
# print(get_b(line_a))
