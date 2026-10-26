import platform
import ctypes

sys_type = platform.system()
if sys_type == 'Windows':
    if platform.architecture()[0] == '64bit':
        zauxdll = ctypes.WinDLL('Libs//zauxdll.dll')
        print('Windows x64')
    else:
        zauxdll = ctypes.WinDLL('Libs//zmotion.dll')
        print('Windows x86')
elif sys_type == 'Darwin':
    zmcdll = ctypes.CDLL('Libs//zmotion.dylib')
    print("macOS")
elif sys_type == 'Linux':
    zmcdll = ctypes.CDLL('Libs//zmotion.so')
    print("Linux")
else:
    print("OS Not Supported!!")


def search(ip):
    ip_bytes = ip.encode('utf-8')
    p_ip = ctypes.c_char_p(ip_bytes)
    zauxdll.ZAux_SearchEth(p_ip, 200)
    print("ip:" + ip + 'res:', p_ip.value)


class ZMCWrapper:
    def __init__(self):
        self.handle = ctypes.c_void_p()
        self.sys_ip = ""
        self.sys_info = ""
        self.is_connected = False
        self.state_changed = 0

    def connect(self, ip):
        if self.handle.value is not None:
            self.disconnect()
        ip_bytes = ip.encode('utf-8')
        p_ip = ctypes.c_char_p(ip_bytes)
        print("Connecting to", ip, "...")
        ret = zauxdll.ZAux_OpenEth(p_ip, ctypes.pointer(self.handle))

        if ret == 0:
            msg = ip + " Connected"
            self.sys_ip = ip
            self.is_connected = True
            # print(msg)
        else:
            msg = "Connection Failed, Error " + str(ret)
            self.is_connected = False
            # print(msg)
        self.state_changed |= 1
        return ret

    def disconnect(self):
        ret = zauxdll.ZAux_Close(self.handle)
        self.is_connected = False
        self.state_changed |= 1
        return ret

    def set_atype(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetAtype(self.handle, int(axis), iValue)
        return ret

    def set_units(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetUnits(self.handle, int(axis), ctypes.c_float(iValue))
        return ret

    def set_accel(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetAccel(self.handle, int(axis), ctypes.c_float(iValue))
        return ret

    def set_decel(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetDecel(self.handle, int(axis), ctypes.c_float(iValue))
        return ret

    def set_max_speed(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetMaxSpeed(self.handle, int(axis), ctypes.c_int(iValue))
        return ret

    def set_speed(self, axis, iValue):
        if (axis in range(3, 6)) or (axis in range(9, 12)):
            iValue /= 2
        ret = zauxdll.ZAux_Direct_SetSpeed(self.handle, int(axis), ctypes.c_float(iValue))
        return ret

    def set_creep(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetCreep(self.handle, int(axis), ctypes.c_float(iValue))
        return ret

    def get_atype(self, axis):
        iValue = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAtype(self.handle, int(axis), ctypes.byref(iValue))
        if ret == 0:
            print("Get Axis (", axis, ") Atype:", iValue.value)
        else:
            print("Get Axis (", axis, ") Atype fail!")
        return ret

    def get_units(self, axis):
        iValue = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetUnits(self.handle, int(axis), ctypes.byref(iValue))
        if ret == 0:
            print("Get Axis (", axis, ") Units:", iValue.value)
        else:
            print("Get Axis (", axis, ") Units fail!")
        return ret

    def get_accel(self, axis):
        iValue = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetAccel(self.handle, int(axis), ctypes.byref(iValue))
        return ret, iValue.value

    def get_decel(self, axis):
        iValue = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetDecel(self.handle, int(axis), ctypes.byref(iValue))
        return ret, iValue.value

    def get_speed(self, axis):
        iValue = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetSpeed(self.handle, int(axis), ctypes.byref(iValue))
        if ret == 0:
            print("Get Axis (", axis, ") Speed:", iValue.value)
        else:
            print("Get Axis (", axis, ") Speed fail!")
        return ret, int(iValue.value)

    def move(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_Single_Move(self.handle, int(axis), ctypes.c_float(iValue))
        return ret

    def v_move(self, axis, dir_):
        ret = zauxdll.ZAux_Direct_Single_Vmove(self.handle, int(axis), dir_)
        return ret

    def move_to(self, axis, ipos):
        ret = zauxdll.ZAux_Direct_Single_MoveAbs(self.handle, int(axis), ctypes.c_float(ipos))
        return ret

    def stop(self, axis, imode=0):
        ret = zauxdll.ZAux_Direct_Single_Cancel(self.handle, int(axis), imode)
        return ret

    def platform_to_home(self, axis, imode):
        ret = zauxdll.ZAux_Direct_Single_Datum(self.handle, int(axis), imode)
        if ret == 0:
            print("axis (", axis, ") Datum submitted!")
        else:
            print("Datum fail!")
        return ret

    def get_pos(self, axis):
        iPos = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetMpos(self.handle, int(axis), ctypes.byref(iPos))
        if ret == 0:
            #            print("Get Axis (", axis, ") MPos:", iPos.value)
            return iPos.value
        else:
            print("Get Axis (", axis, ") MPos fail!")
            return 100000000

    def set_pos(self, axis, iPos):
        ret = zauxdll.ZAux_Direct_SetMpos(self.handle, int(axis), ctypes.c_float(iPos))
        return ret

    def is_in_motion(self, axis):
        iValue = ctypes.c_int()
        zauxdll.ZAux_Direct_GetIfIdle(self.handle, int(axis), ctypes.byref(iValue))
        return iValue.value

    def get_state(self, axis):
        iValue = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAxisStatus(self.handle, int(axis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def get_DatumIn(self, axis):
        iValue = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetDatumIn(self.handle, int(axis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def get_FwdIn(self, axis):
        iValue = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetFwdIn(self.handle, int(axis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def get_BckIn(self, axis):
        iValue = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetRevIn(self.handle, int(axis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def set_DatumIn(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetDatumIn(self.handle, int(axis), iValue)
        return ret

    def set_FwdIn(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetFwdIn(self.handle, int(axis), iValue)
        return ret

    def set_BckIn(self, axis, iValue):
        ret = zauxdll.ZAux_Direct_SetRevIn(self.handle, int(axis), iValue)
        return ret

