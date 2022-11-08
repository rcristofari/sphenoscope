from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
from qtwidgets import Toggle, PasswordEdit
import logging
import paho.mqtt.client as mqtt

class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, main):
        super().__init__()
        self.setWindowTitle("Settings")
        self.main = main
        self.left = 0
        self.top = 0
        self.width = 400
        self.height = 300
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.tab_widget = SettingsTabWidget(self.main)
        self.setCentralWidget(self.tab_widget)


class SettingsTabWidget(QtWidgets.QWidget):

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
                height: 25px; width: 100px;
                padding: 5px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
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

        self.general_tab = GeneralTab(self.main)
        self.general_tab.setBackgroundRole(QtGui.QPalette.Window)
        self.general_tab.setAutoFillBackground(True)

        self.mqtt_tab = MqttTab(self.main)
        self.mqtt_tab.setBackgroundRole(QtGui.QPalette.Window)
        self.mqtt_tab.setAutoFillBackground(True)

        self.mysql_tab = MySQLTab(self.main)
        self.mysql_tab.setBackgroundRole(QtGui.QPalette.Window)
        self.mysql_tab.setAutoFillBackground(True)

        # Add tabs

        self.tabs.addTab(self.mqtt_tab, "MQTT")
        self.tabs.addTab(self.mysql_tab, "MySQL")
        self.tabs.addTab(self.general_tab, "General")

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

class MqttTab(QtWidgets.QWidget):

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main

        self.getMqttSettings()

        self.layout = QtWidgets.QGridLayout()

        self.mqtt_host_label = QtWidgets.QLabel(self)
        self.mqtt_host_label.setText("MQTT Host")
        self.mqtt_host_line = QtWidgets.QLineEdit(self)
        #self.mqtt_host_line.insert(self.mqtt_host)
        self.mqtt_host_line.insert(self.main.network_conf["MQTT"]["host"])
        self.mqtt_host_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mqtt_host_label, 0, 0, 1, 1)
        self.layout.addWidget(self.mqtt_host_line, 0, 1, 1, 3)

        self.mqtt_port_label = QtWidgets.QLabel(self)
        self.mqtt_port_label.setText("MQTT Port")
        self.mqtt_port_line = QtWidgets.QLineEdit(self)
        self.mqtt_port_line.insert(str(self.main.network_conf["MQTT"]["port"]))
        self.mqtt_port_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mqtt_port_label, 1, 0, 1, 1)
        self.layout.addWidget(self.mqtt_port_line, 1, 1, 1, 3)

        self.mqtt_dchanel_label = QtWidgets.QLabel(self)
        self.mqtt_dchanel_label.setText("Detections chanel")
        self.mqtt_dchanel_line = QtWidgets.QLineEdit(self)
        self.mqtt_dchanel_line.insert(self.main.network_conf["MQTT"]["detection_chanel"])
        self.mqtt_dchanel_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mqtt_dchanel_label, 2, 0, 1, 1)
        self.layout.addWidget(self.mqtt_dchanel_line, 2, 1, 1, 3)

        self.mqtt_schanel_label = QtWidgets.QLabel(self)
        self.mqtt_schanel_label.setText("Status chanel")
        self.mqtt_schanel_line = QtWidgets.QLineEdit(self)
        self.mqtt_schanel_line.insert(self.main.network_conf["MQTT"]["status_chanel"])
        self.mqtt_schanel_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mqtt_schanel_label, 3, 0, 1, 1)
        self.layout.addWidget(self.mqtt_schanel_line, 3, 1, 1, 3)

        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.saveMqttSetting)
        self.save_button.setEnabled(False)
        self.layout.addWidget(self.save_button, 4, 2, 1, 2)

        self.setLayout(self.layout)

    def getMqttSettings(self):
        self.mqtt_host = "127.0.0.1"
        self.mqtt_port = 1883
        self.mqtt_detections = "detections/all"
        self.mqtt_status = "status/all"

        with open("./conf/network.conf", 'r') as cnffile:
            for line in cnffile:
                if not line.startswith("#"):
                    param, value = line.strip("\n").split("=")
                    match param:
                        case "mqtt_host":
                            self.mqtt_host = value
                        case "mqtt_port":
                            try:
                                self.mqtt_port = int(value)
                            except ValueError:
                                self.mqtt_port = 1883
                        case "mqtt_detections":
                            self.mqtt_detections = value
                        case "mqtt_status":
                            self.mqtt_status = value

    def saveMqttSetting(self):
        new_mqtt_host = self.mqtt_host_line.text()
        new_mqtt_port = self.mqtt_port_line.text()
        new_mqtt_detections = self.mqtt_dchanel_line.text()
        new_mqtt_status = self.mqtt_schanel_line.text()
        # Overwrite the configuration file with the new settings:
        with open("./conf/network.conf", 'r') as cnffile:
            all_lines = cnffile.readlines()
        with open("./conf/network.conf", 'w') as cnffile:
            for line in all_lines:
                if not line.startswith("mqtt_"):
                    cnffile.write(line)
                else:
                    param = line.split("=")[0]
                    match param:
                        case "mqtt_host":
                            cnffile.write(f"mqtt_host={new_mqtt_host}\n")
                        case "mqtt_port":
                            cnffile.write(f"mqtt_port={new_mqtt_port}\n")
                        case "mqtt_detections":
                            cnffile.write(f"mqtt_detections={new_mqtt_detections}\n")
                        case "mqtt_status":
                            cnffile.write(f"mqtt_status={new_mqtt_status}\n")
        # Disable the Save button until a lineEdit is modified
        self.disableSave()
        #log.info("MQTT settings changed by user.") #NOT WORKING YET

    def enableSave(self):
        self.save_button.setEnabled(True)

    def disableSave(self):
        self.save_button.setEnabled(False)


