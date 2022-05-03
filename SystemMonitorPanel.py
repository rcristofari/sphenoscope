from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
import queue


class SystemMonitorPanel(QtWidgets.QMainWindow):

    def __init__(self, main, n_antennas=4, *args, **kwargs):

        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)

        self.main = main

        #--------------------------------------------------------------------------------------------------------------#
        # Don't hard-code all that, set it up in a conf file (same for land/sea colors below)
        # The colors for Land and Sea
        self.colors = {"Terre": "#FE8D03", "Mer": "#08098C"}
        # The colors and sounds for alarms, later to be defined in a conf file / through a settings menu
        self.alarm_colors = {'1': "#E76F51", '2': "#F4A261", '3': "#E9C46A", '4': "#2A9D8F", '5': "#264653"}
        #--------------------------------------------------------------------------------------------------------------#

        self.n_antennas = n_antennas

        self._setupUi(self)

        self.lcd_queue = queue.Queue()
        #self.connection_requested()

        self.console_timer = QtCore.QTimer()
        self.console_timer.timeout.connect(self._poll_console_queue)
        self.console_timer.start(50)

    def _setupUi(self, MainWindow):
        self.SysMonitorWindow = QtWidgets.QWidget(MainWindow)

        self.verticalLayout = QtWidgets.QVBoxLayout(self.SysMonitorWindow)
        self.verticalLayout.setContentsMargins(36, 12, 36, 12)
        self.verticalLayout.setObjectName("verticalLayout")

        self.MainGrid = QtWidgets.QGridLayout()
        self.MainGrid.setHorizontalSpacing(24)
        self.MainGrid.setVerticalSpacing(36)

        # --------------------------------------------------------------------------------------------------------------#
        self.sysmonitor_views = []

        for i in range(self.n_antennas):
            yx = f'{i:02b}'
            y = int(yx[0])
            x = int(yx[1])
            self.sysmonitor_views.append(SysMonitorView(self.SysMonitorWindow, self.main.gate_order[i]))
            self.MainGrid.addLayout(self.sysmonitor_views[i], y, x, 1, 1)

        # --------------------------------------------------------------------------------------------------------------#
        self.verticalLayout.addLayout(self.MainGrid)
        MainWindow.setCentralWidget(self.SysMonitorWindow)

    def write(self, payload):
        print("CALLED")
        self.lcd_queue.put(payload)

    def _poll_console_queue(self):
        while not self.lcd_queue.empty():
            payload = self.lcd_queue.get()
            if payload:
                for i in range(4):
                    self.sysmonitor_views[i].sea_lcds[0].display(payload[i*2])
                    self.sysmonitor_views[i].land_lcds[0].display(payload[i*2+1])

class SysMonitorView(QtWidgets.QGridLayout):

    def __init__(self, mainWindow, antenna_name):

        super().__init__()

        self.setSpacing(6)

        self.antenna_name = QtWidgets.QLabel(mainWindow)
        self.antenna_name.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:18pt; font-weight:600;\">" + antenna_name.upper() + "</span></p></body></html>")
        self.addWidget(self.antenna_name, 0, 0, 1, 2) ## CHECK THAT

        self.AntennaGrid = QtWidgets.QGridLayout()
        self.AntennaGrid.setHorizontalSpacing(12)
        self.AntennaGrid.setVerticalSpacing(12)

        self.sea_label = QtWidgets.QLabel()
        self.sea_label.setText("MER")
        self.sea_label.setStyleSheet("""font-size: 14pt; text-align: center;""")
        self.sea_label.setAlignment(QtCore.Qt.AlignCenter)
        self.addWidget(self.sea_label, 1, 0, 1, 1)

        self.land_label = QtWidgets.QLabel()
        self.land_label.setText("TERRE")
        self.land_label.setStyleSheet("""font-size: 14pt; text-align: center;""")
        self.land_label.setAlignment(QtCore.Qt.AlignCenter)
        self.addWidget(self.land_label, 1, 1, 1, 1)

        self.pulselabel = QtWidgets.QLabel()
        self.pulselabel.setText("TIRIS pulse frequency")
        self.land_label.setStyleSheet("""font-size: 12pt;""")
        self.addWidget(self.pulselabel, 2, 0, 1, 1)

        self.land_lcds, self.sea_lcds, self.labels = [], [], []
        labels = ["Hertz", "last 15 min.", "last hour", "last 24 hours"]

        self.sea_lcds.append(QtWidgets.QLCDNumber())
        self.sea_lcds[0].setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self.sea_lcds[0].setStyleSheet("""background-color: #39393A; color: #55917F; border-radius: 10px; buffer: 5px;""")
        self.addWidget(self.sea_lcds[0], 3, 0, 1, 1)

        self.land_lcds.append(QtWidgets.QLCDNumber())
        self.land_lcds[0].setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self.land_lcds[0].setStyleSheet("""background-color: #39393A; color: #55917F; border-radius: 10px;""")
        self.addWidget(self.land_lcds[0], 3, 1, 1, 1)

        self.labels.append(QtWidgets.QLabel())
        self.labels[0].setText(labels[0])
        self.labels[0].setStyleSheet("""font-size: 14pt;""")
        self.addWidget(self.labels[0], 3, 2, 1, 1)

        self.detectlabel = QtWidgets.QLabel()
        self.detectlabel.setText("Recent detections per antenna")
        self.detectlabel.setStyleSheet("""font-size: 12pt;""")
        self.addWidget(self.detectlabel, 4, 0, 1, 1)

        ## CHANGE LABEL COLORS DEPENDING ON ISSUES - IF NO DETECTION IN 1H, go orange, etc... AND RING AN ALARM IF TIRIS GOES TO 0 HZ

        for i in range(1, 4):
            self.sea_lcds.append(QtWidgets.QLCDNumber())
            self.sea_lcds[i].setSegmentStyle(QtWidgets.QLCDNumber.Flat)
            self.sea_lcds[i].setStyleSheet("""background-color: #39393A; color: #55917F; border-radius: 10px;""")
            self.addWidget(self.sea_lcds[i], i+5, 0, 1, 1)

            self.land_lcds.append(QtWidgets.QLCDNumber())
            self.land_lcds[i].setSegmentStyle(QtWidgets.QLCDNumber.Flat)
            self.land_lcds[i].setStyleSheet("""background-color: #39393A; color: #55917F; border-radius: 10px;""")
            self.addWidget(self.land_lcds[i], i+5, 1, 1, 1)

            self.labels.append(QtWidgets.QLabel())
            self.labels[i].setText(labels[i])
            self.labels[i].setStyleSheet("""font-size: 14pt;""")
            self.addWidget(self.labels[i], i+5, 2, 1, 1)
