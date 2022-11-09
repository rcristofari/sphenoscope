from MainApp import MysqlConnect

connexion = MysqlConnect(usr="root", pwd="", db="antavia_cro_new", host="127.0.01", port=3306, legacy=False)

birds = connexion.fetchall("SELECT rfid, sex FROM birds;")

this_bird = birds[1000]
print(this_bird[0])

detections = connexion.fetchall(f"SELECT * FROM detections WHERE rfid = '{this_bird[0]}';")
print(detections)

select id, rfid, antenna_id, timediff(dtime, prev_dtime) as delta from
(select * , LAG(dtime, 1) OVER (PARTITION BY rfid ORDER BY id) as prev_dtime from
(select * from detections limit 5000) as s)
 as lagged;