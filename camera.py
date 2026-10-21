from camera_.CameraParams_header import *
from camera_.MvCameraControl_class import *
from camera_.MvErrorDefine_const import *


class Camera:
    def __init__(self, n):
        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()
        deviceList = MV_CC_DEVICE_INFO_LIST()
        MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)
        stDeviceList = cast(deviceList.pDeviceInfo[int(n)], POINTER(MV_CC_DEVICE_INFO)).contents
        self.obj_cam = MvCamera()
        self.obj_cam.MV_CC_CreateHandle(stDeviceList)
        self.obj_cam.MV_CC_OpenDevice()
        self.obj_cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        self.obj_cam.MV_CC_SetImageNodeNum(2)
        self.obj_cam.MV_CC_StartGrabbing()

        stPayloadSize = MVCC_INTVALUE_EX()
        NeedBufSize = 5120**2  # int(stPayloadSize.nCurValue)
        self.buf_grab_image = (NeedBufSize * ctypes.c_ubyte)()
        self.buf_grab_image_size = NeedBufSize
        ret_temp = self.obj_cam.MV_CC_GetIntValueEx("PayloadSize", stPayloadSize)
        if ret_temp != MV_OK:
            return
        self.obj_cam.MV_CC_SetFloatValue("ExposureTime", float(2000))
        self.obj_cam.MV_CC_SetFloatValue("ExposureTime", float(300))

    def grab(self):
        self.obj_cam.MV_CC_GetOneFrameTimeout(self.buf_grab_image, self.buf_grab_image_size, self.stFrameInfo)
