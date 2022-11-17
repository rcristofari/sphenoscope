import sys, logging, signal, pymysql, re, os, json
from functools import wraps
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from MainGui import MainGui
import SystemMonitorPanel

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
        QtCore.QCoreApplication.setApplicationName('sphenoscope')

        # Load MQTT and SQL parameters from conf file:
        self.alarm_file = "./conf/alarms.json"
        self.network_file = "./conf/network.json"
        self.settings_file = "./conf/settings.json"

        self.network_conf = self.load_configuration_json(self.network_file)
        self.settings = self.load_settings_json(self.settings_file)

        # Status bar message:
        self.status_message = ""

        #--------------------------------------------------------------------------------------------------------------#
        # Initialize the MQTT client system
        self.client = mqtt.Client()
        self.client.enable_logger(mqtt_log)
        self.client.on_log = self.on_log
        try:
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.connect_to_mqtt_server(self.network_conf["MQTT"]["host"], int(self.network_conf["MQTT"]["port"]))
            self.status_message += "MQTT data stream established"
        except ConnectionRefusedError:
            print("MQTT not connected.")
            self.status_message += "FAILED TO CONNECT TO MQTT DATA STREAM"

        #--------------------------------------------------------------------------------------------------------------#
        # Initialize the MySQL database connection:
        print(f"Attempting connexion as {self.network_conf['MYSQL']['usr']}")
        self.db = MysqlConnect(usr=self.network_conf["MYSQL"]["usr"], pwd=self.network_conf["MYSQL"]["pwd"], db=self.network_conf["MYSQL"]["db"], host=self.network_conf["MYSQL"]["host"], port=self.network_conf["MYSQL"]["port"], legacy=self.settings["legacy"])
        status = self.db.connect()
        if status == 0:
            self.mysql_connected = True
            self.status_message += " | MySQL connexion established"
        else:
            self.mysql_connected = False
            self.status_message += " | MYSQL NOT CONNECTED"

        # Define the place indices (relative to GUI frames)
        self.gates = {"Bretelle Sud": 2,
                      "Autoroute": 0,
                      "Prado": 1,
                      "Manchoduc": 3}
        self.gate_order = {0: "Autoroute",
                           1: "Prado",
                           2: "Bretelle Sud",
                           3: "Manchoduc"}

        #Antenna order in the DB (can be loaded directly from DB at init. too)
        self.antennas = {1: "Bretelle Sud Mer",
                         2: "Bretelle Sud Terre",
                         3: "Autoroute Mer",
                         4: "Autoroute Terre",
                         5: "Manchoduc Mer",
                         6: "Manchoduc Terre",
                         7: "Prado Mer",
                         8: "Prado Terre"}

        # Get alarms in use from MySql:
        all_alarms = self.db.get_alarms() if self.mysql_connected else []
        self.db_alarm_names, self.db_alarm_descriptions = [], []
        if self.mysql_connected:
            for a in all_alarms:
                self.db_alarm_names.append(a[1])
                self.db_alarm_descriptions.append(a[2])
        self.alarms = dict(zip(self.db_alarm_names, self.db_alarm_descriptions))
        self.alarm_conf = self.load_alarms_json(self.alarm_file, all_alarms)

        self.window = MainGui(self)

        # We retrieve the past <= 300 detections, add them to the processing queue
        # and store their actual number (always 300 normally)

        self.history_length = self.get_history_from_mysql() if self.mysql_connected else 0

    def app_is_exiting(self):
        if self.client.is_connected():
            self.client.disconnect()
            self.client.loop_stop()

    def _sigint_handler(self, signal, frame):
        print("Keyboard interrupt caught, running close handlers...")
        self.app_is_exiting()
        sys.exit(0)

    #------------------------------------------------------------------------------------------------------------------#
    # LOAD CONFIGURATION FILES
    def load_configuration_json(self, jsonfile):
        with open(jsonfile, 'r') as f:
            network_conf = json.load(f)
            return network_conf

    def load_alarms_json(self, jsonfile, all_alarms):
        # This function reads in alarms from the json file,
        # and fills in the missing data with default values
        with open(jsonfile, 'r') as f:
            alarm_conf = json.load(f)
            for item in alarm_conf:
                if "color" not in alarm_conf[item] or not alarm_conf[item]["color"] or not re.search(r'^#[0-9a-fA-F]{6}$', alarm_conf[item]["color"]):
                    alarm_conf[item]["color"] = "#999999"
                if "sound" not in alarm_conf[item] or not alarm_conf[item]["sound"] or not os.path.isfile(alarm_conf[item]["sound"]):
                    alarm_conf[item]["sound"] = "/home/robin/sphenoscope/resources/ding.wav"
        for a in all_alarms:
            if a[1] not in alarm_conf:
                alarm_conf[a[1]] = {"color": "#999999", "sound": "/home/robin/sphenoscope/resources/ding.wav"}
        updated_json = json.dumps(alarm_conf, indent=4)
        with open(jsonfile, 'w') as f:
            f.write(updated_json)
        return alarm_conf

    def load_settings_json(self, jsonfile):
        # This function loads the general settings from the json file
        with open(jsonfile, 'r') as f:
            settings = json.load(f)
            if not settings["legacy"]:
                settings["legacy"] = False
            else:
                try:
                    settings["legacy"] = False if settings["legacy"].upper() in ("FALSE", "F") else True
                except AttributeError:
                    pass
        updated_json = json.dumps(settings, indent=4)
        with open(jsonfile, 'w') as f:
            f.write(updated_json)
        return settings

    #------------------------------------------------------------------------------------------------------------------#
    # HANDLE MQTT CONNEXION
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

    def reset_mqtt_connexion(self):
        self.disconnect_from_mqtt_server()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("Connection succeeded.")
        elif rc > 0:
            if rc < len(mqtt_rc_codes):
                log.warning("Connection failed with error: %s", mqtt_rc_codes[rc])
            else:
                log.warning("Connection failed with unknown error %d", rc)
        client.subscribe(self.network_conf["MQTT"]["detection_chanel"])
        client.subscribe(self.network_conf["MQTT"]["status_chanel"])
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
            # We only refresh things if the monitor tab is active, to avoid slowing down the application
            #print(f"Current tab pointer: {self.window.tab_widget.tabs.currentWidget()}")
            if isinstance(self.window.tab_widget.tabs.currentWidget(), SystemMonitorPanel.SystemMonitorPanel):
                # we also refresh detection stats
                contents = self.get_detection_stats(sentence)
                # we forward the whole data to the monitor tab
                self.window.tab_widget.sysmonitor_tab.write(contents)

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

    #------------------------------------------------------------------------------------------------------------------#
    # HANDLE MYSQL CONNEXION

    def reset_mysql_connexion(self):
        if self.db:
            self.db.disconnect()
        self.db = MysqlConnect(usr=self.network_conf["MYSQL"]["usr"], pwd=self.network_conf["MYSQL"]["pwd"], db=self.network_conf["MYSQL"]["db"], host=self.network_conf["MYSQL"]["host"], port=self.network_conf["MYSQL"]["port"], legacy=self.settings["legacy"])

    def get_detection_stats(self, sentence):
        line = sentence.split(",")
        freqs = []
        for i in range(8):
            try:
                freqs.append(float(line[i+1].strip("'").strip()))
            except ValueError:
                freqs.append(0)
        d_in_15, d_in_60, d_in_24 = self.db.get_detection_counts()
        #antenna_indices = [x+1 for x in range(8)]
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

    def get_history_from_mysql(self):
        # This function gets the last 300 detections from the mysql database
        result = self.db.get_detection_history()
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

        return len(result) if result else 0


