TEST_LEN=600
PORT="10299"
INFILE="noise_4ch.raw"
killall xsim xgdb xrun
xrun -l #makes things more stable for some weird reason
sox -n -c 4 -b 32 -r 16000 -e signed-integer $INFILE synth $TEST_LEN whitenoise vol 1.0
# xkill
# killall xscope_host_endpoint
make
xrun --xscope-port localhost:"$PORT" main.xe & 
# xsim --xscope "-realtime localhost:$PORT" main.xe &
sleep 2
time ./host/xscope_host_endpoint $INFILE $PORT
diff $INFILE "$INFILE"2

if [ $? -eq 0 ]
then
  echo "PASS: Binary files identical."
else
  echo "Diff Error" >&2
fi
killall xsim xgdb xrun
