import numpy as np
import cv2


def rpy_matrix(yaw, pitch, roll):
    # Convert angles to radians if they are in degrees
    y = np.radians(yaw)
    p = np.radians(pitch)
    r = np.radians(roll)

    # Yaw matrix (Rotation around Z)
    Rz = np.array([
        [np.cos(y), -np.sin(y), 0],
        [np.sin(y), np.cos(y), 0],
        [0, 0, 1]
    ])

    # Pitch matrix (Rotation around Y)
    Ry = np.array([
        [np.cos(p), 0, np.sin(p)],
        [0, 1, 0],
        [-np.sin(p), 0, np.cos(p)]
    ])

    # Roll matrix (Rotation around X)
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(r), -np.sin(r)],
        [0, np.sin(r), np.cos(r)]
    ])

    # Total Rotation = Rz * Ry * Rx (Yaw -> Pitch -> Roll)
    return Rz @ Ry @ Rx


if __name__ == "__main__":
    img = np.zeros((800, 800, 3))
    points = np.array([
        [0, 0, 0],
        [100, 0, 0],
        [0, 100, 0],
        [0, 0, 100],
    ])
    for i in points:
        x, y, z = i
        cv2.circle(img, (100 + x, 100 + y), 3, (255, 0, 0), 2)
        in_ = i.T
        out_ = rpy_matrix(0, 0, 20) @ in_
        print(out_)
        x_, y_, z_ = out_.T
        cv2.circle(img, (100 + int(x_), 100 + int(y_)), 3, (0, 255, 0), 2)

    cv2.imshow("e", img)
    while cv2.waitKey(5) != 113:
        pass
