# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'log_in_menu.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LogInWindow(object):
    def setupUi(self, LogInWindow):
        LogInWindow.setObjectName("LogInWindow")
        LogInWindow.resize(300, 160)
        self.label = QtWidgets.QLabel(LogInWindow)
        self.label.setGeometry(QtCore.QRect(0, 0, 300, 31))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(LogInWindow)
        self.label_2.setGeometry(QtCore.QRect(6, 32, 121, 21))
        self.label_2.setObjectName("label_2")
        self.line_login = QtWidgets.QLineEdit(LogInWindow)
        self.line_login.setGeometry(QtCore.QRect(0, 50, 300, 30))
        self.line_login.setObjectName("line_login")
        self.label_3 = QtWidgets.QLabel(LogInWindow)
        self.label_3.setGeometry(QtCore.QRect(6, 82, 121, 21))
        self.label_3.setObjectName("label_3")
        self.line_password = QtWidgets.QLineEdit(LogInWindow)
        self.line_password.setGeometry(QtCore.QRect(0, 100, 300, 30))
        self.line_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.line_password.setClearButtonEnabled(False)
        self.line_password.setObjectName("line_password")
        self.button_cancel = QtWidgets.QPushButton(LogInWindow)
        self.button_cancel.setGeometry(QtCore.QRect(200, 130, 91, 31))
        self.button_cancel.setObjectName("button_cancel")
        self.button_login = QtWidgets.QPushButton(LogInWindow)
        self.button_login.setGeometry(QtCore.QRect(110, 130, 91, 31))
        self.button_login.setObjectName("button_login")

        self.retranslateUi(LogInWindow)
        QtCore.QMetaObject.connectSlotsByName(LogInWindow)

    def retranslateUi(self, LogInWindow):
        _translate = QtCore.QCoreApplication.translate
        LogInWindow.setWindowTitle(_translate("LogInWindow", "Dialog"))
        self.label.setText(_translate("LogInWindow", "<html><head/><body><p><span style=\" font-size:14pt;\">Microsoft Log In</span></p></body></html>"))
        self.label_2.setText(_translate("LogInWindow", "<html><head/><body><p><span style=\" font-size:11pt;\">Login (mail)</span></p></body></html>"))
        self.label_3.setText(_translate("LogInWindow", "<html><head/><body><p><span style=\" font-size:11pt;\">Password</span></p></body></html>"))
        self.button_cancel.setText(_translate("LogInWindow", "Cancel"))
        self.button_login.setText(_translate("LogInWindow", "Log In"))
