import cv2
import numpy as np
import dearpygui.dearpygui as dpg


def get_k(line):
    x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
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


def rotate_z(context, angle1, right):
    if right:
        axis = context.axis[context.z2_ang_i]['idx']
    else:
        axis = context.axis[context.z1_ang_i]['idx']

    # context.logger.log_warning(str(axis) + " " + str(dir))
    # return

    if axis != -1:
        context.current_axis = axis
        if context.zplatform.is_connected:
            # print("moving on axis = ", abs(context.current_axis))
            steps_per_degree = 2360
            print(angle1)
            context.zplatform.move(axis, steps_per_degree*angle1)
            # print(self.angle1, self.angle2, self.angle1 - self.angle2)
        else:
            print("not connected")


def move_x(context, delta, right, obj):
    if right:
        axis = context.axis[context.x2_line_i]['idx']
    else:
        axis = context.axis[context.x1_line_i]['idx']
    if axis != -1:
        context.current_axis = axis
        if context.zplatform.is_connected:
            # print("moving on axis = ", abs(context.current_axis))

            print(delta)
            # 32.961405521725055
            context.zplatform.move(axis, delta * 1600/38)
        else:
            print("not connected")
    # context.zcontrollers.move_axis(int(context.axis[context.z2_line_i]['dir_fw']),
    #                                 context.axis[context.z2_line_i]['idx'])
# k, b = 2, 3
# line_a = [0.1, get_y(0.1, k, 3), 5, get_y(5, 2, 3)]
# print(get_b(line_a))
