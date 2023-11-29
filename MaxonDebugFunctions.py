    def _ResetPortName(self, devicename, protocolstackname, interfacename):
        """
        C function signature:
        BOOL VCS_ResetPortNameSelection(char* DeviceName, char* ProtocolStackName, char*
        InterfaceName, DWORD* pErrorCode)
        """
        ResetPortName = self._VCS.VCS_ResetPortNameSelection
        ResetPortName.restype = c_int32
        ResetPortName.argtypes = [c_char_p, c_char_p, c_char_p, POINTER(c_uint32)]
        error_out = c_uint32(0)

        res = ResetPortName(devicename, protocolstackname, interfacename, byref(error_out))

        if res == 0:
            raise RuntimeError(f"Failed to reset port name enumeration with error code {hex(error_out.value)}.")
    
    def _GetPortName(self, devicename, protocolstackname, interfacename) -> str:
        """
        C function signature:
        BOOL VCS_GetPortNameSelection(char* DeviceName, char* ProtocolStackName, char*
        InterfaceName, BOOL StartOfSelection, char* pPortSel, WORD MaxStrSize, BOOL* pEndOfSelection,
        DWORD* pErrorCode)
        """

        self._ResetPortName(devicename, protocolstackname, interfacename)

        GetPortName = self._VCS.VCS_GetPortNameSelection

        GetPortName.restype = c_int32
        GetPortName.argtypes = [c_char_p, c_char_p, c_char_p, c_int32, c_char_p, c_uint16, POINTER(c_int32), POINTER(c_uint32)]

        startofselection = c_int(1)
        maxstrsize = c_uint16(200)
        portname = create_string_buffer(maxstrsize.value)
        endofselection = c_int32(0)
        error_out = c_uint32(0)

        res = GetPortName(devicename, protocolstackname, interfacename, startofselection, portname, maxstrsize, byref(endofselection), byref(error_out))
        if res == 0:
            raise RuntimeError(f"Failed to get port name with error code {hex(error_out.value)}.")

        print(portname.value)

    def _GetDeviceName(self):
        """
        C function signature:
        BOOL VCS_GetDeviceNameSelection(BOOL StartOfSelection, char* pDeviceNameSel, WORD
        MaxStrSize, BOOL* pEndOfSelection, DWORD* pErrorCode)
        """
        GetDeviceName = self._VCS.VCS_GetDeviceNameSelection
        GetDeviceName.restype = c_int32
        GetDeviceName.argtypes = [c_int, c_char_p, c_uint16, POINTER(c_int32), POINTER(c_uint32)]

        startofselection = c_int(1)
        maxstrsize = c_uint16(200)
        devicename = create_string_buffer(maxstrsize.value)
        endofselection = c_int32(0)
        error_out = c_uint32(0)

        res = GetDeviceName(startofselection, devicename, maxstrsize, byref(endofselection), byref(error_out))

        return devicename
    
    def _GetProtocolStackName(self):
        """
        C function signature:
        BOOL VCS_GetProtocolStackNameSelection(char* DeviceName, BOOL StartOfSelection, char*
        pProtocolStackNameSel, WORD MaxStrSize, BOOL* pEndOfSelection, DWORD* pErrorCode)
        """
        GetProtocolStackName = self._VCS.VCS_GetProtocolStackNameSelection
        GetProtocolStackName.restype = c_int32
        GetProtocolStackName.argtypes = [c_char_p, c_int32, c_char_p, c_uint16, POINTER(c_int32), POINTER(c_uint32)]

        devicename = c_char_p(b"EPOS4")
        startofselection = c_int32(1)
        maxstrsize = c_uint16(200)
        protocolstackname = create_string_buffer(maxstrsize.value)
        endofselection = c_int32(0)
        error_out = c_uint32(0)

        res = GetProtocolStackName(devicename, startofselection, protocolstackname, maxstrsize, byref(endofselection), byref(error_out))

        if res == 0:
            raise RuntimeError(f"Failed to get protocol stack name with error {hex(error_out.value)}")

        return protocolstackname
    
    def _GetInterfaceName(self):
        """
        C function signature:
        BOOL VCS_GetInterfaceNameSelection(char* DeviceName, char* ProtocolStackName, BOOL
        StartOfSelection, char* pInterfaceNameSel, WORD MaxStrSize, BOOL* pEndOfSelection, DWORD*
        pErrorCode)
        """
        GetInterfaceName = self._VCS.VCS_GetInterfaceNameSelection
        GetInterfaceName.restype = c_int32
        GetInterfaceName.argtypes = [c_char_p, c_char_p, c_int32, c_char_p, c_uint16, POINTER(c_int32), POINTER(c_uint32)]
        devicename = c_char_p(b"EPOS4")
        protocolstackname = c_char_p(b"MAXON SERIAL V2")
        startofselection = c_int32(1)
        maxstrsize = c_uint16(200)
        interfacename = create_string_buffer(maxstrsize.value)
        endofselection = c_int32(0)
        error_out = c_uint32(0)
        res = GetInterfaceName(devicename, protocolstackname, startofselection, interfacename, maxstrsize, endofselection, error_out)

        if res == 0:
            raise RuntimeError(f"Failed to get interface name with error {hex(error_out.value)}")

        return interfacename