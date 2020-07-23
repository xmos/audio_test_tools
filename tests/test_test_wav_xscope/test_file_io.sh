TEST_LEN=0.1
INFILE="noise_4ch_60s.raw"
sox -n -c 4 -b 32 -r 16000 -e signed-integer $INFILE synth $TEST_LEN whitenoise vol 1.0
# xkill
# killall xscope_host_endpoint
make
# xrun --xscope-port localhost:10234 main.xe & 
xsim --xscope "-realtime localhost:10234" main.xe &
sleep 1
./host/xscope_host_endpoint $INFILE
diff $INFILE "$INFILE"2

if [ $? -eq 0 ]
then
  echo "Pass: Binary files identical."
  exit 0
else
  echo "Error: Binary files differ" >&2
  exit 1
fi
