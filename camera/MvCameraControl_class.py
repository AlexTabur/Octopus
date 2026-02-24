# -- coding: utf-8 --

import ctypes
from ctypes import *

from camera.CameraParams_const import *

dllname = "MvCameraControl.dll"
if "winmode" in ctypes.WinDLL.__init__.__code__.co_varnames:
    MvCamCtrldll = WinDLL(dllname, winmode=0)
else:
    MvCamCtrldll = WinDLL(dllname)


def ToHexStr(num):
    if num < 0:
        num = num + 2 ** 32
    return hex(num)
class _MV_PY_OBJECT_(Structure):
    pass


_MV_PY_OBJECT_._fields_ = [
    ('PyObject', py_object),
]
MV_PY_OBJECT = _MV_PY_OBJECT_


class MvCamera():

    def __init__(self):
        self._handle = c_void_p()  # 记录当前连接设备的句柄
        self.handle = pointer(self._handle)  # 创建句柄指针

    #####设备的基本指令和操作#####
    # Get SDK Version
    @staticmethod
    def MV_CC_GetSDKVersion():
        MvCamCtrldll.MV_CC_GetSDKVersion.restype = c_uint
        # C原型：unsigned int __stdcall MV_CC_GetSDKVersion();
        return MvCamCtrldll.MV_CC_GetSDKVersion()

    # Get supported Transport Layer
    @staticmethod
    def MV_CC_EnumerateTls():
        MvCamCtrldll.MV_CC_EnumerateTls.restype = c_uint
        # C原型：int __stdcall MV_CC_EnumerateTls();
        return MvCamCtrldll.MV_CC_EnumerateTls()

    # Enumerate Device
    @staticmethod
    def MV_CC_EnumDevices(nTLayerType, stDevList):
        MvCamCtrldll.MV_CC_EnumDevices.argtype = (c_uint, c_void_p)
        MvCamCtrldll.MV_CC_EnumDevices.restype = c_uint
        # C原型:int __stdcall MV_CC_EnumDevices(unsigned int nTLayerType, MV_CC_DEVICE_INFO_LIST* pstDevList)
        # ret =
        # if ret != 0:
        #     print("enum devices fail! ret[0x%x]" % ret)
        #     
        return MvCamCtrldll.MV_CC_EnumDevices(c_uint(nTLayerType), byref(stDevList))

    # Enumerate device according to manufacture name
    @staticmethod
    def MV_CC_EnumDevicesEx(nTLayerType, stDevList, strManufacturerName):
        MvCamCtrldll.MV_CC_EnumDevicesEx.argtype = (c_uint, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_EnumDevicesEx.restype = c_uint
        # C原型:int __stdcall MV_CC_EnumDevicesEx(IN unsigned int nTLayerType, IN OUT MV_CC_DEVICE_INFO_LIST* pstDevList, IN const char* strManufacturerName);
        return MvCamCtrldll.MV_CC_EnumDevicesEx(c_uint(nTLayerType), byref(stDevList),
                                                strManufacturerName.encode('ascii'))

    # Enumerate device according to the specified ordering
    @staticmethod
    def MV_CC_EnumDevicesEx2(nTLayerType, stDevList, strManufacturerName, enSortMethod):
        MvCamCtrldll.MV_CC_EnumDevicesEx2.argtype = (c_uint, c_void_p, c_void_p, c_uint)
        MvCamCtrldll.MV_CC_EnumDevicesEx2.restype = c_uint
        # C原型:int __stdcall MV_CC_EnumDevicesEx2(IN unsigned int nTLayerType, IN OUT MV_CC_DEVICE_INFO_LIST* pstDevList, IN const char* strManufacturerName, IN MV_SORT_METHOD enSortMethod);
        return MvCamCtrldll.MV_CC_EnumDevicesEx2(c_uint(nTLayerType), byref(stDevList),
                                                 strManufacturerName.encode('ascii'), c_uint(enSortMethod))

    # Is the device accessible
    @staticmethod
    def MV_CC_IsDeviceAccessible(stDevInfo, nAccessMode):
        MvCamCtrldll.MV_CC_IsDeviceAccessible.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_CC_IsDeviceAccessible.restype = c_uint
        # C原型：bool __stdcall MV_CC_IsDeviceAccessible(IN MV_CC_DEVICE_INFO* pstDevInfo, IN unsigned int nAccessMode);
        return MvCamCtrldll.MV_CC_IsDeviceAccessible(byref(stDevInfo), nAccessMode)

    #  Set SDK log path
    def MV_CC_SetSDKLogPath(self, SDKLogPath):
        MvCamCtrldll.MV_CC_SetSDKLogPath.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_SetSDKLogPath.restype = c_uint
        # C原型:int MV_CC_SetSDKLogPath(IN const char * strSDKLogPath);
        return MvCamCtrldll.MV_CC_SetSDKLogPath(byref(SDKLogPath))

    # Create Device Handle
    def MV_CC_CreateHandle(self, stDevInfo):
        MvCamCtrldll.MV_CC_DestroyHandle.argtype = c_void_p
        MvCamCtrldll.MV_CC_DestroyHandle.restype = c_uint
        MvCamCtrldll.MV_CC_DestroyHandle(self.handle)

        MvCamCtrldll.MV_CC_CreateHandle.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_CreateHandle.restype = c_uint
        ret = MvCamCtrldll.MV_CC_CreateHandle(byref(self.handle), byref(stDevInfo))
        if ret != 0:
            print("create handle fail! ret[0x%x]" % ret)
            
        # C原型:int MV_CC_CreateHandle(void ** handle, MV_CC_DEVICE_INFO* pstDevInfo)
        return ret

    # Create Device Handle without log
    def MV_CC_CreateHandleWithoutLog(self, stDevInfo):
        MvCamCtrldll.MV_CC_DestroyHandle.argtype = c_void_p
        MvCamCtrldll.MV_CC_DestroyHandle.restype = c_uint
        MvCamCtrldll.MV_CC_DestroyHandle(self.handle)

        MvCamCtrldll.MV_CC_CreateHandleWithoutLog.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_CreateHandleWithoutLog.restype = c_uint
        # C原型:int MV_CC_CreateHandleWithoutLog(void ** handle, MV_CC_DEVICE_INFO* pstDevInfo)
        return MvCamCtrldll.MV_CC_CreateHandleWithoutLog(byref(self.handle), byref(stDevInfo))

    # Destroy Device Handle
    def MV_CC_DestroyHandle(self):
        MvCamCtrldll.MV_CC_DestroyHandle.argtype = c_void_p
        MvCamCtrldll.MV_CC_DestroyHandle.restype = c_uint
        ret = MvCamCtrldll.MV_CC_DestroyHandle(self.handle)
        if ret != 0:
            print("destroy handle fail! ret[0x%x]" % ret)
            
        return ret

    # Open Device
    def MV_CC_OpenDevice(self, nAccessMode=MV_ACCESS_Exclusive, nSwitchoverKey=0):
        MvCamCtrldll.MV_CC_OpenDevice.argtype = (c_void_p, c_uint32, c_uint16)
        MvCamCtrldll.MV_CC_OpenDevice.restype = c_uint
        # C原型:int MV_CC_OpenDevice(void* handle, unsigned int nAccessMode, unsigned short nSwitchoverKey)
        ret = MvCamCtrldll.MV_CC_OpenDevice(self.handle, nAccessMode, nSwitchoverKey)
        if ret != 0:
            print("open device fail! ret[0x%x]" % ret)
            
        return ret

    # Close Device
    def MV_CC_CloseDevice(self):
        MvCamCtrldll.MV_CC_CloseDevice.argtype = c_void_p
        MvCamCtrldll.MV_CC_CloseDevice.restype = c_uint
        ret = MvCamCtrldll.MV_CC_CloseDevice(self.handle)
        if ret != 0:
            print("close deivce fail! ret[0x%x]" % ret)
            
        return ret

    # Is The Device Connected
    def MV_CC_IsDeviceConnected(self):
        MvCamCtrldll.MV_CC_IsDeviceConnected.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_IsDeviceConnected.restype = c_bool
        # C原型：bool __stdcall MV_CC_IsDeviceConnected(IN void* handle);
        return MvCamCtrldll.MV_CC_IsDeviceConnected(self.handle)

    # Register the image callback function
    def MV_CC_RegisterImageCallBackEx(self, CallBackFun, pUser):
        MvCamCtrldll.MV_CC_RegisterImageCallBackEx.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_RegisterImageCallBackEx.restype = c_uint
        # C原型:int MV_CC_RegisterImageCallBackEx(void* handle, void(* cbOutput)(unsigned char * pData, MV_FRAME_OUT_INFO_EX* pFrameInfo, void* pUser),void* pUser);
        return MvCamCtrldll.MV_CC_RegisterImageCallBackEx(self.handle, CallBackFun, pUser)

    # Register the image callback function
    def MV_CC_RegisterImageCallBackForRGB(self, CallBackFun, pUser):
        MvCamCtrldll.MV_CC_RegisterImageCallBackForRGB.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_RegisterImageCallBackForRGB.restype = c_uint
        # C原型:int MV_CC_RegisterImageCallBackForRGB(void* handle, void(* cbOutput)(unsigned char * pData, MV_FRAME_OUT_INFO_EX* pFrameInfo, void* pUser),void* pUser);
        return MvCamCtrldll.MV_CC_RegisterImageCallBackForRGB(self.handle, CallBackFun, pUser)

    # Register the image callback function
    def MV_CC_RegisterImageCallBackForBGR(self, CallBackFun, pUser):
        MvCamCtrldll.MV_CC_RegisterImageCallBackForBGR.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_RegisterImageCallBackForBGR.restype = c_uint
        # C原型:int MV_CC_RegisterImageCallBackForBGR(void* handle, void(* cbOutput)(unsigned char * pData, MV_FRAME_OUT_INFO_EX* pFrameInfo, void* pUser),void* pUser);
        return MvCamCtrldll.MV_CC_RegisterImageCallBackForBGR(self.handle, CallBackFun, pUser)

    # Start Grabbing
    def MV_CC_StartGrabbing(self):
        MvCamCtrldll.MV_CC_StartGrabbing.argtype = c_void_p
        MvCamCtrldll.MV_CC_StartGrabbing.restype = c_uint
        ret = MvCamCtrldll.MV_CC_StartGrabbing(self.handle)
        if ret != 0:
            print("failed to grab image ret[0x%x]" % ret)
            
        return ret

    # Stop Grabbing
    def MV_CC_StopGrabbing(self):
        MvCamCtrldll.MV_CC_StopGrabbing.argtype = c_void_p
        MvCamCtrldll.MV_CC_StopGrabbing.restype = c_uint
        ret = MvCamCtrldll.MV_CC_StopGrabbing(self.handle)
        if ret != 0:
            print("stop grabbing fail! ret[0x%x]" % ret)
            
        return ret

    # Get one frame of RGB data, this function is using query to get data query whether the internal cache has data, get data if there has, return error code if no data
    def MV_CC_GetImageForRGB(self, pData, nDataSize, stFrameInfo, nMsec):
        MvCamCtrldll.MV_CC_GetImageForRGB.argtype = (c_void_p, c_void_p, c_uint, c_void_p, c_uint)
        MvCamCtrldll.MV_CC_GetImageForRGB.restype = c_uint
        # C原型:int MV_CC_GetImageForRGB(IN void* handle, IN OUT unsigned char * pData , IN unsigned int nDataSize, IN OUT MV_FRAME_OUT_INFO_EX* pstFrameInfo, int nMsec);
        return MvCamCtrldll.MV_CC_GetImageForRGB(self.handle, pData, nDataSize, byref(stFrameInfo), nMsec)

    # Get one frame of BGR data, this function is using query to get data query whether the internal cache has data, get data if there has, return error code if no data
    def MV_CC_GetImageForBGR(self, pData, nDataSize, stFrameInfo, nMsec):
        MvCamCtrldll.MV_CC_GetImageForBGR.argtype = (c_void_p, c_void_p, c_uint, c_void_p, c_uint)
        MvCamCtrldll.MV_CC_GetImageForBGR.restype = c_uint
        # C原型:int MV_CC_GetImageForBGR(IN void* handle, IN OUT unsigned char * pData , IN unsigned int nDataSize, IN OUT MV_FRAME_OUT_INFO_EX* pstFrameInfo, int nMsec);
        return MvCamCtrldll.MV_CC_GetImageForBGR(self.handle, pData, nDataSize, byref(stFrameInfo), nMsec)

    # Get a frame of an image using an internal cache(Cannot be used together with the interface of MV_CC_Display)
    def MV_CC_GetImageBuffer(self, stFrame, nMsec):
        MvCamCtrldll.MV_CC_GetImageBuffer.argtype = (c_void_p, c_void_p, c_uint)
        MvCamCtrldll.MV_CC_GetImageBuffer.restype = c_uint
        # C原型:int MV_CC_GetImageBuffer(IN void* handle, OUT MV_FRAME_OUT* pstFrame, IN unsigned int nMsec);
        return MvCamCtrldll.MV_CC_GetImageBuffer(self.handle, byref(stFrame), nMsec)

    # Get a frame of an image using an internal cache(Cannot be used together with the interface of MV_CC_Display)
    def MV_CC_FreeImageBuffer(self, stFrame):
        MvCamCtrldll.MV_CC_FreeImageBuffer.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FreeImageBuffer.restype = c_uint
        # C原型:int MV_CC_FreeImageBuffer(IN void* handle, IN MV_FRAME_OUT* pstFrame);
        return MvCamCtrldll.MV_CC_FreeImageBuffer(self.handle, byref(stFrame))

    # Timeout mechanism is used to get image, and the SDK waits inside until the data is returned
    def MV_CC_GetOneFrameTimeout(self, pData, nDataSize, stFrameInfo, nMsec=1000):
        MvCamCtrldll.MV_CC_GetOneFrameTimeout.argtype = (c_void_p, c_void_p, c_uint, c_void_p, c_uint)
        MvCamCtrldll.MV_CC_GetOneFrameTimeout.restype = c_uint
        # C原型:int MV_CC_GetOneFrameTimeout(void* handle, unsigned char * pData , unsigned int nDataSize, MV_FRAME_OUT_INFO_EX* pFrameInfo, unsigned int nMsec)
        return MvCamCtrldll.MV_CC_GetOneFrameTimeout(self.handle, pData, nDataSize, byref(stFrameInfo), nMsec)

    # if Image buffers has retrieved the data，Clear them
    def MV_CC_ClearImageBuffer(self):
        MvCamCtrldll.MV_CC_ClearImageBuffer.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_ClearImageBuffer.restype = c_uint
        # C原型:int MV_CC_ClearImageBuffer(IN void* handle);
        return MvCamCtrldll.MV_CC_ClearImageBuffer(self.handle)

    #  Get the number of valid images in the current image buffer
    def MV_CC_GetValidImageNum(self, nValidImageNum):
        MvCamCtrldll.MV_CC_GetValidImageNum.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetValidImageNum.restype = c_uint
        # C原型:int MV_CC_GetValidImageNum(IN void* handle, OUT unsigned int *pnValidImageNum);
        return MvCamCtrldll.MV_CC_GetValidImageNum(self.handle, c_uint(nValidImageNum))

    # Get a frame of an image using an internal cache(Cannot be used together with the interface of MV_CC_Display)
    def MV_CC_DisplayOneFrame(self, stDisplayInfo):
        MvCamCtrldll.MV_CC_DisplayOneFrame.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_DisplayOneFrame.restype = c_uint
        # C原型:int MV_CC_DisplayOneFrame(IN void* handle, IN MV_DISPLAY_FRAME_INFO* pstDisplayInfo);
        return MvCamCtrldll.MV_CC_DisplayOneFrame(self.handle, byref(stDisplayInfo))

    # Get a frame of an image using an internal cache(Cannot be used together with the interface of MV_CC_Display)
    def MV_CC_DisplayOneFrameEx(self, hWnd, stDisplayInfo):
        MvCamCtrldll.MV_CC_DisplayOneFrameEx.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_DisplayOneFrameEx.restype = c_uint
        # C原型:int MV_CC_DisplayOneFrameEx(IN void* handle, IN void* hWnd, IN MV_DISPLAY_FRAME_INFO_EX* pstDisplayInfo);
        return MvCamCtrldll.MV_CC_DisplayOneFrameEx(self.handle, hWnd, byref(stDisplayInfo))

    # Set the number of the internal image cache nodes in SDK, Greater than or equal to 1, to be called before the capture
    def MV_CC_SetImageNodeNum(self, nNum):
        MvCamCtrldll.MV_CC_SetImageNodeNum.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_CC_SetImageNodeNum.restype = c_uint
        # C原型:int MV_CC_SetImageNodeNum(IN void* handle, unsigned int nNum);
        ret = MvCamCtrldll.MV_CC_SetImageNodeNum(self.handle, c_uint(nNum))
        if ret != 0:
            print("setImageModeNum failed ret[0x%x]" % ret)
            
        return ret

    # Set Grab Strategy
    def MV_CC_SetGrabStrategy(self, enGrabStrategy):
        MvCamCtrldll.MV_CC_SetGrabStrategy.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_CC_SetGrabStrategy.restype = c_uint
        # C原型:int MV_CC_SetGrabStrategy(IN void* handle, IN MV_GRAB_STRATEGY enGrabStrategy);
        return MvCamCtrldll.MV_CC_SetGrabStrategy(self.handle, c_uint(enGrabStrategy))

    # Set The Size of Output Queue(Only work under the strategy of MV_GrabStrategy_LatestImages，rang：1-ImageNodeNum)
    def MV_CC_SetOutputQueueSize(self, nOutputQueueSize):
        MvCamCtrldll.MV_CC_SetOutputQueueSize.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_CC_SetOutputQueueSize.restype = c_uint
        # C原型:int MV_CC_SetOutputQueueSize(IN void* handle, IN unsigned int nOutputQueueSize);
        return MvCamCtrldll.MV_CC_SetOutputQueueSize(self.handle, nOutputQueueSize)

    # Get device information
    def MV_CC_GetDeviceInfo(self, stDevInfo):
        MvCamCtrldll.MV_CC_GetDeviceInfo.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetDeviceInfo.restype = c_uint
        # C原型:int MV_CC_GetDeviceInfo(IN void * handle, IN OUT MV_CC_DEVICE_INFO* pstDevInfo);
        return MvCamCtrldll.MV_CC_GetDeviceInfo(self.handle, byref(stDevInfo))

    # Get various type of information
    def MV_CC_GetAllMatchInfo(self, stInfo):
        MvCamCtrldll.MV_CC_GetAllMatchInfo.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetAllMatchInfo.restype = c_uint
        # C原型:int MV_CC_GetAllMatchInfo(IN void* handle, IN OUT MV_ALL_MATCH_INFO* pstInfo);
        return MvCamCtrldll.MV_CC_GetAllMatchInfo(self.handle, byref(stInfo))

    # Get Integer value
    def MV_CC_GetIntValueEx(self, strKey, stIntValue):
        MvCamCtrldll.MV_CC_GetIntValueEx.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetIntValueEx.restype = c_uint
        # C原型:int MV_CC_GetIntValueEx(IN void* handle,IN const char* strKey,OUT MVCC_INTVALUE_EX *pstIntValue);
        return MvCamCtrldll.MV_CC_GetIntValueEx(self.handle, strKey.encode('ascii'), byref(stIntValue))

    # Set Integer value
    def MV_CC_SetIntValueEx(self, strKey, nValue):
        MvCamCtrldll.MV_CC_SetIntValueEx.argtype = (c_void_p, c_void_p, c_uint)
        MvCamCtrldll.MV_CC_SetIntValueEx.restype = c_uint
        # C原型:int MV_CC_SetIntValueEx(IN void* handle,IN const char* strKey,IN int64_t nValue);
        return MvCamCtrldll.MV_CC_SetIntValueEx(self.handle, strKey.encode('ascii'), c_uint(nValue))

    # Get Integer value
    def MV_CC_GetIntValue(self, strKey, stIntValue):
        MvCamCtrldll.MV_CC_GetIntValue.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetIntValue.restype = c_uint
        # C原型:int MV_CC_GetIntValue(void* handle,char* strKey,MVCC_INTVALUE *pIntValue)
        return MvCamCtrldll.MV_CC_GetIntValue(self.handle, strKey.encode('ascii'), byref(stIntValue))

    # Set Integer value
    def MV_CC_SetIntValue(self, strKey, nValue):
        MvCamCtrldll.MV_CC_SetIntValue.argtype = (c_void_p, c_void_p, c_uint32)
        MvCamCtrldll.MV_CC_SetIntValue.restype = c_uint
        # C原型:int MV_CC_SetIntValue(void* handle, char* strKey, unsigned int nValue)
        return MvCamCtrldll.MV_CC_SetIntValue(self.handle, strKey.encode('ascii'), c_uint32(nValue))

    # Get Enum value
    def MV_CC_GetEnumValue(self, strKey, stEnumValue):
        MvCamCtrldll.MV_CC_GetEnumValue.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetEnumValue.restype = c_uint
        # C原型:int MV_CC_GetEnumValue(void* handle,char* strKey,MVCC_ENUMVALUE *pEnumValue)
        return MvCamCtrldll.MV_CC_GetEnumValue(self.handle, strKey.encode('ascii'), byref(stEnumValue))

    # Set Enum value
    def MV_CC_SetEnumValue(self, strKey, nValue):
        MvCamCtrldll.MV_CC_SetEnumValue.argtype = (c_void_p, c_void_p, c_uint32)
        MvCamCtrldll.MV_CC_SetEnumValue.restype = c_uint
        # C原型:int MV_CC_SetEnumValue(void* handle,char* strKey,unsigned int nValue)
        ret = MvCamCtrldll.MV_CC_SetEnumValue(self.handle, strKey.encode('ascii'), c_uint32(nValue))
        if ret != 0:
            print("set trigger mode fail! ret[0x%x]" % ret)
            
        return ret

    #  Get the symbolic of the specified value of the Enum type node
    def MV_CC_GetEnumEntrySymbolic(self, strKey, stEnumEntry):
        MvCamCtrldll.MV_CC_GetEnumEntrySymbolic.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetEnumEntrySymbolic.restype = c_uint
        # C原型:int MV_CC_GetEnumEntrySymbolic(IN void* handle,IN const char* strKey,IN OUT MVCC_ENUMENTRY* pstEnumEntry);
        return MvCamCtrldll.MV_CC_GetEnumEntrySymbolic(self.handle, strKey.encode('ascii'), byref(stEnumEntry))

    # Set Enum value
    def MV_CC_SetEnumValueByString(self, strKey, sValue):
        MvCamCtrldll.MV_CC_SetEnumValueByString.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SetEnumValueByString.restype = c_uint
        # C原型:int MV_CC_SetEnumValueByString(void* handle,char* strKey,char* sValue)
        ret = MvCamCtrldll.MV_CC_SetEnumValueByString(self.handle, strKey.encode('ascii'), sValue.encode('ascii'))
        if ret != 0:
            print("warning: set trigger mode off fail! ret[0x%x]" % ret)
        return ret

    # Get Float value
    def MV_CC_GetFloatValue(self, strKey, stFloatValue):
        MvCamCtrldll.MV_CC_GetFloatValue.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetFloatValue.restype = c_uint
        # C原型:int MV_CC_GetFloatValue(void* handle,char* strKey,MVCC_FLOATVALUE *pFloatValue)
        return MvCamCtrldll.MV_CC_GetFloatValue(self.handle, strKey.encode('ascii'), byref(stFloatValue))

    # Set float value
    def MV_CC_SetFloatValue(self, strKey, fValue):
        MvCamCtrldll.MV_CC_SetFloatValue.argtype = (c_void_p, c_void_p, c_float)
        MvCamCtrldll.MV_CC_SetFloatValue.restype = c_uint
        # C原型:int MV_CC_SetFloatValue(void* handle,char* strKey,float fValue)
        return MvCamCtrldll.MV_CC_SetFloatValue(self.handle, strKey.encode('ascii'), c_float(fValue))

    # Get Boolean value
    def MV_CC_GetBoolValue(self, strKey, BoolValue):
        MvCamCtrldll.MV_CC_GetBoolValue.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetBoolValue.restype = c_uint
        # C原型:int MV_CC_GetBoolValue(void* handle,char* strKey,bool *pBoolValue)
        ret = MvCamCtrldll.MV_CC_GetBoolValue(self.handle, strKey.encode('ascii'), byref(BoolValue))
        
        if ret != 0:
            print("get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)
        return ret

    # Set Boolean value
    def MV_CC_SetBoolValue(self, strKey, bValue):
        MvCamCtrldll.MV_CC_SetBoolValue.argtype = (c_void_p, c_void_p, c_bool)
        MvCamCtrldll.MV_CC_SetBoolValue.restype = c_uint
        # C原型:int MV_CC_SetBoolValue(void* handle,char* strKey,bool bValue)
        return MvCamCtrldll.MV_CC_SetBoolValue(self.handle, strKey.encode('ascii'), bValue)

    # Get String value
    def MV_CC_GetStringValue(self, strKey, StringValue):
        MvCamCtrldll.MV_CC_GetStringValue.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetStringValue.restype = c_uint
        # C原型:int MV_CC_GetStringValue(void* handle,char* strKey,MVCC_STRINGVALUE *pStringValue)
        return MvCamCtrldll.MV_CC_GetStringValue(self.handle, strKey.encode('ascii'), byref(StringValue))

    # Set String value
    def MV_CC_SetStringValue(self, strKey, sValue):
        MvCamCtrldll.MV_CC_SetStringValue.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SetStringValue.restype = c_uint
        # C原型:int MV_CC_SetStringValue(void* handle,char* strKey,char * sValue)
        return MvCamCtrldll.MV_CC_SetStringValue(self.handle, strKey.encode('ascii'), sValue.encode('ascii'))

    # Send Command
    def MV_CC_SetCommandValue(self, strKey):
        MvCamCtrldll.MV_CC_SetCommandValue.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SetCommandValue.restype = c_uint
        # C原型:int MV_CC_SetCommandValue(void* handle,char* strKey)
        return MvCamCtrldll.MV_CC_SetCommandValue(self.handle, strKey.encode('ascii'))

    # Invalidate GenICam Nodes
    def MV_CC_InvalidateNodes(self):
        MvCamCtrldll.MV_CC_InvalidateNodes.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_InvalidateNodes.restype = c_uint
        # C原型:int MV_CC_InvalidateNodes(IN void* handle);
        return MvCamCtrldll.MV_CC_InvalidateNodes(self.handle)

    #  Device Local Upgrade
    def MV_CC_LocalUpgrade(self, strFilePathName):
        MvCamCtrldll.MV_CC_LocalUpgrade.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_LocalUpgrade.restype = c_uint
        # C原型:int MV_CC_LocalUpgrade(IN void* handle, const void* strFilePathName);
        return MvCamCtrldll.MV_CC_LocalUpgrade(self.handle, byref(strFilePathName))

    #  Get Upgrade Progress
    def MV_CC_GetUpgradeProcess(self, nProcess):
        MvCamCtrldll.MV_CC_GetUpgradeProcess.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetUpgradeProcess.restype = c_uint
        # C原型:int MV_CC_GetUpgradeProcess(IN void* handle, unsigned int* pnProcess);
        return MvCamCtrldll.MV_CC_GetUpgradeProcess(self.handle, byref(nProcess))

    #####寄存器读写 和异常、事件回调#####
    # Read Memory
    def MV_CC_ReadMemory(self, pBuffer, nAddress, nLength):
        MvCamCtrldll.MV_CC_ReadMemory.argtype = (c_void_p, c_void_p, c_uint, c_uint)
        MvCamCtrldll.MV_CC_ReadMemory.restype = c_uint
        # C原型:int MV_CC_ReadMemory(IN void* handle , void *pBuffer, int64_t nAddress, int64_t nLength);
        return MvCamCtrldll.MV_CC_ReadMemory(self.handle, pBuffer, c_uint(nAddress), nLength)

    # Write Memory
    def MV_CC_WriteMemory(self, pBuffer, nAddress, nLength):
        MvCamCtrldll.MV_CC_WriteMemory.argtype = (c_void_p, c_void_p, c_uint, c_uint)
        MvCamCtrldll.MV_CC_WriteMemory.restype = c_uint
        # C原型:int MV_CC_WriteMemory(IN void* handle, const void *pBuffer, int64_t nAddress, int64_t nLength);
        return MvCamCtrldll.MV_CC_WriteMemory(self.handle, pBuffer, c_uint(nAddress), nLength)

    # Register Exception Message CallBack, call after open device
    def MV_CC_RegisterExceptionCallBack(self, ExceptionCallBackFun, pUser):
        MvCamCtrldll.MV_CC_RegisterExceptionCallBack.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_RegisterExceptionCallBack.restype = c_uint
        # C原型:int MV_CC_RegisterExceptionCallBack(void* handle, void(* cbException)(unsigned int nMsgType, void* pUser),void* pUser)
        return MvCamCtrldll.MV_CC_RegisterExceptionCallBack(self.handle, ExceptionCallBackFun, pUser)

    # Register event callback, which is called after the device is opened
    def MV_CC_RegisterAllEventCallBack(self, EventCallBackFun, pUser):
        MvCamCtrldll.MV_CC_RegisterAllEventCallBack.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_RegisterAllEventCallBack.restype = c_uint
        # C原型:int MV_CC_RegisterAllEventCallBack(void* handle, void(__stdcall* cbEvent)(MV_EVENT_OUT_INFO * pEventInfo, void* pUser), void* pUser);
        return MvCamCtrldll.MV_CC_RegisterAllEventCallBack(self.handle, EventCallBackFun, pUser)

    # Register single event callback, which is called after the device is opened
    def MV_CC_RegisterEventCallBackEx(self, pEventName, EventCallBackFun, pUser):
        MvCamCtrldll.MV_CC_RegisterEventCallBackEx.argtype = (c_void_p, c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_RegisterEventCallBackEx.restype = c_uint
        # C原型:int MV_CC_RegisterEventCallBackEx(void* handle, char* pEventName,void(* cbEvent)(MV_EVENT_OUT_INFO * pEventInfo, void* pUser),void* pUser)
        return MvCamCtrldll.MV_CC_RegisterEventCallBackEx(self.handle, pEventName.encode('ascii'), EventCallBackFun,
                                                          pUser)

    # ch:设置枚举超时时间，仅支持GigE协议，范围 0-UINT_MAX | en：Set enumerate device timeout,only GigE support
    # 在调用MV_CC_EnumDevices等枚举接口前使用该接口，可设置枚举GIGE设备的网卡最大超时时间（默认100ms）,可以减少最大超时时间，来加快枚举GIGE设备的速度
    # Before calling enum device interfaces,call MV_GIGE_SetEnumDevTimeout to set max timeout,can reduce the maximum timeout to speed up the enumeration of GigE devices
    def MV_GIGE_SetEnumDevTimeout(self, nMilTimeout):
        MvCamCtrldll.MV_GIGE_SetEnumDevTimeout.argtype = (c_uint)
        MvCamCtrldll.MV_GIGE_SetEnumDevTimeout.restype = c_uint
        # C原型:int MV_GIGE_SetEnumDevTimeout(IN unsigned int nMilTimeout)
        return MvCamCtrldll.MV_GIGE_SetEnumDevTimeout(c_uint(nMilTimeout))

    #####GigEVision 设备独有的接口#####
    # ch:强制修改IP | en：Force IP
    def MV_GIGE_ForceIpEx(self, nIP, nSubNetMask, nDefaultGateWay):
        MvCamCtrldll.MV_GIGE_ForceIpEx.argtype = (c_void_p, c_uint, c_uint, c_uint)
        MvCamCtrldll.MV_GIGE_ForceIpEx.restype = c_uint
        # C原型:int MV_GIGE_ForceIpEx(void* handle, unsigned int nIP, unsigned int nSubNetMask, unsigned int nDefaultGateWay)
        return MvCamCtrldll.MV_GIGE_ForceIpEx(self.handle, c_uint(nIP), c_uint(nSubNetMask), c_uint(nDefaultGateWay))

    # IP configuration method
    def MV_GIGE_SetIpConfig(self, nType):
        MvCamCtrldll.MV_GIGE_SetIpConfig.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_GIGE_SetIpConfig.restype = c_uint
        # C原型:int MV_GIGE_SetIpConfig(void* handle, unsigned int nType)
        return MvCamCtrldll.MV_GIGE_SetIpConfig(self.handle, c_uint(nType))

    # ch:设置仅使用某种模式,type: MV_NET_TRANS_x，不设置时，默认优先使用driver | en: Set to use only one mode,type: MV_NET_TRANS_x. When do not set, priority is to use driver by default
    def MV_GIGE_SetNetTransMode(self, nType):
        MvCamCtrldll.MV_GIGE_SetNetTransMode.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_GIGE_SetNetTransMode.restype = c_uint
        # C原型:int MV_GIGE_SetNetTransMode(IN void* handle, unsigned int nType);
        return MvCamCtrldll.MV_GIGE_SetNetTransMode(self.handle, c_uint(nType))

    # Get net transmission information
    def MV_GIGE_GetNetTransInfo(self, pstInfo):
        MvCamCtrldll.MV_GIGE_GetNetTransInfo.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_GetNetTransInfo.restype = c_uint
        # C原型:int MV_GIGE_GetNetTransInfo(IN void* handle, MV_NETTRANS_INFO* pstInfo);
        return MvCamCtrldll.MV_GIGE_GetNetTransInfo(self.handle, byref(pstInfo))

    #  Setting the ACK mode of devices Discovery
    def MV_GIGE_SetDiscoveryMode(self, nMode):
        MvCamCtrldll.MV_GIGE_SetDiscoveryMode.argtype = (c_uint)
        MvCamCtrldll.MV_GIGE_SetDiscoveryMode.restype = c_uint
        # C原型:int MV_GIGE_SetDiscoveryMode(unsigned int nMode);
        return MvCamCtrldll.MV_GIGE_SetDiscoveryMode(c_uint(nMode))

    # ch:设置GVSP取流超时时间| en: Set GVSP streaming timeout
    def MV_GIGE_SetGvspTimeout(self, nMillisec):
        MvCamCtrldll.MV_GIGE_SetGvspTimeout.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_GIGE_SetGvspTimeout.restype = c_uint
        # C原型:int MV_GIGE_SetGvspTimeout(void* handle, unsigned int nMillisec);
        return MvCamCtrldll.MV_GIGE_SetGvspTimeout(self.handle, c_uint(nMillisec))

    # Get GVSP streaming timeout
    def MV_GIGE_GetGvspTimeout(self, pnMillisec):
        MvCamCtrldll.MV_GIGE_GetGvspTimeout.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_GetGvspTimeout.restype = c_uint
        # C原型:int MV_GIGE_GetGvspTimeout(IN void* handle, unsigned int* pnMillisec);
        return MvCamCtrldll.MV_GIGE_GetGvspTimeout(self.handle, byref(pnMillisec))

    # ch:设置GVCP命令超时时间| en: Set GVCP cammand timeout
    def MV_GIGE_SetGvcpTimeout(self, nMillisec):
        MvCamCtrldll.MV_GIGE_SetGvcpTimeout.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_GIGE_SetGvcpTimeout.restype = c_uint
        # C原型:int MV_GIGE_SetGvcpTimeout(void* handle, unsigned int nMillisec);
        return MvCamCtrldll.MV_GIGE_SetGvcpTimeout(self.handle, c_uint(nMillisec))

    # Get GVCP cammand timeout
    def MV_GIGE_GetGvcpTimeout(self, pnMillisec):
        MvCamCtrldll.MV_GIGE_GetGvcpTimeout.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_GetGvcpTimeout.restype = c_uint
        # C原型:int MV_GIGE_GetGvcpTimeout(IN void* handle, unsigned int* pnMillisec);
        return MvCamCtrldll.MV_GIGE_GetGvcpTimeout(self.handle, byref(pnMillisec))

    # ch:设置重传GVCP命令次数| en: Set the number of retry GVCP cammand
    def MV_GIGE_SetRetryGvcpTimes(self, nRetryGvcpTimes):
        MvCamCtrldll.MV_GIGE_SetRetryGvcpTimes.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_GIGE_SetRetryGvcpTimes.restype = c_uint
        # C原型:int MV_GIGE_SetRetryGvcpTimes(IN void* handle, unsigned int nRetryGvcpTimes);
        return MvCamCtrldll.MV_GIGE_SetRetryGvcpTimes(self.handle, c_uint(nRetryGvcpTimes))

    # Get GVCP cammand timeout
    def MV_GIGE_GetRetryGvcpTimes(self, pnRetryGvcpTimes):
        MvCamCtrldll.MV_GIGE_GetRetryGvcpTimes.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_GetRetryGvcpTimes.restype = c_uint
        # C原型:int MV_GIGE_GetRetryGvcpTimes(IN void* handle, unsigned int* pnRetryGvcpTimes);
        return MvCamCtrldll.MV_GIGE_GetRetryGvcpTimes(self.handle, byref(pnRetryGvcpTimes))

    # Get the optimal Packet Size, Only support GigE Camera
    def MV_CC_GetOptimalPacketSize(self):
        MvCamCtrldll.MV_CC_GetOptimalPacketSize.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_GetOptimalPacketSize.restype = c_uint
        # C原型:int __stdcall MV_CC_GetOptimalPacketSize(void* handle);
        return MvCamCtrldll.MV_CC_GetOptimalPacketSize(self.handle)

    # ch:设置是否打开重发包支持，及重发包设置| en: Set whethe to enable resend, and set resend
    def MV_GIGE_SetResend(self, bEnable, nMaxResendPercent=10, nResendTimeout=50):
        MvCamCtrldll.MV_GIGE_SetResend.argtype = (c_void_p, c_uint, c_uint, c_uint)
        MvCamCtrldll.MV_GIGE_SetResend.restype = c_uint
        # C原型:int  MV_GIGE_SetResend(void* handle, unsigned int bEnable, unsigned int nMaxResendPercent = 10, unsigned int nResendTimeout = 50);
        return MvCamCtrldll.MV_GIGE_SetResend(self.handle, c_uint(bEnable), c_uint(nMaxResendPercent),
                                              c_uint(nResendTimeout))

    #  set the max resend retry times
    def MV_GIGE_SetResendMaxRetryTimes(self, nRetryTimes):
        MvCamCtrldll.MV_GIGE_SetResendMaxRetryTimes.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_GIGE_SetResendMaxRetryTimes.restype = c_uint
        # C原型:int MV_GIGE_SetResendMaxRetryTimes(void* handle, unsigned int nRetryTimes);
        return MvCamCtrldll.MV_GIGE_SetResendMaxRetryTimes(self.handle, c_uint(nRetryTimes))

    #  get the max resend retry times
    def MV_GIGE_GetResendMaxRetryTimes(self, nRetryTimes):
        MvCamCtrldll.MV_GIGE_GetResendMaxRetryTimes.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_GetResendMaxRetryTimes.restype = c_uint
        # C原型:int MV_GIGE_GetResendMaxRetryTimes(void* handle, unsigned int* pnRetryTimes);
        return MvCamCtrldll.MV_GIGE_GetResendMaxRetryTimes(self.handle, byref(nRetryTimes))

    #  set time interval between same resend requests
    def MV_GIGE_SetResendTimeInterval(self, nMillisec):
        MvCamCtrldll.MV_GIGE_SetResendTimeInterval.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_GIGE_SetResendTimeInterval.restype = c_uint
        # C原型:int MV_GIGE_SetResendTimeInterval(void* handle, unsigned int nMillisec)
        return MvCamCtrldll.MV_GIGE_SetResendTimeInterval(self.handle, c_uint(nMillisec))

    #  get time interval between same resend requests
    def MV_GIGE_GetResendTimeInterval(self, nMillisec):
        MvCamCtrldll.MV_GIGE_GetResendTimeInterval.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_GetResendTimeInterval.restype = c_uint
        # C原型:int MV_GIGE_GetResendTimeInterval(void* handle, unsigned int* pnMillisec)
        return MvCamCtrldll.MV_GIGE_GetResendTimeInterval(self.handle, byref(nMillisec))

    # ch:设置传输模式，可以为单播模式、组播模式等 |en:Set transmission type,Unicast or Multicast
    def MV_GIGE_SetTransmissionType(self, stTransmissionType):
        MvCamCtrldll.MV_GIGE_SetTransmissionType.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_SetTransmissionType.restype = c_uint
        # C原型:int MV_GIGE_SetTransmissionType(void* handle, MV_TRANSMISSION_TYPE * pstTransmissionType)
        return MvCamCtrldll.MV_GIGE_SetTransmissionType(self.handle, byref(stTransmissionType))

    # Issue Action Command
    def MV_GIGE_IssueActionCommand(self, pstActionCmdInfo, pstActionCmdResults):
        MvCamCtrldll.MV_GIGE_IssueActionCommand.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_IssueActionCommand.restype = c_uint
        # C原型:int  MV_GIGE_IssueActionCommand(IN MV_ACTION_CMD_INFO* pstActionCmdInfo, OUT MV_ACTION_CMD_RESULT_LIST* pstActionCmdResults);
        return MvCamCtrldll.MV_GIGE_IssueActionCommand(byref(pstActionCmdInfo), byref(pstActionCmdResults))

    # Get Multicast Status
    def MV_GIGE_GetMulticastStatus(self, pstDevInfo, pbStatus):
        MvCamCtrldll.MV_GIGE_GetMulticastStatus.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_GIGE_GetMulticastStatus.restype = c_uint
        # C原型:int MV_GIGE_GetMulticastStatus(IN MV_CC_DEVICE_INFO* pstDevInfo, OUT bool* pbStatus);
        return MvCamCtrldll.MV_GIGE_GetMulticastStatus(byref(pstDevInfo), byref(pbStatus))

    #####CameraLink 设备独有的接口#####
    # ch:设置设备波特率| en: Set device bauderate using one of the CL_BAUDRATE_XXXX value
    def MV_CAML_SetDeviceBauderate(self, nBaudrate):
        MvCamCtrldll.MV_CAML_SetDeviceBauderate.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_CAML_SetDeviceBauderate.restype = c_uint
        # C原型:int MV_CAML_SetDeviceBauderate(IN void* handle, unsigned int nBaudrate);
        return MvCamCtrldll.MV_CAML_SetDeviceBauderate(self.handle, c_uint(nBaudrate))

    # Returns the current device bauderate, using one of the CL_BAUDRATE_XXXX value
    def MV_CAML_GetDeviceBauderate(self, pnCurrentBaudrate):
        MvCamCtrldll.MV_CAML_GetDeviceBauderate.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CAML_GetDeviceBauderate.restype = c_uint
        # C原型:int MV_CAML_GetDeviceBauderate(IN void* handle,unsigned int* pnCurrentBaudrate);
        return MvCamCtrldll.MV_CAML_GetDeviceBauderate(self.handle, byref(pnCurrentBaudrate))

    # Returns supported bauderates of the combined device and host interface
    def MV_CAML_GetSupportBauderates(self, pnBaudrateAblity):
        MvCamCtrldll.MV_CAML_GetSupportBauderates.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CAML_GetSupportBauderates.restype = c_uint
        # C原型:int MV_CAML_GetSupportBauderates(IN void* handle,unsigned int* pnBaudrateAblity);
        return MvCamCtrldll.MV_CAML_GetSupportBauderates(self.handle, byref(pnBaudrateAblity))

    # Sets the timeout for operations on the serial port
    def MV_CAML_SetGenCPTimeOut(self, nMillisec):
        MvCamCtrldll.MV_CAML_SetGenCPTimeOut.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_CAML_SetGenCPTimeOut.restype = c_uint
        # C原型:int MV_CAML_SetGenCPTimeOut(IN void* handle, unsigned int nMillisec);
        return MvCamCtrldll.MV_CAML_SetGenCPTimeOut(self.handle, c_uint(nMillisec))

    #####U3V 设备独有的接口#####
    # Set transfer size of U3V device
    def MV_USB_SetTransferSize(self, nTransferSize):
        MvCamCtrldll.MV_USB_SetTransferSize.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_USB_SetTransferSize.restype = c_uint
        # C原型:int MV_USB_SetTransferSize(IN void* handle, unsigned int nTransferSize);
        return MvCamCtrldll.MV_USB_SetTransferSize(self.handle, c_uint(nTransferSize))

    # Get transfer size of U3V device
    def MV_USB_GetTransferSize(self, pnTransferSize):
        MvCamCtrldll.MV_USB_GetTransferSize.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_USB_GetTransferSize.restype = c_uint
        # C原型:int MV_USB_GetTransferSize(IN void* handle, unsigned int* pnTransferSize);
        return MvCamCtrldll.MV_USB_GetTransferSize(self.handle, byref(pnTransferSize))

    # Set transfer ways of U3V device
    def MV_USB_SetTransferWays(self, nTransferWays):
        MvCamCtrldll.MV_USB_SetTransferWays.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_USB_SetTransferWays.restype = c_uint
        # C原型:int MV_USB_SetTransferWays(IN void* handle, unsigned int nTransferWays);
        return MvCamCtrldll.MV_USB_SetTransferWays(self.handle, c_uint(nTransferWays))

    # Get transfer ways of U3V device
    def MV_USB_GetTransferWays(self, pnTransferWays):
        MvCamCtrldll.MV_USB_GetTransferWays.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_USB_GetTransferWays.restype = c_uint
        # C原型:int MV_USB_GetTransferWays(IN void* handle, unsigned int* pnTransferWays);
        return MvCamCtrldll.MV_USB_GetTransferWays(self.handle, byref(pnTransferWays))

    #  Register the stream exception callback, which is called after the device is opened. Only the U3V camera is supported
    def MV_USB_RegisterStreamExceptionCallBack(self, CallBackFun, pUser):
        MvCamCtrldll.MV_USB_RegisterStreamExceptionCallBack.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_USB_RegisterStreamExceptionCallBack.restype = c_uint
        # C原型:int MV_USB_RegisterStreamExceptionCallBack(void* handle, void(__stdcall* cbException)(MV_CC_STREAM_EXCEPTION_TYPE enExceptionType, void* pUser),void* pUser);
        return MvCamCtrldll.MV_USB_RegisterStreamExceptionCallBack(self.handle, CallBackFun, pUser)

    #  Set the number of U3V device event cache nodes
    def MV_USB_SetEventNodeNum(self, nEventNodeNum):
        MvCamCtrldll.MV_USB_SetEventNodeNum.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_USB_SetEventNodeNum.restype = c_uint
        # C原型:int MV_USB_SetEventNodeNum(IN void* handle, unsigned int nEventNodeNum)
        return MvCamCtrldll.MV_USB_SetEventNodeNum(self.handle, c_uint(nEventNodeNum))

    #ch:设置U3V的同步读写超时时间,范围为0 ~ UINT_MAX(最小值包含0，最大值根据操作系统位数决定) | en: Set Sync timeout
    def MV_USB_SetSyncTimeOut(self, nMills):
        MvCamCtrldll.MV_USB_SetSyncTimeOut.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_USB_SetSyncTimeOut.restype = c_uint
        # C原型:int MV_USB_SetSyncTimeOut(IN void* handle, unsigned int nMills);
        return MvCamCtrldll.MV_USB_SetSyncTimeOut(self.handle, c_uint(nMills))

    #  Get Sync timeout
    def MV_USB_GetSyncTimeOut(self, nMills):
        MvCamCtrldll.MV_USB_GetSyncTimeOut.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_USB_GetSyncTimeOut.restype = c_uint
        # C原型:int MV_USB_GetSyncTimeOut(IN void* handle, unsigned int* pnMills);
        return MvCamCtrldll.MV_USB_GetSyncTimeOut(self.handle, byref(nMills))

    #####GenTL相关接口，其它接口可以复用（部分接口不支持）#####
    # Enumerate Interfaces with GenTL
    def MV_CC_EnumInterfacesByGenTL(stIFList, strGenTLPath):
        MvCamCtrldll.MV_CC_EnumInterfacesByGenTL.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_EnumInterfacesByGenTL.restype = c_uint
        # C原型:int MV_CC_EnumInterfacesByGenTL(IN OUT MV_GENTL_IF_INFO_LIST* pstIFList, IN const char * strGenTLPath);
        return MvCamCtrldll.MV_CC_EnumInterfacesByGenTL(byref(stIFList), strGenTLPath.encode('ascii'))

    # ch:通过GenTL Interface枚举设备 | en:Enumerate Devices with GenTL interface
    def MV_CC_EnumDevicesByGenTL(stIFInfo, stDevList):
        MvCamCtrldll.MV_CC_EnumDevicesByGenTL.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_EnumDevicesByGenTL.restype = c_uint
        # C原型:int MV_CC_EnumDevicesByGenTL(IN MV_GENTL_IF_INFO* pstIFInfo, IN OUT MV_GENTL_DEV_INFO_LIST* pstDevList);
        return MvCamCtrldll.MV_CC_EnumDevicesByGenTL(stIFInfo, byref(stDevList))

    #  Unload cti library
    def MV_CC_UnloadGenTLLibrary(self, GenTLPath):
        MvCamCtrldll.MV_CC_UnloadGenTLLibrary.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_UnloadGenTLLibrary.restype = c_uint
        # C原型:int MV_CC_UnloadGenTLLibrary(IN const char * pGenTLPath);
        return MvCamCtrldll.MV_CC_UnloadGenTLLibrary(byref(GenTLPath))

    # Create Device Handle with GenTL Device Info
    def MV_CC_CreateHandleByGenTL(self, stDevInfo):
        MvCamCtrldll.MV_CC_DestroyHandle.argtype = c_void_p
        MvCamCtrldll.MV_CC_DestroyHandle.restype = c_uint
        MvCamCtrldll.MV_CC_DestroyHandle(self.handle)

        MvCamCtrldll.MV_CC_CreateHandleByGenTL.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_CreateHandleByGenTL.restype = c_uint
        # C原型:int MV_CC_CreateHandleByGenTL(OUT void ** handle, IN const MV_GENTL_DEV_INFO* pstDevInfo);
        return MvCamCtrldll.MV_CC_CreateHandleByGenTL(byref(self.handle), byref(stDevInfo))

    #####XML解析树的生成#####
    # Get camera feature tree XML
    def MV_XML_GetGenICamXML(self, pData, nDataSize, pnDataLen):
        MvCamCtrldll.MV_XML_GetGenICamXML.argtype = (c_void_p, c_void_p, c_uint, c_void_p)
        MvCamCtrldll.MV_XML_GetGenICamXML.restype = c_uint
        # C原型:int MV_XML_GetGenICamXML(IN void* handle, IN OUT unsigned char* pData, IN unsigned int nDataSize, OUT unsigned int* pnDataLen);
        return MvCamCtrldll.MV_XML_GetGenICamXML(self.handle, pData, c_uint(nDataSize), byref(pnDataLen))

    # Get Access mode of cur node
    def MV_XML_GetNodeAccessMode(self, strName, penAccessMode):
        MvCamCtrldll.MV_XML_GetNodeAccessMode.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_XML_GetNodeAccessMode.restype = c_uint
        # C原型:int MV_XML_GetNodeAccessMode(IN void* handle, IN const char * strName, OUT MV_XML_AccessMode *penAccessMode);
        return MvCamCtrldll.MV_XML_GetNodeAccessMode(self.handle, strName.encode('ascii'), byref(penAccessMode))

    # Get Interface Type of cur node
    def MV_XML_GetNodeInterfaceType(self, strName, penInterfaceType):
        MvCamCtrldll.MV_XML_GetNodeInterfaceType.argtype = (c_void_p, c_void_p, c_void_p)
        MvCamCtrldll.MV_XML_GetNodeInterfaceType.restype = c_uint
        # C原型:int MV_XML_GetNodeInterfaceType(IN void* handle, IN const char * strName, OUT MV_XML_InterfaceType *penInterfaceType);
        return MvCamCtrldll.MV_XML_GetNodeInterfaceType(self.handle, strName.encode('ascii'), byref(penInterfaceType))

    #####附加接口#####
    # Save image, support Bmp and Jpeg.
    def MV_CC_SaveImageEx2(self, stSaveParam):
        MvCamCtrldll.MV_CC_SaveImageEx2.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SaveImageEx2.restype = c_uint
        # C原型:int MV_CC_SaveImageEx2(void* handle, MV_SAVE_IMAGE_PARAM_EX* pSaveParam)
        return MvCamCtrldll.MV_CC_SaveImageEx2(self.handle, byref(stSaveParam))

    # Save the image file
    def MV_CC_SaveImageToFile(self, stSaveFileParam):
        MvCamCtrldll.MV_CC_SaveImageToFile.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SaveImageToFile.restype = c_uint
        # C原型:int MV_CC_SaveImageToFile(IN void* handle, MV_SAVE_IMG_TO_FILE_PARAM* pstSaveFileParam);
        return MvCamCtrldll.MV_CC_SaveImageToFile(self.handle, byref(stSaveFileParam))

    # Save 3D point data, support PLY、CSV and OBJ
    def MV_CC_SavePointCloudData(self, stPointDataParam):
        MvCamCtrldll.MV_CC_SavePointCloudData.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SavePointCloudData.restype = c_uint
        # C原型:int MV_CC_SavePointCloudData(IN void* handle, MV_SAVE_POINT_CLOUD_PARAM* pstPointDataParam);
        return MvCamCtrldll.MV_CC_SavePointCloudData(self.handle, byref(stPointDataParam))

    #  Rotate image
    def MV_CC_RotateImage(self, stRotateParam):
        MvCamCtrldll.MV_CC_RotateImage.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_RotateImage.restype = c_uint
        # C原型:int MV_CC_RotateImage(IN void* handle, IN OUT MV_CC_ROTATE_IMAGE_PARAM* pstRotateParam);
        return MvCamCtrldll.MV_CC_RotateImage(self.handle, byref(stRotateParam))

    # Flip image
    def MV_CC_FlipImage(self, stFlipParam):
        MvCamCtrldll.MV_CC_FlipImage.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FlipImage.restype = c_uint
        # C原型:int MV_CC_FlipImage(IN void* handle, IN OUT MV_CC_FLIP_IMAGE_PARAM* pstFlipParam);
        return MvCamCtrldll.MV_CC_FlipImage(self.handle, byref(stFlipParam))

    # Pixel format conversion
    def MV_CC_ConvertPixelType(self, stConvertParam):
        MvCamCtrldll.MV_CC_ConvertPixelType.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_ConvertPixelType.restype = c_uint
        # C原型:int MV_CC_ConvertPixelType(void* handle, MV_CC_PIXEL_CONVERT_PARAM* pstCvtParam)
        return MvCamCtrldll.MV_CC_ConvertPixelType(self.handle, byref(stConvertParam))

    # Interpolation algorithm type setting
    def MV_CC_SetBayerCvtQuality(self, nBayerCvtQuality):
        MvCamCtrldll.MV_CC_SetBayerCvtQuality.argtype = (c_void_p, c_uint)
        MvCamCtrldll.MV_CC_SetBayerCvtQuality.restype = c_uint
        # C原型:int MV_CC_SetBayerCvtQuality(IN void* handle, IN unsigned int nBayerCvtQuality);
        return MvCamCtrldll.MV_CC_SetBayerCvtQuality(self.handle, c_uint(nBayerCvtQuality))

    # Filter type of the bell interpolation quality algorithm setting
    def MV_CC_SetBayerFilterEnable(self, bFilterEnable):
        MvCamCtrldll.MV_CC_SetBayerFilterEnable.argtype = (c_void_p, c_bool)
        MvCamCtrldll.MV_CC_SetBayerFilterEnable.restype = c_uint
        # C原型：int __stdcall MV_CC_SetBayerFilterEnable(IN void* handle, IN bool bFilterEnable);
        return MvCamCtrldll.MV_CC_SetBayerFilterEnable(self.handle, c_bool(bFilterEnable))

    #  Set Gamma value
    def MV_CC_SetBayerGammaValue(self, fBayerGammaValue):
        MvCamCtrldll.MV_CC_SetBayerGammaValue.argtype = (c_void_p, c_float)
        MvCamCtrldll.MV_CC_SetBayerGammaValue.restype = c_uint
        # C原型：int __stdcall MV_CC_SetBayerGammaValue(IN void* handle, IN float fBayerGammaValue);
        return MvCamCtrldll.MV_CC_SetBayerGammaValue(self.handle, c_float(fBayerGammaValue))

    # Set Gamma value
    def MV_CC_SetGammaValue(self, enSrcPixelType, fGammaValue):
        MvCamCtrldll.MV_CC_SetGammaValue.argtype = (c_void_p, c_int, c_float)
        MvCamCtrldll.MV_CC_SetGammaValue.restype = c_uint
        # C原型:int MV_CC_SetGammaValue(IN void* handle, enum MvGvspPixelType enSrcPixelType, IN float fGammaValue);
        return MvCamCtrldll.MV_CC_SetGammaValue(self.handle, c_int(enSrcPixelType), c_float(fGammaValue))

    #ch：设置Bayer格式的Gamma信息 | en: Set Gamma param
    def MV_CC_SetBayerGammaParam(self, stGammaParam):
        MvCamCtrldll.MV_CC_SetBayerGammaParam.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SetBayerGammaParam.restype = c_uint
        # C原型：int __stdcall MV_CC_SetBayerGammaParam(IN void* handle, IN MV_CC_GAMMA_PARAM* pstGammaParam);
        return MvCamCtrldll.MV_CC_SetBayerGammaParam(self.handle, byref(stGammaParam))

    # Set CCM param,Scale default 1024
    def MV_CC_SetBayerCCMParam(self, stCCMParam):
        MvCamCtrldll.MV_CC_SetBayerCCMParam.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SetBayerCCMParam.restype = c_uint
        # C原型：int __stdcall MV_CC_SetBayerCCMParam(IN void* handle, IN MV_CC_CCM_PARAM* pstCCMParam);
        return MvCamCtrldll.MV_CC_SetBayerCCMParam(self.handle, byref(stCCMParam))

    # Set CCM param
    def MV_CC_SetBayerCCMParamEx(self, stCCMParam):
        MvCamCtrldll.MV_CC_SetBayerCCMParamEx.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_SetBayerCCMParamEx.restype = c_uint
        # C原型：int __stdcall MV_CC_SetBayerCCMParamEx(IN void* handle, IN MV_CC_CCM_PARAM_EX* pstCCMParam);
        return MvCamCtrldll.MV_CC_SetBayerCCMParamEx(self.handle, byref(stCCMParam))

    # Adjust image contrast
    def MV_CC_ImageContrast(self, stConstrastParam):
        MvCamCtrldll.MV_CC_ImageContrast.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_ImageContrast.restype = c_uint
        # C原型：int __stdcall MV_CC_ImageContrast(IN void* handle, IN OUT MV_CC_CONTRAST_PARAM* pstContrastParam);
        return MvCamCtrldll.MV_CC_ImageContrast(self.handle, byref(stConstrastParam))

    # High Bandwidth Decode
    def MV_CC_HBDecode(self, stDecodeParam):
        MvCamCtrldll.MV_CC_HB_Decode.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_HB_Decode.restype = c_uint
        # C原型：int __stdcall MV_CC_HB_Decode(IN void* handle, IN OUT MV_CC_HB_DECODE_PARAM* pstDecodeParam);
        return MvCamCtrldll.MV_CC_HB_Decode(self.handle, byref(stDecodeParam))

    # Draw Rect Auxiliary Line
    def MV_CC_DrawRect(self, stRectInfo):
        MvCamCtrldll.MV_CC_DrawRect.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_DrawRect.restype = c_uint
        # C原型: int __stdcall MV_CC_DrawRect(IN void* handle, IN MVCC_RECT_INFO* pRectInfo);
        return MvCamCtrldll.MV_CC_DrawRect(self.handle, byref(stRectInfo))

    # Draw Circle Auxiliary Line
    def MV_CC_DrawCircle(self, stCircleInfo):
        MvCamCtrldll.MV_CC_DrawCircle.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_DrawCircle.restype = c_uint
        # C原型: int __stdcall MV_CC_DrawCircle(IN void* handle, IN MVCC_CIRCLE_INFO* pCircleInfo);
        return MvCamCtrldll.MV_CC_DrawCircle(self.handle, byref(stCircleInfo))

    # Draw Line Auxiliary Line
    def MV_CC_DrawLines(self, stLineInfo):
        MvCamCtrldll.MV_CC_DrawLines.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_DrawLines.restype = c_uint
        # C原型: int __stdcall MV_CC_DrawLines(IN void* handle, IN MVCC_LINES_INFO* pLinesInfo);
        return MvCamCtrldll.MV_CC_DrawLines(self.handle, byref(stLineInfo))

    # Save camera feature
    def MV_CC_FeatureSave(self, strFileName):
        MvCamCtrldll.MV_CC_FeatureSave.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FeatureSave.restype = c_uint
        # C原型:int MV_CC_FeatureSave(void* handle, char* pFileName)
        return MvCamCtrldll.MV_CC_FeatureSave(self.handle, strFileName.encode('ascii'))

    # Load camera feature
    def MV_CC_FeatureLoad(self, strFileName):
        MvCamCtrldll.MV_CC_FeatureLoad.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FeatureLoad.restype = c_uint
        # C原型:int MV_CC_FeatureLoad(void* handle, char* pFileName)
        return MvCamCtrldll.MV_CC_FeatureLoad(self.handle, strFileName.encode('ascii'))

    # Read the file from the camera
    def MV_CC_FileAccessRead(self, stFileAccess):
        MvCamCtrldll.MV_CC_FileAccessRead.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FileAccessRead.restype = c_uint
        # C原型:int MV_CC_FileAccessRead(void* handle, MV_CC_FILE_ACCESS * pstFileAccess)
        return MvCamCtrldll.MV_CC_FileAccessRead(self.handle, byref(stFileAccess))

    # Read the file from the camera
    def MV_CC_FileAccessReadEx(self, stFileAccessEx):
        MvCamCtrldll.MV_CC_FileAccessReadEx.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FileAccessReadEx.restype = c_uint
        # C原型:int MV_CC_FileAccessReadEx(IN void* handle, IN OUT MV_CC_FILE_ACCESS_EX * pstFileAccessEx)
        return MvCamCtrldll.MV_CC_FileAccessReadEx(self.handle, byref(stFileAccessEx))

    # Write the file to camera
    def MV_CC_FileAccessWrite(self, stFileAccess):
        MvCamCtrldll.MV_CC_FileAccessWrite.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FileAccessWrite.restype = c_uint
        # C原型:int MV_CC_FileAccessWrite(void* handle, MV_CC_FILE_ACCESS * pstFileAccess)
        return MvCamCtrldll.MV_CC_FileAccessWrite(self.handle, byref(stFileAccess))

    # Write the file to camera
    def MV_CC_FileAccessWriteEx(self, stFileAccessEx):
        MvCamCtrldll.MV_CC_FileAccessWriteEx.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_FileAccessWriteEx.restype = c_uint
        # C原型:int MV_CC_FileAccessWriteEx(IN void* handle, IN MV_CC_FILE_ACCESS_EX * pstFileAccessEx)
        return MvCamCtrldll.MV_CC_FileAccessWriteEx(self.handle, byref(stFileAccessEx))

    # Get File Access Progress
    def MV_CC_GetFileAccessProgress(self, stFileAccessProgress):
        MvCamCtrldll.MV_CC_GetFileAccessProgress.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_GetFileAccessProgress.restype = c_uint
        # C原型:int MV_CC_GetFileAccessProgress(void* handle, MV_CC_FILE_ACCESS_PROGRESS * pstFileAccessProgress)
        return MvCamCtrldll.MV_CC_GetFileAccessProgress(self.handle, byref(stFileAccessProgress))

    # Start Record
    def MV_CC_StartRecord(self, stRecordParam):
        MvCamCtrldll.MV_CC_StartRecord.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_StartRecord.restype = c_uint
        # C原型:int __stdcall MV_CC_StartRecord(IN void* handle, IN MV_CC_RECORD_PARAM* pstRecordParam);
        return MvCamCtrldll.MV_CC_StartRecord(self.handle, byref(stRecordParam))

    # ch: 输入录像数据 | en:Input RAW data to Record
    def MV_CC_InputOneFrame(self, stInputFrameInfo):
        MvCamCtrldll.MV_CC_InputOneFrame.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_InputOneFrame.restype = c_uint
        # C原型：int __stdcall MV_CC_InputOneFrame(IN void* handle, IN MV_CC_INPUT_FRAME_INFO * pstInputFrameInfo);
        return MvCamCtrldll.MV_CC_InputOneFrame(self.handle, byref(stInputFrameInfo))

    # Stop Record
    def MV_CC_StopRecord(self):
        MvCamCtrldll.MV_CC_StopRecord.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_StopRecord.restype = c_uint
        # C原型：int __stdcall MV_CC_StopRecord(IN void* handle);
        return MvCamCtrldll.MV_CC_StopRecord(self.handle)

    # Open the GUI interface for getting or setting camera parameters
    def MV_CC_OpenParamsGUI(self):
        MvCamCtrldll.MV_CC_OpenParamsGUI.argtype = (c_void_p)
        MvCamCtrldll.MV_CC_OpenParamsGUI.restype = c_uint
        # C原型: __stdcall MV_CC_OpenParamsGUI(IN void* handle);
        return MvCamCtrldll.MV_CC_OpenParamsGUI(self.handle)

    # Reconstruct Image(For time-division exposure function)
    def MV_CC_ReconstructImage(self, stReconstructParam):
        MvCamCtrldll.MV_CC_ReconstructImage.argtype = (c_void_p, c_void_p)
        MvCamCtrldll.MV_CC_ReconstructImage.restype = c_uint
        # C原型：int __stdcall MV_CC_ReconstructImage(IN void* ha