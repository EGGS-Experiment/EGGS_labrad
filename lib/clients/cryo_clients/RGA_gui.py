# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\barium133\Code\barium\lib\clients\gui\RGA_gui.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class RGA_UI(QtGui.QWidget):
    def setupUi(self):
        Form = self
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(400, 300)
        self.frame = QtGui.QFrame(Form)
        self.frame.setGeometry(QtCore.QRect(10, 10, 381, 281))
        self.frame.setFrameShape(QtGui.QFrame.Box)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.rga_filament_checkbox = QtGui.QCheckBox(self.frame)
        self.rga_filament_checkbox.setGeometry(QtCore.QRect(200, 80, 91, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.rga_filament_checkbox.setFont(font)
        self.rga_filament_checkbox.setTristate(False)
        self.rga_filament_checkbox.setObjectName(_fromUtf8("rga_filament_checkbox"))
        self.label_2 = QtGui.QLabel(self.frame)
        self.label_2.setGeometry(QtCore.QRect(200, 180, 171, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(self.frame)
        self.label_3.setGeometry(QtCore.QRect(200, 110, 171, 16))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_3.setFont(font)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.rga_voltage_spinbox = QtGui.QSpinBox(self.frame)
        self.rga_voltage_spinbox.setGeometry(QtCore.QRect(200, 200, 171, 41))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.rga_voltage_spinbox.setFont(font)
        self.rga_voltage_spinbox.setMaximum(2500)
        self.rga_voltage_spinbox.setSingleStep(200)
        self.rga_voltage_spinbox.setKeyboardTracking(False)
        self.rga_voltage_spinbox.setObjectName(_fromUtf8("rga_voltage_spinbox"))
        self.label = QtGui.QLabel(self.frame)
        self.label.setGeometry(QtCore.QRect(10, 10, 211, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.rga_id_button = QtGui.QPushButton(self.frame)
        self.rga_id_button.setGeometry(QtCore.QRect(200, 40, 81, 31))
        self.rga_id_button.setObjectName(_fromUtf8("rga_id_button"))
        self.rga_mass_lock_spinbox = QtGui.QDoubleSpinBox(self.frame)
        self.rga_mass_lock_spinbox.setGeometry(QtCore.QRect(200, 130, 171, 41))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.rga_mass_lock_spinbox.setFont(font)
        self.rga_mass_lock_spinbox.setMaximum(250.0)
        self.rga_mass_lock_spinbox.setSingleStep(0.5)
        self.rga_mass_lock_spinbox.setKeyboardTracking(False)
        self.rga_mass_lock_spinbox.setProperty("value", 0.0)
        self.rga_mass_lock_spinbox.setObjectName(_fromUtf8("rga_mass_lock_spinbox"))
        self.rga_hv_button = QtGui.QPushButton(self.frame)
        self.rga_hv_button.setGeometry(QtCore.QRect(200, 240, 171, 31))
        self.rga_hv_button.setObjectName(_fromUtf8("rga_hv_button"))
        self.rga_fl_button = QtGui.QPushButton(self.frame)
        self.rga_fl_button.setGeometry(QtCore.QRect(290, 70, 81, 31))
        self.rga_fl_button.setObjectName(_fromUtf8("rga_fl_button"))
        self.rga_read_buffer_button = QtGui.QPushButton(self.frame)
        self.rga_read_buffer_button.setGeometry(QtCore.QRect(10, 40, 91, 31))
        self.rga_read_buffer_button.setObjectName(_fromUtf8("rga_read_buffer_button"))
        self.rga_buffer_text = QtGui.QPlainTextEdit(self.frame)
        self.rga_buffer_text.setGeometry(QtCore.QRect(10, 80, 181, 191))
        self.rga_buffer_text.setObjectName(_fromUtf8("rga_buffer_text"))
        self.rga_clear_button = QtGui.QPushButton(self.frame)
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

