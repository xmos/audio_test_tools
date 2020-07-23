TEST_LEN=3
PORT="12903"
INFILE="noise_4ch.raw"
sox -n -c 4 -b 32 -r 16000 -e signed-integer $INFILE synth $TEST_LEN whitenoise vol 1.0
# xkill
# killall xscope_host_endpoint
make
xrun --xscope-port localhost:"$PORT" main.xe & 
# xsim --xscope "-realtime localhost:$PORT" main.xe &
sleep 1
time ./host/xscope_host_endpoint $INFILE $PORT
diff $INFILE "$INFILE"2

if [ $? -eq 0 ]
then
  echo "Pass: Binary files identical."
else
  echo "Diff Error" >&2
fi
killall xsim xgdb xrun
