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

import pyvisa

class DS335:
    def __init__(self, address="GPIB0::22::INSTR"):
        resource_manager = pyvisa.ResourceManager()
        self._instrument = resource_manager.open_resource(address)

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

    def identify(self):
        return self._instrument.query('*IDN?')
    
    def set_frequency(self, frequency: float):
        """
        Sets function generator frequency in Hz.

        Parameters
        ----------
        frequency
            Frequency to set in Hz.
        """
        self.write(f"FREQ {frequency}")
    
    def read_frequency(self) -> float:
        return float(self.query("FREQ?"))
    
    def read_amplitude(self) -> float:
        """
        Returns peak-to-peak amplitude in Volts.
        """
        amplitude_string = self.query("AMPL? VP")
        return float(amplitude_string[:-3])
    
    def set_amplitude(self, amplitude: float):
        """
        Sets peak-to-peak amplitude in Volts. Alias for `set_amplitude_pp`.
        """
        self.set_amplitude_pp(amplitude)
    
    def set_amplitude_pp(self, amplitude: float):
        """
        Sets peak-to-peak amplitude in Volts.

        Parameters
        ----------
        amplitude
            Peak-to-peak amplitude in Volts.
        """
        self.write(f"FREQ {amplitude}VP")

    def set_amplitude_rms(self, amplitude: float):
        """
        Sets RMS amplitude in Volts.
        
        Parameters
        ----------
        amplitude
            RMS amplitude in Volts.
        """
        self.write(f"FREQ {amplitude}VR")
    
    def get_function(self) -> str:
        """
        Gets type of function currently being generated.

        Parameters
        ----------
        func
            Type of function being generated.
            Available types are 'sine', 'square', 'triangle', 'ramp', and 'noise'.
        """
        function_types = ['sine', 'square', 'triangle', 'ramp', 'noise']
        func = int(self.query("FUNC?"))
        return function_types[func]
    
    def set_function(self, func: str):
        """
        Sets function type.

        Parameters
        ----------
        func
            Type of function to generate.
            Available types are 'sine', 'square', 'triangle', 'ramp', and 'noise'.
        """
        function_types = {
            'sin': 0,
            'sine': 0,
            'square': 1,
            'triangle': 2,
            'ramp': 3,
            'noise': 4
        }
        self.write(f"FUNC {function_types[func.lower()]}")

def main():
    function_generator = DS335()
    # print(function_generator.read_frequency())
    # function_generator.set_frequency(1600)
    # print(function_generator.read_frequency())
    # function_generator.set_frequency(1540)
    # print(function_generator.read_frequency())
    # print(function_generator.read_amplitude())
    # print(function_generator.get_function())
    # function_generator.set_function('triangle')
    # print(function_generator.get_function())
    # function_generator.set_function('sin')
    # print(function_generator.get_function())
if __name__ == "__main__":
    main()