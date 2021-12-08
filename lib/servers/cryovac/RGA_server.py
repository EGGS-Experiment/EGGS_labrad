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

from labrad.units import WithUnit
from labrad.server import Signal, setting

from twisted.internet.task import LoopingCall
from twisted.internet.defer import returnValue, inlineCallbacks, DeferredLock

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

_SRS_EOL = '\r'


class RGA_Server(SerialDeviceServer):
    name = 'RGA Server'
    regKey = 'RGAServer'
    port = 'COM48'
    serNode = 'mongkok'

    timeout = WithUnit(8.0, 's')
    baudrate = 28800

    # STARTUP
    def initServer(self):
        super().initServer()
        self.listeners = set()
        # polling stuff
        # self.refresher = LoopingCall(self.poll)
        # from twisted.internet.reactor import callLater
        # callLater(1, self.refresher.start, 5)
        # communications lock
        self.comm_lock = DeferredLock()
        # RGA type
        self.m_max = 100

    def stopServer(self):
        if hasattr(self, 'refresher'):
            if self.refresher.running:
                self.refresher.stop()
        super().stopServer()

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        """Remove a context object."""
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        """Get all listeners except for the context owner."""
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified


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
    @setting(211, 'Ionizer Electron Energy', energy='i', returns='i')
    def electronEnergy(self, c, energy=None):
        """
        Set the electron energy (in eV).
        """
        if energy is not None:
            if (energy < 25) or (energy > 105):
                raise Exception('Invalid Input.')
            yield self._setter('EE', energy)
        resp = yield self._getter('EE')
        returnValue(int(resp))

    @setting(212, 'Ionizer Ion Energy', energy='i', returns='i')
    def ionEnergy(self, c, energy=None):
        """
        Set the ion energy (in eV).
        """
        if energy is not None:
            if energy not in (0, 1):
                raise Exception('Invalid Input.')
            yield self._setter('IE', energy)
        resp = yield self._getter('IE')
        returnValue(int(resp))

    @setting(221, 'Ionizer Emission Current', current='v', returns='v')
    def emissionCurrent(self, c, current=None):
        """
        Set the electron emission current (in mA).
        """
        if current is not None:
            if (current < 0) or (current > 150):
                raise Exception('Invalid Input.')
            yield self._setter('FL', current)
        resp = yield self._getter('FL')
        returnValue(float(resp))

    @setting(222, 'Ionizer Focus Voltage', voltage='i', returns='i')
    def focusVoltage(self, c, voltage=None):
        """
        Set the focus plate voltage (in V).
        """
        if voltage is not None:
            if (voltage < 0) or (voltage > 150):
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
        #todo: see whether error prevents things

    @setting(312, 'Detector Noise Floor', level='i', returns='i')
    def noiseFloor(self, c, level=None):
        """
        Set the detector noise floor.
        """
        if level is not None:
            if (level < 0) or (level > 7):
                raise Exception('Invalid Input.')
            yield self._setter('NF', level)
        resp = yield self._getter('NF')
        returnValue(int(resp))

    @setting(313, 'Detector CDEM', returns='i')
    def cdem(self, c):
        """
        Check whether the electron multiplier is available.
        """
        resp = yield self._getter('MO')
        returnValue(int(resp))

    @setting(321, 'Detector CDEM Voltage', voltage='i', returns='i')
    def cdemVoltage(self, c, voltage=None):
        """
        Set the electron multiplier voltage bias.
        """
        if voltage is not None:
            if (voltage < 0) or (voltage > 2490):
                raise Exception('Invalid Input.')
            yield self._setter('HV', voltage)
        resp = yield self._getter('HV')
        returnValue(int(resp))


    # SCANNING
    @setting(411, 'Scan Mass Initial', mass='i', returns='i')
    def massInitial(self, c, mass=None):
        """
        Set the initial mass for scanning.
        """
        if mass is not None:
            if (mass < 0) or (mass > self.m_max):
                raise Exception('Invalid Input.')
            yield self._setter('MI', mass)
        resp = yield self._getter('MI')
        returnValue(int(resp))

    @setting(412, 'Scan Mass Final', mass='i', returns='i')
    def massFinal(self, c, mass=None):
        """
        Set the final mass for scanning.
        """
        if mass is not None:
            if (mass < 0) or (mass > self.m_max):
                raise Exception('Invalid Input.')
            yield self._setter('MF', mass)
        resp = yield self._getter('MF')
        returnValue(int(resp))

    @setting(413, 'Scan Mass Steps', steps='i', returns='i')
    def massSteps(self, c, steps=None):
        """
        Set the number of steps per amu during scanning.
        """
        if steps is not None:
            if (steps < 10) or (steps > 25):
                raise Exception('Invalid Input.')
            yield self._setter('SA', steps)
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

    @setting(421, 'Scan Start', mode='s', num_scans='i', returns='*1w')
    def scanStart(self, c, mode, num_scans):
        """
        Start a given number of scans in either analog or histogram mode.
        """
        # check input
        if (num_scans < 0) or (num_scans > 255):
            raise Exception('Invalid Input.')

        # create scan message
        msg = None
        bytes_to_read = 0
        if mode.lower() in ('a', 'analog'):
            yield self.ser.write('AP?\r')
            bytes_to_read = yield self.ser.read_line(_SRS_EOL)
            bytes_to_read = num_scans * 4 * (int(bytes_to_read) + 1)
            msg = 'SC' + str(num_scans) + _SRS_EOL
        elif mode.lower() in ('h', 'histogram'):
            yield self.ser.write('HP?\r')
            bytes_to_read = yield self.ser.read(_SRS_EOL)
            bytes_to_read = num_scans * 4 * (int(bytes_to_read) + 1)
            msg = 'HS' + str(num_scans) + _SRS_EOL
        else:
            raise Exception('Invalid Input.')

        # initiate blocking scan
        yield self.comm_lock.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read(bytes_to_read)
        yield self.comm_lock.release()

        # process scan
        current_arr = [int.from_bytes(resp[i:i+4], 'big') for i in range(0, bytes_to_read, 4)]
        returnValue(current_arr)


    # SINGLE MASS MEASUREMENT
    @setting(511, 'SMM Start', mass='i', returns='v')
    def singleMassMeasurement(self, c, mass):
        """
        Start a single mass measurement.
        """
        if (mass < 0) or (mass > self.m_max):
            raise Exception('Invalid Input.')

        # start a single mass measurement
        msg = 'MR' + str(mass) + _SRS_EOL

        yield self.comm_lock.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_SRS_EOL)
        yield self.comm_lock.release()

        # set the rods back to zero
        yield self._query('MR', 0, True, False)

        # return the result
        returnValue(float(resp))


    # TOTAL PRESSURE MEASUREMENT
    @setting(611, 'TPM Start', returns='v')
    def totalPressureMeasurement(self, c):
        """
        Start a total pressure measurement.
        """
        # set the electron multiplier voltage to zero
        # which automatically enables total pressure measurement
        yield self._query('HV', 0, True, False)

        # start a total pressure measurement
        msg = 'TP?' + _SRS_EOL

        yield self.comm_lock.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_SRS_EOL)
        yield self.comm_lock.release()

        # return the result
        returnValue(float(resp))

    # HELPER
    @inlineCallbacks
    def _setter(self, chString, param):
        """
        Change device parameters.
        """
        msg = chString + str(param) + _SRS_EOL
        yield self.ser.write(msg)
        status = yield self.ser.read_line(_SRS_EOL)
        # process status byte echo for errors
        # todo: convert to binary array then AND the errors
        # convert string input into binary
        status = format(int(status), '08b')
        print('status: ' + str(status))

    @inlineCallbacks
    def _getter(self, chString):
        """
        Get data from the device.
        """
        msg = chString + '?' + _SRS_EOL
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_SRS_EOL)
        returnValue(resp)


if __name__ == "__main__":
    from labrad import util
    util.runServer(RGA_Server())
