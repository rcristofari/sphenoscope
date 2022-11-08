
# This script handles two "antennas" (Mer and Terre) in order to be able to fake real penguin passing from one antenna to the next
import time
import random
import serial
import sys

port_0 = str(sys.argv[1])
port_1 = str(sys.argv[2])

prob_penguin = 0.05
prob_penguin_recatch = 0.8
prob_penguin_stays = 0.5
prob_invalid = 0.01
Hz = 1

portWrite = [serial.Serial(port_0, baudrate=9600, timeout=1.0), serial.Serial(port_1, baudrate=9600, timeout=1.0)]

this_antenna = 0
prev_B = [False, False]
already_detected = False
next_move = "leaves"

tps = []
with open("/home/robin/Penguins/antavia_fixed/TIRIS_SIM/rfid_list", 'r') as tpin:
	for line in tpin:
		tps.append(line.strip('\n'))

random.shuffle(tps)
this_tp = tps[0]

delay = 1/(Hz*2)
prev_time = time.time()

while True:
	if time.time() - prev_time < delay:
		pass

	else:
		prev_time = time.time()
		# do we have a detection ?
		if random.random() <= prob_penguin:
			# We detect a penguin.
			first_seen_on = this_antenna

			# What does it do next ?
			if not already_detected:
				if random.random() <= prob_penguin_stays:
					next_move = "stays"
				elif random.random() <= prob_penguin_recatch:
					next_move = "moves"
					already_detected = True
				else:
					next_move = "hangs"
			else:
				if random.random() <= prob_penguin_stays:
					next_move = "stays"
				else:
					next_move = "leaves"

		if next_move == "stays" and this_antenna == first_seen_on:
			portWrite[this_antenna].write(bytes("L" + this_tp + "\n\n", "UTF-8"))
			if random.random() <= prob_penguin_stays:
				next_move = "stays"
			else:
				if random.random() <= prob_penguin_recatch and not already_detected:
					next_move = "moves"
					already_detected = True
				else:
					next_move = "hangs"

		elif next_move == "moves" and this_antenna != first_seen_on:
			portWrite[this_antenna].write(bytes("L" + this_tp + "\n\n", "UTF-8"))
			if random.random() <= prob_penguin_stays:
				next_move = "stays"
			else:
				next_move = "leaves"

		elif next_move == "hangs":
			if random.random() <= prob_invalid:
				portWrite[this_antenna].write(b"LI\n\n")
			else:
				portWrite[this_antenna].write(b"L\n\n")
			if random.random() <= prob_penguin_recatch:
				next_move = "moves"
			elif random.random() <= prob_penguin_stays:
				next_move = "stays"


		elif next_move == "leaves":
			random.shuffle(tps)
			this_tp = tps[0]
			if random.random() <= prob_invalid:
				portWrite[this_antenna].write(b"LI\n\n")
			else:
				portWrite[this_antenna].write(b"L\n\n")

		if not prev_B[this_antenna]:
			portWrite[this_antenna].write(b"B\n\n")
			prev_B[this_antenna] = True
		else:
			prev_B[this_antenna] = False

		this_antenna = abs(this_antenna - 1)
