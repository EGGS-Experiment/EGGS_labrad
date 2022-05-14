__all__ = [
    "QDetachableTabWidget", "TextChangingButton", 'Lockswitch', 'SerialConnection_Client',
    'QSerialConnection', 'QCustomProgressBar', 'QCustomSlideIndicator', 'QCustomGroupBox',
    'QClientHeader', 'QClientMenuHeader', 'QChannelHolder', 'QInitializePlaceholder'
]


from .QDetachableTab import QDetachableTabWidget
from .QCustomTextChangingButton import TextChangingButton, Lockswitch
from .QSerialConnection import QSerialConnection, SerialConnection_Client
from .QCustomProgressBar import QCustomProgressBar
from .QCustomSlideIndicator import QCustomSlideIndicator
from .QCustomGroupBox import QCustomGroupBox, QChannelHolder
from .QClientHeader import QClientHeader
from .QClientMenuHeader import QClientMenuHeader
from .QInitializePlaceholder import QInitializePlaceholder
# todo: create record button widget
