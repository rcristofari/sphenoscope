from PyQt5 import QtWidgets
from MainApp import MainApp
import sys
#----------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Sphenoscope")
    main = MainApp()
    app.exec_()
#----------------------------------------------------------------------------------------------------------------------#
