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
        print("WL:  ", wm.get_wavelength().ghz)
        time.sleep(0.2)

if __name__ == "__main__":
    main()
