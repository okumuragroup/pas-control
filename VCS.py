# This code is part of the Okumura Photoacoustic Spectroscopy software package.
# Copyright (C) 2023 Greg Jones

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ctypes import *

"""
Data Types:
DWORD uint32
BOOL int32 (1 true 0 false)
WORD uint16
BYTE uint8
"""
BOOL = c_int32
DWORD = c_uint32
WORD = c_uint16
BYTE = c_uint8

class VCSError(Exception):
    pass

class VCS:
    def __init__(self) -> None:
        path_to_dll = R'C:\Program Files (x86)\maxon motor ag\EPOS IDX\EPOS2\04 Programming\Windows DLL\LabVIEW\maxon EPOS\Resources\EposCmd64.dll'
        ## Maxon documentation says EposCmd uses __stdcall convention, so using WinDLL.
        self._nodeid = None
        self._VCS = WinDLL(path_to_dll)
    
    def _OpenDevice(self) -> c_void_p:
        """
        C function signature:
        HANDLE VCS_OpenDevice(char* DeviceName, char* ProtocolStackName, char* InterfaceName,
        char* PortName, DWORD* pErrorCode)

        """
        OpenDevice = self._VCS.VCS_OpenDevice
        OpenDevice.restype = c_void_p
        OpenDevice.argtypes = [c_char_p, c_char_p, c_char_p, c_char_p, POINTER(c_int)]
        devicename = c_char_p(b"EPOS2")
        protocolstackname = c_char_p(b"MAXON SERIAL V2")
        interfacename = c_char_p(b"USB")
        portname = c_char_p(b"USB1")
        error_out = c_int()
        for i in range(0,10):
            portname = f"USB{i}".encode('ASCII')
            handle = OpenDevice(devicename, 
                                protocolstackname, 
                                interfacename, 
                                portname, 
                                byref(error_out))
            if error_out.value == 0x10000008:
                continue
            elif error_out.value != 0:
                raise VCSError(f"Failed to open device and acquire handle with error code {hex(error_out.value)}.")
            print(f"Connected on port {portname.decode()}")
            return handle
        raise VCSError("Failed to find port for Maxon motor device (tried USB0-USB9).")

    def _CloseDevice(self) -> None:
        """
        C function signature:
        BOOL VCS_CloseDevice(HANDLE KeyHandle, DWORD* pErrorCode)
        """
        CloseDevice = self._VCS.VCS_CloseDevice
        CloseDevice.argtypes = [c_void_p, 
                                POINTER(c_uint32)]
        CloseDevice.restype = c_int32

        error_out = c_uint32()

        success_flag = CloseDevice(self._handle, byref(error_out))

        if success_flag == 0:
            raise VCSError(f"Failed to close device with error code {hex(error_out.value)}")

    def _GetObject(self, object_index, object_subindex, NbOfBytesToRead, type=None, nodeid=None):
        """
        C function signature:
        BOOL VCS_GetObject(HANDLE KeyHandle, WORD NodeId, WORD ObjectIndex, BYTE
        ObjectSubIndex, void* pData, DWORD NbOfBytesToRead, DWORD* pNbOfBytesRead, DWORD*
        pErrorCode)

        If type is specified, returns C data type. Otherwise, returns a pointer to a buffer of the size
        given by NbOfBytesToRead.
        """
        if nodeid == None:
            # Get nodeid from object state, default status
            nodeid = self._nodeid
        else:
            # We end up using this command with
            nodeid = WORD(nodeid)
        GetObject = self._VCS.VCS_GetObject
        GetObject.restype = c_int32
        GetObject.argtypes = [c_void_p, WORD, WORD, BYTE, c_void_p, DWORD, POINTER(DWORD), POINTER(DWORD)]
        #returned_data = create_string_buffer(NbOfBytesToRead)
        returned_data = (c_byte * NbOfBytesToRead)()
        error_out = DWORD(0)
        num_bytes_actually_read = DWORD(0)
        res = GetObject(self._handle, nodeid, WORD(object_index), BYTE(object_subindex), byref(returned_data), 
                        DWORD(NbOfBytesToRead), num_bytes_actually_read, error_out)
        
        if res == 0:
            raise VCSError(f"Failed to get object at object_index {hex(object_index)}, subindex {object_subindex} with err: {hex(error_out.value)}.")
        if type:
            return cast(returned_data, POINTER(type)).contents
        else:
            return returned_data

    def _SetObject(self, object_index, object_subindex, data, NbOfBytesToWrite):
        """
        C function signature:
        BOOL VCS_SetObject(HANDLE KeyHandle, WORD NodeId, WORD ObjectIndex, BYTE
        ObjectSubIndex, void* pData, DWORD NbOfBytesToWrite, DWORD* pNbOfBytesWritten, DWORD*
        pErrorCode)

        data should be a ctypes type (not a pointer to it)
        """
        fun = self._VCS.VCS_SetObject
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, WORD, BYTE, c_void_p, DWORD, POINTER(DWORD), POINTER(DWORD)]

        num_bytes_written = DWORD(0)
        error_out = DWORD(0)

        res = fun(self._handle, self._nodeid, WORD(object_index), BYTE(object_subindex), byref(data), DWORD(NbOfBytesToWrite), 
                  byref(num_bytes_written), byref(error_out))
        
        if num_bytes_written.value != NbOfBytesToWrite:
            raise VCSError(f"Didn't write the correct # of bytes. Expected to write {NbOfBytesToWrite}, wrote {num_bytes_written.value}.")
        
        if res == 0:
            raise VCSError(f"Failed to set object index {hex(object_index)}, subindex {object_subindex} with err: {hex(error_out.value)}")

    def _SetProtocolStackSettings(self) -> None:
        """
        BOOL VCS_SetProtocolStackSettings(HANDLE KeyHandle, DWORD Baudrate, DWORD Timeout,
        DWORD* pErrorCode)
        """
        SetProtocolStackSettings = self._VCS.VCS_SetProtocolStackSettings
        SetProtocolStackSettings.restype = c_int32
        SetProtocolStackSettings.argtypes = [c_void_p, c_uint32, c_uint32, POINTER(c_uint32)]
        #baudrate = c_uint32(38400) # From Sacher docs, in baud (bit/s)
        #timeout = c_uint32(100) # from Sacher docs, in ms from Maxon doc
        baudrate = DWORD(1000000)
        timeout = DWORD(500)
        error_out = c_uint32(0)
        res = SetProtocolStackSettings(self._handle, baudrate, timeout, error_out)

        if res == 0:
            raise VCSError(f"Failed to set baudrate and timeout in initialization. Err info: {hex(error_out.value)}")
    
    def _GetNodeId(self):
        return self._GetObject(0x2000, 0, 2, type=WORD, nodeid=0)
        #return cast(nodeid, POINTER(WORD)).contents

    def _GetEnableState(self):
        """
        BOOL VCS_GetEnableState(HANDLE KeyHandle, WORD NodeId, BOOL* pIsEnabled, DWORD*
        pErrorCode)
        """
        GetEnableState = self._VCS.VCS_GetEnableState
        GetEnableState.restype = c_int32
        GetEnableState.argtypes = [c_void_p, WORD, POINTER(BOOL), POINTER(DWORD)]
        isenabled = BOOL(0)
        error_out = DWORD(0)
        res = GetEnableState(self._handle, self._nodeid, byref(isenabled), byref(error_out))

        if res == 0:
            raise VCSError(f"Failed to get enable state with err: {hex(error_out.value)}")
        
        if isenabled.value == 1:
            return True
        elif isenabled.value == 0:
            return False
        else:
            raise VCSError(f"Bad return value from GetEnableState. Returned {isenabled.value}, expected 0 or 1.")
    
    def _SetEnableState(self) -> None:
        """
        BOOL VCS_SetEnableState(HANDLE KeyHandle, WORD NodeId, DWORD* pErrorCode)
        """
        fun = self._VCS.VCS_SetEnableState
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, POINTER(DWORD)]
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to set device state to enabled with err: {hex(error_out.value)}")

    def _SetDisableState(self):
        fun = self._VCS.VCS_SetDisableState
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, POINTER(DWORD)]
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to set device state to disabled with err: {hex(error_out.value)}")

    # def _SetEncoderParameter(self):
    #     """
    #     The original LabView code used the VCS_SetEncoderParameter function which appears to no longer be documented.
    #     I found old documentation for this function at the URL below:
    #     https://github.com/RIVeR-Lab/eposcmd/blob/master/EposCmd/EposCmdImpl.cpp
    #     which gave the C function signature as follows:
    #     VCS_SetEncoderParameter(HANDLE KeyHandle, WORD NodeId, WORD Counts, WORD PositionSensorType, DWORD* pErrorCode)
    #     """
    #     fun = self._VCS.VCS_SetEncoderParameter
    #     fun.restype = BOOL
    #     fun.argtypes = [c_void_p, WORD, WORD, WORD, POINTER(DWORD)]
    #     error_out = DWORD(0)
    #     counts = WORD(512)
    #     position_sensor_type = WORD(4)
    #     res = fun(self._handle, self._nodeid, counts, position_sensor_type, byref(error_out))
    #     if res == 0:
    #         raise VCSError(f"Failed to set encoder parameters with err: {hex(error_out.value)}")

    def _SetEncoderParameter(self):
        """
        This is a reimplementation of VCS_SetEncoderParameter based on an old 32-bit DLL EPOS2 command manual which
        describes the behavior as simply setting these two firmware values. Directly using VCS_SetObject here to
        set the documented values.
        """
        counts = DWORD(512)
        position_sensor_type = WORD(4)
        try:
            self._SetObject(0x2210, 1, counts, 4)
        except VCSError as exc:
            raise VCSError("Failed to set # of pulses/turn") from exc
        try:
            self._SetObject(0x2210, 2, position_sensor_type, 2)
        except VCSError as exc:
            """
            The original LabView code errors with 0x06090300 (value out of range), and simply ignored the error.
            This implementation is able to distinguish that it is in fact the position_sensor_type value
            which is out of range. We continue to try to set this value to mimic the old LabView code,
            but ignore the resulting error.
            """
            pass

    def _ClearFault(self) -> None:
        """
        BOOL VCS_ClearFault(HANDLE KeyHandle, WORD NodeId, DWORD* pErrorCode)
        """
        ClearFault = self._VCS.VCS_ClearFault
        ClearFault.restype = BOOL
        ClearFault.argtypes = [c_void_p, WORD, POINTER(DWORD)]
        error_out = DWORD(0)
        res = ClearFault(self._handle, self._nodeid, byref(error_out))
        
        if res == 0:
            raise VCSError(f"Failed to clear faults with err: {hex(error_out.value)}")

    def _GetOperationMode(self):
        """
        BOOL VCS_GetOperationMode(HANDLE KeyHandle, WORD NodeId, __int8* pMode, DWORD* pErrorCode)
        Profile Postion Mode (PPM) 1
        Profile Velocity Mode (PVM) 3
        Homing Mode (HM) 6
        Interpolated Position Mode (IPM) 7
        """
        fun = self._VCS.VCS_GetOperationMode
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, POINTER(c_int8), POINTER(DWORD)]
        operation_mode = c_int8(0)
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, byref(operation_mode), byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to get motor operation mode with err: {hex(error_out.value)}")
        
        return operation_mode

    def _SetOperationMode(self, mode=1):
        """
        BOOL VCS_SetOperationMode(HANDLE KeyHandle, WORD NodeId, __int8 Mode, DWORD*
        pErrorCode)
        """
        fun = self._VCS.VCS_SetOperationMode
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, BYTE, POINTER(DWORD)]
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, BYTE(mode), byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to set operation mode to {mode} with error code: {hex(error_out.value)}")

    def _GetPositionProfile(self):
        """
        BOOL VCS_GetPositionProfile(HANDLE KeyHandle, WORD NodeId, DWORD* pProfileVelocity, DWORD*
        pProfileAcceleration, DWORD* pProfileDeceleration, DWORD* pErrorCode)
        """
        fun = self._VCS.VCS_GetPositionProfile
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, POINTER(DWORD), POINTER(DWORD), POINTER(DWORD), POINTER(DWORD)]
        profile_velocity = DWORD(0)
        profile_acceleration = DWORD(0)
        profile_deceleration = DWORD(0)
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, byref(profile_velocity), byref(profile_acceleration),
                  byref(profile_deceleration), byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to get position profile with error code: {hex(error_out.value)}")

        result_dict = {
            'velocity': profile_velocity.value,
            'acceleration': profile_acceleration.value,
            'deceleration': profile_deceleration.value,
        }

        return result_dict

    def _SetPositionProfile(self, velocity=3000, acceleration=20000, deceleration=20000):
        """
        BOOL VCS_SetPositionProfile(HANDLE KeyHandle, WORD NodeId, DWORD ProfileVelocity, DWORD
        ProfileAcceleration, DWORD ProfileDeceleration, DWORD* pErrorCode)
        """
        fun = self._VCS.VCS_SetPositionProfile
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, DWORD, DWORD, DWORD, POINTER(DWORD)]
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, DWORD(velocity), DWORD(acceleration), DWORD(deceleration), byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to set position profile with error code: {hex(error_out.value)}.")

    def _GetPositionIs(self):
        """
        BOOL VCS_GetPositionIs(HANDLE KeyHandle, WORD NodeId, long* pPositionIs, DWORD*
        pErrorCode)
        """
        fun = self._VCS.VCS_GetPositionIs
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, POINTER(c_long), POINTER(DWORD)]
        position = c_long(0)
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, byref(position), byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to get position with error code: {hex(error_out.value)}")
        return position.value

    def _MoveToPosition(self, position, absolute=True, immediately=True):
        """
        BOOL VCS_MoveToPosition(HANDLE KeyHandle, WORD NodeId, long TargetPosition, BOOL
        Absolute, BOOL Immediately, DWORD* pErrorCode)
        """
        fun = self._VCS.VCS_MoveToPosition
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, c_long, BOOL, BOOL, POINTER(DWORD)]
        error_out = DWORD(0)
        position_param = c_long(position)
        absolute_param = BOOL(1) if absolute else BOOL(0)
        immediately_param = BOOL(1) if immediately else BOOL(0)
        res = fun(self._handle, self._nodeid, position_param, absolute_param, immediately_param, byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to move to position with error code: {hex(error_out.value)}")

    def _GetMovementState(self) -> bool:
        """
        BOOL VCS_GetMovementState(HANDLE KeyHandle, WORD NodeId, BOOL* pTargetReached, DWORD*
        pErrorCode)
        """
        fun = self._VCS.VCS_GetMovementState
        fun.restype = BOOL
        fun.argtypes = [c_void_p, WORD, POINTER(BOOL), POINTER(DWORD)]
        target_reached = BOOL(0)
        error_out = DWORD(0)
        res = fun(self._handle, self._nodeid, byref(target_reached), byref(error_out))
        if res == 0:
            raise VCSError(f"Failed to get movement state with error code: {hex(error_out.value)}")
        return True if target_reached.value == 1 else False
