from ast import literal_eval
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.labrad_client.registry_gui import RegistryGUI
# todo: duplicate context when interacting with editor widget so things can be done while we move away
# todo: simplify confusing web of signals


class RegistryClient(GUIClient):
    """
    Displays all connections to the LabRAD manager
    as well as their documentation.
    """

    name = 'Registry Client'
    servers = {'reg': 'Registry'}
    menuCreate = False

    def getgui(self):
        if self.gui is None:
            self.gui = RegistryGUI(self)
        return self.gui

    def initClient(self):
        # create directory holder
        self.directory_list = ["Home"]

    @inlineCallbacks
    def initData(self):
        # cd into root directory
        yield self.reg.cd('')
        yield self.changeDirectory('...')

    def initGUI(self):
        self.gui.browserWidget.changeDirectory.connect(lambda _dirname: self.changeDirectory(_dirname))
        self.gui.browserWidget.removeDirectory.connect(lambda _dirname: self.removeDirectory(_dirname))
        self.gui.browserWidget.refreshDirectory.connect(lambda: self.displayDirectory())
        self.gui.browserWidget.openKey.connect(lambda _keyname: self.openKey(_keyname))
        self.gui.browserWidget.removeKey.connect(lambda _keyname: self.removeKey(_keyname))

        self.gui.editorWidget.createDirectorySignal.connect(lambda _dirname, tmp1: self.makeDirectory(_dirname, tmp1))
        self.gui.editorWidget.createKeySignal.connect(lambda _keyname, _value, tmp1: self.makeKey(_keyname, _value, tmp1))

    @inlineCallbacks
    def displayDirectory(self):
        """
        Displays the current directory in the GUI
        """
        directories, keys = yield self.reg.dir()
        self.gui.browserWidget.set(self.directory_list, directories, keys)


    # SLOTS
    @inlineCallbacks
    def changeDirectory(self, directoryname):
        """
        CDs to the given registry directory and updates the GUI.
        Arguments:
            directoryname (str): the name of the directory to CD into.
                                    None causes a refresh.
                                    '...' goes up one directory.
        """
        # change directory
        if directoryname == '...':
            # go up a directory
            yield self.reg.cd(1)
            # remove current directory from directory list
            if len(self.directory_list) > 1:
                self.directory_list.pop()
        elif directoryname is not None:
            self.directory_list.append(directoryname)
            yield self.reg.cd(directoryname)

        # update the GUI
        yield self.displayDirectory()

    @inlineCallbacks
    def makeDirectory(self, directoryname, tmparg):
        """
        Makes a subdirectory in the current directory and updates the GUI.
        Arguments:
            directoryname (str): the name of the directory to create.
        """
        yield self.reg.mkdir(directoryname)
        yield self.displayDirectory()

    @inlineCallbacks
    def removeDirectory(self, directoryname):
        """
        Removes a subdirectory from the current registry directory and updates the GUI.
        Arguments:
            directoryname (str): the name of the directory to remove.
        """
        try:
            yield self.reg.rmdir(directoryname)
            yield self.displayDirectory()
        except Exception as e:
            print('Error in removeDirectory: {}'.format(e))

    @inlineCallbacks
    def openKey(self, keyname):
        """
        Opens a key for viewing/editing in the GUI.
        """
        value = yield self.reg.get(keyname)
        self.gui.editorWidget.openKey(keyname, value, self.directory_list)

    @inlineCallbacks
    def makeKey(self, keyname, value, tmparg):
        """
        Removes a key from the current registry directory and updates the GUI.
        """
        # process string into literals
        try:
            value = literal_eval(value)
        except Exception as e:
            print("Error in makeKey (unable to process value): {}".format(e))
            raise
        try:
            yield self.reg.set(keyname, value)
            yield self.displayDirectory()
        except Exception as e:
            print("Error in makeKey (unable to set value): {}".format(e))

    @inlineCallbacks
    def removeKey(self, keyname):
        """
        Removes a key from the current registry directory and updates the GUI.
        """
        yield self.reg.del_(keyname)
        yield self.displayDirectory()


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(RegistryClient)
