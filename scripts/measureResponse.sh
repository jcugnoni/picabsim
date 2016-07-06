ecasound -f:16,2,32000 -a:1 -i jack,system,capture -o capture.wav -a:2 -i ../wav/Sweep-44100-16-M-8.0s.wav -o jack,system -t 12
