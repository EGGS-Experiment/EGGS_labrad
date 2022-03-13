from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QDoubleSpinBox, QComboBox, QCheckBox, QGridLayout


class QCustomPID(QFrame):

    def __init__(self, DACPort=0, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(DACPort)

    def makeLayout(self, DACPort):
        main_font = QFont('MS Shell Dlg 2', pointSize=16)
        main_alignment = Qt.AlignRight

        # labels
        pLabel = QLabel('P')
        iLabel = QLabel('I')
        dLabel = QLabel('D')
        dtLabel = QLabel('dt')
        factorLabel = QLabel('Factor (V)')
        exponentLabel = QLabel('THz*10^')
        polarityLabel = QLabel('Polarity')
        sensLabel = QLabel('PID Sensitivity')
        sensLabel.setAlignment(Qt.AlignCenter)
        sensLabel.setFont(main_font)

        for label in (pLabel, iLabel, dLabel, dtLabel, factorLabel, exponentLabel, polarityLabel):
            label.setFont(main_font)
            label.setAlignment(main_alignment)

        # PID control
        self.spinP = QDoubleSpinBox()
        self.spinI = QDoubleSpinBox()
        self.spinD = QDoubleSpinBox()
        self.spinDt = QDoubleSpinBox()

        for spinbox in (self.spinP, self.spinI, self.spinD, self.spinDt):
            spinbox.setFont(main_font)
            spinbox.setDecimals(3)
            spinbox.setSingleStep(0.001)
            spinbox.setRange(0, 100)
            spinbox.setKeyboardTracking(False)

        # other control elements
        self.spinFactor = QDoubleSpinBox()
        self.spinFactor.setFont(main_font)
        self.spinFactor.setDecimals(2)
        self.spinFactor.setSingleStep(0.01)
        self.spinFactor.setRange(0, 9.99)
        self.spinFactor.setKeyboardTracking(False)

        self.spinExp = QDoubleSpinBox()
        self.spinExp.setFont(main_font)
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        self.spinExp.setRange(-6, 3)
        self.spinExp.setKeyboardTracking(False)

        self.polarityBox = QComboBox(self)
        self.polarityBox.addItem("Positive")
        self.polarityBox.addItem("Negative")

        self.useDTBox = QCheckBox('Use Const dt')
        self.useDTBox.setFont(main_font)

        # set layout
        layout = QGridLayout()
        layout.minimumSize()

        layout.addWidget(pLabel, 0, 0, 1, 1)
        layout.addWidget(self.spinP, 0, 1, 1, 1)
        layout.addWidget(iLabel, 1, 0, 1, 1)
        layout.addWidget(self.spinI, 1, 1, 1, 1)
        layout.addWidget(dLabel, 2, 0, 1, 1)
        layout.addWidget(self.spinD, 2, 1, 1, 1)

        layout.addWidget(self.useDTBox, 0, 3, 1, 1)
        layout.addWidget(dtLabel, 1, 2, 1, 1)
        layout.addWidget(self.spinDt, 1, 3, 1, 1)
        layout.addWidget(polarityLabel, 2, 2, 1, 1)
        layout.addWidget(self.polarityBox, 2, 3, 1, 1)

        layout.addWidget(sensLabel, 0, 4, 1, 2)
        layout.addWidget(factorLabel, 1, 4, 1, 1)
        layout.addWidget(self.spinFactor, 1, 5, 1, 1)
        layout.addWidget(exponentLabel, 2, 4, 1, 1)
        layout.addWidget(self.spinExp, 2, 5, 1, 1)

        self.setLayout(layout)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(QCustomPID)