class MySQLTab(QtWidgets.QWidget):

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.getMySQLSettings()

        self.layout = QtWidgets.QGridLayout()

        self.mysql_host_label = QtWidgets.QLabel(self)
        self.mysql_host_label.setText("MySQL Host")
        self.mysql_host_line = QtWidgets.QLineEdit(self)
        self.mysql_host_line.insert(self.main.network_conf["MYSQL"]["host"])
        #self.mysql_host_line.insert(self.mysql_host)
        self.mysql_host_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mysql_host_label, 0, 0, 1, 1)
        self.layout.addWidget(self.mysql_host_line, 0, 1, 1, 3)

        self.mysql_port_label = QtWidgets.QLabel(self)
        self.mysql_port_label.setText("MySQL Port")
        self.mysql_port_line = QtWidgets.QLineEdit(self)
        self.mysql_port_line.insert(str(self.main.network_conf["MYSQL"]["port"]))
        self.mysql_port_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mysql_port_label, 1, 0, 1, 1)
        self.layout.addWidget(self.mysql_port_line, 1, 1, 1, 3)

        self.mysql_user_label = QtWidgets.QLabel(self)
        self.mysql_user_label.setText("MySQL User")
        self.mysql_user_line = QtWidgets.QLineEdit(self)
        self.mysql_user_line.insert(self.main.network_conf["MYSQL"]["usr"])
        self.mysql_user_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mysql_user_label, 2, 0, 1, 1)
        self.layout.addWidget(self.mysql_user_line, 2, 1, 1, 3)

        self.mysql_pwd_label = QtWidgets.QLabel(self)
        self.mysql_pwd_label.setText("MySQL Password")
        self.mysql_pwd_line = PasswordEdit()
        #self.mysql_pwd_line = QtWidgets.QLineEdit(self)
        self.mysql_pwd_line.insert(self.main.network_conf["MYSQL"]["pwd"])
        self.mysql_pwd_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mysql_pwd_label, 3, 0, 1, 1)
        self.layout.addWidget(self.mysql_pwd_line, 3, 1, 1, 3)

        self.mysql_schema_label = QtWidgets.QLabel(self)
        self.mysql_schema_label.setText("MySQL Schema")
        self.mysql_schema_line = QtWidgets.QLineEdit(self)
        self.mysql_schema_line.insert(self.main.network_conf["MYSQL"]["db"])
        self.mysql_schema_line.textChanged[str].connect(self.enableSave)
        self.layout.addWidget(self.mysql_schema_label, 4, 0, 1, 1)
        self.layout.addWidget(self.mysql_schema_line, 4, 1, 1, 3)

        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.saveMySQLSetting)
        self.save_button.setEnabled(False)
        self.layout.addWidget(self.save_button, 5, 2, 1, 2)

        self.setLayout(self.layout)

    def getMySQLSettings(self):
        self.mysql_host = "127.0.0.1"
        self.mysql_port = 3306
        self.mysql_usr = "root"
        self.mysql_pwd = ""
        self.mysql_db = "antavia_cro_new_testing"

        with open("./conf/network.conf", 'r') as cnffile:
            for line in cnffile:
                if not line.startswith("#"):
                    param, value = line.strip("\n").split("=")
                    match param:
                        case "mysql_host":
                            self.mysql_host = value
                        case "mysql_port":
                            try:
                                self.mysql_port = int(value)
                            except ValueError:
                                self.mysql_port = 3306
                        case "mysql_usr":
                            self.mysql_usr = value
                        case "mysql_pwd":
                            if value:
                                self.mysql_pwd = value
                            else:
                                self.mysql_pwd = ""
                        case "mysql_db":
                            self.mysql_db = value

    def saveMySQLSetting(self):
        new_mysql_host = self.mysql_host_line.text()
        new_mysql_port = self.mysql_port_line.text()
        new_mysql_usr = self.mysql_user_line.text()
        new_mysql_pwd = self.mysql_pwd_line.text()
        new_mysql_db = self.mysql_schema_line.text()

        # Overwrite the configuration file with the new settings:
        with open("./conf/network.conf", 'r') as cnffile:
            all_lines = cnffile.readlines()
        with open("./conf/network.conf", 'w') as cnffile:
            for line in all_lines:
                if not line.startswith("mysql_"):
                    cnffile.write(line)
                else:
                    param = line.split("=")[0]
                    match param:
                        case "mysql_host":
                            cnffile.write(f"mysql_host={new_mysql_host}\n")
                        case "mysql_port":
                            cnffile.write(f"mysql_port={new_mysql_port}\n")
                        case "mysql_usr":
                            cnffile.write(f"mysql_detections={new_mysql_usr}\n")
                        case "mysql_pwd":
                            cnffile.write(f"mysql_status={new_mysql_pwd}\n")
                        case "mysql_db":
                            cnffile.write(f"mysql_db={new_mysql_db}\n")

        self.main.reset_mysql_connexion()

        # Disable the Save button until a lineEdit is modified
        self.disableSave()
        #log.info("MySQL settings changed by user.") # NOT WORKING YET

    def enableSave(self):
        self.save_button.setEnabled(True)

    def disableSave(self):
        self.save_button.setEnabled(False)


