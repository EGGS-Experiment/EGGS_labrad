from channelConfiguration import channelConfiguration as ChConfig
from ddsConfiguration import ddsConfiguration as ddsConfig
# TODO: Does this really need to be imported, looks unused
# Double checked this by searching for remoteChannel in the project
from remoteChannel import remoteChannel


class hardwareConfiguration(object):
    channelTotal = 32
    timeResolution = '40.0e-9'  # seconds
    timeResolvedResolution = 10.0e-9
    maxSwitches = 1022
    # duration of advanceDDS and resetDDS TTL pulses in units of timesteps
    resetstepDuration = 2
    collectionTimeRange = (0.010, 5.0)  # range for normal pmt counting
    sequenceTimeRange = (0.0, 85.0)  # range for duration of pulse sequence
    isProgrammed = False
    sequenceType = None  # none for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal'  # default PMT mode
    # default counting rates
    collectionTime = {'Normal': 0.100, 'Differential': 0.100}
    okDeviceID = 'Pulser'
    okDeviceFile = 'pulser_2013_06_05.bit'
    lineTriggerLimits = (0, 15000)  # values in microseconds
    secondPMT = False
    DAC = False

    # name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    channelDict = {}
    channelDict['866DP'] = ChConfig(12, False, True, False, True)
    channelDict['crystallization'] = ChConfig(1, True, False, False, False)
    channelDict['bluePI'] = ChConfig(2, True, False, True, False)
    channelDict['camera'] = ChConfig(5, False, False, True, True)
    channelDict['coil_dir'] = ChConfig(6, False, False, True, True)
    # ------------INTERNAL CHANNEgiLS----------------------------------------#
    channelDict['Internal866'] = ChConfig(0, False, False, False, False)
    channelDict['DiffCountTrigger'] = ChConfig(16, False, False, False, False)
    channelDict['TimeResolvedCount'] = ChConfig(17, False, False, False, False)
    channelDict['AdvanceDDS'] = ChConfig(18, False, False, False, False)
    channelDict['ResetDDS'] = ChConfig(19, False, False, False, False)
    channelDict['ReadoutCount'] = ChConfig(20, False, False, False, False)

    # address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
    ddsDict = {}
    ddsDict['866DP'] = ddsConfig(0, (70.0, 90.0), (-63.0, -5.0), 80.0, -33.0)
    ddsDict['global397'] = ddsConfig(1, (70.0, 100.0), (-63.0, -12.0), 90.0, -33.0)
    ddsDict['radial'] = ddsConfig(2, (90.0, 130.0), (-63.0, -12.0), 110.0, -63.0)
#   ddsDict['radial'] = ddsConfig(2, (74.0, 74.0), (-63.0, -5.0), 74.0, -63.0)
    ddsDict['854DP'] = ddsConfig(3, (70.0, 90.0), (-63.0, -4.0), 80.0, -33.0)
    ddsDict['729DP'] = ddsConfig(4, (150.0, 250.0), (-63.0, -5.0), 220.0, -33.0)

    remoteChannels = {}
