import pyvisa

from MaxonMotor import MaxonMotor

class SacherLion:
    def __init__(self, address="GPIB0::12::INSTR"):
        resource_manager = pyvisa.ResourceManager()
        self._instrument = resource_manager.open_resource(address)
        self._instrument.read_termination = '\r\n'
        self._motor = MaxonMotor()

    def identify(self):
        return self._instrument.query('*IDN?')

    def query(self, visa_command: str) -> str:
        """
        For direct use of VISA query.
        
        Parameters
        ----------
        visa_command
            String to pass as a VISA query, with no extra newline. (e.g. "*IDN?")
        """
        return self._instrument.query(visa_command)

    def write(self, visa_command: str) -> None:
        """
        For direct use of VISA write.
        
        Parameters
        ----------
        visa_command
            String to pass as a VISA write, with no extra newline.
        """

        self._instrument.write(visa_command)
    
    def working_hours(self) -> str:
        """
        Returns the working hours of the laser in HH:MM:SS.
        """
        return self.query(':SYSTEM:Laser:Hours?')
    
    def system_status(self) -> str:
        status = self.query(':SYSTEM:STATUS?')
        assert int(status) >= 0
        assert int(status) < 77777

        if int(status) == 0:
            return "OK"

        digits = f"{status:0>5}"[::-1] # Digits from least to most significant

        laser_errors = [
            "I-Limit reached",
            "Laser Open Load / Compliance Voltage too low",
            "Error Laser requires TEC enabled"
        ]

        tec_errors = [
            "Temperature Watch Out of Window",
            "Temperature Out of Range",
            "Temperature Not Reached"
        ]

        range_errors = [
            "Modulation Voltage Out of Range",
            "Photodiode Out of Range",
            "Piezo Voltage Out of Range"
        ]

        loop_errors = [
            "Laser Head Loop Open",
            "Extern Interlock Loop Open",
            "TEC Loop Open"
        ]

        device_errors = [
            "Remote Control Command Error",
            "Temperature Coupling Out of Range",
            "Device Over Temperature"
        ]

        error_digit = [ laser_errors, tec_errors, range_errors, loop_errors, device_errors ]

        error_string = ""

        for i, digit in enumerate(digits):
            if int(digit) == 0:
                continue
            error_type = error_digit[i]
            for j, bit in enumerate(str(bin(int(digit)))[::-1]): # From least to most significant bit
                if int(bit) == 1:
                    error_string += error_type[j] + "\n"
        
        return error_string
    
    def serial_number(self) -> str:
        return self.query(":SYSTEM:SERIALNUMBER?")
    
    def get_current_limit(self) -> float:
        """
        Gets laser current limit in mA.
        """
        return 1000*float(self.query(":LASER:ILIMIT?"))
    
    def get_current(self) -> float:
        """
        Gets laser current in mA.
        """
        return 1000*float(self.query(":LASER:CURRENT?"))
    
    def set_current(self, I: float) -> None:
        """
        Sets laser current in mA.

        Parameters
        ----------
        I
            Laser current in mA.
        Raises
        ------
        ValueError
            If you try to set the laser current outside the range of 130 - 150 mA.
        """
        if I < 130:
            raise ValueError("Tried to set laser current below 130 mA.")
        elif I > 150:
            raise ValueError("Tried to set laser current above 150 mA.")
        
        self._instrument.write(f":LASER:CURRENT {I:0.1f}mA")

    def get_laser_mode(self) -> str:
        """
        Gets operating mode of laser.

        Returns
        -------
        mode : str
            "IMODE" or "PMODE"
        """
        return self.query(":LASER:MODE?")
        
    def laser_on(self) -> None:
        self._instrument.write(":LASER:STATUS 1")
    
    def laser_off(self) -> None:
        self._instrument.write(":LASER:STATUS 0")
    
    def set_piezo_voltage(self, V: float) -> None:
        """
        Sets piezo potential in volts.

        Parameters
        ----------
        V
            Voltage to set in volts.
        
            
        Raises
        -----
        ValueError
            If trying to set the piezo voltage outside the range of -13V to +13V.
        """
        if V > 13:
            raise ValueError("Cannot set piezo voltage above 13 V.")
        elif V < -13:
            raise ValueError("Cannot set piezo voltage below -13 V.")
        self._instrument.write(f"PIEZO:OFFSET {V}V")
    
    def get_piezo_voltage(self) -> float:
        """
        Returns the current piezo voltage in Volts.
        """
        return self.query(":PIEZO:OFFSET?")




def main():
    laser = SacherLion()
    print(laser.identify())
    print(f"Laser Operating Hours: {laser.working_hours()}")
    print(f"Current System Status: {laser.system_status()}")
    print(f"Laser Current: {laser.get_current()} mA")
    print(f"Piezo Voltage: {laser.get_piezo_voltage()} V")
    print("Setting new piezo voltage of 1.0 V")
    laser.set_piezo_voltage(1.0)
    print(f"New Piezo Voltage: {laser.get_piezo_voltage()} V")
    laser.set_current()





if __name__ == "__main__":
    main()


