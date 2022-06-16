"""
Contains functions useful for LabRAD clients.
"""
from PyQt5.QtWidgets import QApplication

__all__ = ["runGUI", "runClient", "createTrunk", "wav2RGB"]


# run functions
def runGUI(client, *args, **kwargs):
    """
    Runs a LabRAD GUI file written using PyQt5.
    Passes any constructor arguments to the client class.
    """
    from os import _exit

    # widgets require a QApplication to run
    app = QApplication([])

    # instantiate gui
    gui = client(*args, **kwargs)

    # set up UI if needed
    try:
        gui.setupUi()
    except Exception as e:
        print('No need to setup UI')
    # run GUI file
    gui.show()
    _exit(app.exec())


def runClient(client, *args, **kwargs):
    """
    Runs a LabRAD client written using PyQt5.
    Passes any constructor arguments to the client class.
    """
    # widgets require a QApplication to run
    app = QApplication([])

    # reactor may already be installed
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(e)
        raise e

    # instantiate client with a reactor
    from twisted.internet import reactor
    client_tmp = client(reactor, *args, **kwargs)

    # show client
    if hasattr(client_tmp, 'show'):
        client_tmp.show()
    elif hasattr(client_tmp, 'gui'):
        gui_tmp = client_tmp.gui
        if hasattr(gui_tmp, 'show'):
            client_tmp.gui.show()

    # start reactor
    reactor.callWhenRunning(app.exec)
    reactor.addSystemEventTrigger('after', 'shutdown', client_tmp.close)
    reactor.runReturn()

    # close client on exit
    try:
        client_tmp.close()
    except Exception as e:
        print(e)


# recording functions
def createTrunk(name):
    """
    Creates a trunk name for data in data_vault corresponding
    to the current date.

    Arguments:
        name    (str)   : the name of the client.
    Returns:
                (*str)  : the trunk to create in data_vault.
    """
    from datetime import datetime
    date = datetime.now()

    trunk1 = '{0:d}_{1:02d}_{2:02d}'.format(date.year, date.month, date.day)
    trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(name, date.hour, date.minute)

    return ['', str(date.year), '{:02d}'.format(date.month), trunk1, trunk2]


# wav2RGB: adapted from http://codingmess.blogspot.com/2009/05/conversion-of-wavelength-in-nanometers.html
def wav2RGB(wavelength):
    """
    Converts a wavelength to RGB.
    Arguments:
        wavelength  (float)  : the wavelength (in nm).
    Returns:
                    (tuple of int, int, int): the converted RGB values.
    """
    wavelength = int(wavelength)
    R, G, B, SSS = 0, 0, 0, 0

    # get RGB values
    if wavelength < 380:
        R, G, B = 1.0, 0.0, 1.0
    elif (wavelength >= 380) and (wavelength < 440):
        R = -(wavelength - 440.) / (440. - 350.)
        G, B = 0.0, 1.0
    elif (wavelength >= 440) and (wavelength < 490):
        R, B = 0.0, 1.0
        G = (wavelength - 440.) / (490. - 440.)
    elif (wavelength >= 490) and (wavelength < 510):
        R, G = 0.0, 1.0
        B = -(wavelength - 510.) / (510. - 490.)
    elif (wavelength >= 510) and (wavelength < 580):
        R = (wavelength - 510.) / (580. - 510.)
        G, B = 1.0, 0.0
    elif (wavelength >= 580) and (wavelength < 645):
        R, B = 1.0, 0.0
        G = -(wavelength - 645.) / (645. - 580.)
    elif (wavelength >= 645) and (wavelength <= 780):
        R, G, B = 1.0, 0.0, 0.0
    elif wavelength > 780:
        R, G, B = 1.0, 0.0, 0.0

    # intensity correction
    if wavelength < 380:
        SSS = 0.6
    elif (wavelength >= 380) and (wavelength < 420):
        SSS = 0.3 + 0.7 * (wavelength - 350) / (420 - 350)
    elif (wavelength >= 420) and (wavelength <= 700):
        SSS = 1.0
    elif (wavelength > 700) and (wavelength <= 780):
        SSS = 0.3 + 0.7 * (780 - wavelength) / (780 - 700)
    elif wavelength > 780:
        SSS = 0.3

    SSS *= 255
    return int(SSS * R), int(SSS * G), int(SSS * B)
