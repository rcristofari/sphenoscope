 select transitions.*, if(birds.sex is not null, birds.sex, "I") as sex from 
	(select 
		 id, 
		 rfid, 
		 prev_dtime as start, 
		 dtime as end,
		 year(dtime) as ystart,
		 year(prev_dtime) as yend,
		 if(dtime > concat(year(prev_dtime), "-09-01"), 
			year(prev_dtime)+1, 
            year(prev_dtime)
            ) as season,
		 dayofyear(prev_dtime) as dstart, 
		 dayofyear(dtime) as dend,
		 datediff(prev_dtime, "1997-01-01") as abs_start_since_epoch,
		 datediff(dtime, "1997-01-01") as abs_end_since_epoch,
		 if(prev_dtime > concat(year(prev_dtime), "-09-01"), 
			dayofyear(prev_dtime) - dayofyear(concat(year(prev_dtime), "-09-01")), 
            dayofyear(prev_dtime) + (dayofyear(concat(year(prev_dtime)-1, "-12-31")) - dayofyear(concat(year(prev_dtime)-1, "-09-01")))
			) as dstart_season,
		 if(dtime > concat(year(dtime), "-09-01"), 
			dayofyear(dtime) - dayofyear(concat(year(dtime), "-09-01")), 
            dayofyear(dtime) + (dayofyear(concat(year(dtime)-1, "-12-31")) - dayofyear(concat(year(dtime)-1, "-09-01")))
            ) as dend_season,
		case
			when mod(antenna_id, 2) = 0 and mod(prev_antenna_id, 2) = 0 then "IS_IN"
			when mod(antenna_id, 2) <> 0 and mod(prev_antenna_id, 2) <> 0 then "IS_OUT"
			when mod(antenna_id, 2) = 0 and mod(prev_antenna_id, 2) <> 0 and antenna_id - prev_antenna_id = 1 then "GOES_OUT"
			when mod(antenna_id, 2) <> 0 and mod(prev_antenna_id, 2) = 0 and prev_antenna_id - antenna_id = 1 then "COMES_IN"
			else "UNRESOLVED"
			end as movement,
		if(timediff(dtime, prev_dtime) < "00:30:00", "SHORT", if(timediff(dtime, prev_dtime) > "00:30:00", "LONG", "UNRESOLVED")) as duration,
		datediff(dtime, prev_dtime) as days
	from (
		select * , 
			LAG(dtime, 1) OVER (PARTITION BY rfid ORDER BY dtime) as prev_dtime, 
            LAG(antenna_id, 1) OVER (PARTITION BY rfid ORDER BY dtime) as prev_antenna_id 
		from (
			select * from detections
			) as s
		) as lagged
	) as transitions, birds 
where transitions.rfid = birds.rfid 
and duration != "UNRESOLVED" 
and movement != "UNRESOLVED" 
and !(movement = "IS_IN" and days > 80)
and !(movement in ("COMES_IN", "GOES_OUT") and duration = "LONG");
