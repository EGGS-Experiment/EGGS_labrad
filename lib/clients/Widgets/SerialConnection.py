from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFrame


class SerialConnection(QFrame):

    def setupUi(self):
        self.resize(315, 95)
        self.setWindowTitle("Device")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.widget = QtWidgets.QWidget(self)
        self.widget.setGeometry(QtCore.QRect(0, 10, 314, 80))
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.device_label = QtWidgets.QLabel(self.widget)
        self.device_label.setText("Device")
        font = QtGui.QFont()
        font.setPointSize(18)
        self.device_label.setFont(font)
        self.device_label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout_3.addWidget(self.device_label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.node_layout = QtWidgets.QVBoxLayout()
        self.node_label = QtWidgets.QLabel(self.widget)
        self.node_label.setText("Node")
        self.node_layout.addWidget(self.node_label)
        self.node = QtWidgets.QComboBox(self.widget)
        self.node_layout.addWidget(self.node)
        self.horizontalLayout.addLayout(self.node_layout)
        self.port_layout = QtWidgets.QVBoxLayout()
        self.port_label = QtWidgets.QLabel(self.widget)
        self.port_label.setText("Port")
        self.port_layout.addWidget(self.port_label)
        self.port = QtWidgets.QComboBox(self.widget)
        self.port_layout.addWidget(self.port)
        self.horizontalLayout.addLayout(self.port_layout)
        self.connect = QtWidgets.QPushButton(self.widget)
        self.connect.setText("Connect")
        self.horizontalLayout.addWidget(self.connect)
        self.disconnect = QtWidgets.QPushButton(self.widget)
        self.disconnect.setText("Disconnect")
        self.horizontalLayout.addWidget(self.disconnect)
        self.verticalLayout_3.addLayout(self.horizontalLayout)


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(SerialConnection)