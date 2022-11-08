from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
from PyQt5.QtCore import Qt, pyqtSignal
import json, os

class AlarmsWindow(QtWidgets.QMainWindow):

    def __init__(self, main):
        super().__init__()
        # This allows to access MainApp attributes / methods from here
        self.main = main
        self.setWindowTitle("Alarms")
        self.left = 0
        self.top = 0
        self.width = 600
        self.height = len(self.main.alarms)*40
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.alarms_widget = AlarmsWidget(main)
        self.setCentralWidget(self.alarms_widget)

    def call_close(self):
        print("EXECUTING")
        self.close()


class AlarmsWidget(QtWidgets.QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main

        self.layout = QtWidgets.QGridLayout()
        self.alarm_label = QtWidgets.QLabel(self)
        self.alarm_label.setText("Available alarms")
        self.layout.addWidget(self.alarm_label, 0, 0, 1, 1)

        self.n_alarms = self.refresh_alarm_settings()

        self.cancelbutton = QtWidgets.QPushButton(self)
        self.cancelbutton.setText("Cancel")
        self.cancelbutton.clicked.connect(self.call_close)
        self.cancelbutton.setEnabled(True)
        self.layout.addWidget(self.cancelbutton, self.n_alarms+2, 0, 1, 2)

        self.savebutton = QtWidgets.QPushButton(self)
        self.savebutton.setText("Save")
        self.savebutton.clicked.connect(self.call_save)
        self.savebutton.setEnabled(True)
        self.layout.addWidget(self.savebutton, self.n_alarms+2, 2, 1, 2)
        self.setLayout(self.layout)

    def __del__(self):
        self.close()

    def refresh_alarm_settings(self):
        print(self.main.alarm_conf)
        self.labels, self.colors, self.sounds = [], [], []
        for i, a in enumerate(self.main.alarm_conf):
            print(i, a)
            # Labels
            self.labels.append(QtWidgets.QLabel(self))
            self.labels[i].setText(str(a))
            self.layout.addWidget(self.labels[i], i+1, 0, 1, 1)
            # Color pickers
            self.colors.append(ColorButton(color=self.main.alarm_conf[a]["color"], main=self.main, alarm=a))
            self.layout.addWidget(self.colors[i], i+1, 1, 1, 1)
            # File pickers
            cle = ClickableLineEdit(self.main.alarm_conf[a]["sound"], self.main, a)
            cle.clicked.connect(cle.getfiles)
            self.sounds.append(cle)
            self.layout.addWidget(self.sounds[i], i+1, 2, 1, 1)
        return i


    def call_close(self):
        print("CLOSING")
        self.__del__()

    def call_save(self):
        json_obj = json.dumps(self.main.alarm_conf, indent=4)
        with open(self.main.alarm_file, 'w') as f:
            f.write(json_obj)
        self.refresh_alarm_settings()

class ColorButton(QtWidgets.QPushButton):

    colorChanged = pyqtSignal(object)

    def __init__(self, *args, color=None, main, alarm, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)
        self._default = color
        self.main = main
        self.alarm = alarm
        self._color = None
        self.pressed.connect(self.onColorPicker)
        self.setColor(self._default)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit(color)
        if self._color:
            self.setStyleSheet(f"background-color: {self._color}; border: none; height: 30px; border-style: outset; padding: 2px; border-width: 0px ; border-radius: 4px;")
            self.setText(color)
            self.main.alarm_conf[self.alarm]["color"] = self._color
        else:
            self.setStyleSheet("")

    def onColorPicker(self):
        dlg = QtWidgets.QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(QtGui.QColor(self._color))
        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def getColor(self):
        return self._color

class ClickableLineEdit(QtWidgets.QLineEdit):

    clicked = pyqtSignal()
    def __init__(self, widget, main, alarm):
        super().__init__(widget)
        self.main = main
        self.alarm = alarm
        self.widget = widget

    def mousePressEvent(self,QMouseEvent):
        self.clicked.emit()

    def getfiles(self):
        dlg = QtWidgets.QFileDialog(self, 'Open file',  self.main.alarm_conf[self.alarm]["sound"], "Sound files (*.mp3 *.wav);;All Files (*)")
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        self.file = self.main.alarm_conf[self.alarm]["sound"]
        if dlg.exec_():
            self.file = dlg.selectedFiles()[0]
            self.main.alarm_conf[self.alarm]["sound"] = self.file
            self.setText(self.file)
        return self.file