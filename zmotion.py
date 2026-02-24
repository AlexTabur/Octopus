import platform
import ctypes

#
systype = platform.system()
if systype == 'Windows':
    if platform.architecture()[0] == '64bit':
#        zauxdll = ctypes.WinDLL('Libs//zmotion64.dll')
        zauxdll = ctypes.WinDLL('Libs//zauxdll.dll')
        print('Windows x64')
    else:
        zauxdll = ctypes.WinDLL('Libs//zmotion.dll')
        print('Windows x86')
elif systype == 'Darwin':
    zmcdll = ctypes.CDLL('Libs//zmotion.dylib')
    print("macOS")
elif systype == 'Linux':
    zmcdll = ctypes.CDLL('Libs//zmotion.so')
    print("Linux")
else:
    print("OS Not Supported!!")

class ZMCWrapper:
    # Инициализация параметров
    def __init__(self):
        self.handle = ctypes.c_void_p()
        self.sys_ip = ""
        self.sys_info = ""
        self.is_connected = False
        self.state_changed = 0

    # Поискадресов
#    def search(self, ip, console=[]):
        #ip_val = ctypes.create_string_buffer(b'', 1024)
        #ret = zauxdll.ZAux_SearchEth(ctypes.byref(iplist), 1024, 200)
        #ret = zauxdll.ZAux_SearchEth(ctypes.byref(ip), 1024, 200)
        #s = iplist.value.decode()
        #str_iplist = s.split()
        #num = len(str_iplist)
        #print(num," Controller(s) Found")
        #print(*str_iplist, sep='\n')
        #console.append("Searching...")
  #      console.append(num," Controller(s) Found")
        #return str_iplist, num

    def search(self, ip, console=[]):
        #ip_val = ctypes.create_string_buffer(b'', 1024)
        ip_bytes = ip.encode('utf-8')
        p_ip = ctypes.c_char_p(ip_bytes)
        ret = zauxdll.ZAux_SearchEth(p_ip, 200)
        print("ip:"+ip+'res:',p_ip.value)

    #   Подключение контроллера
    def connect(self, ip, console=[]):
        if self.handle.value is not None:
            self.disconnect()
        ip_bytes = ip.encode('utf-8')
        p_ip = ctypes.c_char_p(ip_bytes)
        print("Connecting to", ip, "...")
        ret = zauxdll.ZAux_OpenEth(p_ip, ctypes.pointer(self.handle))
        msg = "Connected"
        if ret == 0:
            msg = ip + " Connected"
            self.sys_ip = ip
            self.is_connected = True
            print("Connected")
        else:
            msg = "Connection Failed, Error " + str(ret)
            self.is_connected = False
            print("Failed")
        self.state_changed |= 1
        return ret

    # Отключение
    def disconnect(self):
        ret = zauxdll.ZAux_Close(self.handle)
        self.is_connected = False
        self.state_changed |= 1
        return ret