class GeneralTab(QtWidgets.QWidget):

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.getMySQLSettings()

        self.layout = QtWidgets.QGridLayout()

        self.settings_legacy_label = QtWidgets.QLabel(self)
        self.settings_legacy_label.setText("Use Legacy database")
        self.settings_legacy_toggle = Toggle()
        self.layout.addWidget(self.settings_legacy_label, 0, 0, 1, 1)
        self.layout.addWidget(self.settings_legacy_toggle, 0, 4, 1, 1)


        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.saveMySQLSetting)
        self.save_button.setEnabled(True)
        self.layout.addWidget(self.save_button, 5, 2, 1, 2)

        #self.mysql_dstream_box = QtWidgets.QTextEdit(self)
        #self.layout.addWidget(self.mysql_dstream_box, 6, 0, 1, 4)

        self.setLayout(self.layout)

    def getMySQLSettings(self):
        self.mysql_host = "127.0.0.1"
        self.mysql_port = 3306
        self.mysql_usr = "root"
        self.mysql_pwd = ""
        self.mysql_db = "antavia_cro_new_testing"

        with open("./conf/network.conf", 'r') as cnffile:
            for line in cnffile:
                if not line.startswith("#"):
                    param, value = line.strip("\n").split("=")
                    match param:
                        case "mysql_host":
                            self.mysql_host = value
                        case "mysql_port":
                            try:
                                self.mysql_port = int(value)
                            except ValueError:
                                self.mysql_port = 3306
                        case "mysql_usr":
                            self.mysql_usr = value
                        case "mysql_pwd":
                            if value:
                                self.mysql_pwd = value
                            else:
                                self.mysql_pwd = ""
                        case "mysql_db":
                            self.mysql_db = value

    def saveMySQLSetting(self):
        new_mysql_host = self.mysql_host_line.text()
        new_mysql_port = self.mysql_port_line.text()
        new_mysql_usr = self.mysql_user_line.text()
        new_mysql_pwd = self.mysql_pwd_line.text()
        new_mysql_db = self.mysql_schema_line.text()

        # Overwrite the configuration file with the new settings:
        with open("./conf/network.conf", 'r') as cnffile:
            all_lines = cnffile.readlines()
        with open("./conf/network.conf", 'w') as cnffile:
            for line in all_lines:
                if not line.startswith("mysql_"):
                    cnffile.write(line)
                else:
                    param = line.split("=")[0]
                    match param:
                        case "mysql_host":
                            cnffile.write(f"mysql_host={new_mysql_host}\n")
                        case "mysql_port":
                            cnffile.write(f"mysql_port={new_mysql_port}\n")
                        case "mysql_usr":
                            cnffile.write(f"mysql_detections={new_mysql_usr}\n")
                        case "mysql_pwd":
                            cnffile.write(f"mysql_status={new_mysql_pwd}\n")
                        case "mysql_db":
                            cnffile.write(f"mysql_db={new_mysql_db}\n")

        self.main.reset_mysql_connexion()

        # Disable the Save button until a lineEdit is modified
        self.disableSave()
        #log.info("MySQL settings changed by user.") # NOT WORKING YET

    def enableSave(self):
        self.save_button.setEnabled(True)

    def disableSave(self):
        self.save_button.setEnabled(False)