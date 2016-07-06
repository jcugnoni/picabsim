# auto start py-jconv-http.py if in 1st shell
if [ `tty` == '/dev/tty1' ]; then
  echo "Running JConvolver interface"
  /home/pi/jackstart.sh
  sleep 5
  /home/pi/py-jconv-http.py &
fi

