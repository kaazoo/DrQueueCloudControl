#!/bin/bash

while true; do
  NOW=`date +%Y-%m-%d-%H:%M:%S`
  python2.7 dqcc.py &>$NOW.log
  NOW=`date`
  echo "DQCC died at $NOW. Restarting ..."
  echo "DQCC died at $NOW" | mail -s "DQCC died and will be restarted in 5 seconds" root
  sleep 5
done

