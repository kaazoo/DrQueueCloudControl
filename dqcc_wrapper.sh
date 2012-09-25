#!/bin/bash

i=1
while [ 1 = 1 ]
do
  ruby dqcc_daemon.rb run
  sleep 5
  echo ""
  echo ""
  echo "DQCC died $i time(s). Restarting ..."
  echo ""
  let i=$i+1
done