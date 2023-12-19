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
import time

import numpy as np

from Frequency import Frequency
from VCS import VCS, VCSError

DEBUG=True

class MaxonMotor(VCS):
    def __init__(self) -> None:
        super().__init__()
        self.connect()
        ## Read calibration constants from motor EPROM
        self._calibration_parameters = self.read_calibration_parameters()
        ## Check to make sure reading home position and position relative to home is working
        last_stored_position = self.read_stored_position()
        motor_rel_position = self.read_temp_motor_position()
        if DEBUG:
            print(f"Last stored position: {last_stored_position}")
            print(f"Motor rel position: {motor_rel_position}")
            print(f"Calibration parameters: {self._calibration_parameters}")

    def __del__(self) -> None:
        print("Closing connection to motor.")
        self._CloseDevice()

    def connect(self):
        """
        Connects to motor and puts the motor in well-defined initial state.
        """
        self._handle = self._OpenDevice()
        self._SetProtocolStackSettings()
        self._nodeid = self._GetNodeId()
        self._ClearFault()
        enabled = self._GetEnableState()
        while(enabled):
            self._SetDisableState()
        self._SetEncoderParameter()
        mode = self._GetOperationMode()
        if mode != 1: # If not in profile position mode
            self._SetOperationMode(1)
        position_profile = self._GetPositionProfile()
        if position_profile['velocity'] > 11400 or position_profile['acceleration'] > 20000 or position_profile['deceleration'] > 20000:
            default_position_profile = {
                'velocity': 3000,
                'acceleration': 20000,
                'deceleration': 20000,
            }
            self._SetPositionProfile(**default_position_profile)

    def get_wavelength(self):
        return self.position_to_wavelength(self.read_stored_position())
    
    def read_stored_position(self):
        """
        Reads stored position which corresponds to the position scale used to convert to wavelength.
        """
        return self._GetObject(0x2081, 0, 4, c_int32).value
    
    def read_temp_motor_position(self):
        """
        Reads motor's self-reported position. We use this value only to track how far the motor moves after a single
        `go_to_wavelength` operation.
        """
        return self._GetPositionIs()
    
    def read_calibration_parameters(self):
        """
        Reads calibration constants from motor EPROM. These constants relate the absolute position of
        the motor to the wavelength via a quadratic A*(position**2) + B*position + C. Also reads constants
        storing minimum and maximum wavelength.
        """
        A = self._uint32_to_double(self._GetObject(0x200C, 1, 4, c_uint32).value)
        B = self._uint32_to_double(self._GetObject(0x200C, 2, 4, c_uint32).value)
        C = self._uint32_to_double(self._GetObject(0x200C, 3, 4, c_uint32).value)
        ## Working, but we want to restrict to tigher range.
        # wavelength_array = cast(self._GetObject(0x200C, 4, 4), POINTER(c_uint16))
        # min_wavelength = wavelength_array[1] / 10 # in nm
        # max_wavelength = wavelength_array[0] / 10 # in nm
        min_wavelength = 756.5
        max_wavelength = 781.1
        calc_parameters = {
            'A': A,
            'B': B,
            'C': C,
            'min_wavelength': min_wavelength,
            'max_wavelength': max_wavelength,
        }
        return calc_parameters

    def position_to_wavelength(self, abs_position: int)-> float:
        """
        Converts absolute motor position to wavelength.
        """
        A = self._calibration_parameters['A']
        B = self._calibration_parameters['B']
        C = self._calibration_parameters['C']
        wavelength = A*(abs_position**2) + B*abs_position + C
        return wavelength

    def wavelength_to_position(self, wavelength: float) -> int:
        """
        Converts wavelength to absolute motor position (target of stored position).
        """
        A = self._calibration_parameters['A']
        B = self._calibration_parameters['B']
        C = self._calibration_parameters['C']
        ## Determine whether graph is descending or ascending between 0 and 5000
        if self.position_to_wavelength(5000) - self.position_to_wavelength(0) > 0:
            ascending = True
        else:
            ascending = False
        part1 = -B/(2*A)
        part2 = np.sqrt(  B**2 / (4*A**2)  - (C - wavelength)/A  )

        ## A > 0 and ascending yields plus, inverting one should give minus, inverting both should give plus again.
        if A > 0 and ascending:
            return int(part1 + part2)
        elif A > 0 and not ascending:
            return int(part1 - part2)
        elif A < 0 and ascending:
            return int(part1 - part2)
        elif A < 0 and not ascending:
            return int(part1 + part2)

    def go_to_wavelength(self, freq: Frequency):
        wavelength = freq.nm
        min = self._calibration_parameters['min_wavelength']
        max = self._calibration_parameters['max_wavelength']
        if wavelength < min or wavelength > max:
            raise ValueError("Wavelength {wavelength} out of range. Min: {min}, Max: {max}.")
        old_temp_pos = self.read_temp_motor_position()
        stored_position = self.read_stored_position()
        target_position = int(self.wavelength_to_position(wavelength))
        diff_position = target_position - stored_position

        def write_final_position():
            cur_temp_pos = self.read_temp_motor_position()
            shift = cur_temp_pos - old_temp_pos
            final_stored_position = stored_position + shift
            try:
                self._write_stored_pos(final_stored_position)
            except VCSError as exc:
                print(f"Failed to correctly set home position. This could leave motor in undefined state. Home position should be set to {final_stored_position}")
                raise exc

        if diff_position < 0:
            hysteresis_offset = 10000
            try:
                self._move(diff_position-hysteresis_offset)
            except VCSError as exc:
                write_final_position()
                raise exc
            try:
                self._move(hysteresis_offset)
            except VCSError as exc:
                write_final_position()
                raise exc
        else:
            try:
                self._move(diff_position)
            except VCSError as exc:
                write_final_position()
                raise exc
        write_final_position()

    def _move(self, rel_position):
        """
        Moves to position relative to previous position. Should only be used by `go_to_wavelength()` or
        for manual adjustments of motor position. Notably, this method does not shift the stored position.
        """
        self._SetEnableState()
        try:
            self._MoveToPosition(rel_position, absolute=False, immediately=True)
            while True:
                target_reached = self._GetMovementState()
                if target_reached:
                    break
                time.sleep(0.25)
        except VCSError as exc:
            self._SetDisableState()
            raise exc
        self._SetDisableState()

    def _write_stored_pos(self, abs_position):
        self._SetObject(0x2081, 0, c_int32(abs_position), 4)

    def _uint32_to_double(self, input):
        """
        This is the utterly insane encoding of a floating point number used by Sacher to store calibration constants
        on the EPROM of the motor. This decoding has been verified to match results of the LabVIEW decoding.
        The sign of the mantissa is stored in the most significant digit, followed by the mantissa (which has its radix 7
        *decimal* places from its least significant digit), followed by the sign bit of the exponent, followed by the exponent.
        The encoding uses 2 as the base of its exponent.
        """
        binstr = str(bin(input))[2:] # strip 0b
        ndigits = len(binstr)
        binstr = (32 - ndigits)*"0" + binstr # left pad with zeros to yield 32-bit string
        msign = 1 if int(binstr[0]) == 0 else -1
        mantissa = int("0b" + binstr[1:24],2) / 1000000
        esign = 1 if int(binstr[24]) == 0 else -1
        exponent = int("0b" + binstr[25:],2)
        result = msign*mantissa * 2**(esign*exponent)
        return result
    
    def _debug_shift_home_from_wavelength(self, wavelength):
        correct_home_position = int(self.wavelength_to_position(wavelength))
        self._write_stored_pos(correct_home_position)

def main():
    motor = MaxonMotor()
    print(f"Initial motor wavelength: {motor.get_wavelength()}")
    motor.go_to_wavelength(760.0)
    print(f"Final motor wavelength:{motor.get_wavelength()}")

if __name__ == "__main__":
    main()
