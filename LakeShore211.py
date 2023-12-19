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

import serial

class LS211:
    def __init__(self, com):
        self._interface = serial.Serial(com,
                                        baud=9600,
                                        bytesize=7, parity='O', stopbits = 1,
                                        xonxoff=True)
 
    def identify(self) -> str:
        return self.query("*IDN?\r\n")

    def read_temperature_celsius(self) -> float:
        return float(self.query("CRDG?\r\n"))
   
    def query(self, query: str, multiline: bool = False) -> str:
        """
        Send query on serial interface.

        Parameters
        ----------
        query
            Query command to send
        multiline
            Set to true if expecting a multiline response.
        """
        if multiline:
            raise NotImplementedError("No support yet for multiline queries.")
        
        ### Write query string
        if query[-2:] == '\r\n':
            self._interface.write(query.encode('ascii'))
        elif query[-1] == '\n':
            properly_terminated_query = query[:-1] + '\r\n'
            self._interface.write(properly_terminated_query.encode('ascii'))
        else:
            properly_terminated_query = query + '\r\n'
            self._interface.write(properly_terminated_query.encode('ascii'))

        ### Read response
        read_bytes = self._interface.readline()
        if read_bytes[-2:] == '\r\n'.encode('ascii'):
            return read_bytes[:-2].decode('ascii')
        else:
            raise IOError(f"Response not terminated with \r\n, instead returned bytes were: {read_bytes.decode('ascii')}")
