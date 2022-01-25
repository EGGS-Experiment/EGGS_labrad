"""
### BEGIN NODE INFO
[info]
name = RGA Server
version = 1.4.1
description = Connects to the SRSx00 RGA

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
import numpy as np

from labrad.units import WithUnit
from labrad.server import Signal, setting

from twisted.internet.defer import returnValue, inlineCallbacks
from EGGS_labrad.servers import SerialDeviceServer

_SRS_EOL = '\r'


class RGA_Server(SerialDeviceServer):
    """
    Talks to the SRS RGAx00 residual gas analyzer.
    """

    name = 'RGA Server'
    regKey = 'RGAServer'
    port = 'COM63'
    serNode = 'mongkok'

    timeout = WithUnit(8.0, 's')
    baudrate = 28800

    # SIGNALS
    buffer_update = Signal(999999, 'signal: buffer_update', '(ss)')


    # STARTUP
    def initServer(self):
        super().initServer()
        # RGA type
        self.m_max = 200
        self.current_to_pressure = None


    # STATUS
    @setting(111, 'Initialize', level='i', returns='')
    def initialize(self, c, level=0):
        """
        Initialize the RGA.
        """
        if level not in (0, 1, 2):
            raise Exception('Invalid Input.')
        yield self._setter('IN', level)


    # IONIZER
    @setting(211, 'Ionizer Electron Energy', energy=['', 'i', 's'], returns='i')
    def electronEnergy(self, c, energy=None):
        """
        Set the electron energy (in eV).
        """
        if energy is not None:
            if type(energy) is int:
                if (energy < 25) or (energy > 105):
                    raise Exception('Invalid Input.')
            elif type(energy) is str:
                if energy != '*':
                    raise Exception('Invalid Input.')
            yield self._setter('EE', energy)
        resp = yield self._getter('EE')
        returnValue(int(resp))

    @setting(212, 'Ionizer Ion Energy', energy=['', 'i', 's'], returns='i')
    def ionEnergy(self, c, energy=None):
        """
        Set the ion energy (in eV).
        """
        if energy is not None:
            if type(energy) is int:
                if energy not in (0, 1):
                    raise Exception('Invalid Input.')
            elif type(energy) is str:
                if energy != '*':
                    raise Exception('Invalid Input.')
            yield self._setter('IE', energy)
        resp = yield self._getter('IE')
        returnValue(int(resp))

    @setting(221, 'Ionizer Filament', current=['', 'v', 's'], returns='v')
    def filament(self, c, current=None):
        """
        Set the filament current (in mA). Also known as electron emission current.
        """
        if current is not None:
            if type(current) is float:
                if (current < 0) or (current > 3.5):
                    raise Exception('Invalid Input.')
            elif type(current) is str:
                if current != '*':
                    raise Exception('Invalid Input.')
            yield self._setter('FL', current)
        resp = yield self._getter('FL')
        returnValue(float(resp))

    @setting(222, 'Ionizer Focus Voltage', voltage=['', 'i', 's'], returns='i')
    def focusVoltage(self, c, voltage=None):
        """
        Set the focus plate voltage (in V).
        """
        if voltage is not None:
            if type(voltage) is int:
                if (voltage < 0) or (voltage > 150):
                    raise Exception('Invalid Input.')
            elif type(voltage) is str:
                if voltage != '*':
                    raise Exception('Invalid Input.')
            yield self._setter('VF', voltage)
        resp = yield self._getter('VF')
        returnValue(int(resp))


    # DETECTOR
    @setting(311, 'Detector Calibrate', returns='s')
    def calibrate(self, c):
        """
        Calibrate the detector.
        """
        yield self._setter('CA', '')

    @setting(312, 'Detector Noise Floor', level=['', 'i', 's'], returns='i')
    def noiseFloor(self, c, level=None):
        """
        Set the detector noise floor.
        """
        if level is not None:
            if type(level) is int:
                if (level < 0) or (level > 7):
                    raise Exception('Invalid Input.')
            elif type(level) is str:
                if level != '*':
                    raise Exception('Invalid Input.')
            yield self._setter('NF', level, False)
        resp = yield self._getter('NF')
        returnValue(int(resp))

    @setting(313, 'Detector CDEM', returns='i')
    def cdem(self, c):
        """
        Check whether the electron multiplier is available.
        """
        resp = yield self._getter('MO')
        returnValue(int(resp))

    @setting(321, 'Detector CDEM Voltage', voltage=['', 'i', 's'], returns='i')
    def cdemVoltage(self, c, voltage=None):
        """
        Set the electron multiplier voltage bias.
        """
        if voltage is not None:
            if type(voltage) is int:
                if (voltage < 0) or (voltage > 2490):
                    raise Exception('Invalid Input.')
            elif type(voltage) is str:
                if voltage != '*':
                    raise Exception('Invalid Input.')
            yield self._setter('HV', voltage)
        resp = yield self._getter('HV')
        returnValue(int(resp))


    # SCANNING
    @setting(411, 'Scan Mass Initial', mass=['', 'i', 's'], returns='i')
    def massInitial(self, c, mass=None):
        """
        Set the initial mass for scanning.
        """
        if mass is not None:
            if type(mass) is int:
                if (mass < 0) or (mass > self.m_max):
                    raise Exception('Invalid Input.')
            elif type(mass) is str:
                if mass != '*':
                    raise Exception('Invalid Input.')
            # set value
            yield self._setter('MI', mass, False)
        # query
        resp = yield self._getter('MI')
        returnValue(int(resp))

    @setting(412, 'Scan Mass Final', mass=['', 'i', 's'], returns='i')
    def massFinal(self, c, mass=None):
        """
        Set the final mass for scanning.
        """
        if mass is not None:
            if type(mass) is int:
                if (mass < 0) or (mass > self.m_max):
                    raise Exception('Invalid Input.')
            elif type(mass) is str:
                if mass != '*':
                    raise Exception('Invalid Input.')
            # set value
            yield self._setter('MF', mass, False)
        # query
        resp = yield self._getter('MF')
        returnValue(int(resp))

    @setting(413, 'Scan Mass Steps', steps=['', 'i', 's'], returns='i')
    def massSteps(self, c, steps=None):
        """
        Set the number of steps per amu during scanning.
        """
        if steps is not None:
            if type(steps) is int:
                if (steps < 10) or (steps > 25):
                    raise Exception('Invalid Input.')
            elif type(steps) is str:
                if steps != '*':
                    raise Exception('Invalid Input.')
            # set value
            yield self._setter('SA', steps, False)
        # query
        resp = yield self._getter('SA')
        returnValue(int(resp))

    @setting(414, 'Scan Points', mode='s', returns='i')
    def scanPoints(self, c, mode):
        """
        Get the number of points per scan in either analog or histogram mode.
        """
        resp = None
        if mode.lower() in ('a', 'analog'):
            resp = yield self._getter('AP')
        elif mode.lower() in ('h', 'histogram'):
            resp = yield self._getter('HP')
        else:
            raise Exception('Invalid Input.')
        returnValue(int(resp))

    @setting(421, 'Scan Start', mode='s', num_scans='i', returns='*2v')
    def scanStart(self, c, mode, num_scans):
        """
        Start a given number of scans in either analog or histogram mode.
        """
        # check input
        if (num_scans < 0) or (num_scans > 255):
            raise Exception('Invalid Input.')

        #todo: get pressure conversion

        # get initial and final masses
        mass_initial = yield self._getter('MI')
        mass_initial = int(mass_initial)
        mass_final = yield self._getter('MF')
        mass_final = int(mass_final)

        # create scan message
        msg = None
        num_points = 0
        bytes_to_read = 0
        if mode.lower() in ('a', 'analog'):
            # getter
            yield self.ser.acquire()
            yield self.ser.write('AP?\r')
            num_points = yield self.ser.read_line(_SRS_EOL)
            self.ser.release()
            # process
            num_points = int(num_points)
            bytes_to_read = num_scans * 4 * (num_points + 1)
            msg = 'SC' + str(num_scans) + _SRS_EOL
        elif mode.lower() in ('h', 'histogram'):
            # getter
            yield self.ser.acquire()
            yield self.ser.write('HP?\r')
            num_points = yield self.ser.read_line(_SRS_EOL)
            self.ser.release()
            # process
            num_points = int(num_points)
            bytes_to_read = num_scans * 4 * (num_points + 1)
            msg = 'HS' + str(num_scans) + _SRS_EOL
        else:
            raise Exception('Invalid Input.')
        # initiate scan
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read(bytes_to_read)
        self.ser.release()
        # process scan
        current_arr = [int.from_bytes(resp[i: i+4], 'big') for i in range(0, bytes_to_read, 4)]
        # create axis
        amu_arr = list(np.linspace(mass_initial, mass_final, num_points))
        returnValue([amu_arr, current_arr[:-1]])


    # SINGLE MASS MEASUREMENT
    @setting(511, 'SMM Start', mass='i', returns='w')
    def singleMassMeasurement(self, c, mass):
        """
        Start a single mass measurement.
        """
        # sanitize input
        if (mass < 0) or (mass > self.m_max):
            raise Exception('Invalid Input.')
        # start a single mass measurement
        msg = 'MR' + str(mass) + _SRS_EOL
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read(4)
        #todo: get pressure conversion
        # set the rods back to zero
        yield self.ser.write('MR0\r')
        self.ser.release()
        # process and return the result
        current = int.from_bytes(resp, 'big')
        returnValue(current)


    # TOTAL PRESSURE MEASUREMENT
    @setting(611, 'TPM Start', returns='w')
    def totalPressureMeasurement(self, c):
        """
        Start a total pressure measurement.
        """
        # set the electron multiplier voltage to zero which
        # automatically enables total pressure measurement
        yield self._setter('HV', 0)
        # start a total pressure measurement
        #todo: get pressure conversion
        msg = 'TP?' + _SRS_EOL
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read(4)
        self.ser.release()
        # process and return result
        pressure = int.from_bytes(resp, 'big')
        returnValue(pressure)


    # HELPER
    @inlineCallbacks
    def _setter(self, chString, param, resp=True):
        """
        Change device parameters.
        """
        msg = chString + str(param) + _SRS_EOL
        status = ''
        # write and read response
        yield self.ser.acquire()
        yield self.ser.write(msg)
        if resp:
            status = yield self.ser.read_line(_SRS_EOL)
        self.ser.release()
        # convert status response to binary
        if status != '':
            status = format(int(status), '08b')
            self.buffer_update(('status', status))

    @inlineCallbacks
    def _getter(self, chString):
        """
        Get data from the device.
        """
        # query device for parameter value
        msg = chString + '?' + _SRS_EOL
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_SRS_EOL)
        self.ser.release()
        # send out buffer response to clients
        self.buffer_update((chString, resp.strip()))
        returnValue(resp)


if __name__ == "__main__":
    from labrad import util
    util.runServer(RGA_Server())
