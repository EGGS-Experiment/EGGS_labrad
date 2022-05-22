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
from EGGS_labrad.servers import SerialDeviceServer, PollingServer

from RGA_errors import _SRS_RGA_STATUS_QUERIES

_SRS_EOL = '\r'
_SRS_MAX_PRESSURE = 1e-5


class RGA_Server(SerialDeviceServer, PollingServer):
    """
    Talks to the SRS RGAx00 residual gas analyzer.
    All core device functions which take a numerical parameter can also accept
    "*" as input, which sets the component/function to its default value.
    """

    name = 'RGA Server'
    regKey = 'RGA Server'
    port = 'COM55'
    serNode = 'mongkok'

    timeout = WithUnit(8.0, 's')
    baudrate = 28800

    POLL_ON_STARTUP = True
    POLL_INTERVAL_ON_STARTUP = 2

    # SIGNALS
    buffer_update = Signal(999999, 'signal: buffer_update', '(ss)')


    # STARTUP
    def initServer(self):
        super().initServer()
        # RGA type
        self.m_max = 200
        self.current_to_pressure = None
        # Interlock
        self.interlock_active = True
        self.interlock_pressure = _SRS_MAX_PRESSURE

    @inlineCallbacks
    def initSerial(self, serStr, port, **kwargs):
        super().initSerial(serStr, port, **kwargs)
        # expand serial buffer size on connect
        if self.ser is not None:
            yield self.ser.buffer_size(100000)


    # STATUS
    @setting(111, 'Initialize', level='i', returns='')
    def initialize(self, c, level=0):
        """
        Initialize the RGA.
            Level 0 initialization sets up serial communications
                and checks the ECU.
            Level 1 initialization resets the RGA to its factory settings.
            Level 2 initialization activates standby mode.
        Arguments:
            level   (int)   : the level of initialization. Must be one of (0, 1, 2).
        """
        if level not in (0, 1, 2):
            raise Exception('Error: Invalid Input.')
        yield self._setter('IN', level, c)

    @setting(121, 'Errors', returns='*s')
    def errors(self, c):
        """
        Get all errors from the RGA.
        Returns:
            (*str)    : a list of active errors.
        """
        # getter
        yield self.ser.acquire()
        yield self.ser.write('ER?\r')
        error_status = yield self.ser.read_line(_SRS_EOL)
        self.ser.release()
        error_status = error_status.strip()
        # convert status response to binary
        error_status = format(int(error_status), '08b')
        error_status = error_status[::-1]
        # parse the STATUS byte for error flags
        error_list = []
        for bit_number, query_parameters in _SRS_RGA_STATUS_QUERIES.items():
            if error_status[bit_number] == '1':
                query_msg, dict_tmp = query_parameters
                # query the component-specific status register for flags
                yield self.ser.acquire()
                yield self.ser.write('{:s}?\r'.format(query_msg))
                component_register = yield self.ser.read_line(_SRS_EOL)
                self.ser.release()
                # convert component response to binary
                component_register = format(int(component_register.strip()), '08b')
                component_register = component_register[::-1]
                # parse response
                error_list_tmp = [error_msg for bit_number, error_msg in dict_tmp.items()
                                  if component_register[bit_number] == '1']
                error_list.extend(error_list_tmp)
        returnValue(error_list)

    @setting(131, 'Degas', time=['', 'i', 's'], returns='')
    def degas(self, c, time):
        """
        Degas the filament.
        Args:
            time    (int)   : the amount of time (in mintues) to degas the filament.
                                Must be in [0, 20]. Default is 3 minutes.
        # todo: test degas function
        """
        if time is not None:
            if type(time) is int:
                if time not in range(21):
                    raise Exception('Error: invalid input.')
            elif type(time) is str:
                if time != '*':
                    raise Exception('Error: invalid input.')
            yield self._setter('DG', time, c)


    # IONIZER
    @setting(211, 'Ionizer Electron Energy', energy=['', 'i', 's'], returns='i')
    def electronEnergy(self, c, energy=None):
        """
        Get/set the electron impact ionization energy.
        Arguments:
            energy  (int)   : the electron impact ionization energy (in eV).
                                Must be in [25, 105]. Default is 70.
        Returns:
                    (int)   : the electron impact ionization energy (in eV).
        """
        if energy is not None:
            if type(energy) is int:
                if (energy < 25) or (energy > 105):
                    raise Exception('Error: invalid input.')
            elif type(energy) is str:
                if energy != '*':
                    raise Exception('Error: invalid input.')
            yield self._setter('EE', energy, c)
        resp = yield self._getter('EE', c)
        returnValue(int(resp))

    @setting(212, 'Ionizer Ion Energy', energy=['', 'i', 's'], returns='i')
    def ionEnergy(self, c, energy=None):
        """
        Get/set the ion energy. This is achieved by adjusting the anode grid voltage.
        Ion energy can be one of two possible levels:
            low (represented by 0) = 8 eV
            high (represented by 1) = 12 eV
        Arguments:
            energy  (int)   : the ion energy level.
                                Must be one of (0, 1). Default is 1.
        Returns:
                    (int)   : the ion energy level.
        """
        if energy is not None:
            if type(energy) is int:
                if energy not in (0, 1):
                    raise Exception('Error: invalid input.')
            elif type(energy) is str:
                if energy != '*':
                    raise Exception('Error: invalid input.')
            yield self._setter('IE', energy, c)
        resp = yield self._getter('IE', c)
        returnValue(int(resp))

    @setting(221, 'Ionizer Filament', current=['', 'v', 's'], returns='v')
    def filament(self, c, current=None):
        """
        Get/set the ionizer filament current. Also known as electron emission current.
            The RGA has a firmware protection mode where the filament will shut off
            if the pressure exceeds a certain value.
            Note: activating the filament may heat the chamber and degas, increasing pressure.
        Arguments:
            current (float) : the ionizer filament current (in mA).
                                Must be in [0, 3.5]. Default is 1.
        Returns:
        """
        if current is not None:
            if type(current) is float:
                if (current < 0) or (current > 3.5):
                    raise Exception('Error: invalid input.')
            elif type(current) is str:
                if current != '*':
                    raise Exception('Error: invalid input.')
            yield self._setter('FL', current, c)
        resp = yield self._getter('FL', c)
        returnValue(float(resp))

    @setting(222, 'Ionizer Focus Voltage', voltage=['', 'i', 's'], returns='i')
    def focusVoltage(self, c, voltage=None):
        """
        Get/set the focus plate voltage. This is a biasing voltage which
            draws ions into the quadrupole mass filter.
        Arguments:
            voltage (int)   : the focus plate voltage (in V).
        Returns:
                    (int)   : the focus plate voltage (in V).
        """
        if voltage is not None:
            if type(voltage) is int:
                if (voltage < 0) or (voltage > 150):
                    raise Exception('Error: invalid input.')
            elif type(voltage) is str:
                if voltage != '*':
                    raise Exception('Error: invalid input.')
            yield self._setter('VF', voltage, c)
        resp = yield self._getter('VF', c)
        returnValue(int(resp))


    # DETECTOR
    @setting(311, 'Detector Calibrate', returns='')
    def calibrate(self, c):
        """
        Calibrate the detector.
        """
        yield self._setter('CA', '', c)

    @setting(312, 'Detector Noise Floor', level=['', 'i', 's'], returns='i')
    def noiseFloor(self, c, level=None):
        """
        Get/set the detector noise floor. This sets the rate and detection limits
            for ion current measurements. A lower value reduces bandwidth and increases
            accuracy, but also increases overhead and scan times.
        Arguments:
            level   (int)   :   the noise floor level.
                                    Must be in [0, 7]. Default is 4.
        Returns:
                    (int)   :   the noise floor level.
        """
        if level is not None:
            if type(level) is int:
                if (level < 0) or (level > 7):
                    raise Exception('Error: invalid input.')
            elif type(level) is str:
                if level != '*':
                    raise Exception('Error: invalid input.')
            yield self._setter('NF', level, c, False)
        resp = yield self._getter('NF', c)
        returnValue(int(resp))

    @setting(313, 'Detector CDEM', returns='b')
    def cdem(self, c):
        """
        Check whether the electron multiplier (CDEM) is available.
        Returns:
                    (bool)  :   whether a CDEM is available.
        """
        resp = yield self._getter('MO', c)
        returnValue(bool(int(resp)))

    @setting(321, 'Detector CDEM Voltage', voltage=['', 'i', 's'], returns='i')
    def cdemVoltage(self, c, voltage=None):
        """
        Get/set the electron multiplier (CDEM) voltage bias.
        Arguments:
            voltage (int)   :   the
        Returns:
                    (int)   :
        """
        if voltage is not None:
            if type(voltage) is int:
                if (voltage < 0) or (voltage > 2490):
                    raise Exception('Error: invalid input.')
            elif type(voltage) is str:
                if voltage != '*':
                    raise Exception('Error: invalid input.')
            yield self._setter('HV', voltage, c)
        resp = yield self._getter('HV', c)
        returnValue(int(resp))


    # SCANNING
    @setting(411, 'Scan Mass Initial', mass=['', 'i', 's'], returns='i')
    def massInitial(self, c, mass=None):
        """
        Get/set the initial mass for scanning.
        Arguments:
            mass    (int)   :   the initial mass (in amu).
                                    Must be in [1, M_MAX]. Default is 1.
        Returns:
                    (int)   :   the initial mass (in amu).
        """
        if mass is not None:
            if type(mass) is int:
                if (mass < 0) or (mass > self.m_max):
                    raise Exception('Error: invalid input.')
            elif type(mass) is str:
                if mass != '*':
                    raise Exception('Error: invalid input.')
            # set value
            yield self._setter('MI', mass, c, False)
        # query
        resp = yield self._getter('MI', c)
        returnValue(int(resp))

    @setting(412, 'Scan Mass Final', mass=['', 'i', 's'], returns='i')
    def massFinal(self, c, mass=None):
        """
        Get/set the final mass for scanning.
        Arguments:
            mass    (int)   :   the final mass (in amu).
                                    Must be in [1, M_MAX]. Default is M_MAX.
        Returns:
                    (int)   :   the final mass (in amu).
        """
        if mass is not None:
            if type(mass) is int:
                if (mass < 0) or (mass > self.m_max):
                    raise Exception('Error: invalid input.')
            elif type(mass) is str:
                if mass != '*':
                    raise Exception('Error: invalid input.')
            # set value
            yield self._setter('MF', mass, c, False)
        # query
        resp = yield self._getter('MF', c)
        returnValue(int(resp))

    @setting(413, 'Scan Mass Steps', steps=['', 'i', 's'], returns='i')
    def massSteps(self, c, steps=None):
        """
        Get/set the number of steps per amu during scanning.
        Arguments:
            steps   (int)   :   the number of steps per amu.
                                    Must be in range [10, 25]. Default is 10.
        Returns:
                    (int)   :   the number of steps per amu.
        """
        if steps is not None:
            if type(steps) is int:
                if (steps < 10) or (steps > 25):
                    raise Exception('Error: invalid input.')
            elif type(steps) is str:
                if steps != '*':
                    raise Exception('Error: invalid input.')
            # set value
            yield self._setter('SA', steps, c, False)
        # query
        resp = yield self._getter('SA', c)
        returnValue(int(resp))

    @setting(414, 'Scan Points', mode='s', returns='i')
    def scanPoints(self, c, mode):
        """
        Get the number of points per scan in either analog or histogram mode.
        Arguments:
            mode    (str)   : the scan mode to get points for.
                                Must be one of ('a', 'analog') or ('h', 'histogram').
        Returns:
                    (int)   :   the number of points per scan.
        """
        resp = None
        if mode.lower() in ('a', 'analog'):
            resp = yield self._getter('AP', c)
        elif mode.lower() in ('h', 'histogram'):
            resp = yield self._getter('HP', c)
        else:
            raise Exception('Error: invalid input.')
        returnValue(int(resp))

    @setting(421, 'Scan Start', mode='s', num_scans='i', returns='*2v')
    def scanStart(self, c, mode, num_scans):
        """
        Start a given number of scans in either analog or histogram mode.
        Arguments:
            mode        (str)   :   the scan mode. Can be 'a' or 'analog' for analog mode,
                                    and 'h' or 'histogram for histogram mode.
            num_scans   (int)   :   the number of scans to conduct.
        Returns:
                        (*2v)   :   [[scan amu values], [scan 1 results], [scan 2 results], ...]
        """
        # check input
        if (num_scans < 0) or (num_scans > 255):
            raise Exception('Error: invalid input.')
        # get pressure conversion factor
        sp = yield self._getter('SP', c)
        sp = 1e-13 / float(sp)
        # get initial and final masses
        mass_initial = yield self._getter('MI', c)
        mass_initial = int(mass_initial)
        mass_final = yield self._getter('MF', c)
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
            # additional 1 is for total pressure measurement, which is returned with each scan
            bytes_to_read = num_scans * 4 * (num_points + 1)
            msg = 'HS' + str(num_scans) + _SRS_EOL
        else:
            raise Exception('Error: invalid input.')
        # initiate scan
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read(bytes_to_read)
        self.ser.release()
        # parse response as 32-bit little endian signed floating point values
        current_arr = np.array([int.from_bytes(resp[i: i+4], 'little', signed=True)
                                for i in range(0, bytes_to_read, 4)])
        # multiply values by current to pressure conversion factor
        current_arr = current_arr.astype(np.float32) * sp
        # split up response into desired number of scans
        current_arr = np.array_split(current_arr, num_scans)
        # remove total pressure value
        current_arr = [array[:-1] for array in current_arr]
        # create x-axis
        amu_arr = [np.linspace(mass_initial, mass_final, num_points)]
        # combine x-axis and y-axes values into a single return
        returnArr = np.concatenate((amu_arr, current_arr), axis=0)
        returnValue(returnArr)


    # SINGLE MASS MEASUREMENT
    @setting(511, 'SMM Start', mass='i', returns='v')
    def singleMassMeasurement(self, c, mass):
        """
        Start a single mass measurement.
        Arguments:
            mass    (int)   : the mass species to measure (in amu).
        Returns:
                    (float) : the partial pressure of the mass species (in mbar).
        """
        # sanitize input
        if (mass < 0) or (mass > self.m_max):
            raise Exception('Error: invalid input.')
        # get partial pressure conversion
        st = yield self._getter('ST', c)
        st = 1e-13 / float(st)
        # start a single mass measurement
        msg = 'MR' + str(mass) + _SRS_EOL
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read(4)
        # set the rods back to zero
        yield self.ser.write('MR0\r')
        self.ser.release()
        # process and return the result
        print('text:', resp)
        if type(resp) == str:
            resp = bytes(resp, encoding='utf-8')
        current = int.from_bytes(resp, 'little', signed=True)
        returnValue(current * st)


    # TOTAL PRESSURE MEASUREMENT
    @setting(611, 'TPM Start', returns='v')
    def totalPressureMeasurement(self, c):
        """
        Start a total pressure measurement.
        Returns:
                (float) : the total pressure (in mbar).
        """
        # set the electron multiplier voltage to zero which
        # automatically enables total pressure measurement
        yield self._setter('HV', 0, c)
        # get total pressure conversion factor
        sp = yield self._getter('SP', c, c)
        sp = 1e-13 / float(sp)
        # start a total pressure measurement
        msg = 'TP?' + _SRS_EOL
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read(4)
        self.ser.release()
        # process and return result
        if type(resp) == str:
            resp = bytes(resp, encoding='utf-8')
        current = int.from_bytes(resp, 'little', signed=True)
        returnValue(current * sp)


    # INTERLOCK
    @setting(811, 'Interlock', status='b', press='v', returns='(bv)')
    def interlock(self, c, status=None, press=None):
        """
        Activates an interlock, switching off the ion pump
            and getter if pressure exceeds a given value.
            Pressure is taken from the Twistorr74 turbo pump server.
        Arguments:
            status  (bool)  : the interlock status.
            press   (float) : the maximum pressure (in mbar).
        Returns:
                    (bool)  : the interlock status.
                    (float) :  the maximum pressure (in mbar).
        """
        # empty call returns getter
        if (status is None) and (press is None):
            return (self.interlock_active, self.interlock_pressure)
        # ensure pressure is valid
        if press is None:
            pass
        elif (press < 1e-11) or (press > 1e-4):
            raise Exception('Error: invalid pressure interlock range. Must be between (1e-11, 1e-4) mbar.')
        else:
            self.interlock_pressure = press
        # set interlock parameters
        self.interlock_active = status
        return (self.interlock_active, self.interlock_pressure)


    # HELPER
    @inlineCallbacks
    def _setter(self, chString, param, c, resp=True):
        """
        Convenience function to set device parameters.
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
            #self.notifyOtherListeners(None, (chString, resp.strip()), self.buffer_update)
            self.buffer_update(('status', status))

    @inlineCallbacks
    def _getter(self, chString, c):
        """
        Convenience function to get data from the device.
        """
        # query device for parameter value
        msg = chString + '?' + _SRS_EOL
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_SRS_EOL)
        self.ser.release()
        # send out buffer response to clients
        #self.notifyOtherListeners(None, (chString, resp.strip()), self.buffer_update)
        self.buffer_update((chString, resp.strip()))
        returnValue(resp)

    @inlineCallbacks
    def _poll(self):
        """
        Polls the Twistorr74 server for pressure readout and checks the interlock.
        """
        # check interlock
        if self.interlock_active:
            try:
                # try to get twistorr74 server
                yield self.client.refresh()
                tt = yield self.client.twistorr74_server
                # switch off ion pump if pressure is above a certain value
                press_tmp = yield tt.pressure()
                if press_tmp >= self.interlock_pressure:
                    print('Error: Twistorr74 pressure reads {:.2e} mbar.'.format(press_tmp))
                    print('\tAbove threshold of {:.2e} mbar for RGA filament to be on.'.format(self.interlock_pressure))
                    print('\tShutting off the filament.')
                    try:
                        # send shutoff signal
                        yield self.filament(None, 0)
                    except Exception as e:
                        print('Error: unable to shut off filament.')
            except KeyError:
                print('Warning: Twistorr74 server not available for interlock.')
            except Exception as e:
                print('Warning: unable to read pressure from Twistorr74 server.')
                print('\tSkipping this loop.')


    # CONTEXT
    def initContext(self, c):
        """
        Initialize a new context object.
        """
        self.listeners.add(c.ID)

    def expireContext(self, c):
        """
        Remove a context object and stop polling if there are no more listeners.
        """
        self.listeners.remove(c.ID)
        if len(self.listeners) == 0:
            self.refresher.stop()
            print('Stopped polling due to lack of listeners.')

    def getOtherListeners(self, c):
        """
        Get all listeners except for the context owner.
        """
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    def notifyOtherListeners(self, context, message, f):
        """
        Notifies all listeners except the one in the given context, executing function f
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)


if __name__ == "__main__":
    from labrad import util
    util.runServer(RGA_Server())
