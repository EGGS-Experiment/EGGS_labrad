import os
import syntax
from functools import partial
from EGGS_labrad import config

from PyQt5.QtWidgets import QMainWindow, QPushButton, QWidget, QHBoxLayout,\
                            QVBoxLayout, QComboBox, QPlainTextEdit, QFileDialog


class CONFIG_EDITOR(QMainWindow):
    """
    Used to edit configuration files.
    """

    def __init__(self, reactor, clipboard=None, cxn=None, parent=None):
        super(CONFIG_EDITOR, self).__init__(parent)
        self.reactor = reactor
        self.current_file = None
        config_folder = os.path.dirname(config.__file__)
        self.get_config_files([config_folder])
        self.initUI()

    def get_config_files(self, folders='.'):
        # finds all config files in folder
        self.config_path_list = []
        self.config_file_list = []
        for folder in folders:
            for (paths, dirs, files) in os.walk(folder):
                for file in files:
                    # check if filename contains string 'config'
                    if ('config' in file or 'Config' in file or 'CONFIG' in file) \
                            and '.py' in file \
                            and 'example' not in file \
                            and 'sample' not in file \
                            and '.pyc' not in file \
                            and '.jar' not in file \
                            and '.py~' not in file \
                            and '.swp' not in file \
                            and '.git' not in paths:
                        self.config_path_list.append(paths)
                        self.config_file_list.append(file)

    def initUI(self):
        newAction = QPushButton('New')
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Create new file')
        newAction.pressed.connect(self.newFile)

        saveAction = QPushButton('Save')
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save current file')
        saveAction.pressed.connect(self.saveFile)
        
        openAction = QPushButton('Open')
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open a file')
        openAction.pressed.connect(partial(self.openFile, None))
        
        buttonWidget = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(newAction)
        buttons_layout.addWidget(saveAction)
        buttons_layout.addWidget(openAction)
        buttonWidget.setLayout(buttons_layout)
        
        self.comboBoxWidget = QComboBox()
        self.comboBoxWidget.addItem('Choose a file')
        for k, path in sorted(zip(self.config_file_list, self.config_path_list)):
            self.comboBoxWidget.addItem(os.path.join(path, k))

        self.comboBoxWidget.currentIndexChanged.connect(self.open_config_file)

        #self.text = QtWidgets.QTextEdit(self)
        self.text = QPlainTextEdit(self)

        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('Config Editor')
        
        centralWidget = QWidget()
        mylayout = QVBoxLayout()
        mylayout.addWidget(buttonWidget)
        mylayout.addWidget(self.comboBoxWidget)
        mylayout.addWidget(self.text)
        centralWidget.setLayout(mylayout)
        self.setCentralWidget(centralWidget)

        return
        

    def open_config_file(self, current_index):
        full_filename = self.comboBoxWidget.currentText()
        #full_filename = os.path.join(path, filename)
        self.openFile(full_filename)

    def newFile(self):
        self.text.clear()
        self.current_file = None
        self.comboBoxWidget.setCurrentIndex(0)

    def saveFile(self):
        print(self.current_file)
        to_save_filename = None
        if self.current_file is None:
            # dialog appears only for non-config files
            to_save_filename = QFileDialog.getSaveFileName(self, 'Save File', os.getenv('HOME'))[0]
            self.current_file = to_save_filename
        else:
            to_save_filename = self.current_file

        with open(to_save_filename, 'w') as f:
            filedata = self.text.toPlainText()
            f.write(filedata)
            f.close()

    def openFile(self, filename=None):
        # print('filename: ' + str(filename))
        if filename == "Choose a file":
            self.current_file = None
            self.text.clear()
            return
        elif filename is None:
            filename = QFileDialog.getOpenFileName(self, 'Open File', os.getenv('HOME'))

        try:
            f = open(filename, 'r')
            filedata = f.read()
            highlight = syntax.PythonHighlighter(self.text.document())
            self.text.setPlainText(filedata)
            self.text.show()

            self.current_file = filename
            f.close()            
        except Exception as e:
            return
         
    def closeEvent(self, event):
        #self.reactor.stop()
        if self.reactor.running:
            self.reactor.stop()
        return
    

if __name__ == '__main__':
    from EGGS_labrad.clients import runClient
    runClient(CONFIG_EDITOR)

