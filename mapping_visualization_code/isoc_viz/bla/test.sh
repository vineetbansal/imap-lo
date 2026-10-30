#!/bin/sh
#

a=0
while read line
  do 
  gamma=$line;
  echo $gamma;
  a=`expr $a + 1`;
  echo $a;
done < gam2.txt

exit
exit status 0
