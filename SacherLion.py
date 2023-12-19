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
import collections
import threading
import time

import pyvisa

from Frequency import Frequency
from HighFinesseWSUltimate2 import HighFinesseWavemeter
from MaxonMotor import MaxonMotor

class FailedToLockLaser(Exception):
    pass

class SacherLion:
    def __init__(self, address="GPIB0::12::INSTR"):
        resource_manager = pyvisa.ResourceManager()
        self._instrument = resource_manager.open_resource(address)
        self._instrument.read_termination = '\r\n'
        self._motor = MaxonMotor()

        self._stop_locking = threading.Event()
        self._is_locking = threading.Event()

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
        return float(self.query(":PIEZO:OFFSET?"))
    
    def go_to_frequency(self, freq: Frequency, wavemeter: HighFinesseWavemeter, timeout: float = 30, **kwargs):
        """
        Tunes laser to target frequency using motor and piezo.

        Parameters
        ----------
        freq
            Target frequency
        wavemeter
            Wavemeter object to measure actual frequency.
        timeout
            Maximum amount of time in seconds to wait for piezo to tune to target frequency.
        """
        self._motor.go_to_wavelength(freq)

        kwargs['stable_after'] = 3 if 'stable_after' not in kwargs else kwargs['stable_after']
        kwargs['tol'] = Frequency(10, 'mhz') if 'tol' not in kwargs else kwargs['tol']
        lock = self.lock(freq, wavemeter, **kwargs)
        lock.wait(timeout)
        self.stop_locking()

    def lock(self,
             setpoint: Frequency,
             wavemeter: HighFinesseWavemeter,
             **kwargs):
        """
        Locks laser using only piezo. 

        Parameters
        ----------
        setpoint
            Frequency desired.
        wavemeter
            Wavemeter object that is used to read frequency.
        successfully_locked
            Event that signals when lock is achieved.
        tol
            Tolerance for locking.
        P
            Tunable parameter for PI lock.
        I
            Tunable parameter for PI lock.
        tau
            Number of samples to use for integration in PI lock.
        stable_after
            Consider laser locked after ``stable_after`` contiguous samples where ``abs(setpoint - measured_frequency) < tol``
        """
        print(f"Entered locking")
        ### Stop locking if the user accidentally forgot to stop locking
        self.stop_locking()
        while self._is_locking.is_set():
            time.sleep(0.1)
        
        ### Reset stop locking signal in preparation for new lock
        self._stop_locking.clear()

        ### Set up new locking thread and start it
        successfully_locked = threading.Event()
        laser_lock_thread = threading.Thread(target=self._lock_piezo, name="wavelength_locking_thread", args=(setpoint, wavemeter, successfully_locked), kwargs=kwargs, daemon=True)
        laser_lock_thread.start()
        return successfully_locked
    
    def stop_locking(self):
        self._stop_locking.set()
    
    def _lock_piezo(self,
                   setpoint: Frequency,
                   wavemeter: HighFinesseWavemeter,
                   successfully_locked: threading.Event,
                   tol: Frequency = Frequency(3e-3, 'ghz'),
                   P: float = 1.0,
                   I: float = 1.0,
                   tau: int = 10,
                   stable_after: int = 10):
        """
        Locks laser using only piezo. 

        Parameters
        ----------
        setpoint
            Frequency desired.
        wavemeter
            Wavemeter object that is used to read frequency.
        successfully_locked
            Event that signals when lock is achieved.
        tol
            Tolerance for locking.
        P
            Tunable parameter for PI lock.
        I
            Tunable parameter for PI lock.
        tau
            Number of samples to use for integration in PI lock.
        stable_after
            Consider laser locked after ``stable_after`` contiguous samples where ``abs(setpoint - measured_frequency) < tol``
        """
        print("Entered lock function...")
        self._is_locking.set()
        history = collections.deque(maxlen=tau)
        ## Begin PI loop
        counter = 0
        ## Scale P and I to K_p and T_i
        Kp = P * 1.5 * 0.5 ## Manual suggests ~ -1.5 GHz change / +1V piezo, empirically damping by 0.5 seems to work well
        piezo_voltage = self.get_piezo_voltage()
        begin_locking_time = time.time()
        while True:
            ## Stops locking when requested
            if self._stop_locking.is_set():
                self._is_locking.clear()
                return
            
            if not successfully_locked.is_set():
                current_time = time.time()
                ### If we've tried locking for more than 30 seconds and we're not locked, give up.
                if (current_time - begin_locking_time > 30):
                    self.stop_locking()
                    self._is_locking.clear()
                    raise FailedToLockLaser()
            
            current_frequency = wavemeter.get_frequency()
            err = current_frequency.ghz - setpoint.ghz # in GHz

            if abs(err) < tol.ghz:
                if not successfully_locked.is_set():
                    counter += 1
            else:
                ### Out of tolerance
                counter = 0
                ### If we fell out of tolerance, signal that we are no longer locked and restart our timer
                if successfully_locked.is_set():
                    successfully_locked.clear()
                    begin_locking_time = time.time()
            if counter > stable_after:
                successfully_locked.set()
            
            history.append(err)
            print(f"Setpoint (GHz): {setpoint.ghz}")
            print(f"Current frequency (GHz): {current_frequency.ghz}")
            print(f"Current distance from setpoint in GHz: {err}")
            response = Kp*(err + I*(sum(history)/min(tau, len(history)))) # in V
            #response = Kp*err

            # print(f"Old piezo voltage: {piezo_voltage}")
            #print(f"Calculated response: {response}\n")
            # print(f"Setting new voltage to: {piezo_voltage+response}")
            scale_counter = 0
            while scale_counter < 6:
                scaled_response = response*(10**-scale_counter)
                if abs(scaled_response) > 0.1:
                    scale_counter += 1
                    continue
                if abs(scaled_response) < 0.001:
                    break
                try:
                    self.set_piezo_voltage(piezo_voltage + scaled_response)
                    piezo_voltage += scaled_response
                    break
                except ValueError:
                    print(f"Response {scaled_response} too big, trying smaller step.")
                    scale_counter += 1
                except pyvisa.errors.VisaIOError as ex:
                    print(ex.description)

            #print("We're locking...")
            time.sleep(0.1)

def test_simple_lock():
    laser = SacherLion()
    wavemeter = HighFinesseWavemeter()
    try:
        successfully_locked = laser.lock(Frequency(760.01, 'nm'), wavemeter)
        while not successfully_locked.is_set():
            #print("Happily doing other things....")
            time.sleep(0.1)
    except FailedToLockLaser:
        print("Failed to lock laser.")
    laser.stop_locking()



def main():
    test_simple_lock()

if __name__ == "__main__":
    main()

def test_simple_functions():
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


    
