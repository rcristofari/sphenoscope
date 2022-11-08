# Kill all runnign socat/sim processes
for pid in `ps aux | grep socat | sed -E "s/[ ]+/ /g" | cut -f 2 -d " "` ; do kill -9 $pid ; done
for pid in `ps aux | grep comportsim | sed -E "s/[ ]+/ /g" | cut -f 2 -d " "` ; do kill -9 $pid ; done

# Set up the virtual ports
socat -d -d pty,raw,echo=0,link=/dev/00 pty,raw,echo=0,link=/dev/tx00 &
socat -d -d pty,raw,echo=0,link=/dev/01 pty,raw,echo=0,link=/dev/tx01 &
socat -d -d pty,raw,echo=0,link=/dev/02 pty,raw,echo=0,link=/dev/tx02 &
socat -d -d pty,raw,echo=0,link=/dev/03 pty,raw,echo=0,link=/dev/tx03 &
socat -d -d pty,raw,echo=0,link=/dev/04 pty,raw,echo=0,link=/dev/tx04 &
socat -d -d pty,raw,echo=0,link=/dev/05 pty,raw,echo=0,link=/dev/tx05 &
socat -d -d pty,raw,echo=0,link=/dev/06 pty,raw,echo=0,link=/dev/tx06 &
socat -d -d pty,raw,echo=0,link=/dev/07 pty,raw,echo=0,link=/dev/tx07 &

# Set Python talking to the transmit ports
python3 comportsim.py "/dev/tx00" "/dev/tx01" &
python3 comportsim.py "/dev/tx02" "/dev/tx03" &
python3 comportsim.py "/dev/tx04" "/dev/tx05" &
python3 comportsim.py "/dev/tx06" "/dev/tx07" &
