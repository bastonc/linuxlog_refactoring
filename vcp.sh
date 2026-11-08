#!/bin/bash
clear
virtual_port='ttyS20'
string_port=`dmesg | grep 'ttyS*' | grep 'at I/O'|awk '{print $4}'`
#string_port=`dmesg | grep 'ttyS*' | grep 'at I/O'`
#tty_string_1=${string_port%'at'*}
#tty_string_2=${tty_string_1#*: }

sudo -v
clear
sudo socat pty,raw,echo=0,link=/dev/$virtual_port pty,raw,echo=0,link=/dev/$string_port &
if [ $? -ne 0 ]
then
echo "ERROR"
exit 1
else
  echo "----------- Virtual COM port for LinuxLog ------------"
  echo -en " \n\n   You physical COM port: \t$string_port\n"
  echo -en "   LinuxLog CAT port name:  \t/dev/ttyS20 \n \n"
  echo -e "             $string_port <-COM-> $virtual_port \n \n"
  echo "------------------------------------------------------"
  echo 'OK'
  sleep 2
  sudo chmod 777 /dev/ttyS20
  echo 'READY'
fi




