# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QApplication, QFrame, QCheckBox, QLabel,\
    QSpinBox, QDoubleSpinBox, QPushButton, QPlainTextEdit

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)

class RGA_UI(QWidget):
    def setupUi(self):
        Form = self
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(400, 300)
        self.frame = QFrame(Form)
        self.frame.setGeometry(QtCore.QRect(10, 10, 381, 281))
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.rga_filament_checkbox = QCheckBox(self.frame)
        self.rga_filament_checkbox.setGeometry(QtCore.QRect(200, 80, 91, 21))
        font = QFont()
        font.setPointSize(8)
        self.rga_filament_checkbox.setFont(font)
        self.rga_filament_checkbox.setTristate(False)
        self.rga_filament_checkbox.setObjectName(_fromUtf8("rga_filament_checkbox"))
        self.label_2 = QLabel(self.frame)
        self.label_2.setGeometry(QtCore.QRect(200, 180, 171, 21))
        font = QFont()
        font.setPointSize(8)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QLabel(self.frame)
        self.label_3.setGeometry(QtCore.QRect(200, 110, 171, 16))
        font = QFont()
        font.setPointSize(8)
        self.label_3.setFont(font)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.rga_voltage_spinbox = QSpinBox(self.frame)
        self.rga_voltage_spinbox.setGeometry(QtCore.QRect(200, 200, 171, 41))
        font = QFont()
        font.setPointSize(12)
        self.rga_voltage_spinbox.setFont(font)
        self.rga_voltage_spinbox.setMaximum(2500)
        self.rga_voltage_spinbox.setSingleStep(200)
        self.rga_voltage_spinbox.setKeyboardTracking(False)
        self.rga_voltage_spinbox.setObjectName(_fromUtf8("rga_voltage_spinbox"))
        self.label = QLabel(self.frame)
        self.label.setGeometry(QtCore.QRect(10, 10, 211, 21))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.rga_id_button = QPushButton(self.frame)
        self.rga_id_button.setGeometry(QtCore.QRect(200, 40, 81, 31))
        self.rga_id_button.setObjectName(_fromUtf8("rga_id_button"))
        self.rga_mass_lock_spinbox = QDoubleSpinBox(self.frame)
        self.rga_mass_lock_spinbox.setGeometry(QtCore.QRect(200, 130, 171, 41))
        font = QFont()
        font.setPointSize(12)
        self.rga_mass_lock_spinbox.setFont(font)
        self.rga_mass_lock_spinbox.setMaximum(250.0)
        self.rga_mass_lock_spinbox.setSingleStep(0.5)
        self.rga_mass_lock_spinbox.setKeyboardTracking(False)
        self.rga_mass_lock_spinbox.setProperty("value", 0.0)
        self.rga_mass_lock_spinbox.setObjectName(_fromUtf8("rga_mass_lock_spinbox"))
        self.rga_hv_button = QPushButton(self.frame)
        self.rga_hv_button.setGeometry(QtCore.QRect(200, 240, 171, 31))
        self.rga_hv_button.setObjectName(_fromUtf8("rga_hv_button"))
        self.rga_fl_button = QPushButton(self.frame)
        self.rga_fl_button.setGeometry(QtCore.QRect(290, 70, 81, 31))
        self.rga_fl_button.setObjectName(_fromUtf8("rga_fl_button"))
        self.rga_read_buffer_button = QPushButton(self.frame)
        self.rga_read_buffer_button.setGeometry(QtCore.QRect(10, 40, 91, 31))
        self.rga_read_buffer_button.setObjectName(_fromUtf8("rga_read_buffer_button"))
        self.rga_buffer_text = QPlainTextEdit(self.frame)
        self.rga_buffer_text.setGeometry(QtCore.QRect(10, 80, 181, 191))
        self.rga_buffer_text.setObjectName(_fromUtf8("rga_buffer_text"))
        self.rga_clear_button = QPushButton(self.frame)
        self.rga_clear_button.setGeometry(QtCore.QRect(100, 40, 91, 31))
        self.rga_clear_button.setObjectName(_fromUtf8("rga_clear_button"))

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self):
        Form = self
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.rga_filament_checkbox.setText(_translate("Form", "Filament", None))
        self.label_2.setText(_translate("Form", "Electronmultiplier Voltage (V)", None))
        self.label_3.setText(_translate("Form", "Mass Lock (AMU)", None))
        self.label.setText(_translate("Form", "RGA Client", None))
        self.rga_id_button.setText(_translate("Form", "ID?", None))
        self.rga_hv_button.setText(_translate("Form", "hv?", None))
        self.rga_fl_button.setText(_translate("Form", "fl?", None))
        self.rga_read_buffer_button.setText(_translate("Form", "Read Buffer", None))
        self.rga_clear_button.setText(_translate("Form", "Clear", None))

if __name__=="__main__":
    import sys
    app = QApplication(sys.argv)
    client = RGA_UI()
    client.setupUi()
    client.show()
    app.exec_()