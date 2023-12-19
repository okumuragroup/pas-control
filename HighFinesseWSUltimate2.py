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

import os
import time
from pylablib.devices import HighFinesse

from Frequency import Frequency

class HighFinesseWavemeter:
    def __init__(self):
        app_folder = r"C:\Program Files (x86)\HighFinesse\Wavelength Meter WS Ultimate 1543"
        dll_path = os.path.join(app_folder, "Projects", "64")
        app_path = os.path.join(app_folder, "wlm_wsu.exe")
        self._wm = HighFinesse.WLM(1543, dll_path=dll_path, app_path=app_path)

    def __del__(self):
        self._wm.close()

    def get_frequency_from_wavelength(self) -> Frequency:
        """
        Returns frequency by querying vacuum wavelength. Redundant with get_frequency.
        """
        return Frequency(self._wm.get_wavelength() * 10**9, unit='nm')
    
    def get_frequency(self) -> Frequency:
        """
        Get frequency from wavemeter.
        """
        return Frequency(self._wm.get_frequency()/10**9, unit='ghz')

def main():
    wm = HighFinesseWavemeter()
    for i in range(20):
        print("Freq: ", wm.get_frequency().ghz)
        print("WL:  ", wm.get_frequency().nm)
        time.sleep(0.2)

if __name__ == "__main__":
    main()
