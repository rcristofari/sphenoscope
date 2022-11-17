from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import qApp
from AntennaPanel import AntennaPanel
from SystemMonitorPanel import SystemMonitorPanel
from ColonyMonitorPanel import ColonyMonitorPanel
from SettingsWindow import SettingsWindow
from AlarmsWindow import AlarmsWindow

class MainGui(QtWidgets.QMainWindow):

    def __init__(self, main):

        super().__init__()

        self.setWindowTitle("Sphenoscope")

        self.main = main

        self.left = 0
        self.top = 0
        self.width = 1567
        self.height = 846
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.tab_widget = TabWidget(main)
        self.setCentralWidget(self.tab_widget)

        #--------------------------------------------------------------------------------------------------------------#
        # Add menu bar
        self.menubar = QtWidgets.QMenuBar()

        # Menu headers:
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1567, 29))
        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.menubar.addMenu(self.fileMenu)
        self.editMenu = QtWidgets.QMenu("&Edit", self)
        self.menubar.addMenu(self.editMenu)
        self.aboutMenu = QtWidgets.QMenu("&About", self)
        self.menubar.addMenu(self.aboutMenu)

        # Menu items:
        self.exitAction = QtWidgets.QAction("Exit", self)
        self.fileMenu.addAction(self.exitAction)
        self.alarmsAction = QtWidgets.QAction("&Alarms", self)
        self.editMenu.addAction(self.alarmsAction)
        self.settingsAction = QtWidgets.QAction("&Settings", self)
        self.editMenu.addAction(self.settingsAction)
        self.versionAction = QtWidgets.QAction("&Version", self)
        self.aboutMenu.addAction(self.versionAction)
        self.setMenuBar(self.menubar)

        # Define the Exit action
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(qApp.quit)

        # Define the Settings action
        self.settingsAction.setShortcut('Ctrl+S')
        self.settingsAction.setStatusTip('Open the Settings dialog')
        self.settingsAction.triggered.connect(self.showSettingsWindow)

        # Define the Alarms action
        self.alarmsAction.setShortcut('Ctrl+A')
        self.alarmsAction.setStatusTip('Open the Alarms dialog')
        self.alarmsAction.triggered.connect(self.showAlarmsWindow)

        #--------------------------------------------------------------------------------------------------------------#
        # Add status bar
        self.statusbar = QtWidgets.QStatusBar()
        self.statusbar.showMessage(self.main.status_message)
        self.setStatusBar(self.statusbar)

        self.show()

    def showSettingsWindow(self):
        self.dialog = SettingsWindow(self.main)
        self.dialog.show()

    def showAlarmsWindow(self):
        self.dialog = AlarmsWindow(self.main)
        self.dialog.show()

class TabWidget(QtWidgets.QWidget):

    def __init__(self, main):
        super(QtWidgets.QWidget, self).__init__()
        self.main = main
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setStyleSheet("""
             QTabBar {
                background-color: rgb(0, 0, 0, 0);
                qproperty-drawBase: 0;
            }
            QTabBar::tab {
                margin-left: 2px;
                margin-right: 2px;
                height: 25px; width: 200px;
                padding: 5px;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #DDDDDD;
                border-bottom: none;}

            QTabBar::tab:!selected {
                background-color: #BBBBBB;
                margin-top: 2px;
                margin-bottom: -2px;
                border-bottom: none;}
            """)

        # Initialize tab screen
        self.tabs = QtWidgets.QTabWidget()

        self.liveview_tab = AntennaPanel(self.main, n_antennas=4)
        self.liveview_tab.setBackgroundRole(QtGui.QPalette.Window)
        self.liveview_tab.setAutoFillBackground(True)

        self.sysmonitor_tab = SystemMonitorPanel(self.main, n_antennas=4)
        self.sysmonitor_tab.setBackgroundRole(QtGui.QPalette.Window)
        self.sysmonitor_tab.setAutoFillBackground(True)

        self.colomonitor_tab = ColonyMonitorPanel(self.main, n_antennas=4)
        self.colomonitor_tab.setBackgroundRole(QtGui.QPalette.Window)
        self.colomonitor_tab.setAutoFillBackground(True)

        # Add tabs
        self.tabs.addTab(self.liveview_tab, "LiveView")
        self.tabs.addTab(self.sysmonitor_tab, "System monitor")
        self.tabs.addTab(self.colomonitor_tab, "Colony monitor")

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

