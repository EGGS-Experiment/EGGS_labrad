"""
### BEGIN NODE INFO
[info]
name = multiplexerserver
version = 1.0
description =
instancename = multiplexerserver

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue
import ctypes
from twisted.internet import reactor

UPDATEEXP = 122387
CHANSIGNAL = 122485
FREQSIGNAL = 122456
LOCKSIGNAL = 112456
OUTPUTCHANGED = 121212
PIDVOLTAGE = 902484
CHANNELLOCK = 282388
AMPCHANGED = 142308
UPDATEPATTERN = 462916


class MultiplexerServer(LabradServer):
    """
    Multiplexer server for WS-U wavelength meter.

    A DLL is required to run this server.  See initServer for the path location
    for the library.
    """
    name = 'multiplexerserver'

    # Set up signals to be sent to listeners
    channel_text = 'signal: selected channels changed'
    measuredchanged = Signal(CHANSIGNAL, channel_text, '(ib)')
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(iv)')
    updateexp = Signal(UPDATEEXP, 'signal: update exp', '(ii)')
    lockchanged = Signal(LOCKSIGNAL, 'signal: lock changed', 'b')
    outputchanged = Signal(OUTPUTCHANGED, 'signal: output changed', 'b')
    voltage_text = 'signal: pidvoltage changed'
    pidvoltagechanged = Signal(PIDVOLTAGE, voltage_text, '(iv)')
    channellock = Signal(CHANNELLOCK, 'signal: channel lock changed', '(wwb)')
    ampchanged = Signal(AMPCHANGED, 'signal: amplitude changed', '(wv)')
    patternchanged = Signal(UPDATEPATTERN, 'signal: pattern changed', '(i*v)')
    
    def initServer(self):

        # load wavemeter dll file for use of API functions self.d and self.l
        # are dummy c_types for unused wavemeter functions

        dll_path = "C:\Windows\System32\wlmData.dll"
        self.wmdll = ctypes.windll.LoadLibrary(dll_path)
        self.d = ctypes.c_double(0)
        self.l = ctypes.c_long(0)
        self.b = ctypes.c_bool(0)

        self.set_pid_variables()

        # Getting the amplitude in the GetAmplitudeNum function can
        # return the max, min, and average of the interference pattern
        self.AmplitudeMin = ctypes.c_long(0)
        self.AmplitudeMax = ctypes.c_long(2)
        self.AmplitudeAvg = ctypes.c_long(4)
                
        self.set_dll_variables()
        
        self.WavemeterVersion = self.wmdll.GetWLMVersion(ctypes.c_long(1))

        self.pattern1_ptr = None
        self.set_interferometer_pattern_variables()

        self.listeners = set()

        self.measureChan()

        
        

    def set_pid_variables(self):
        """
        Each variable that can be changed (P,I,D,etc..) in the
        SetPIDSettings function is assigned a constant which must be
        passed to the function when calling. Below is the map.
        """
        self.PID_P = ctypes.c_long(1034)
        self.PID_I = ctypes.c_long(1035)
        self.PID_D = ctypes.c_long(1036)
        self.PID_dt = ctypes.c_long(1060)
        self.PIDConstdt = ctypes.c_long(1059)
        self.DeviationSensitivityFactor = ctypes.c_long(1037)
        self.DeviationSensitivityDimension = ctypes.c_long(1040)
        self.DeviationUnit = ctypes.c_long(1041)
        self.DeviationPolarity = ctypes.c_long(1038)
        self.DeviationChannel = ctypes.c_long(1063)
        self.UseFrequencyUnits = ctypes.c_long(2)

    def set_dll_variables(self):
        """
        Allocate c_types for dll functions.
        """
        self.wmdll.GetActiveChannel.restype = ctypes.c_long
        self.wmdll.GetAmplitudeNum.restype = ctypes.c_long
        self.wmdll.GetDeviationMode.restype = ctypes.c_bool
        self.wmdll.GetDeviationSignalNum.restype = ctypes.c_double
        self.wmdll.GetExposureNum.restype = ctypes.c_long
        self.wmdll.GetFrequencyNum.restype = ctypes.c_double
        self.wmdll.GetPIDCourseNum.restype = ctypes.c_long
        self.wmdll.GetSwitcherMode.restype = ctypes.c_long
        self.wmdll.GetSwitcherSignalStates.restype = ctypes.c_long
        self.wmdll.GetChannelsCount.restype = ctypes.c_long
        self.wmdll.GetPIDSetting.restype = ctypes.c_long
        self.wmdll.GetWLMVersion.restype = ctypes.c_long
        self.wmdll.GetPatternDataNum.restype = ctypes.c_long

        self.wmdll.SetDeviationMode.restype = ctypes.c_long
        self.wmdll.SetDeviationSignalNum.restype = ctypes.c_double
        self.wmdll.SetExposureNum.restype = ctypes.c_long
        self.wmdll.SetPIDCourseNum.restype = ctypes.c_long
        self.wmdll.SetSwitcherSignalStates.restype = ctypes.c_long
        self.wmdll.SetSwitcherMode.restype = ctypes.c_long
        self.wmdll.SetDeviationSignal.restype = ctypes.c_long
        self.wmdll.SetPIDSetting.restype = ctypes.c_long
        self.wmdll.SetActiveChannel.restype = ctypes.c_long

    def set_interferometer_pattern_variables(self):
        self.wmdll.SetPattern(ctypes.c_long(0), ctypes.c_long(1))
        length0 = self.wmdll.GetPatternItemCount(ctypes.c_long(0))
        ref0 = (ctypes.c_long * length0)()
        self.pattern1_ptr = ctypes.cast(ref0, ctypes.POINTER(ctypes.c_ulong))        
        # use in future if want second interferometer
        #self.wmdll.SetPattern(ctypes.c_long(1), ctypes.c_long(1))
        #length1 = self.wmdll.GetPatternItemCount(ctypes.c_long(1))
        #ref1 = (ctypes.c_long * length1)()
        #self.pattern2_ptr = ctypes.cast(ref1, ctypes.POINTER(ctypes.c_ulong))
        
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(1, "check_wlm_running")
    def instance(self, c):
        instance = self.wmdll.Instantiate
        instance.restype = ctypes.c_long
        RFC = ctypes.c_long(-1)
        # RFC, reason for call, used to check if wavemeter is running
        # (in wavemeter .h library)
        status = yield instance(RFC, self.l, self.l, self.l)
        returnValue(status)

    # Set functions

    @setting(93, "set_active_channel", chan='w')
    def set_active_channel(self, c, chan):
        chan_c = ctypes.c_long(chan)
        yield self.wmdll.SetActiveChannel(ctypes.c_long(1), self.l, chan_c, self.l)

    @setting(10, "set_exposure_time", chan='i', ms='i')
    def set_exposure_time(self, c, chan, ms):
        notified = self.getOtherListeners(c)
        ms_c = ctypes.c_long(ms)
        chan_c = ctypes.c_long(chan)
        yield self.wmdll.SetExposureNum(chan_c, 1,  ms_c)
        self.updateexp((chan, ms), notified)

    @setting(11, "set_lock_state", state='b')
    def set_lock_state(self, c, state):
        """ Turns on PID regulation for all channels. Must be on
        for individual channel locking to work."""
        notified = self.getOtherListeners(c)
        state_c = ctypes.c_bool(state)
        yield self.wmdll.SetDeviationMode(state_c)
        self.lockchanged(state, notified)

    @setting(12, "set_switcher_mode", mode='b')
    def set_switcher_mode(self, c, mode):
        """ Allows measuring of multiple channels with multiplexer.
        Should always be set to on."""
        mode_c = ctypes.c_long(mode)
        yield self.wmdll.SetSwitcherMode(mode_c)

    @setting(13, "set_switcher_signal_state", chan='i', state='b')
    def set_switcher_signal_state(self, c, chan, state):
        """ Turns on and off individual channel measurement"""
        notified = self.getOtherListeners(c)
        chan_c = ctypes.c_long(chan)
        state_c = ctypes.c_long(state)
        yield self.wmdll.SetSwitcherSignalStates(chan_c, state_c,
                                                 ctypes.c_long(1))

        self.measuredchanged((chan, state), notified)

    @setting(14, "set_pid_course", dacPort='w', course='v')
    def set_pid_course(self, c, dacPort, course):
        """Set reference frequency in THz for the PID control"""
        chan_c = ctypes.c_long(dacPort)
        course_c = ctypes.c_char_p('=' + str(course))
        yield self.wmdll.SetPIDCourseNum(chan_c, course_c)

    @setting(15, "set_dac_voltage", dacPort='i', value='v')
    def set_dac_voltage(self, c, dacPort, value):
        """Sets voltage of specified DAC channel in V. Can only be used
        when all PID control is off: set_lock_state = 0"""
        chan_c = ctypes.c_long(dacPort)
        # convert Volts to mV
        value = value*1000
        value_c = ctypes.c_double(value)
        yield self.wmdll.SetDeviationSignalNum(chan_c, value_c)

    @setting(16, "set_wlm_output", output='b')
    def set_wlm_output(self, c, output):
        """Start or stops wavemeter
        """
        notified = self.getOtherListeners(c)
        if output is True:
            yield self.wmdll.Operation(2)
        else:
            yield self.wmdll.Operation(0)
        self.outputchanged(output, notified)

    @setting(17, "set_pid_p", dacPort='w', P='v')
    def set_pid_p(self, c, dacPort, P):
        """Sets the P PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_double(P)
        yield self.wmdll.SetPIDSetting(self.PID_P, port_c, self.l, value)

    @setting(18, "set_pid_i", dacPort='w', I='v')
    def set_pid_i(self, c, dacPort, I):
        """Sets the I PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_double(I)
        yield self.wmdll.SetPIDSetting(self.PID_I, port_c, self.l, value)

    @setting(19, "set_pid_d", dacPort='w', D='v')
    def set_pid_d(self, c, dacPort, D):
        """Sets the D PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_double(D)
        yield self.wmdll.SetPIDSetting(self.PID_D, port_c, self.l, value)

    @setting(39, "set_pid_dt", dacPort='w', dt='v')
    def set_pid_dt(self, c, dacPort, dt):
        """Sets the dt PID settings for a given DAC port."""
        if dt <= 0:
            returnValue("dt must be greater than zero")
        else:
            port_c = ctypes.c_long(dacPort)
            value = ctypes.c_double(dt)
            yield self.wmdll.SetPIDSetting(self.PID_dt, port_c, self.l, value)

    @setting(121, "set_const_dt", dacPort='w', dt='b')
    def set_const_dt(self, c, dacPort, dt):
        """Activates the dt PID settings for a given DAC port. This makes each
        dt in the integration constant as opposed to oscillating values based
        on the system time, which changes when changing wm settings."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_long(dt)
        yield self.wmdll.SetPIDSetting(self.PIDConstdt, port_c, value, self.d)

    @setting(40, "set_pid_sensitivity", dacPort='w', sensitivityFactor='v',
             sensitivityExponent='i')
    def set_pid_sensitivity(self, c, dacPort, sensitivityFactor,
                            sensitivityExponent):
        """Sets the sensitivity of the analog output for a given DAC port.
        Sensitivity = (sensitivityFactor*V)/(THz*10^[sensitivityExponent])
        sensitivityFactor range is [1,9.99]."""
        port_c = ctypes.c_long(dacPort)
        sFactor = ctypes.c_double(sensitivityFactor)
        sExponent = ctypes.c_long(sensitivityExponent)
        # Make sure the units are set to frequency
        yield self.wmdll.SetPIDSetting(self.DeviationUnit, port_c,
                                       self.UseFrequencyUnits, self.d)

        yield self.wmdll.SetPIDSetting(self.DeviationSensitivityDimension,
                                       port_c, sExponent, self.d)

        yield self.wmdll.SetPIDSetting(self.DeviationSensitivityFactor, port_c,
                                       self.l, sFactor)

    @setting(41, "set_pid_polarity", dacPort='w', polarity='i')
    def set_pid_polarity(self, c, dacPort, polarity):
        """Sets the polarity for a given DAC port. Allowed values are +/- 1."""
        if polarity == 1 or polarity == -1:
            port_c = ctypes.c_long(dacPort)
            value = ctypes.c_long(polarity)
            yield self.wmdll.SetPIDSetting(self.DeviationPolarity, port_c,
                                           value, self.d)

        else:
            returnValue("Polarity must be +/- 1")

    @setting(42, "set_channel_lock", dacPort='w', waveMeterChannel='w',
             lock='b')
    def set_channel_lock(self, c, dacPort, waveMeterChannel, lock):
        """Locks a wavemeter channel to a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        chan_c = ctypes.c_long(waveMeterChannel)

        # Check to ensure a valid PID Course number is set, otherwise
        # trying to lock a channel turns off lock to main PID lock switch

        course_c = ctypes.create_string_buffer(1024)
        yield self.wmdll.GetPIDCourseNum(port_c, ctypes.pointer(course_c))
        course = float(course_c.value)
        if self.WavemeterVersion == 1312:
            returnValue("Version of WLM does not support individual locking")
        if course <= 0:
            returnValue("Set PID Course to a valid number")
        else:
            notified = self.getOtherListeners(c)
            if lock == 1:
                yield self.wmdll.SetPIDSetting(self.DeviationChannel, port_c,
                                               chan_c, self.d)

            elif lock == 0:
                yield self.wmdll.SetPIDSetting(self.DeviationChannel, port_c,
                                               ctypes.c_long(0), self.d)

            self.channellock((dacPort, waveMeterChannel, lock), notified)

    # Get Functions

    @setting(20, "get_amplitude", chan='w', returns='v')
    def get_amplitude(self, c, chan):
        chan_c = ctypes.c_long(chan)
        amp = yield self.wmdll.GetAmplitudeNum(chan_c, self.AmplitudeMax,
                                               self.l)

        self.ampchanged((chan, amp))
        returnValue(amp)

    @setting(21, "get_exposure", chan='i', returns='i')
    def get_exposure(self, c, chan):
        chan_c = ctypes.c_long(chan)
        exp = yield self.wmdll.GetExposureNum(chan_c, 1, self.l)
        returnValue(exp)

    @setting(22, "get_frequency", chan='i', returns='v')
    def get_frequency(self, c, chan):
        chan_c = ctypes.c_long(chan)
        freq = yield self.wmdll.GetFrequencyNum(chan_c, self.d)
        self.freqchanged((chan, freq))
        returnValue(freq)

    @setting(23, "get_lock_state", returns='b')
    def get_lock_state(self, c):
        state = yield self.wmdll.GetDeviationMode(0)
        returnValue(state)

    @setting(24, "get_switcher_mode", returns='b')
    def get_switcher_mode(self, c):
        state = yield self.wmdll.GetSwitcherMode(0)
        returnValue(bool(state))

    @setting(25, "get_output_voltage", dacPort='w', returns='v')
    def get_output_voltage(self, c, dacPort):
        """Gets the output voltage (mV) of the specified DAC channel"""
        chan_c = ctypes.c_long(dacPort)
        volts = yield self.wmdll.GetDeviationSignalNum(chan_c, self.d)
        self.pidvoltagechanged((dacPort, volts))
        returnValue(volts)

    @setting(26, "get_switcher_signal_state", chan='i', returns='b')
    def get_switcher_signal_state(self, c, chan):
        chan_c = ctypes.c_long(chan)
        use_c = ctypes.c_long(0)
        show_c = ctypes.c_long(0)
        yield self.wmdll.GetSwitcherSignalStates(chan_c, ctypes.pointer(use_c),
                                                 ctypes.pointer(show_c))

        use = bool(use_c)
        returnValue(use)

    @setting(27, "get_pid_course", dacPort='w', returns='s')
    def get_pid_course(self, c, dacPort):
        chan_c = ctypes.c_long(dacPort)
        course_c = ctypes.create_string_buffer(1024)
        yield self.wmdll.GetPIDCourseNum(chan_c, ctypes.pointer(course_c))
        value = str(course_c.value)
        returnValue(value)

    @setting(28, "get_wlm_output", returns='b')
    def get_wlm_output(self, c):
        value = yield self.wmdll.GetOperationState(ctypes.c_short(0))
        if value == 2:
            value = True
        else:
            value = False
        returnValue(value)

    @setting(29, "get_channel_lock", dacPort='w', waveMeterChannel='w',
             returns='?')
    def get_channel_lock(self, c, dacPort, waveMeterChannel):
        """ Checks if the wm channel is assigned to the DAC port, equivalent to
        that wm channel being locked. 0 means no channel assigned which is
        equivalent to unlocked."""
        if self.WavemeterVersion == 1312:
            returnValue(0)
        port_c = ctypes.c_long(dacPort)
        wmChannel = ctypes.c_long()
        yield self.wmdll.GetPIDSetting(self.DeviationChannel, port_c,
                                       ctypes.pointer(wmChannel), self.d)

        returnChannel = wmChannel.value
        if returnChannel == waveMeterChannel:
            returnValue(1)
        elif returnChannel == 0:
            returnValue(0)

    @setting(31, "get_total_channels", returns='w')
    def get_total_channels(self, c):
        count = yield self.wmdll.GetChannelsCount(ctypes.c_long(0))
        returnValue(count)

    @setting(32, "get_pid_p", dacPort='w', returns='v')
    def get_pid_p(self, c, dacPort):
        """Gets the P PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        P = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_P, port_c, self.l,
                                       ctypes.pointer(P))

        returnValue(P.value)

    @setting(33, "get_pid_i", dacPort='w', returns='v')
    def get_pid_i(self, c, dacPort):
        """Gets the I PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        I = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_I, port_c, self.l,
                                       ctypes.pointer(I))

        returnValue(I.value)

    @setting(34, "get_pid_d", dacPort='w', returns='v')
    def get_pid_d(self, c, dacPort):
        """Gets the D PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        D = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_D, port_c, self.l,
                                       ctypes.pointer(D))

        returnValue(D.value)

    @setting(35, "get_pid_dt", dacPort='w', returns='v')
    def get_pid_dt(self, c, dacPort):
        """Gets the dt PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        dt = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_dt, port_c, self.l,
                                       ctypes.pointer(dt))

        returnValue(dt.value)

    @setting(122, "get_const_dt", dacPort='w', returns='i')
    def get_const_dt(self, c, dacPort):
        """Gets the dt PID settings for a given DAC port. This makes each dt in
        the integration constant as opposed to oscillating values based on the
        system time, which changes when changing wm settings."""
        port_c = ctypes.c_long(dacPort)
        dt = ctypes.c_long()
        
        if self.WavemeterVersion == 1312:
            dummyarg = self.l
        else:
            dummyarg = self.d
            
        yield self.wmdll.GetPIDSetting(self.PIDConstdt, port_c,
                                       ctypes.pointer(dt), dummyarg)

        returnValue(dt.value)

    @setting(55, "get_pid_sensitivity", dacPort='w', returns='*v')
    def get_pid_sensitivity(self, c, dacPort):
        """Gets the PID sensitivity for a given DAC port
        [sensitivity factor, sensitivity power]."""
        port_c = ctypes.c_long(dacPort)
        sFactor = ctypes.c_double()
        sExponent = ctypes.c_long()
        
        if self.WavemeterVersion == 1312:
            dummyarg = self.l
        else:
            dummyarg = self.d
            
        yield self.wmdll.GetPIDSetting(self.DeviationSensitivityDimension,
                                       port_c, ctypes.pointer(sExponent),
                                       dummyarg)

        yield self.wmdll.GetPIDSetting(self.DeviationSensitivityFactor, port_c,
                                       self.l, ctypes.pointer(sFactor))

        returnValue([sFactor.value, sExponent.value])

    @setting(36, "get_pid_polarity", dacPort='w', returns='i')
    def get_pid_polarity(self, c, dacPort):
        """Gets the polarity for a given DAC port. Allowed values are +/- 1."""
        port_c = ctypes.c_long(dacPort)
        polarity = ctypes.c_long()
        
        if self.WavemeterVersion == 1312:
            dummyarg = self.l
        else:
            dummyarg = self.d
            
        yield self.wmdll.GetPIDSetting(self.DeviationPolarity, port_c,
                                       ctypes.pointer(polarity), dummyarg)

        returnValue(polarity.value)
        
    @setting(37, "get_wavemeter_pattern", chan='i', returns = '*2v')
    def get_wavemeter_pattern(self, c, chan):
        """
        Gets the wavemeter pattern. Broadcast signal with results.

        """
        yield self.wmdll.GetPatternDataNum(ctypes.c_ulong(chan),\
                    ctypes.c_long(0), self.pattern1_ptr)
        # use every other data point
        IF1 = self.pattern1_ptr[:1024:2]
        self.patternchanged((chan, IF1))
        returnValue([IF1])

    def measureChan(self):
        # TODO: Improve this with a looping call
        reactor.callLater(0.1, self.measureChan)
        count = self.wmdll.GetChannelsCount(ctypes.c_long(0))
        for chan in range(count):
            if self.get_switcher_signal_state(self, chan + 1):
                self.get_frequency(self, chan + 1)
                self.get_output_voltage(self, chan + 1)
                self.get_amplitude(self, chan + 1)
                self.get_wavemeter_pattern(self, chan + 1)


if __name__ == "__main__":
    from labrad import util
    util.runServer(MultiplexerServer())
