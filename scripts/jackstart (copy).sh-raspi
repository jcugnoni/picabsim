#!/bin/bash

## Stop the ntp service
sudo service ntp stop

## Stop the triggerhappy service
sudo service triggerhappy stop

## Stop the dbus service. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
#sudo service dbus stop

## Stop the console-kit-daemon service. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
sudo killall console-kit-daemon

## Stop the polkitd service. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
sudo killall polkitd

## Only needed when Jack2 is compiled with D-Bus support (Jack2 in the AutoStatic RPi audio repo is compiled without D-Bus support)
#export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket

## Remount /dev/shm to prevent memory allocation errors
sudo mount -o remount,size=128M /dev/shm

## Kill the usespace gnome virtual filesystem daemon. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
sudo killall gvfsd

## Kill the userspace D-Bus daemon. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
#sudo killall dbus-daemon

## Kill the userspace dbus-launch daemon. Warning: this can cause unpredictable behaviour when running a desktop environment on the RPi
#sudo killall dbus-launch

## Uncomment if you'd like to disable the network adapter completely
#echo -n “1-1.1:1.0” | sudo tee /sys/bus/usb/drivers/smsc95xx/unbind
## In case the above line doesn't work try the following
#echo -n “1-1.1” | sudo tee /sys/bus/usb/drivers/usb/unbind

## Set the CPU scaling governor to performance
echo -n performance | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

## And finally start JACK
#jackd -P70 -p16 -t2000 -d alsa -dhw:UA25 -p 128 -n 3 -r 44100 -s &
sudo service triggerhappy stop
sudo service ntp stop
#nohup service dbus stop
sudo killall console-kit-daemon
sudo killall polkitd
sudo killall gvfsd
#sudo  killall dbus-daemon
#sudo  killall dbus-launch

# fix for dbus enabled jackd...
export DISPLAY=:0

# dbus-launch started, DBUS_SESSION_BUS_ADDRESS exported:
export `dbus-launch | grep ADDRESS` 

# dbus-launch started, DBUS_SESSION_BUS_PID exported
export `dbus-launch | grep PID` 
rm nohup.out
#nohup jackd -P84 -p16 -t2000 -d alsa -dhw:CODEC -X seq -p 128 -n 3 -r 32000 -s nohup_jackd.out 2>&1 &
nohup jackd -P84 -p16 -t2000 -d alsa -dhw:CODEC -X seq -p 128 -n 2 -r 32000 -s nohup_jackd.out 2>&1 &
#nohup a2j &

exit
