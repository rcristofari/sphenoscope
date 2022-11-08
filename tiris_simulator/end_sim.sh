# Kill all runnign socat/sim processes
for pid in `ps aux | grep socat | sed -E "s/[ ]+/ /g" | cut -f 2 -d " "` ; do kill -9 $pid ; done
for pid in `ps aux | grep comportsim | sed -E "s/[ ]+/ /g" | cut -f 2 -d " "` ; do kill -9 $pid ; done

