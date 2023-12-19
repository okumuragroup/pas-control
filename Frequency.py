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

import scipy.constants

class Frequency:
    """
    Wrapper for frequencies which transparently does unit conversions.

    Parameters
    ----------
    input: float
        Numerical value of frequency/wavelength.
    unit: {'ghz', 'nm', 'cm-1'}
        Unit of `input`.

    Attributes
    ----------
    ghz: float
        Frequency in GHz.
    cm: float
        Frequency expressed in equivalent inverse vacuum wavelength (cm-1).
    nm: float
        Frequency expressed in equivalent vacuum wavelength (nm).

    """
    def __init__(self, input: float, unit: str):
        self.c = scipy.constants.speed_of_light # in m/s

        unit = unit.lower()
        if unit == 'ghz':
            self._ghz = input
        elif unit == 'thz':
            self._ghz = input * 1000
        elif unit == 'mhz':
            self._ghz = input / 1000
        elif unit == 'nm':
            self._ghz = self.c / input # 10^9 factors from nm and GHz cancel
        elif unit == 'cm-1':
            self._ghz = input * self.c * 10**(-7)
        else:
            raise ValueError("Unit argument to frequency must be one of: GHz, nm, or cm-1")

    @property
    def ghz(self) -> float:
        return self._ghz
    
    @property
    def thz(self) -> float:
        return self._ghz / 1000
    
    @property
    def mhz(self) -> float:
        return self._ghz * 1000
    
    @property
    def nm(self) -> float:
        return self.c / self.ghz
    
    @property
    def cm(self) -> float:
        return self.ghz / (self.c * 10**(-7))
    


def main():
    testfreq = Frequency(500.0, 'nm')
    print(testfreq.ghz)
    print(testfreq.cm)
    print(testfreq.nm)
    testfreq2 = Frequency(20000.0, 'cm-1')
    print(testfreq2.ghz)
    print(testfreq2.cm)
    print(testfreq2.nm)

if __name__ == "__main__":
    main()


    
