# This code is part of the Okumura Photoacoustic Spectroscopy software package.
# Copyright (C) 2023  Greg Jones

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

import time
from pymeasure.adapters import VISAAdapter
import pymeasure.instruments.srs


class SR830:
    def __init__(self, address="GPIB0::8::INSTR") -> None:
        self._adapter = VISAAdapter(address)
        self._lockin = pymeasure.instruments.srs.SR830(self._adapter)
    
    def x(self):
        return self._lockin.x
    
    def y(self):
        return self._lockin.y
    
    def xy(self):
        return self._lockin.xy
    
def main():
    lockin = SR830()
    for i in range(20):
        print("X: ", lockin.x())
        print("Y: ", lockin.y())
        print("XY: ", lockin.xy())
        time.sleep(0.2)

if __name__ == "__main__":
    main()
