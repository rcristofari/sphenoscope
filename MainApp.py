import os, sys, struct, time, logging, functools, queue, signal, getpass, pymysql
import paho.mqtt.client as mqtt
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from MainGui import MainGui

# default logging output
log = logging.getLogger('main')

# logger to pass to the MQTT library
mqtt_log = logging.getLogger('mqtt')
mqtt_log.setLevel(logging.WARNING)
mqtt_rc_codes = ['Success', 'Incorrect protocol version', 'Invalid client identifier', 'Server unavailable', 'Bad username or password', 'Not authorized']


#----------------------------------------------------------------------------------------------------------------------#
class MainApp(object):

    def __init__(self):

        # Attach a handler to the keyboard interrupt (control-C).
        signal.signal(signal.SIGINT, self._sigint_handler)

        # load any available persistent application settings
        QtCore.QCoreApplication.setApplicationName('Sphenoscope')

        # Initialize the MQTT client system
        self.client = mqtt.Client()
        self.client.enable_logger(mqtt_log)
        self.client.on_log = self.on_log
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # Define the place indices
        self.gates = {"Bretelle Sud": 2, "Autoroute": 0, "Prado": 1, "Manchoduc": 3}

        self.window = MainGui(self)

        self.get_history_from_mysql("127.0.0.1", "root", "UlaqKSZRFR9?wy")

    def app_is_exiting(self):
        if self.client.is_connected():
            self.client.disconnect()
            self.client.loop_stop()

    def _sigint_handler(self, signal, frame):
        print("Keyboard interrupt caught, running close handlers...")
        self.app_is_exiting()
        sys.exit(0)

    def get_history_from_mysql(self, host, usr, pwd, db="antavia_testing", port=3306):
        result = None
        try:
            db = pymysql.connect(host=host, user=usr, passwd=pwd, db=db, port=port)
            cursor = db.cursor()
            cursor.execute("select d.description, d.date_arrivee, a.identifiant_transpondeur, a.nom, a.date_transpondage, a.sexe, a.son_suivi from animaux a, (select a.description, d.date_arrivee, d.animaux_id from detections d, antennes a where d.antenne_id = a.id order by d.date_arrivee desc limit 200) d where a.id = d.animaux_id;")
            result = cursor.fetchall()
        except pymysql.OperationalError:
            pass
        if result:
            for row in result:
                if row[0].endswith("Terre"):
                    passage = row[0][:-6].title()
                    loc = "Terre"
                else:
                    passage = row[0][:-4].title()
                    loc = "Mer"
                t = row[1]
                rfid = row[2]
                if row[3].startswith("auto"):
                    name = "auto"
                else:
                    name = row[3]
                try:
                    rfid_year = datetime.strftime(row[4], "%Y")
                except TypeError:
                    rfid_year = "1970"
                sex = row[5]
                alarm = row[6]
                contents = [passage, loc, datetime.strftime(t, "%Y-%m-%d %H:%M:%S"), rfid, name, rfid_year, sex, alarm]
                self.window.write(contents)

    def connect_to_mqtt_server(self, hostname, portnum):
        if self.client.is_connected():
            pass
        else:
            if portnum is None:
                log.warning("Please specify the server port before attempting connection.")
            else:
                log.debug("Initiating MQTT connection to %s:%d" % (hostname, portnum))
                self.client.connect(hostname, portnum)
                self.client.loop_start()

    def disconnect_from_mqtt_server(self):
        if self.client.is_connected():
             self.client.disconnect()
        else:
            pass
        self.client.loop_stop()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("Connection succeeded.")
        elif rc > 0:
            if rc < len(mqtt_rc_codes):
                log.warning("Connection failed with error: %s", mqtt_rc_codes[rc])
            else:
                log.warning("Connection failed with unknown error %d", rc)
        client.subscribe("detections/all")
        return

    def on_log(client, userdata, level, buf):
        log.debug("on_log level %s: %s", level, userdata)
        return

    def on_disconnect(self, client, userdata, rc):
        log.debug("disconnected")

    def on_message(self, client, userdata, msg):
       print(msg.payload)
       contents = self.parse_nmea(msg.payload)
       self.window.write(contents)

    def parse_nmea(self, payload):
        sentence = payload.decode("UTF-8").strip("\n")
        if sentence.startswith("$RFID"):
            line = sentence.split(",")
            antenna = line[1]
            t = datetime.strptime(line[2] + line[3], "%d%m%y%H%M%S")
            rfid = line[4]
            if line[5].startswith("auto"):
                name = "auto"
            else:
                name = line[5]
            try:
                rfid_date = datetime.strptime(line[6], "%Y-%m-%d")
            except ValueError:
                rfid_date = datetime.strptime("1970-01-01", "%Y-%m-%d")
            rfid_year = datetime.strftime(rfid_date, "%Y")
            sex = line[7]
            alarm = line[8]
            if antenna.endswith("Terre"):
                passage = antenna[:-6]
                loc = "Terre"
            else:
                passage = antenna[:-4]
                loc = "Mer"
            return [passage, loc, datetime.strftime(t, "%Y-%m-%d %H:%M:%S"), rfid, name, rfid_year, sex, alarm]
