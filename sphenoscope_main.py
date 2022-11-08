import os, sys, struct, time, logging, functools, queue, signal, getpass, pymysql
import paho.mqtt.client as mqtt
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from MainApp import MainApp
from qt_material import apply_stylesheet

#----------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main = MainApp()
    #apply_stylesheet(app, theme="dark_amber.xml")
    #apply_stylesheet(app, theme="light_blue.xml")
    #main = MainGui()
    app.exec_()
#----------------------------------------------------------------------------------------------------------------------#
