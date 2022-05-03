import os, sys, struct, time, logging, functools, queue, signal, getpass, pymysql
import paho.mqtt.client as mqtt
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from MainApp import MainApp

#----------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main = MainApp()
    #main = MainGui()
    app.exec_()
#----------------------------------------------------------------------------------------------------------------------#