import sys, logging, signal, pymysql
from functools import wraps
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
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

        # Initialize the database connection:
        self.__db = MysqlConnect(usr="root", pwd="UlaqKSZRFR9?wy", db="antavia_testing")

        # Define the place indices (relative to GUI frames)
        self.gates = {"Bretelle Sud": 2, "Autoroute": 0, "Prado": 1, "Manchoduc": 3}
        self.gate_order = {0: "Autoroute", 1: "Prado", 2: "Bretelle Sud", 3: "Manchoduc"}

        #Antenna order in the DB (can be loaded directly from DB at init. too)
        self.antennas = {1: "Bretelle Sud Mer", 2: "Bretelle Sud Terre", 3: "Autoroute Mer", 4: "Autoroute Terre",
                         5: "Manchoduc Mer", 6: "Manchoduc Terre", 7: "Prado Mer", 8: "Prado Terre"}

        self.window = MainGui(self)

        self.get_history_from_mysql()

    def app_is_exiting(self):
        if self.client.is_connected():
            self.client.disconnect()
            self.client.loop_stop()

    def _sigint_handler(self, signal, frame):
        print("Keyboard interrupt caught, running close handlers...")
        self.app_is_exiting()
        sys.exit(0)

    def get_history_from_mysql(self):

        query = "select d.description, d.date_arrivee, a.identifiant_transpondeur, a.nom, a.date_transpondage, a.sexe, a.son_suivi from animaux a, (select a.description, d.date_arrivee, d.animaux_id from detections d, antennes a where d.antenne_id = a.id order by d.date_arrivee desc limit 200) d where a.id = d.animaux_id;"
        result = self.__db.fetchall(query)

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
                self.window.tab_widget.liveview_tab.write(contents)

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
        client.subscribe("status/all")
        return

    def on_log(client, userdata, level, buf):
        log.debug("on_log level %s: %s", level, userdata)
        return

    def on_disconnect(self, client, userdata, rc):
        log.debug("disconnected")

    def on_message(self, client, userdata, msg):
        sentence = msg.payload.decode("UTF-8").strip("\n")
        print(sentence)

        if sentence.startswith("$RFID"):
            contents = self.parse_nmea(msg.payload)
            self.window.tab_widget.liveview_tab.write(contents)

        elif sentence.startswith("$HERTZ"):
            # we also refresh detection stats
            contents = self.get_detection_stats(sentence)

            # we forward the whole data to the monitor tab
            self.window.tab_widget.sysmonitor_tab.write(contents)

    def get_detection_stats(self, sentence):
        line = sentence.split(",")
        freqs = []
        for i in range(8):
            try:
                freqs.append(float(line[i+1].strip("'").strip()))
            except ValueError:
                freqs.append(0)

        before_15 = datetime.strftime(datetime.now() - timedelta(minutes=15), "%Y-%m-%d %H:%M:%S")
        before_60 = datetime.strftime(datetime.now() - timedelta(minutes=60), "%Y-%m-%d %H:%M:%S")
        before_24 = datetime.strftime(datetime.now() - timedelta(days=1), "%Y-%m-%d %H:%M:%S")
        d_in_15 = self.__db.fetchall(f"select antenne_id, count(id) from detections where date_arrivee > '{before_15}' group by antenne_id order by antenne_id;")
        d_in_60 = self.__db.fetchall(f"select antenne_id, count(id) from detections where date_arrivee > '{before_60}' group by antenne_id order by antenne_id;")
        d_in_24 = self.__db.fetchall(f"select antenne_id, count(id) from detections where date_arrivee > '{before_24}' group by antenne_id order by antenne_id;")

        antenna_indices = [x+1 for x in range(8)]
        contents = [[0]*8, [0]*8, [0]*8, [0]*8]
        for x, y in enumerate(freqs):
            contents[0][x] = y
        if d_in_15:
            for (x, y) in d_in_15:
                contents[1][x-1] = y
        if d_in_60:
            for (x, y) in d_in_60:
                contents[2][x-1] = y
        if d_in_24:
            for (x, y) in d_in_24:
                contents[3][x-1] = y
        return(contents)


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


class MysqlConnect(object):

    def __init__(self, usr, pwd, host='localhost', db='antavia_cro', port=3306):
        self.__usr = usr
        self.__pwd = pwd
        self.__host = host
        self.__dbname = db
        self.__port = int(port)
        self.__db = None
        self.__cursor = None
        self.connect()

    def connect(self):
        try:
            self.__db = pymysql.connect(host=self.__host, user=self.__usr, passwd=self.__pwd, db=self.__dbname, port=self.__port)
            self.__cursor = self.__db.cursor()
            if self.__db.open:
                logging.info(f"Successfully established connection to {self.__dbname} on {self.__host}")
            else:
                logging.error(f"No connexion to {self.__dbname} on {self.__host}")
        except pymysql.OperationalError:
            logging.exception(f"Failed to connect to {self.__host}")

    def _reconnect(func):
        @wraps(func)
        def rec(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)
                return (result)
            except pms.err.OperationalError as e:
                logging.exception("Exception occurred (pymysql)")
                if e[0] == 2013:
                    self.connect()
                    result = func(self, *args, **kwargs)
                    return result
        return rec

    @_reconnect
    def fetchall(self, sql):
        res = None
        try:
            self.__cursor.execute(sql)
            res = self.__cursor.fetchall()
            return res
        except Exception as ex:
            logging.exception(ex)

    @_reconnect
    def fetchone(self, sql):
        res = None
        try:
            self.__cursor.execute(sql)
            res = self.__cursor.fetchone()
            return res
        except Exception as ex:
            logging.exception(ex)