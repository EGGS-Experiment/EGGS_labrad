"""
### BEGIN NODE INFO
[info]
name = RGA Server
version = 1.4.1
description = Connects to the SRS200 RGA

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
from twisted.internet.defer import returnValue, inlineCallbacks

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer


_SRS_EOL = '\r'

class RGA_Server(SerialDeviceServer):
    name = 'RGA Server'
    regKey = 'RGAServer'
    port = 'COM48'
    serNode = 'mongkok'

    timeout = WithUnit(3.0, 's')
    baudrate = 28800

    # STARTUP
    def initServer(self):
        super().initServer()
        self.listeners = set()
        # polling stuff
        self.refresher = LoopingCall(self.poll)
        from twisted.internet.reactor import callLater
        callLater(1, self.refresher.start, 5)

    def stopServer(self):
        if hasattr(self, 'refresher'):
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
    @setting(111, 'Initialize', level='i', returns='i')
    def initialize(self, c, level=0):
        """
        Initialize the RGA.
        """
        if not level:
            level = ''
        elif level not in (0, 1, 2):
            raise Exception('Invalid Input.')
        resp = yield self._query('IN', level, True, True)
        returnValue(resp)


    # IONIZER
    @setting(211, 'Ionizer Electron Energy', energy='i', returns='i')
    def electronEnergy(self, c, energy=0):
        """
        Set the electron energy (in eV).
        """
        if not energy:
            energy = ''
        elif (energy < 25) or (energy > 105):
            raise Exception('Invalid Input.')
        resp = yield self._query('EE', energy, True, True)
        returnValue(int(resp))

    @setting(212, 'Ionizer Ion Energy', energy='i', returns='i')
    def ionEnergy(self, c, energy=None):
        """
        Set the ion energy (in eV).
        """
        if not energy:
            energy = ''
        elif energy not in (0, 1):
            raise Exception('Invalid Input.')
        resp = yield self._query('IE', energy, True, True)
        returnValue(int(resp))

    @setting(221, 'Ionizer Emission Current', current='v', returns='v')
    def emissionCurrent(self, c, current=None):
        """
        Set the electron emission current (in mA).
        """
        if not current:
            current = ''
        elif (current < 0) or (current > 3.5):
            raise Exception('Invalid Input.')
        resp = yield self._query('FL', current, True, True)
        returnValue(float(resp))

    @setting(222, 'Ionizer Focus Voltage', voltage='i', returns='i')
    def focusVoltage(self, c, voltage=None):
        """
        Set the electron emission current (in mA).
        """
        if not voltage:
            voltage = ''
        elif (voltage < 0) or (voltage > 150):
            raise Exception('Invalid Input.')
        resp = yield self._query('FL', voltage, True, True)
        returnValue(int(resp))


    # DETECTOR
    @setting(311, 'Detector Calibrate', returns='s')
    def calibrate(self, c):
        """
        Calibrate the detector.
        """
        resp = yield self._query('CA', '', True, False)
        #todo: see whether error prevents things
        returnValue(int(resp))

    @setting(312, 'Ionizer Noise Floor', level='i', returns='i')
    def noiseFloor(self, c, level=None):
        """
        Set the detector noise floor.
        """
        if not level:
            level = ''
        elif (level < 0) or (level > 7):
            raise Exception('Invalid Input.')
        resp = yield self._query('NF', level, True, True)
        returnValue(int(resp))

    @setting(313, 'Ionizer CDEM', returns='i')
    def cdem(self, c):
        """
        Check whether the electron multiplier is available.
        """
        resp = yield self._query('MO', '', False, True)
        returnValue(int(resp))

    @setting(321, 'Ionizer CDEM Voltage', voltage='i', returns='i')
    def cdemVoltage(self, c, voltage=None):
        """
        Set the electron multiplier voltage bias.
        """
        if not voltage:
            voltage = ''
        elif (voltage < 0) or (voltage > 2490):
            raise Exception('Invalid Input.')
        resp = yield self._query('HV', voltage, True, True)
        returnValue(int(resp))


    # SCANNING
    @setting(411, 'Scan Mass Initial', mass='i', returns='i')
    def massInitial(self, c, mass=None):
        """
        Set the initial mass for scanning.
        """
        if not mass:
            mass = ''
        #todo: check RGA #
        elif (mass < 0) or (mass > 100):
            raise Exception('Invalid Input.')
        resp = yield self._query('MI', mass, True, True)
        returnValue(int(resp))

    @setting(412, 'Scan Mass Final', mass='i', returns='i')
    def massFinal(self, c, mass=None):
        """
        Set the final mass for scanning.
        """
        if not mass:
            mass = ''
        #todo: check RGA #
        elif (mass < 0) or (mass > 100):
            raise Exception('Invalid Input.')
        resp = yield self._query('MF', mass, True, True)
        returnValue(int(resp))

    @setting(413, 'Scan Mass Steps', mass='i', returns='i')
    def massSteps(self, c, mass=None):
        """
        Set the number of steps per amu during scanning.
        """
        if not mass:
            mass = ''
        elif (mass < 10) or (mass > 25):
            raise Exception('Invalid Input.')
        resp = yield self._query('SA', mass, True, True)
        returnValue(int(resp))

    @setting(414, 'Scan Points', mode='s', returns='i')
    def massSteps(self, c, mode):
        """
        Get the number of points per scan in either analog or histogram mode.
        """
        resp = None
        if mode.lower() in ('a', 'analog'):
            resp = yield self._query('AP', '', False, True)
        if mode.lower() in ('h', 'histogram'):
            resp = yield self._query('HP', '', False, True)
        else:
            raise Exception('Invalid Input.')
        returnValue(int(resp))


    @setting(421, 'Scan Start', mode='s', num_scans='i', returns='')
    def massSteps(self, c, mode, num_scans):
        """
        Start a given number of scans in either analog or histogram mode.
        """
        if (num_scans < 0) or (num_scans > 255):
            raise Exception('Invalid Input.')

        if mode.lower() in ('a', 'analog'):
            yield self._query('SC', num_scans, True, False)
        if mode.lower() in ('h', 'histogram'):
            yield self._query('SC', num_scans, True, False)
        else:
            raise Exception('Invalid Input.')
        #todo: get resp


    # SINGLE MASS MEASUREMENT
    @setting(511, 'SMM Start', mass='i', returns='v')
    def massSteps(self, c, mass):
        """
        Start a single mass measurement.
        """
        #todo: check rga settings
        if (mass < 0) or (mass > 100):
            raise Exception('Invalid Input.')

        # start a single mass measurement
        msg = 'MR' + str(mass) + _SRS_EOL
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_SRS_EOL)

        # set the rods back to zero
        yield self._query('MR', 0, True, False)
        returnValue(float(resp))


    # TOTAL PRESSURE MEASUREMENT
    @setting(511, 'SMM Start', mass='i', returns='v')
    def massSteps(self, c, mass):
        """
        Start a single mass measurement.
        """
        #todo: check rga settings
        if (mass < 0) or (mass > 100):
            raise Exception('Invalid Input.')

        # start a single mass measurement
        msg = 'MR' + str(mass) + _SRS_EOL
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_SRS_EOL)

        # set the rods back to zero
        yield self._query('MR', 0, True, False)
        returnValue(float(resp))

    # HELPER
    @inlineCallbacks
    def _query(self, chString, param, setter, getter):
        # write to the device
        if setter:
            msg = chString + str(param) + _SRS_EOL
            yield self.ser.write(msg)
            status = yield self.ser.read_line(_SRS_EOL)
            # process status byte echo for errors
            yield self._parseStatus(status)

        # get data from the device
        if getter:
            msg = chString + '?' + _SRS_EOL
            yield self.ser.write(msg)
            resp = yield self.ser.read_line(_SRS_EOL)
            returnValue(resp)

    def _parseStatus(self, status):
        """
        Parse the status byte echo from the RGA.
        """
        #todo: convert to binary array then AND the errors
        status = byte(status)
        PS_ERR = status & 0x40
        DET_ERR = status & 0x30
        pass


if __name__ == "__main__":
    from labrad import util
    util.runServer(RGA_Server())
