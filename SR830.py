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
