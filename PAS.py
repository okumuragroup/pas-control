import collections
import threading
import time

import Frequency

def scan(frequencies, averages=5):
    for frequency in frequencies:
        print(f"Frequency: {frequency.cm} cm-1")
        is_finished = threading.Event()
        lock_achieved = threading.Event()
        go_to_frequency(frequency.nm)
        print("Is lock achieved before locking?", lock_achieved.is_set())
        laser_lock_thread = threading.Thread(target=lock_laser, name="wavelength_locking_thread", args=(frequency, is_finished, lock_achieved))
        laser_lock_thread.start()
        print("Is lock achieved after starting thread?", lock_achieved.is_set())
        while not lock_achieved:
            time.sleep(0.1)
        print("Did lock get achieved? ", lock_achieved.is_set())
        for i in range(averages):
            signal = read_microphone()
            laser_power = read_power()
            temperature = read_temperature()
            print("We read some data!")
            time.sleep(0.2)
        is_finished.set()
        laser_lock_thread.join()




def go_to_frequency(frequency: Frequency):
    """Uses motor and piezo to move grating to change laser wavelength/frequency."""
    ...

def lock_laser(setpoint: Frequency, quit_locking: threading.Event, lock_achieved: threading.Event, tol: Frequency = Frequency(1e-6,'nm'), P: float = 1.0, I: float = 1.0, tau: int = 10, stable_after: int = 100):
    """Locks laser frequency to a setpoint.

    Parameters
    ----------
    setpoint
        Frequency desired.
    quit_locking
        Event that controls when to stop locking. This function will continue locking until ``quit_locking`` is set from the outside.
    lock_achieved
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
    lock_achieved.set()

    history = collections.deque(maxlen=tau)
    ## Begin PI loop
    counter = 0
    ## Scale P and I to K_p and T_i
    Kp = P * 0.09 ## Manual suggests ~0.09 GHz change / mA current
    Ti = (100 * I) ## Base I of 100 samples
    while True:
        ## Stops locking to setpoint once we've finished collecting data for this wavelength
        if quit_locking.is_set():
            print("Wavelength has finished. Exiting locking.")
            return
        current_frequency = read_laser_frequency()
        err = current_frequency.ghz - setpoint.ghz # in GHz

        if err < tol:
            if not lock_achieved.is_set():
                counter += 1
        else:
            counter = 0
            if lock_achieved.is_set():
                lock_achieved.clear()
        if counter > stable_after:
            lock_achieved.set()
        

        history.append(err)
        response = Kp*(err + (sum(history)/tau)/Ti) # in mA

        laser_current = get_laser_current() # in mA
        try:
            set_laser_current(laser_current + response)
        except:
            pass

        print("We're locking...")
        time.sleep(0.1)

def read_microphone() -> float:
    ...

def read_power() -> float:
    ...

def read_temperature() -> float:
    ...

def read_laser_frequency() -> Frequency:
    ...

def set_piezo_voltage(V: float):
    if V > 13:
        raise ValueError("Cannot set piezo voltage above 13 V.")
    elif V < -13:
        raise ValueError("Cannot set piezo voltage below -13 V.")
    ...

def get_piezo_voltage() -> float:
    ...

def get_laser_current() -> float:
    ...

def set_laser_current(current: float, override_low_power: bool = False):
    if current > 150:
        raise ValueError("Cannot set current above 150 mA.")
    elif current < 130 and not override_low_power:
        raise ValueError("Cannot set laser current below 130 mA.")
    ...

def main():
    frequencies = [ Frequency(x, 'nm') for x in [100.0, 200.0]]
    scan(frequencies)

if __name__ == "__main__":
    main()