## HANDLE FAILURE TO CONNECT - SEND MESSAGE AND PROCEED W/O CRASHING
class MysqlConnect(object):

    def __init__(self, usr, pwd, host, db, port, legacy):
        self.legacy_mode = legacy
        self.__usr = usr
        self.__pwd = pwd
        self.__host = host
        self.dbname = db
        self.__port = int(port)
        self.db = None
        self.__cursor = None

    def connect(self):
        try:
            self.db = pymysql.connect(host=self.__host, user=self.__usr, passwd=self.__pwd, db=self.dbname, port=self.__port)
        except pymysql.err.OperationalError:
            logging.exception(f"Failed to connect to {self.__host}")
            return 1

        if self.db.open:
            self.__cursor = self.db.cursor()
            logging.info(f"Successfully established connection to {self.dbname} on {self.__host}")
            return 0
        else:
            logging.error(f"No connexion to {self.dbname} on {self.__host}")
            return 1

    def disconnect(self):
        if self.db.open:
            self.db.close()

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

    def get_alarms(self):
        if self.legacy_mode is False:
            query = "select * from alarms;"
        else:
            query = "select row_number() over(order by class) as id, class, description from (select distinct(son_suivi) as class, 'unknown' as description from animaux where son_suivi is not null and son_suivi != '') as alarms;"
        result = self.fetchall(query)
        return result

    def get_detection_history(self):
        if self.legacy_mode is False:
            query = "select d.description, d.dtime, b.rfid, b.name, b.rfid_date, b.sex, b.alarm from birds b, (select a.description, d.dtime, d.rfid from detections d, antennas a where d.antenna_id = a.id order by d.id desc LIMIT 300) d where b.rfid = d.rfid;"
        else:
            query = "select d.description, d.date_arrivee, a.identifiant_transpondeur, a.nom, a.date_transpondage, a.sexe, a.son_suivi from animaux a, (select a.description, d.date_arrivee, d.animaux_id from detections d, antennes a where d.antenne_id = a.id order by d.date_arrivee desc limit 300) d where a.id = d.animaux_id;"
        result = self.fetchall(query)
        return result

    def get_detection_counts(self):
        before_15 = datetime.strftime(datetime.now() - timedelta(minutes=15), "%Y-%m-%d %H:%M:%S")
        before_60 = datetime.strftime(datetime.now() - timedelta(minutes=60), "%Y-%m-%d %H:%M:%S")
        before_24 = datetime.strftime(datetime.now() - timedelta(days=1), "%Y-%m-%d %H:%M:%S")
        if self.legacy_mode is False:
            d_in_15 = self.fetchall(f"select antenna_id, count(rfid) from (select * from detections order by id desc limit 5000) as d where dtime > '{before_15}' group by antenna_id order by antenna_id;")
            d_in_60 = self.fetchall(f"select antenna_id, count(rfid) from (select * from detections order by id desc limit 5000) as d where dtime > '{before_60}' group by antenna_id order by antenna_id;")
            d_in_24 = self.fetchall(f"select antenna_id, count(rfid) from (select * from detections order by id desc limit 5000) as d where dtime > '{before_24}' group by antenna_id order by antenna_id;")
        else:
            d_in_15 = self.fetchall(f"select antenne_id, count(animaux_id) from (select * from detections order by id desc limit 5000) as d where date_arrivee > '{before_15}' group by antenne_id order by antenne_id;")
            d_in_60 = self.fetchall(f"select antenne_id, count(animaux_id) from (select * from detections order by id desc limit 5000) as d where date_arrivee > '{before_60}' group by antenne_id order by antenne_id;")
            d_in_24 = self.fetchall(f"select antenne_id, count(animaux_id) from (select * from detections order by id desc limit 5000) as d where date_arrivee > '{before_24}' group by antenne_id order by antenne_id;")
        return (d_in_15, d_in_60, d_in_24)