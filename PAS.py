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

import collections
import threading
import time
import datetime
from pathlib import Path

from Frequency import Frequency
from SacherLion import SacherLion
from DS335 import DS335
from SR830 import SR830
from HighFinesseWSUltimate2 import HighFinesseWavemeter
from drivepy.newport.powermeter import PowerMeter


def scan(frequencies: list[Frequency], fn: str, acoustic_freq: float, averages: int = 5, save_every: int = 5):
    laser = SacherLion()
    aom = DS335()
    lockin = SR830()
    wavemeter = HighFinesseWavemeter()
    powermeter = PowerMeter()

    aom.set_frequency(acoustic_freq)

    if Path(fn).exists():
        raise FileExistsError("File to save already exists. Pick a different filename.")

    with open(fn, 'wt') as file:
        file.write("Time,Laser Frequency (GHz),Lock-in Channel X (Mic),Lock-in Channel Y (Mic),"\
                   "Laser Power,Temperature (C),Pressure\n")

    def save_results(results: list[dict], fn: str):
        with open(fn, 'at', encoding='utf-8') as file:
            for r in results:
                for (time, laserfreq, laserpower, mic,
                     temp, pressure) in zip(r['time'], r['laser_frequency'], r['laser_power'], r['microphone'],
                                            r['temperature'], r['pressure'], strict=True):
                    file.write(f"{time},{laserfreq.ghz},{mic[0]},{mic[1]},{laserpower},{temp},{pressure}\n")

    results = []
    last_saved_iteration = 0
    for ifreq, frequency in enumerate(frequencies):
        if ifreq % save_every == 0:
            save_results(results[last_saved_iteration:ifreq], fn)
            last_saved_iteration = ifreq
        print(f"Frequency: {frequency.cm} cm-1")
        laser.go_to_frequency(frequency, wavemeter)
        lock_achieved = laser.lock(frequency, wavemeter)
        measurements = {
            'time': [],
            'microphone': [],
            'laser_power': [],
            'laser_frequency': [],
            'temperature': [],
            'pressure': [],
        }
        if lock_achieved.wait(30):
            for i in range(averages):
                if lock_achieved.is_set(): # Polling to make sure we're still locked before each measurement
                    measurements['timestamp'].append(str(datetime.datetime.now()))
                    measurements['microphone'].append(lockin.xy())
                    measurements['laser_power'].append(powermeter.readPowerRaw())
                    measurements['laser_frequency'].append(wavemeter.get_frequency())
                    measurements['temperature'].append(read_temperature())
                    measurements['pressure'].append(read_pressure())
                    time.sleep(0.2)
        laser.stop_locking()
        results.append(measurements)

def read_temperature():
    """
    Not yet implemented.
    """
    return ""

def read_pressure():
    """
    Not yet implemented.
    """
    return ""

def main():
    ...

if __name__ == "__main__":
    main()

