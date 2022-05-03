from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
import queue, random


class AntennaPanel(QtWidgets.QMainWindow):

    def __init__(self, main, n_antennas=4, *args, **kwargs):

        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)

        self.main = main
        #--------------------------------------------------------------------------------------------------------------#
        # Don't hard-code all that, set it up in a conf file (same for land/sea colors below)
        # The colors for Land and Sea
        self.colors = {"Terre": "#FE8D03", "Mer": "#08098C"}
        # The colors and sounds for alarms, later to be defined in a conf file / through a settings menu
        self.alarm_colors = {'1': "#E76F51", '2': "#F4A261", '3': "#E9C46A", '4': "#2A9D8F", '5': "#264653"}
        self.alarm_sounds = {'1': QtMultimedia.QSound("/home/robin/sphenoscope/ding.wav")}
        self.individual_colors = ["#f94144", "#f3722c", "#f8961e", "#f9844a", "#f9c74f", "#90be6d", "#43aa8b", "#4d908e", "#577590", "#277da1"]
        #--------------------------------------------------------------------------------------------------------------#

        self.n_antennas = n_antennas
        self._setupUi(self)

        self.console_queue = queue.Queue()
        self.connection_requested()

        self.console_timer = QtCore.QTimer()
        self.console_timer.timeout.connect(self._poll_console_queue)
        self.console_timer.start(50)

        self.show()

    def _setupUi(self, MainWindow):

        self.AntennaWindow = QtWidgets.QWidget(MainWindow)
        self.AntennaWindow.setBackgroundRole(QtGui.QPalette.Dark)
        self.setBackgroundRole(QtGui.QPalette.Dark)

        self.verticalLayout = QtWidgets.QVBoxLayout(self.AntennaWindow)
        self.verticalLayout.setContentsMargins(36, 12, 36, 12)
        self.verticalLayout.setObjectName("verticalLayout")

        self.MainGrid = QtWidgets.QGridLayout()
        self.MainGrid.setHorizontalSpacing(24)
        self.MainGrid.setVerticalSpacing(36)

        #--------------------------------------------------------------------------------------------------------------#
        self.antenna_views = []

        for i in range(self.n_antennas):
            yx = f'{i:02b}'
            y = int(yx[0])
            x = int(yx[1])
            self.antenna_views.append(AntennaView(self.AntennaWindow, self.main.gate_order[i]))
            self.MainGrid.addLayout(self.antenna_views[i], y, x, 1, 1)

        #--------------------------------------------------------------------------------------------------------------#
        self.verticalLayout.addLayout(self.MainGrid)
        MainWindow.setCentralWidget(self.AntennaWindow)

    def highlight_row(self, rfid_table, row_id, alarm_id):
        try:
            for c in range(2, 7):
                rfid_table.item(row_id, c).setBackground(QtGui.QColor(self.alarm_colors[alarm_id]))
        except KeyError:
            pass

    def dtime_color(self, rfid_table):
        if not rfid_table.item(1, 3):
            new_color = random.choice(self.individual_colors)
        else:
            if rfid_table.item(1, 3).text() != rfid_table.item(0, 3).text():
                previous_color = rfid_table.item(1, 1).background().color().name()
                avail_colors = self.individual_colors[:]
                avail_colors.remove(previous_color)
                new_color = random.choice(avail_colors)
            else:
                new_color = rfid_table.item(1, 1).background().color().name()
        rfid_table.item(0, 1).setBackground(QtGui.QColor(new_color))

    def highlight_antenna(self, antenna_box, alarm_id, land_or_sea):
        if land_or_sea == "Terre":
            if alarm_id in self.alarm_colors:
                antenna_box.start_animation()
            else:
                antenna_box.setStyleSheet("QTextEdit{border-color: #FE8D03; border-width: 5px; border-radius: 15px; border-style:solid; background-color: #FFFFFF; color: #000000;}")
        else:
            if alarm_id in self.alarm_colors:
                antenna_box.start_animation()
            else:
                antenna_box.setStyleSheet("QTextEdit{border-color: #08098C; border-width: 5px; border-radius: 15px; border-style:solid; background-color: #FFFFFF; color: #000000;}")

    def play_alarm(self, alarm_id):
        try:
            self.alarm_sounds[alarm_id].play()
        except KeyError:
            pass

    def write(self, payload):
        self.console_queue.put(payload)

    def insert_detection(self, rfid_table, detection):
        # If this detection is a new penguin or the same penguin on another antenna:
        if rfid_table.item(0, 0) is None or detection[3] != rfid_table.item(0, 3).text() or detection[
            0] != rfid_table.item(0, 0).text():
            rfid_table.insertRow(0)
            for i, item in enumerate(detection):
                rfid_table.setItem(0, i, QtWidgets.QTableWidgetItem(str(item)))
                rfid_table.item(0, i).setTextAlignment(QtCore.Qt.AlignCenter)
            rfid_table.item(0, 0).setBackground(QtGui.QColor(self.colors[detection[0]]))
            self.highlight_row(rfid_table, 0, detection[6])
            self.dtime_color(rfid_table)

    def display_antenna(self, antenna_box, detection):
        self.highlight_antenna(antenna_box, detection[6], detection[0])
        antenna_box.setText(detection[2] + "<br>" + detection[3])
        antenna_box.setAlignment(QtCore.Qt.AlignCenter)
        self.play_alarm(detection[6])

    def _poll_console_queue(self):
        while not self.console_queue.empty():
            payload = self.console_queue.get()
            if payload:
                detection = [payload[x] for x in [1, 2, 4, 3, 6, 5, 7]]
                if payload[1] == "Mer":
                    self.display_antenna(self.antenna_views[self.main.gates[payload[0]]].sea_antenna, detection)
                else:
                    self.display_antenna(self.antenna_views[self.main.gates[payload[0]]].land_antenna, detection)

                self.insert_detection(self.antenna_views[self.main.gates[payload[0]]].rfid_table, detection)

    def connection_requested(self):
        hostname = "127.0.0.1"
        portnum = 1883
        self.main.connect_to_mqtt_server(hostname, portnum)