# Настройки параметров оси
    # Установка типа оси
    def set_atype(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetAtype(self.handle, int(iaxis), iValue)
        return ret

    #
    def set_units(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetUnits(self.handle, int(iaxis), ctypes.c_float(iValue))
        return ret

    # Установка ускорения
    def set_accel(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetAccel(self.handle, int(iaxis), ctypes.c_float(iValue))
        return ret

    # Установка замедления
    def set_decel(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetDecel(self.handle, int(iaxis), ctypes.c_float(iValue))
        return ret

    # Устанока скорости
    def set_max_speed(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetMaxSpeed(self.handle, int(iaxis), ctypes.c_int(iValue))
        return ret


    def set_speed(self, iaxis, iValue):
        if (iaxis in range(3, 6)) or (iaxis in range(9, 12)):
            iValue = iValue / 2
        ret = zauxdll.ZAux_Direct_SetSpeed(self.handle, int(iaxis), ctypes.c_float(iValue))
        return ret

    def set_creep(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetCreep(self.handle, int(iaxis), ctypes.c_float(iValue))
        return ret

    # Считавыние параметров оси
    # Читать тип оси
    def get_atype(self, iaxis):
        iValue = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetAtype(self.handle, int(iaxis), ctypes.byref(iValue))
        if ret == 0:
            print("Get Axis (", iaxis, ") Atype:", iValue.value)
        else:
            print("Get Axis (", iaxis, ") Atype fail!")
        return ret

    # Читать единицы измерения
    def get_untis(self, iaxis):
        iValue = (ctypes.c_float)()
        ret = zauxdll.ZAux_Direct_GetUnits(self.handle, int(iaxis), ctypes.byref(iValue))
        if ret == 0:
            print("Get Axis (", iaxis, ") Units:", iValue.value)
        else:
            print("Get Axis (", iaxis, ") Units fail!")
        return ret

    # Читать ускорение
    def get_accel(self, iaxis):
        iValue = (ctypes.c_float)()
        ret = zauxdll.ZAux_Direct_GetAccel(self.handle, int(iaxis), ctypes.byref(iValue))
        return ret, iValue.value

    # Читать замедление
    def get_decel(self, iaxis):
        iValue = (ctypes.c_float)()
        ret = zauxdll.ZAux_Direct_GetDecel(self.handle, int(iaxis), ctypes.byref(iValue))
        return ret, iValue.value

    # Читать скорость
    def get_speed(self, iaxis):
        iValue = (ctypes.c_float)()
        ret = zauxdll.ZAux_Direct_GetSpeed(self.handle, int(iaxis), ctypes.byref(iValue))
        if ret == 0:
            print("Get Axis (", iaxis, ") Speed:",  iValue.value)
        else:
            print("Get Axis (", iaxis, ") Speed fail!")
        return ret, int(iValue.value)

#  Движение
    # Линейное движение
    def move(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_Single_Move(self.handle,  int(iaxis), ctypes.c_float(iValue))
        return ret

    #
    def vmove(self, iaxis, idir):
        ret = zauxdll.ZAux_Direct_Single_Vmove(self.handle,  int(iaxis), idir)
        return ret

    def move_to(self, iaxis, ipos):
        ret = zauxdll.ZAux_Direct_Single_MoveAbs(self.handle,  int(iaxis), ctypes.c_float(ipos))
        return ret


    def stop(self, iaxis, imode=0):
        ret = zauxdll.ZAux_Direct_Single_Cancel(self.handle,  int(iaxis), imode)
        return ret

    def platform_to_home(self, iaxis, imode):
        ret = zauxdll.ZAux_Direct_Single_Datum(self.handle,  int(iaxis), imode)
        if ret == 0:
            print("axis (", iaxis, ") Datum submited!")
        else:
            print("Datum fail!")
        return ret

# Позиции
    def get_pos(self, iaxis):
        iPos = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetMpos(self.handle, int(iaxis), ctypes.byref(iPos))
        if ret == 0:
#            print("Get Axis (", iaxis, ") MPos:", iPos.value)
            return iPos.value
        else:
            print("Get Axis (", iaxis, ") MPos fail!")
            return 100000000

    def set_pos(self, iaxis, iPos):
        ret = zauxdll.ZAux_Direct_SetMpos(self.handle,  int(iaxis), ctypes.c_float(iPos))
        return ret

    def is_in_motion(self, iaxis):
        iValue = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetIfIdle(self.handle,  int(iaxis), ctypes.byref(iValue))
        return iValue.value

    def get_state(self, iaxis):
        iValue = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetAxisStatus(self.handle,  int(iaxis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def get_DatumIn(self, iaxis):
        iValue = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetDatumIn(self.handle,  int(iaxis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def get_FwdIn(self, iaxis):
        iValue = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetFwdIn(self.handle, int(iaxis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def get_BckIn(self, iaxis):
        iValue = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetRevIn(self.handle, int(iaxis), ctypes.byref(iValue))
        if ret == 0:
            return iValue.value
        else:
            return 0xFFFFFFFF

    def set_DatumIn(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetDatumIn(self.handle, int(iaxis), iValue)
        return ret

    def set_FwdIn(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetFwdIn(self.handle, int(iaxis), iValue)
        return ret

    def set_BckIn(self, iaxis, iValue):
        ret = zauxdll.ZAux_Direct_SetRevIn(self.handle, int(iaxis), iValue)
        return ret

    ######################################################################################