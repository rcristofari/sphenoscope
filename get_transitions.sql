select id, rfid, prev_dtime as start, dtime as end, 
case
when mod(antenna_id, 2) = 0 and mod(prev_antenna_id, 2) = 0 then "IS_IN"
when mod(antenna_id, 2) <> 0 and mod(prev_antenna_id, 2) <> 0 then "IS_OUT"
when mod(antenna_id, 2) = 0 and mod(prev_antenna_id, 2) <> 0 and antenna_id - prev_antenna_id = 1 then "GOES_OUT"
when mod(antenna_id, 2) <> 0 and mod(prev_antenna_id, 2) = 0 and prev_antenna_id - antenna_id = 1 then "COMES_IN"
else "UNRESOLVED"
end as movement,
if(timediff(dtime, prev_dtime) < "00:30:00", "SHORT", if(timediff(dtime, prev_dtime) > "00:30:00", "LONG", "UNRESOLVED")) as duration,
datediff(dtime, prev_dtime) as days
from 
(select * , LAG(dtime, 1) OVER (PARTITION BY rfid ORDER BY dtime) as prev_dtime, LAG(antenna_id, 1) OVER (PARTITION BY rfid ORDER BY dtime) as prev_antenna_id from 
(select * from detections) as s)
 as lagged;
