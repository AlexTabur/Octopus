import cv2
import numpy as np

from core.consts import PIX_PER_UM

# https://docs.opencv.org/4.2.0/d4/da8/group__imgcodecs.html
path = "Pics/"


# haystack_img = cv.imread(f'{path}topdown right roi left.bmp')


# There are 6 comparison methods to choose from:
# TM_CCOEFF, TM_CCOEFF_NORMED, TM_CCORR, TM_CCORR_NORMED, TM_SQDIFF, TM_SQDIFF_NORMED
# You can see the differences at a glance here:
# https://docs.opencv.org/master/d4/dc6/tutorial_py_template_matching.html
# Note that the values are inverted for TM_SQDIFF and TM_SQDIFF_NORMED


def find_template1(img, template_img, t_wh):
    if len(img.shape) < 3:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    result = cv2.matchTemplate(img, template_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # print('Best match confidence: %s' % max_val)
    threshold = 0.8
    # if max_val >= threshold:

    top_left = max_loc
    bottom_right = (top_left[0] + t_wh[0], top_left[1] + t_wh[1])
    cv2.rectangle(img, top_left, bottom_right, color=(255, 0, 0), thickness=2, lineType=cv2.LINE_4)
    return img, max_loc


def rotate_image(img, angle):
    image_center = np.array(img.shape[1::-1]) / 2
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    # for i in x:
    #     cv2.circle(image, (i[0], i[1]), 2, (255, 0, 0), 2)
    result = cv2.warpAffine(img, rot_mat, img.shape[1::-1], flags=cv2.INTER_LINEAR)

    return result


def get_matrix(image, angle):
    image_center = np.array(image.shape[1::-1]) / 2
    M = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    M2 = np.zeros((3, 3))
    M2[2, 2] = 1
    M2[0] = M[0]
    M2[1] = M[1]
    return M2


def get_point(image, angle, x):
    # Your transformation matrix M from cv2.getRotationMatrix2D or elsewhere

    # M = ...
    M = get_matrix(image, angle)  #
    # M = np.linalg.inv(M)

    # Original coordinates: (x, y)
    v = np.array([x[0], -x[1], 1], dtype='float32').T

    new_points = M @ v

    # Final result (x_new, y_new)
    return new_points.astype(np.int8)


def get_point2(image, angle, x):
    cx = tuple(np.array(image.shape[1::-1]) / 2)
    alpha = np.cos(np.deg2rad(angle))
    beta = np.sin(np.deg2rad(angle))
    out = [0, 0]
    out[0] = (alpha * x[0] + beta * x[1] + (1 - alpha) * cx[0] - beta * cx[1])
    out[1] = (-beta * x[0] + alpha * x[1] + beta * cx[0] + (1 - alpha) * cx[1])
    return out


def get_points(image, angle, arr):
    out = []
    for i in arr:
        out.append(get_point2(image, angle, i))
    return out


def find_template2(img, angle, right):
    safety_offset = 50*PIX_PER_UM
    step = 127 * PIX_PER_UM
    res_ = rotate_image(img, angle)
    name = f'{path}template right.bmp' if right else f'{path}template left.bmp'
    template_img = cv2.imread(name)
    t_wh = template_img.shape[1], template_img.shape[0]
    if right:
        offset = [200+safety_offset, 590]
    else:
        offset = [-40-safety_offset, 11]
    res_, tl = find_template1(res_, template_img, t_wh)
    x = []
    for i in range(16):
        x.append([tl[0] + offset[0], tl[1] + offset[1] + i * step])
    res2_ = get_points(img, -angle, x)
    return res_, res2_


if __name__ == "__main__":
    img_ = cv2.imread(f'{path}test2.bmp')
    res, res2 = find_template2(img_, 11, False)
    for _ in res2:
        cv2.circle(img_, (int(_[0]), int(_[1])), 1, (0, 255, 0), 2)
    cv2.imshow("bruh", img_)
    A = cv2.waitKey(5)
    while A != 113:
        A = cv2.waitKey(5)
        # print(A)
        pass
