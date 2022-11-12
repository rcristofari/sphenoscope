## SPHENOSCOPE
***
The **SPHENOSCOPE** is a visualisation interface for RFID data, designed to the King penguin monitoring system in the Baie du Marin on Possession Island, Crozet Archipelago. It is essentially a custom MQTT client, with functions to ring alarms for specific birds, monitor the electronic system behind it, and display information about the state of the colony.
***
#### Installation
You simply need to clone the folder into any directory, and ensure you have all dependencies installed. Beyond the standard libraries, you need a local install of the Qt5 framework, including the `pyqt5` Python3 connector, the `pymysql` and `paho.mqtt.client` packages (MySQL and MQTT connectors), the `preferredsoundplayer` package for playing alarms.
***
#### Running & Usage
The Sphenoscope is run simply from the command line as `python3 sphenoscope_main.py`. It can also be started using the provided desktop file.

You will need to edit the configuration to match your network settings, either direcly in the Spehnoscope (`Edit > Settings`) or in the `./conf/network.json` file (the settings should be self-explanatory). If using the legacy database structure (2013-2022 version), you can set the "legacy mode" toggle in `Edit > Settings`, but that should not normally occur at all.

Alarm preferences can also be edited directly from the Edit menu. Note that alarm colors and sound preferences are local to the computer running the Sphenoscope, they can be different on each computer if you wish.

You can use the **mute** buttons to silence a passage for a short duration (e.g. if a penguin is sitting on the antenna and driving you mad). The timeout can be set in `Edit > Settings`.
***
*The **Sphenoscope** is part of the 2022-2023 update of the Antavia system in Crozet, featuring a new suite of tools for acquisition of RFID penguin monitoring data. 
For the backend data collection and recording tools, please see https://github.com/rcristofari/rfid. For migration tools to initialize the database from the legacy version, see https://github.com/rcristofari/antavia_db_v2. Finally, the database can be explored and managed using the dedicated **SPHENOTRON** software, available here: https://github.com/g-bardon/Sphenotron_Python (work in progress).*
***
***Important note:** in this new release, the graphical display of RFID detections (and sound alarms) are entirely isolated from the parsing and storage of the detections themselves. It is completely fine to close / restart the Sphenoscope, it does not stop the actual data recording.*