class BlinkingTextBox(QtWidgets.QTextEdit):

    def __init__(self, parent=None, land_or_sea="land"):
        super().__init__(parent)
        if land_or_sea == "land":
            self.color1 = QtGui.QColor("#D33F49")
            self.color2 = QtGui.QColor("#FEBF71")
            self.border_color = "#FE8D03"
        else:
            self.color1 = QtGui.QColor("#2B2BF3")
            self.color2 = QtGui.QColor("#B2B2FB")
            self.border_color = "#08098C"
        self.setAlignment(QtCore.Qt.AlignCenter)

        self._animation = QtCore.QVariantAnimation(
            self,
            valueChanged=self._animate,
            startValue=0.00001,
            endValue=0.9999,
            duration=500)

    def _animate(self, value):
        qss = """ """
        grad = "border-color: " + self.border_color + "; border-width: 5px; border-radius: 15px; border-style:solid; color: #000000; background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {color1}, stop:{value} {color2}, stop: 1.0 {color1});".format(color1=self.color1.name(), color2=self.color2.name(), value=value)
        qss += grad
        self.setStyleSheet(qss)

    def start_animation(self):
        self._animation.setDirection(QtCore.QAbstractAnimation.Forward)
        self._animation.start()

    def reset_background(self):
        qss = """border-color: %s; border-width: 5px; border-radius: 15px; border-style:solid; background-color: #FFFFFF; color: #000000;""" % self.border_color
        self.setStyleSheet(qss)


class AntennaView(QtWidgets.QGridLayout):

    def __init__(self, mainWindow, antenna_name):

        super().__init__()

        self.setSpacing(12)

        self.antenna_name = QtWidgets.QLabel(mainWindow)
        self.antenna_name.setText("<html><head/><body><p align=\"center\"><span style=\" color:#000000; font-size:18pt; font-weight:600;\">" + antenna_name.upper() + "</span></p></body></html>")
        self.addWidget(self.antenna_name, 0, 0, 1, 2)

        self.sea_antenna = BlinkingTextBox(mainWindow, land_or_sea="sea")
        self.sea_antenna.setEnabled(True)
        self.sea_antenna.setMaximumSize(QtCore.QSize(16777215, 395))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.sea_antenna.setFont(font)
        self.sea_antenna.setReadOnly(True)
        self.sea_antenna.setStyleSheet("QTextEdit{border-color: #08098C; border-width: 5px; border-radius: 15px; border-style:solid; background-color: #FFFFFF; color: #000000;}")
        self.sea_antenna.setText("WAITING...")
        self.sea_antenna.setAlignment(QtCore.Qt.AlignCenter)
        self.addWidget(self.sea_antenna, 1, 0, 1, 1)

        self.land_antenna = BlinkingTextBox(mainWindow, land_or_sea="land")
        self.land_antenna.setEnabled(True)
        self.land_antenna.setMaximumSize(QtCore.QSize(16777215, 297))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.land_antenna.setFont(font)
        self.land_antenna.setReadOnly(True)
        self.sea_antenna.setStyleSheet("QTextEdit{border-color: #FE8D03; border-width: 5px; border-radius: 15px; border-style:solid; background-color: #FFFFFF; color: #000000;}")
        self.sea_antenna.setText("WAITING...")
        self.sea_antenna.setAlignment(QtCore.Qt.AlignCenter)
        self.addWidget(self.land_antenna, 1, 1, 1, 1)

        self.rfid_table = QtWidgets.QTableWidget(mainWindow)
        self.rfid_table.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rfid_table.sizePolicy().hasHeightForWidth())
        self.rfid_table.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Cantarell")
        font.setPointSize(12)
        self.rfid_table.setFont(font)
        self.rfid_table.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.rfid_table.setAutoFillBackground(False)
        self.rfid_table.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.rfid_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.rfid_table.setGridStyle(QtCore.Qt.DotLine)
        self.rfid_table.setColumnCount(7)
        self.rfid_table.setRowCount(0)

        labels = ["Loc", "Time", "Name", "RFID", "Sex", "Year", "Alarm"]
        for i in range(7):
            item = QtWidgets.QTableWidgetItem()
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setText(labels[i])
            self.rfid_table.setHorizontalHeaderItem(i, item)

        self.rfid_table.horizontalHeader().setDefaultSectionSize(100)
        self.rfid_table.horizontalHeader().setMinimumSectionSize(25)
        self.rfid_table.horizontalHeader().setStretchLastSection(True)
        self.rfid_table.verticalHeader().setVisible(False)

        self.header = self.rfid_table.horizontalHeader()
        for c in range(7):
            self.header.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeToContents)

        self.rfid_table.setStyleSheet("QTableView {selection-color: #000000; color: #000000; selection-background-color: #FFFFFF; background-color: #FFFFFF;}")

        self.addWidget(self.rfid_table, 2, 0, 1, 2)

        self.setRowStretch(0, 1)
        self.setRowStretch(1, 1)
        self.setRowStretch(2, 10)